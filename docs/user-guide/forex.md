# 환율 지표

원/외화 매매기준율 등 환율 관련 지표를 조회하는 방법을 설명합니다.

## 원/외화 매매기준율

원/외화 매매기준율(통계표 `731Y001`)을 조회합니다. 일별 데이터이며, 통화별로 환율을 제공합니다.

### 기본 사용법

```python
import ecos

# 원/달러 (기본값)
df = ecos.get_exchange_rate()
print(df.tail())
```

### 옵션 지정

```python
# 원/엔 (100엔당)
df = ecos.get_exchange_rate(currency="JPY")

# 원/유로, 기간 지정
df = ecos.get_exchange_rate(
    currency="EUR",
    start_date="20240101",
    end_date="20241231",
)
```

`get_exchange_rate(currency="USD", start_date=None, end_date=None)` 의 `currency` 인자는 다음 값을 받습니다.

| `currency` | 설명 |
|------------|------|
| `"USD"` | 원/달러 (기본값) |
| `"JPY"` | 원/엔 (100엔당) |
| `"EUR"` | 원/유로 |
| `"CNY"` | 원/위안 (2016-01-04부터 제공) |

!!! info "날짜 형식"
    일별 데이터이므로 `YYYYMMDD` 형식을 사용합니다. 기간을 생략하면 최근 1년이 조회됩니다.

!!! info "영업일 기준"
    환율은 영업일에만 갱신됩니다. 주말·공휴일에는 값이 없으므로 결과가 sparse(빈 날짜가 있는 형태)하게 나옵니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 일자 |
| `value` | float | 매매기준율 (원) |
| `unit` | str | 단위 |

## 실전 활용 예제

### 환율 추이 시각화

```python
import ecos

df = ecos.get_exchange_rate(currency="USD", start_date="20240101")

df.set_index("date")["value"].plot(
    title="원/달러 매매기준율",
    ylabel="환율 (원)",
    figsize=(12, 6),
    grid=True,
)
```

### 여러 통화 비교

```python
import ecos
import pandas as pd

usd = ecos.get_exchange_rate(currency="USD", start_date="20240101")
eur = ecos.get_exchange_rate(currency="EUR", start_date="20240101")

merged = pd.merge(
    usd[["date", "value"]].rename(columns={"value": "USD"}),
    eur[["date", "value"]].rename(columns={"value": "EUR"}),
    on="date",
)

print(merged.tail())
```

## 다음 단계

- [국제수지 지표](bop.md) - 경상·자본·금융계정
- [무역(수출입) 지표](trade.md) - 통관기준 수출입금액
- [금융시장 지표](financial-markets.md) - 주식, 채권 등 금융시장 지표
