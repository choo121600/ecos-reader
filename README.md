# ecos-reader
**한국은행 ECOS Open API Python 클라이언트**

한국은행 ECOS Open API를 Python에서 쉽고 일관된 방식으로 사용할 수 있는 라이브러리입니다.


## 설치

```bash
pip install ecos-reader
```

또는 개발 버전 설치:

```bash
git clone https://github.com/choo121600/ecos-reader.git
cd ecos-reader
pip install -e ".[dev]"
```

## API 키 설정

ECOS API를 사용하려면 한국은행에서 발급받은 API 키가 필요합니다.

[API 키 신청하기](https://ecos.bok.or.kr/api/)

### 방법 1: 환경 변수 (권장)

```bash
export ECOS_API_KEY="your_api_key"
```

또는 `.env` 파일 생성:

```
ECOS_API_KEY=your_api_key
```

> 참고: v0.1.0부터는 라이브러리 import 시점에 `.env`를 자동으로 로드하지 않습니다.
> `.env`를 사용하려면 아래처럼 `ecos.load_env()`를 한 번 호출하세요.

```python
import ecos

ecos.load_env()  # .env 로드 (명시적)
```

### 방법 2: 코드에서 직접 설정

```python
import ecos

ecos.set_api_key("your_api_key")
```

## 빠른 시작

```python
import ecos

# 한국은행 기준금리 조회
df = ecos.get_base_rate()
print(df)
#         date  value unit
# 0 2024-01-01   3.50    %
# 1 2024-02-01   3.50    %
# ...

# 소비자물가지수(CPI) 조회
df = ecos.get_cpi(start_date="202301", end_date="202312")
print(df)

# 국고채 수익률 조회
df = ecos.get_treasury_yield(maturity="10Y")
print(df)

# GDP 조회
df = ecos.get_gdp(frequency="quarterly", basis="real")
print(df)
```

## 두 가지 사용 방식

ecos-reader는 동등한 두 진입점을 제공하며, 둘 다 정규화된 long-format DataFrame을 반환합니다.

| | 큐레이션 함수 | 범용 조회 |
|---|---|---|
| **함수** | `get_base_rate()`, `get_cpi()`, `get_gdp()` … (37개) | `get_series(stat_code, period, …)` |
| **언제** | 자주 쓰는 고가치 지표를 검증된 인자로 바로 | ECOS의 **어떤 통계표든** 직접 |
| **탐색** | 함수 시그니처가 곧 옵션 | `search_tables()` / `list_tables()` / `list_items()` (오프라인) |
| **도달 범위** | 큐레이션된 핵심 지표 | ECOS 전체 (도달 못 하는 통계 없음) |

큐레이션 함수가 없는 통계는 `get_series` 로 직접 조회합니다. 통계표·항목은 **네트워크 없이**
동봉 카탈로그로 탐색합니다.

```python
import ecos

# 1) 통계표 찾기 (오프라인 카탈로그 검색)
hits = ecos.search_tables("소비자물가")
print(hits[["stat_code", "stat_name", "cycle"]].head())

# 2) 임의 시계열 조회 — 윈도우 초과 시 자동 페이지네이션
df = ecos.get_series(
    "901Y009", "monthly",
    start_date="202401", end_date="202412",
    item_code="0",   # 생략 시 전체 항목
)

# 3) 표의 세부 항목(item_code) 탐색
items = ecos.list_items("901Y009")
print(items[["item_code", "item_name", "cycle"]].head())
```

> 큐레이션 함수는 범용 조회 위에 올바른 `(stat_code, item_code, period)`를 검증해 얹은
> 편의 계층입니다. 전체 흐름과 옵션은 [범용 조회 & 탐색 가이드](docs/user-guide/universal-access.md)를 참고하세요.

## 지원 지표

### 금리 지표

| 함수 | 설명 | 주기 |
|-----|------|-----|
| `get_base_rate()` | 한국은행 기준금리 | 월 |
| `get_treasury_yield(maturity)` | 국고채 수익률 (1Y/3Y/5Y/10Y/20Y/30Y) | 일 |
| `get_yield_spread()` | 장단기 금리차 | 일 |
| `get_bank_deposit_rate(basis)` | 예금은행 수신금리 (신규/잔액) | 월 |
| `get_bank_lending_rate(basis)` | 예금은행 대출금리 (신규/잔액) | 월 |

### 물가 지표

| 함수 | 설명 | 주기 |
|-----|------|-----|
| `get_cpi()` | 소비자물가지수 전년동월비 | 월 |
| `get_core_cpi()` | 근원 CPI (식료품·에너지 제외) | 월 |
| `get_ppi()` | 생산자물가지수 전년동월비 | 월 |
| `get_cpi_monthly(sub_category)` | CPI 월별 원지수 (품목·분류별) | 월 |
| `get_cpi_by_category(category)` | CPI 세부 항목별 지수 (상품/서비스 등 8종) | 월 |

### 성장 지표

| 함수 | 설명 | 주기 |
|-----|------|-----|
| `get_gdp(frequency, basis)` | GDP (분기/연간, 실질/명목) | 분기/연 |
| `get_gdp_deflator()` | GDP 디플레이터 | 분기/연 |
| `get_gdp_growth_rate()` | 실질 GDP 성장률 | 분기 |
| `get_gdp_by_industry(basis, seasonal_adj)` | 산업별 GDP (실질/명목, 계절조정/원계열) | 분기/연 |
| `get_gdp_by_expenditure(basis)` | 지출항목별 GDP (실질/명목) | 분기/연 |
| `get_gdp_deflator_by_industry()` | 산업별 GDP 디플레이터 | 분기/연 |

### 통화 지표

| 함수 | 설명 | 주기 |
|-----|------|-----|
| `get_money_supply(indicator)` | 통화량 (M1/M2/Lf) | 월 |
| `get_bank_lending(sector)` | 예금은행 대출금 (전체/가계) | 월 |
| `get_m1_variants(variant)` | M1 세부 (평잔·말잔, 계절조정·원계열) | 월 |
| `get_m2_variants(variant)` | M2 세부 (평잔·말잔, 계절조정·원계열) | 월 |
| `get_m2_by_holder(variant)` | M2 경제주체별 (평잔·말잔, 계절조정·원계열) | 월 |

### 가계금융 지표

| 함수 | 설명 | 주기 |
|-----|------|-----|
| `get_household_credit(category)` | 가계신용 (업권별/용도별) | 분기 |
| `get_household_lending_detail(sub_category)` | 예금취급기관 가계대출 (용도별) | 월 |
| `get_borrower_loan(loan_type, category)` | 차주별 가계대출 (신규/잔액) | 분기 |

### 재정·금융시장 지표

| 함수 | 설명 | 주기 |
|-----|------|-----|
| `get_fiscal_balance()` | 통합재정수지 | 월 |
| `get_stock_index(frequency, sub_category)` | 주가지수 KOSPI (일별/월별) | 일/월 |
| `get_investor_trading(action, metric, sub_category)` | 투자자별 주식거래 | 월 |
| `get_bond_yield(bond_type, measure, sub_category)` | 채권 거래 (종류별/시장별) | 월 |

### 실물경기 지표

| 함수 | 설명 | 주기 |
|-----|------|-----|
| `get_industrial_production(seasonal)` | 전산업생산지수 (원계열/계절조정) | 월 |
| `get_facility_investment(seasonal)` | 설비투자지수 (원지수/계절조정) | 월 |
| `get_composite_index(index)` | 경기종합지수 (선행/동행/후행) | 월 |
| `get_retail_sales(index, frequency)` | 소매판매액지수 (불변/경상/계절조정) | 월/분기/연 |

### 심리 지표

| 함수 | 설명 | 주기 |
|-----|------|-----|
| `get_business_sentiment(sector)` | 기업경기실사지수 BSI 업황전망 (전산업/제조/비제조) | 월 |
| `get_consumer_sentiment()` | 소비자심리지수 (CCSI) | 월 |

### 환율·국제수지·무역 지표

| 함수 | 설명 | 주기 |
|-----|------|-----|
| `get_exchange_rate(currency)` | 원/외화 매매기준율 (USD/JPY/EUR/CNY) | 일 |
| `get_balance_of_payments(account, frequency)` | 국제수지 (경상/자본/금융계정) | 월/분기/연 |
| `get_trade(flow, frequency)` | 수출입금액 통관기준 (수출/수입) | 월/연 |

> ℹ️ v0.3.0 이후 과거 단일 ECOS item만 반환하던 함수들이 전체 시리즈 long-format +
> `sub_category` 선택으로 재설계되었고, `EcosPartialCoverageWarning`은 제거되었습니다.
> 자세한 변경·마이그레이션은 [마이그레이션 가이드](docs/user-guide/migration-v0.3.0.md)를 참고하세요.

## 상세 사용법

### 기간 지정

```python
# 월간 데이터 (YYYYMM 형식)
df = ecos.get_base_rate(start_date="202001", end_date="202312")

# 일간 데이터 (YYYYMMDD 형식)
df = ecos.get_treasury_yield(maturity="3Y", start_date="20240101", end_date="20241231")

# 분기 데이터 (YYYYQN 형식)
df = ecos.get_gdp(frequency="quarterly", start_date="2020Q1", end_date="2024Q4")

# 연간 데이터 (YYYY 형식)
df = ecos.get_gdp(frequency="annual", start_date="2015", end_date="2024")
```

### 고급 사용 예제

#### 1. 통화정책 모니터링

```python
import ecos
import matplotlib.pyplot as plt

# 기준금리와 CPI 동시 조회
base_rate = ecos.get_base_rate(start_date="202001", end_date="202412")
cpi = ecos.get_cpi(start_date="202001", end_date="202412")

# 그래프 그리기
fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(base_rate['date'], base_rate['value'], label='기준금리')
ax2 = ax1.twinx()
ax2.plot(cpi['date'], cpi['value'], color='red', label='CPI')
plt.title('통화정책 모니터링')
plt.show()
```

#### 2. GDP 성장 분석

```python
import ecos

# 실질 GDP 및 성장률 조회
gdp = ecos.get_gdp(frequency="quarterly", basis="real", start_date="2020Q1", end_date="2024Q4")
growth = ecos.get_gdp_growth_rate(frequency="quarterly", start_date="2020Q1", end_date="2024Q4")

# 산업별 기여도 분석
industry_gdp = ecos.get_gdp_by_industry(
    basis="real",
    seasonal_adj=True,
    frequency="quarterly",
    start_date="2023Q1",
    end_date="2023Q4"
)
```

#### 3. 금융시장 대시보드

```python
import ecos

# 주요 금융시장 지표 수집
stock = ecos.get_stock_index(frequency="daily", start_date="20240101", end_date="20241231")
bond = ecos.get_bond_yield(bond_type="종류별", start_date="202401", end_date="202412")
investor = ecos.get_investor_trading(start_date="202401", end_date="202412")

print("주식시장:", len(stock), "rows")
print("채권시장:", len(bond), "rows")
print("투자자거래:", len(investor), "rows")
```

#### 4. 가계부채 모니터링

```python
import ecos

# 가계신용 및 대출 추이
credit = ecos.get_household_credit(category="업권별", start_date="2020Q1", end_date="2024Q4")
lending = ecos.get_household_lending_detail(start_date="202001", end_date="202412")
borrower = ecos.get_borrower_loan(loan_type="잔액", start_date="2023Q1", end_date="2024Q4")

# 가계대출 금리
rate = ecos.get_bank_lending_rate(basis="신규취급액", start_date="202301", end_date="202412")
```

### 캐시 관리

```python
import ecos

# 캐시 비활성화 (실시간 데이터 필요 시)
ecos.disable_cache()

# 캐시 활성화 (기본값)
ecos.enable_cache()

# 캐시 초기화
ecos.clear_cache()
```

### 에러 처리

```python
import ecos
from ecos import EcosAPIError, EcosConfigError, EcosNetworkError

try:
    df = ecos.get_base_rate()
except EcosConfigError as e:
    print(f"API 키 설정 오류: {e}")
except EcosNetworkError as e:
    print(f"네트워크 오류: {e}")
except EcosAPIError as e:
    print(f"API 오류 [{e.code}]: {e.message}")
```

### 로깅 활성화(선택)

라이브러리는 import 시점에 로깅 핸들러를 자동으로 구성하지 않습니다. 필요 시 아래처럼 활성화하세요.

```python
import logging
import ecos

ecos.setup_logging(logging.INFO)
```

### 직접 클라이언트 사용

```python
from ecos import EcosClient

# 클라이언트 생성
client = EcosClient(
    api_key="your_api_key",
    timeout=60,
    max_retries=5,
    use_cache=True,
)

# 통계 데이터 조회
response = client.get_statistic_search(
    stat_code="722Y001",
    period="M",
    start_date="202401",
    end_date="202412",
    item_code1="0101000",
)

# 통계표 목록 조회
tables = client.get_statistic_table_list(start=1, end=10)

# 통계 세부항목 조회
items = client.get_statistic_item_list(stat_code="200Y101")

# 통계용어사전 검색
word_result = client.get_statistic_word(word="소비자물가지수")

# 100대 통계지표 조회
key_stats = client.get_key_statistic_list(start=1, end=10)

# 통계 메타데이터 조회
meta = client.get_statistic_meta(data_name="경제심리지수")
```

## 테스트

```bash
pytest
pytest --cov=src/ecos  # 커버리지 포함
```

## 프로젝트 구조

```
ecos-reader/
├── src/ecos/
│   ├── access.py            # 범용 조회 (get_series, list_items)
│   ├── catalog.py           # 통계표 카탈로그 탐색 (오프라인)
│   ├── client.py            # API 클라이언트
│   ├── parser.py            # 응답 파서
│   ├── constants.py         # 통계코드 정의
│   ├── data/catalog.csv.gz  # 동봉 카탈로그 스냅샷
│   └── indicators/          # 큐레이션 지표 모듈
├── tests/                   # 테스트
├── docs/                    # 문서
└── examples/                # 예제
```

## 문서

전체 문서는 [ecos-reader 공식 문서](https://choo121600.github.io/ecos-reader/)에서 확인할 수 있습니다.

### 로컬에서 문서 빌드

```bash
# 문서 도구 설치
pip install -e ".[docs]"

# 로컬 서버 실행
mkdocs serve

# 브라우저에서 http://127.0.0.1:8000 열기
```

## 프로젝트 문서

- **[구현 현황](IMPLEMENTATION_STATUS.md)**: 2계층 커버리지 모델 — `get_series`로 ECOS 전체 도달 + 큐레이션 함수 37개. 동봉 카탈로그 834노드(검색가능 609개)
- **[기여 가이드](CONTRIBUTING.md)**: 프로젝트 기여 방법
- **[변경 이력](CHANGELOG.md)**: 버전별 변경사항

## 기여하기

ecos-reader는 오픈소스 프로젝트입니다. 기여를 환영합니다!

- 버그 리포트 및 기능 제안: [GitHub Issues](https://github.com/choo121600/ecos-reader/issues)
- 코드 기여: [기여 가이드](CONTRIBUTING.md) 참조
- 구현 현황: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)에서 큐레이션 후보·커버리지 모델 확인

## 라이센스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
