# 무역(수출입) 지표

통관기준 수출입금액 등 무역 관련 지표를 조회하는 방법을 설명합니다.

## 수출입금액

수출입금액 통관기준(통계표 `901Y118`)을 조회합니다. 단위는 천불(천 달러)이며, 월·연 주기를 지원합니다.

### 기본 사용법

```python
import ecos

# 수출금액, 월별 (기본값)
df = ecos.get_trade()
print(df.tail())
```

### 옵션 지정

```python
# 수입금액
df = ecos.get_trade(flow="import")

# 연 주기, 기간 지정
df = ecos.get_trade(flow="export", frequency="annual", start_date="2015", end_date="2024")
```

`get_trade(flow="export", start_date=None, end_date=None, frequency="monthly")` 의 인자는 다음과 같습니다.

| `flow` | 설명 |
|--------|------|
| `"export"` | 수출금액 (기본값) |
| `"import"` | 수입금액 |

| `frequency` | 날짜 형식 |
|-------------|-----------|
| `"monthly"` | `YYYYMM` (기본값) |
| `"annual"` | `YYYY` |

!!! info "날짜 형식"
    `start_date` / `end_date` 형식은 `frequency` 설정에 따라 달라집니다. 기간을 생략하면 주기별 기본 범위가 적용됩니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 시점 |
| `value` | float | 수출입금액 (천불) |
| `unit` | str | 단위 |

## 실전 활용 예제

### 수출·수입 비교와 무역수지

```python
import ecos
import pandas as pd

export = ecos.get_trade(flow="export", start_date="202001")
import_ = ecos.get_trade(flow="import", start_date="202001")

merged = pd.merge(
    export[["date", "value"]].rename(columns={"value": "수출"}),
    import_[["date", "value"]].rename(columns={"value": "수입"}),
    on="date",
)

# 무역수지 (수출 - 수입)
merged["무역수지"] = merged["수출"] - merged["수입"]

print(merged.tail())
```

### 수출 추이 시각화

```python
import ecos

df = ecos.get_trade(flow="export", start_date="202001")

df.set_index("date")["value"].plot(
    title="수출금액 추이 (통관기준)",
    ylabel="수출금액 (천불)",
    figsize=(12, 6),
    grid=True,
)
```

## 다음 단계

- [국제수지 지표](bop.md) - 경상·자본·금융계정
- [환율 지표](forex.md) - 원/외화 매매기준율
- [실물경기 지표](real-economy.md) - 생산·투자·경기종합지수
