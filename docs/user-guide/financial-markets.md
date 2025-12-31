# 금융시장 지표

주가지수, 투자자별 거래, 채권 수익률 등 금융시장 관련 지표를 조회하는 방법을 설명합니다.

## 주가지수 (KOSPI)

한국거래소의 KOSPI 지수를 조회합니다.

### 지원 빈도

- `daily` - 일별 데이터 (기본값)
- `monthly` - 월별 데이터

### 일별 KOSPI

```python
import ecos

# 일별 KOSPI 지수 조회
df = ecos.get_stock_index(frequency="daily")
print(df.tail())
```

### 기간 지정

```python
# 2024년 1월 데이터
df = ecos.get_stock_index(
    frequency="daily",
    start_date="20240101",
    end_date="20240131"
)
```

!!! info "날짜 형식"
    일별 데이터는 `YYYYMMDD` 형식을 사용합니다.

### 월별 KOSPI

```python
import ecos

# 월별 KOSPI 지수 조회
df = ecos.get_stock_index(frequency="monthly")
print(df.tail())
```

### 기간 지정 (월별)

```python
# 2020년부터 2024년까지
df = ecos.get_stock_index(
    frequency="monthly",
    start_date="202001",
    end_date="202412"
)
```

!!! info "날짜 형식"
    월별 데이터는 `YYYYMM` 형식을 사용합니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회일/월 |
| `value` | float | KOSPI 지수 또는 회사수 |
| `unit` | str | 단위 |

### KOSPI 시각화

```python
import ecos
import matplotlib.pyplot as plt

# 2024년 KOSPI 추이
df = ecos.get_stock_index(
    frequency="daily",
    start_date="20240101"
)

# 그래프
df.set_index('date')['value'].plot(
    title='KOSPI 지수 추이',
    ylabel='지수',
    figsize=(14, 6),
    grid=True
)
plt.tight_layout()
plt.show()

# 통계
print(f"최고가: {df['value'].max():.2f}")
print(f"최저가: {df['value'].min():.2f}")
print(f"평균: {df['value'].mean():.2f}")
print(f"변동성 (표준편차): {df['value'].std():.2f}")
```

## 투자자별 주식거래

투자자 유형별 주식 거래 현황을 조회합니다.

### 기본 사용법

```python
import ecos

# 투자자별 거래 조회
df = ecos.get_investor_trading()
print(df.tail())
```

### 기간 지정

```python
# 2024년 데이터
df = ecos.get_investor_trading(
    start_date="202401",
    end_date="202412"
)
```

!!! info "날짜 형식"
    투자자별 거래는 월간 데이터이므로 `YYYYMM` 형식을 사용합니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 거래금액 또는 거래량 |
| `unit` | str | 단위 |

### 투자자별 거래 분석

```python
import ecos
import matplotlib.pyplot as plt

df = ecos.get_investor_trading(start_date="202301")

# 시각화
df.set_index('date')['value'].plot(
    kind='bar',
    title='투자자별 주식거래',
    ylabel='거래금액',
    figsize=(14, 6),
    grid=True
)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

## 채권 수익률

국채 및 회사채 수익률을 조회합니다.

### 지원 유형

- `종류별` - 채권 종류별 수익률 (기본값)
- `시장별` - 시장별 채권 거래 현황

### 종류별 채권 수익률

```python
import ecos

# 채권 종류별 수익률
df = ecos.get_bond_yield(bond_type="종류별")
print(df.tail())
```

### 시장별 채권 거래

```python
import ecos

# 시장별 채권 거래
df = ecos.get_bond_yield(bond_type="시장별")
print(df.tail())
```

### 기간 지정

```python
# 2024년 데이터
df = ecos.get_bond_yield(
    bond_type="종류별",
    start_date="202401",
    end_date="202412"
)
```

!!! info "날짜 형식"
    채권 데이터는 월간 데이터이므로 `YYYYMM` 형식을 사용합니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 수익률 (%) 또는 거래대금 |
| `unit` | str | 단위 |

### 채권 수익률 시각화

```python
import ecos
import matplotlib.pyplot as plt

# 채권 종류별 수익률 추이
df = ecos.get_bond_yield(
    bond_type="종류별",
    start_date="202001"
)

# 그래프
df.set_index('date')['value'].plot(
    title='채권 수익률 추이',
    ylabel='수익률 (%)',
    figsize=(12, 6),
    grid=True
)
plt.tight_layout()
plt.show()
```

## 실전 활용 예제

### 주식 변동성 분석

```python
import ecos
import numpy as np

df = ecos.get_stock_index(
    frequency="daily",
    start_date="20240101"
)

# 일별 수익률 계산
df['returns'] = df['value'].pct_change() * 100

# 변동성 통계
print("KOSPI 변동성 분석:")
print(f"평균 일별 수익률: {df['returns'].mean():.3f}%")
print(f"수익률 표준편차: {df['returns'].std():.3f}%")
print(f"최대 상승: {df['returns'].max():.2f}%")
print(f"최대 하락: {df['returns'].min():.2f}%")

# 변동성 구간 분석
volatility = df['returns'].std()
high_volatility = (df['returns'].abs() > volatility).sum()
print(f"\n고변동성 일수: {high_volatility}일 ({high_volatility/len(df)*100:.1f}%)")
```

### KOSPI vs 채권 수익률 비교

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# 데이터 조회
stock = ecos.get_stock_index(frequency="monthly", start_date="202001")
bond = ecos.get_bond_yield(bond_type="종류별", start_date="202001")

# 데이터 병합
merged = pd.merge(
    stock[['date', 'value']].rename(columns={'value': 'KOSPI'}),
    bond[['date', 'value']].rename(columns={'value': '채권수익률'}),
    on='date',
    how='inner'
)

# 정규화 (2020년 1월 = 100)
if not merged.empty:
    merged['KOSPI_normalized'] = (merged['KOSPI'] / merged['KOSPI'].iloc[0]) * 100
    merged['Bond_normalized'] = (merged['채권수익률'] / merged['채권수익률'].iloc[0]) * 100

    # 시각화
    fig, ax = plt.subplots(figsize=(12, 6))

    merged.set_index('date')[['KOSPI_normalized', 'Bond_normalized']].plot(
        ax=ax,
        title='KOSPI vs 채권 수익률 (정규화)',
        ylabel='지수 (2020.01 = 100)',
        grid=True
    )
    plt.legend(['KOSPI', '채권 수익률'])
    plt.tight_layout()
    plt.show()
```

### 주식 모멘텀 분석

```python
import ecos

df = ecos.get_stock_index(
    frequency="daily",
    start_date="20240101"
)

# 이동평균선 계산
df['MA5'] = df['value'].rolling(window=5).mean()
df['MA20'] = df['value'].rolling(window=20).mean()
df['MA60'] = df['value'].rolling(window=60).mean()

# 골든크로스/데드크로스 신호
df['signal'] = 0
df.loc[df['MA5'] > df['MA20'], 'signal'] = 1  # 골든크로스
df.loc[df['MA5'] < df['MA20'], 'signal'] = -1  # 데드크로스

# 시각화
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# KOSPI와 이동평균선
df.set_index('date')[['value', 'MA5', 'MA20', 'MA60']].plot(
    ax=ax1,
    title='KOSPI와 이동평균선',
    ylabel='지수',
    grid=True
)
ax1.legend(['KOSPI', 'MA5', 'MA20', 'MA60'])

# 매매 신호
df.set_index('date')['signal'].plot(
    ax=ax2,
    kind='area',
    title='매매 신호 (골든크로스/데드크로스)',
    ylabel='신호',
    grid=True,
    color=['red' if x < 0 else 'green' if x > 0 else 'gray' for x in df['signal']]
)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.set_ylim(-1.5, 1.5)

plt.tight_layout()
plt.show()

# 최근 신호
recent_signal = df.iloc[-1]['signal']
if recent_signal > 0:
    print("✅ 골든크로스 - 상승 신호")
elif recent_signal < 0:
    print("⚠️ 데드크로스 - 하락 신호")
else:
    print("➡️ 중립")
```

### 위험자산 vs 안전자산 선호도

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# 데이터 조회
stock = ecos.get_stock_index(frequency="monthly", start_date="202001")
bond = ecos.get_bond_yield(bond_type="종류별", start_date="202001")

# 전월대비 변화율
merged = pd.merge(
    stock[['date', 'value']].rename(columns={'value': 'stock'}),
    bond[['date', 'value']].rename(columns={'value': 'bond'}),
    on='date',
    how='inner'
)

merged['stock_change'] = merged['stock'].pct_change() * 100
merged['bond_change'] = merged['bond'].pct_change() * 100

# 위험 선호도 지표 (주식 수익률 - 채권 수익률)
merged['risk_preference'] = merged['stock_change'] - merged['bond_change']

# 시각화
merged = merged.dropna()

merged.set_index('date')['risk_preference'].plot(
    kind='bar',
    title='위험자산 선호도 지표',
    ylabel='주식 수익률 - 채권 수익률 변화 (%p)',
    figsize=(14, 6),
    grid=True,
    color=['green' if x > 0 else 'red' for x in merged['risk_preference']]
)
plt.axhline(y=0, color='black', linestyle='-', linewidth=1)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 최근 트렌드
recent_avg = merged.tail(3)['risk_preference'].mean()
print(f"\n최근 3개월 평균 위험 선호도: {recent_avg:.2f}%p")
if recent_avg > 0:
    print("✅ 위험자산 선호 (Risk-On)")
else:
    print("⚠️ 안전자산 선호 (Risk-Off)")
```

## 다음 단계

- [금리 지표](interest-rates.md) - 금리와 금융시장의 관계 분석
- [재정 지표](fiscal.md) - 재정정책과 금융시장
- [예제: 거시경제 대시보드](../examples/dashboard.md) - 금융시장과 다른 지표를 결합한 대시보드
