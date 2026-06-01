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

# 월별 KOSPI 종가(지수) 조회
df = ecos.get_stock_index(frequency="monthly")
print(df.tail())

# 같은 통계표의 다른 항목 선택 (시가총액·거래대금·KOSDAQ 지수 등)
df = ecos.get_stock_index(frequency="monthly", sub_category="KOSPI_시가총액")
```

!!! note "v0.3.0 정정 (#60)"
    월별 기본값이 `1010000`(KOSPI 회사수, 오류)에서 `1070000`(KOSPI 종가, 지수)로
    정정되었습니다. 회사수 등 다른 항목이 필요하면 `sub_category`로 선택하세요.

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
| `value` | float | KOSPI 지수 (기본) 또는 선택한 항목 값 |
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

투자자(기관·개인·외국인 등) 유형별 주식 거래를 조회합니다. `action`(매도/매수/순매수)과
`metric`(거래대금/거래량)을 선택할 수 있습니다.

### 매개변수

- `action`: 거래 행위 — `순매수`(기본값) / `매수` / `매도`
- `metric`: 측정 지표 — `거래대금`(기본값) / `거래량`
- `sub_category`: 특정 투자자 선택 (항목명 또는 item_code). 미지정 시 전체 투자자
  long-format 반환.

### 기본 사용법

```python
import ecos

# 투자자별 순매수 거래대금 (long-format: date, category_value, value, unit)
df = ecos.get_investor_trading()
print(df.tail())

# 외국인 순매수만 (item_code 사용 — 라벨 변동에 안정적)
df = ecos.get_investor_trading(sub_category="S22CC")

# 투자자별 매수 거래량
df = ecos.get_investor_trading(action="매수", metric="거래량")
```

!!! note "v0.3.0 재설계 (#60)"
    이전에는 단일 항목(기타법인 매도)만 반환했으나, 이제 투자자별 전체 시리즈를
    제공합니다. `category_value`는 ECOS 라벨(예: `개인(순매수)`)을 따르며, 안정적
    선택을 위해 `sub_category`에 item_code(예: `S22CB`)도 사용할 수 있습니다.

!!! info "날짜 형식"
    투자자별 거래는 월간 데이터이므로 `YYYYMM` 형식을 사용합니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `category_value` | str | 투자자명 (sub_category 미지정 시) |
| `value` | float | 거래금액 또는 거래량 |
| `unit` | str | 단위 |

### 투자자별 거래 분석

```python
import ecos

# 외국인 순매수 추이 (단일 투자자 선택)
df = ecos.get_investor_trading(sub_category="S22CC", start_date="202301")
df.set_index('date')['value'].plot(
    title='외국인 순매수 거래대금', ylabel='거래대금', figsize=(14, 6), grid=True
)
```

## 채권 수익률

국채 및 회사채 수익률을 조회합니다.

### 지원 유형

- `종류별` - 채권 종류별 수익률 (기본값)
- `시장별` - 시장별 채권 거래 현황

### 매개변수

- `bond_type`: 분류 기준 — `종류별`(기본값, 합계/국채/지방채/특수채/회사채/외국채) / `시장별`(합계/국채전문/일반채권/소액채권/신고매매)
- `measure`: 측정 지표 — `거래대금`(기본값) / `거래량` / `상장잔액`·`상장종목수`(종류별 전용)
- `sub_category`: 세부 분류(분류명 또는 item_code). 미지정 시 전체 분류 long-format 반환.

### 종류별 채권 거래

```python
import ecos

# 종류별 거래대금 전체 (long-format: date, category_value, value, unit)
df = ecos.get_bond_market(bond_type="종류별")
print(df.tail())

# 국채만
df = ecos.get_bond_market(sub_category="국채")
```

### 시장별 채권 거래

```python
import ecos

# 시장별 거래대금 전체
df = ecos.get_bond_market(bond_type="시장별")

# 시장별 거래량, 국채전문 유통시장만
df = ecos.get_bond_market(bond_type="시장별", measure="거래량", sub_category="0202")
```

!!! note "v0.3.0 재설계 (#63)"
    이전에는 합계 단일 시계열만 반환했으나, 이제 종류/시장 전체 분류를 제공합니다.
    long-format에는 '합계' 행도 포함되므로 단순 합산에 주의하세요. 분류명이 길거나
    중복될 수 있어 단일 선택은 item_code(종류별 `4`=국채, 시장별 `0202`=국채전문)를
    권장합니다.

### 기간 지정

```python
# 2024년 데이터
df = ecos.get_bond_market(
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
| `category_value` | str | 분류명 (sub_category 미지정 시) |
| `value` | float | 거래대금/거래량 등 measure 값 |
| `unit` | str | 단위 |

### 채권 수익률 시각화

```python
import ecos
import matplotlib.pyplot as plt

# 채권 종류별 수익률 추이
df = ecos.get_bond_market(
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
bond = ecos.get_bond_market(bond_type="종류별", start_date="202001")

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
bond = ecos.get_bond_market(bond_type="종류별", start_date="202001")

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
