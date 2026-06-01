# 실물경기 지표

전산업생산, 설비투자, 경기종합지수, 소매판매 등 실물경기 흐름을 보여주는 지표를 조회하는 방법을 설명합니다.

## 전산업생산지수

전산업생산지수(통계표 `901Y033`)를 조회합니다. 광공업뿐 아니라 서비스업, 건설업 등을 포함한 전체 산업의 생산 활동 수준을 나타내는 월별 지수(기준 2020=100)입니다.

### 기본 사용법

```python
import ecos

# 전산업생산지수 (원계열)
df = ecos.get_industrial_production()
print(df.tail())
```

### 옵션 지정

```python
# 기간 지정
df = ecos.get_industrial_production(
    start_date="202001",
    end_date="202412"
)

# 계절조정 계열
df = ecos.get_industrial_production(seasonal=True)
```

`get_industrial_production(start_date=None, end_date=None, seasonal=False, frequency="monthly")` 의 `seasonal=True` 를 지정하면 원계열 대신 계절조정 계열을 조회합니다. `frequency` 로 월(`monthly`, 기본)·분기(`quarterly`)·연(`annual`) 주기를 선택합니다.

```python
# 연간 주기
df = ecos.get_industrial_production(frequency="annual")
```

!!! info "날짜 형식"
    `frequency` 가 `monthly` 이면 `YYYYMM`, `quarterly` 이면 `YYYYQn`, `annual` 이면 `YYYY` 형식을 사용합니다. 기간을 생략하면 주기별 기본 범위가 적용됩니다.

!!! warning "계절조정 + 연간 조합 불가"
    `seasonal=True` 와 `frequency="annual"` 을 함께 지정하면 `ValueError` 가 발생합니다.
    ECOS가 계절조정 연간 계열을 제공하지 않기 때문입니다(연간 데이터엔 계절성이 없음).
    `seasonal=False` 또는 `frequency="monthly"`/`"quarterly"` 를 사용하세요.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 전산업생산지수 (2020=100) |
| `unit` | str | 단위 |

## 설비투자지수

설비투자지수(통계표 `901Y066`)를 조회합니다. 기업의 기계·운송장비 등 설비 투자 동향을 나타내는 월별 지수(기준 2020=100)입니다.

### 기본 사용법

```python
import ecos

df = ecos.get_facility_investment()
print(df.tail())
```

### 옵션 지정

```python
# 기간 지정
df = ecos.get_facility_investment(start_date="202001", end_date="202412")

# 계절조정 계열
df = ecos.get_facility_investment(seasonal=True)

# 연간 주기
df = ecos.get_facility_investment(frequency="annual")
```

`get_facility_investment(start_date=None, end_date=None, seasonal=False, frequency="monthly")` 의 인자 구조는 전산업생산지수와 동일합니다. `frequency` 로 월(`monthly`, 기본)·분기(`quarterly`)·연(`annual`) 주기를 선택합니다.

!!! warning "계절조정 + 연간 조합 불가"
    전산업생산지수와 동일하게 `seasonal=True` 와 `frequency="annual"` 조합은 `ValueError` 가
    발생합니다. `seasonal=False` 또는 `frequency="monthly"`/`"quarterly"` 를 사용하세요.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 설비투자지수 (2020=100) |
| `unit` | str | 단위 |

## 경기종합지수

경기종합지수(CI, 통계표 `901Y067`)를 조회합니다. 경기의 국면과 전환점을 판단하기 위해 작성하는 월별 지수입니다.

### 기본 사용법

```python
import ecos

# 동행종합지수 (기본값)
df = ecos.get_composite_index()
print(df.tail())
```

### 옵션 지정

```python
# 선행종합지수
df = ecos.get_composite_index(index="leading")

# 후행종합지수, 기간 지정
df = ecos.get_composite_index(index="lagging", start_date="202001", end_date="202412")
```

`get_composite_index(index="coincident", start_date=None, end_date=None)` 의 `index` 인자는 다음 값을 받습니다.

| `index` | 설명 |
|---------|------|
| `"coincident"` | 동행종합지수 (기본값) |
| `"leading"` | 선행종합지수 |
| `"lagging"` | 후행종합지수 |

!!! info "날짜 형식"
    월별 데이터이므로 `YYYYMM` 형식을 사용합니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 경기종합지수 |
| `unit` | str | 단위 |

## 소매판매액지수

소매판매액지수(재별 및 상품군별, 통계표 `901Y100`)를 상품군별로 조회합니다. 소비 동향을 나타내는 지수(기준 2020=100)이며, 월·분기·연 주기를 지원합니다. partial-coverage 규약(#56)에 따라 `sub_category` 미지정 시 전체 상품군을 long-format으로, 지정 시 해당 상품군 단일 시계열만 반환합니다.

### 기본 사용법

```python
import ecos

# 불변지수, 월별, 전체 상품군 long-format (date, category_value, value, unit)
df = ecos.get_retail_sales()
print(df.tail())
```

### 옵션 지정

```python
# 음식료품 단일 시계열
df = ecos.get_retail_sales(sub_category="음식료품")

# 경상지수, 음식료품, 연 주기 조합
df = ecos.get_retail_sales("nominal", sub_category="음식료품", frequency="annual")

# 계절조정지수, 분기 주기
df = ecos.get_retail_sales(index="seasonal", frequency="quarterly")
```

`get_retail_sales(index="real", sub_category=None, start_date=None, end_date=None, frequency="monthly")` 의 인자는 다음과 같습니다.

| `index` | 설명 |
|---------|------|
| `"real"` | 불변지수 (기본값) |
| `"nominal"` | 경상지수 |
| `"seasonal"` | 계절조정지수 |

| `frequency` | 날짜 형식 |
|-------------|-----------|
| `"monthly"` | `YYYYMM` (기본값) |
| `"quarterly"` | `YYYYQn` (예: `2024Q1`) |
| `"annual"` | `YYYY` |

`sub_category` 는 상품군 분류명(예: `총지수`, `내구재`, `음식료품`) 또는 item_code(예: `G31`)로 지정합니다.

!!! info "날짜 형식"
    `start_date` / `end_date` 형식은 `frequency` 설정에 따라 달라집니다. 기간을 생략하면 주기별 기본 범위가 적용됩니다.

!!! warning "계절조정 + 연간 조합 불가"
    `index="seasonal"` 과 `frequency="annual"` 을 함께 지정하면 `ValueError` 가 발생합니다.
    ECOS가 계절조정 연간 계열을 제공하지 않기 때문입니다.
    `index="nominal"`/`"real"` 또는 `frequency="monthly"`/`"quarterly"` 를 사용하세요.

### 반환 데이터 구조

`sub_category` 미지정 시 long-format(상품군별), 지정 시 단일 시계열을 반환합니다. 통계표는 계층형(총지수+내구재/준내구재/비내구재+세부품목)이라 상품군 간 단순 합산은 금지합니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 시점 |
| `category_value` | str | 상품군명 (long-format, `sub_category` 미지정 시) |
| `value` | float | 소매판매액지수 (2020=100) |
| `unit` | str | 단위 |

## 실전 활용 예제

### 동행지수와 선행지수 비교

```python
import ecos
import pandas as pd

coincident = ecos.get_composite_index(index="coincident", start_date="202001")
leading = ecos.get_composite_index(index="leading", start_date="202001")

merged = pd.merge(
    coincident[["date", "value"]].rename(columns={"value": "동행"}),
    leading[["date", "value"]].rename(columns={"value": "선행"}),
    on="date",
)

print(merged.tail())

merged.set_index("date").plot(
    title="경기종합지수 동행 vs 선행",
    figsize=(12, 6),
    grid=True,
)
```

### 생산과 소비 동향 결합

```python
import ecos

production = ecos.get_industrial_production(start_date="202001")
retail = ecos.get_retail_sales(sub_category="총지수", start_date="202001")

print("전산업생산 최근 값:", production["value"].iloc[-1])
print("소매판매 총지수 최근 값:", retail["value"].iloc[-1])
```

## 다음 단계

- [심리 지표](sentiment.md) - 기업·소비자 심리지수
- [성장 지표](growth.md) - GDP 등 경제성장 지표
- [무역(수출입) 지표](trade.md) - 통관기준 수출입금액
