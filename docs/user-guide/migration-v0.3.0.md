# v0.3.0 마이그레이션 가이드 (Partial-coverage 재설계)

v0.3.0은 **BREAKING** 릴리스입니다. 함수명이 전체 시리즈를 시사하지만 실제로는 단일
ECOS 항목만 반환하던 함수들([#56](https://github.com/choo121600/ecos-reader/issues/56))이
모두 **전체 시리즈 long-format + `sub_category` 선택**으로 재설계되었습니다.

## 한눈에 보기

| 변경 | 내용 |
|------|------|
| 기본 반환 | 단일 시계열(`date, value, unit`) → **전체 분류 long-format**(`date, category_value, value, unit`) |
| 단일 시계열 | `sub_category=` 인자로 명시 선택 |
| `EcosPartialCoverageWarning` | **제거됨** (더 이상 발생하지 않음) |

`sub_category` 미지정 시 long-format은 통계표의 **모든 항목(총계·소계 포함)** 을 담습니다.
계층형 통계표는 `category_value`를 단순 합산하면 중복 집계되므로, 특정 시계열은
`sub_category`로 선택하세요. 분류명이 길거나 중복될 수 있어 안정적 선택에는 `item_code`를
권장합니다.

## 경고 클래스 제거

`ecos.EcosPartialCoverageWarning` 및 내부 `ecos.indicators._deprecations` 모듈이
제거되었습니다([#64](https://github.com/choo121600/ecos-reader/issues/64)). 아래처럼 경고를
억제하던 코드는 더 이상 필요하지 않으므로 삭제하세요.

```python
# 제거: v0.3.0부터 불필요
import warnings, ecos
warnings.simplefilter("ignore", ecos.EcosPartialCoverageWarning)  # AttributeError
```

## 함수별 변경

### 성장 (#59)

```python
# Before (v0.2.x): 농림어업 단일 시계열 + 경고
df = ecos.get_gdp_by_industry()

# After (v0.3.0): 전체 산업 long-format
df = ecos.get_gdp_by_industry()                      # 전체 산업
df = ecos.get_gdp_by_industry(sub_category="제조업")  # 단일 산업
```

`get_gdp_by_expenditure`, `get_gdp_deflator_by_industry`도 동일하게 `sub_category`를 지원합니다.

### 주식 (#60)

```python
# get_stock_index(monthly): 1010000(회사수, 오류) → 1070000(KOSPI 종가, 지수)로 정정
df = ecos.get_stock_index(frequency="monthly")                         # KOSPI 지수
df = ecos.get_stock_index(frequency="monthly", sub_category="KOSPI_시가총액")

# get_investor_trading: 기타법인 매도 단일 → 투자자별 전체
df = ecos.get_investor_trading()                                       # 투자자별 순매수 거래대금
df = ecos.get_investor_trading(action="매수", metric="거래량")
df = ecos.get_investor_trading(sub_category="S22CC")                   # 외국인 순매수
```

### 물가 (#61)

```python
# get_cpi_monthly: 총지수 단일 → 전체 COICOP 품목
df = ecos.get_cpi_monthly()                          # 전체 품목 long-format
df = ecos.get_cpi_monthly(sub_category="총지수")      # 기존 동작
df = ecos.get_cpi_monthly(sub_category="A01101")     # 쌀
```

특수분류(상품/서비스/근원 등)는 기존 `get_cpi_by_category`를 그대로 사용합니다.

### 통화 (#62)

```python
# get_household_lending_detail: 단일 항목 → 용도×기관 전체 분류
df = ecos.get_household_lending_detail()                       # 전체 분류 long-format
df = ecos.get_household_lending_detail(sub_category="11100A0")  # 주택관련대출-예금취급기관
```

### 채권 (#63)

```python
# get_bond_yield: 합계 단일 → 채권종류/시장 전체 분류 + measure 선택
df = ecos.get_bond_yield()                                    # 종류별 거래대금 전체
df = ecos.get_bond_yield(sub_category="국채")                  # 국채만
df = ecos.get_bond_yield(bond_type="시장별", measure="거래량")  # 시장별 거래량
df = ecos.get_bond_yield(bond_type="시장별", sub_category="0202")  # 국채전문 유통시장
```

!!! warning "위치 인자 주의"
    재설계된 함수들은 새 인자(`sub_category`, `action`, `measure` 등)가 `start_date`
    앞에 추가되었습니다. `start_date`/`end_date`는 **키워드 인자**로 넘기세요.
    ```python
    ecos.get_investor_trading(start_date="202401", end_date="202412")  # OK
    ecos.get_investor_trading("202401", "202412")                      # 잘못된 바인딩
    ```

## 기존 단일 항목 동작이 꼭 필요하다면

`sub_category`로 동일 항목을 선택하거나, 저수준 API로 직접 조회할 수 있습니다.

```python
client = ecos.EcosClient()
df = client.get_statistic_search(
    stat_code="200Y104", period="Q", start_date="2024Q1", end_date="2024Q4",
    item_code1="1101",  # 농림어업
)
```
