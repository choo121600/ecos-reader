# 심리 지표

기업과 소비자의 경기 심리를 나타내는 지표를 조회하는 방법을 설명합니다.

## 기업경기실사지수 (BSI)

기업경기실사지수(BSI) 업황전망(통계표 `512Y014`)을 조회합니다. 기업이 체감하는 경기를 나타내는 월별 지수로, 기준값 100을 넘으면 긍정적으로 응답한 기업이 더 많음을 뜻합니다.

### 기본 사용법

```python
import ecos

# 전산업 (기본값)
df = ecos.get_business_sentiment()
print(df.tail())
```

### 옵션 지정

```python
# 제조업
df = ecos.get_business_sentiment(sector="manufacturing")

# 비제조업, 기간 지정
df = ecos.get_business_sentiment(
    sector="non_manufacturing",
    start_date="202001",
    end_date="202412",
)
```

`get_business_sentiment(sector="all", start_date=None, end_date=None)` 의 `sector` 인자는 다음 값을 받습니다.

| `sector` | 설명 |
|----------|------|
| `"all"` | 전산업 (기본값) |
| `"manufacturing"` | 제조업 |
| `"non_manufacturing"` | 비제조업 |

!!! info "날짜 형식"
    월별 데이터이므로 `YYYYMM` 형식을 사용합니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 기업경기실사지수 (기준 100) |
| `unit` | str | 단위 |

## 소비자심리지수 (CSI)

소비자심리지수(CSI, 통계표 `511Y002`)를 조회합니다. 소비자동향조사 결과를 종합한 월별 지수로, 100을 기준으로 그 이상이면 소비 심리가 낙관적임을 뜻합니다.

### 기본 사용법

```python
import ecos

df = ecos.get_consumer_sentiment()
print(df.tail())
```

### 기간 지정

```python
df = ecos.get_consumer_sentiment(start_date="202301", end_date="202312")
```

`get_consumer_sentiment(start_date=None, end_date=None)` 는 별도 옵션 없이 기간만 지정합니다.

!!! info "날짜 형식"
    월별 데이터이므로 `YYYYMM` 형식을 사용합니다. 기간을 생략하면 최근 24개월이 조회됩니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 소비자심리지수 (기준 100) |
| `unit` | str | 단위 |

## 실전 활용 예제

### 기업·소비자 심리 비교

```python
import ecos
import pandas as pd

bsi = ecos.get_business_sentiment(start_date="202001")
csi = ecos.get_consumer_sentiment(start_date="202001")

merged = pd.merge(
    bsi[["date", "value"]].rename(columns={"value": "BSI"}),
    csi[["date", "value"]].rename(columns={"value": "CSI"}),
    on="date",
)

print(merged.tail())

merged.set_index("date").plot(
    title="기업경기실사지수 vs 소비자심리지수",
    figsize=(12, 6),
    grid=True,
)
```

### 기준선 대비 심리 판단

```python
import ecos

df = ecos.get_consumer_sentiment(start_date="202001")
latest = df["value"].iloc[-1]

if latest >= 100:
    print(f"소비 심리 낙관 (CSI {latest})")
else:
    print(f"소비 심리 비관 (CSI {latest})")
```

## 다음 단계

- [실물경기 지표](real-economy.md) - 생산·투자·경기종합지수
- [환율 지표](forex.md) - 원/외화 매매기준율
- [성장 지표](growth.md) - GDP 등 경제성장 지표
