# 통화 지표

통화량(M1, M2, Lf)과 은행 대출 등 통화 관련 지표를 조회하는 방법을 설명합니다.

## 통화량

통화량은 경제 내에서 유통되는 화폐의 총량을 나타내는 지표입니다.

### 지원 지표

- `M1` - 협의통화 (현금 + 요구불예금)
- `M2` - 광의통화 (M1 + 저축성예금 + 단기금융상품 등)
- `Lf` - 금융기관 유동성 (M2 + 장기금융상품 등)

### M2 통화량

가장 널리 사용되는 통화량 지표입니다.

```python
import ecos

# M2 통화량 조회
df = ecos.get_money_supply(indicator="M2")
print(df.tail())
```

### 기간 지정

```python
# 2020년 1월부터 2024년 12월까지
df = ecos.get_money_supply(
    indicator="M2",
    start_date="202001",
    end_date="202412"
)
```

!!! info "날짜 형식"
    통화량은 월간 데이터이므로 `YYYYMM` 형식을 사용합니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 통화량 (10억원) |
| `unit` | str | 단위 (십억원) |

### 시각화

```python
import ecos
import matplotlib.pyplot as plt

# M2 통화량 추이
df = ecos.get_money_supply(indicator="M2", start_date="202001")

# 조원 단위로 변환
df['value_trillion'] = df['value'] / 1000

# 그래프
df.set_index('date')['value_trillion'].plot(
    title='M2 통화량 추이',
    ylabel='통화량 (조원)',
    figsize=(12, 6),
    grid=True
)
plt.tight_layout()
plt.show()

# 통계
print(f"현재 M2: {df.iloc[-1]['value_trillion']:.0f}조원")
print(f"1년 전 대비 증가: {df.iloc[-1]['value_trillion'] - df.iloc[-12]['value_trillion']:.0f}조원")
```

### M1, M2, Lf 비교

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# 세 지표 조회
m1 = ecos.get_money_supply(indicator="M1", start_date="202001")
m2 = ecos.get_money_supply(indicator="M2", start_date="202001")
lf = ecos.get_money_supply(indicator="Lf", start_date="202001")

# 조원 단위로 변환 및 병합
merged = pd.merge(
    m1[['date', 'value']].rename(columns={'value': 'M1'}),
    m2[['date', 'value']].rename(columns={'value': 'M2'}),
    on='date'
)
merged = pd.merge(
    merged,
    lf[['date', 'value']].rename(columns={'value': 'Lf'}),
    on='date'
)

# 조원 단위로 변환
merged[['M1', 'M2', 'Lf']] = merged[['M1', 'M2', 'Lf']] / 1000

# 시각화
merged.set_index('date').plot(
    title='통화량 지표 비교',
    ylabel='통화량 (조원)',
    figsize=(12, 6),
    grid=True
)
plt.legend(['M1 (협의통화)', 'M2 (광의통화)', 'Lf (유동성)'])
plt.tight_layout()
plt.show()
```

## 은행 대출

은행의 가계 및 기업 대출 잔액을 조회합니다.

### 지원 부문

- `household` - 가계대출
- `corporate` - 기업대출
- `total` - 전체 대출 (가계 + 기업)

### 가계대출

```python
import ecos

# 가계대출 잔액 조회
df = ecos.get_bank_lending(sector="household")
print(df.tail())
```

### 기업대출

```python
import ecos

# 기업대출 잔액 조회
df = ecos.get_bank_lending(sector="corporate")
print(df.tail())
```

### 전체 대출

```python
import ecos

# 전체 대출 잔액 조회
df = ecos.get_bank_lending(sector="total")
print(df.tail())
```

### 기간 지정

```python
df = ecos.get_bank_lending(
    sector="household",
    start_date="202001",
    end_date="202412"
)
```

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 대출 잔액 (10억원) |
| `unit` | str | 단위 (십억원) |

### 가계 vs 기업 대출 비교

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# 두 부문 조회
household = ecos.get_bank_lending(sector="household", start_date="202001")
corporate = ecos.get_bank_lending(sector="corporate", start_date="202001")

# 데이터 병합
merged = pd.merge(
    household[['date', 'value']].rename(columns={'value': '가계'}),
    corporate[['date', 'value']].rename(columns={'value': '기업'}),
    on='date'
)

# 조원 단위로 변환
merged[['가계', '기업']] = merged[['가계', '기업']] / 1000

# 시각화
merged.set_index('date').plot(
    title='은행 대출 현황',
    ylabel='대출 잔액 (조원)',
    figsize=(12, 6),
    grid=True
)
plt.legend(['가계대출', '기업대출'])
plt.tight_layout()
plt.show()

# 비율 계산
merged['total'] = merged['가계'] + merged['기업']
merged['household_ratio'] = (merged['가계'] / merged['total']) * 100

print(f"\n가계대출 비중: {merged.iloc[-1]['household_ratio']:.1f}%")
```

## 실전 활용 예제

### 통화량 증가율 계산

```python
import ecos

df = ecos.get_money_supply(indicator="M2", start_date="202001")

# 전년동월대비 증가율
df['yoy_growth'] = df['value'].pct_change(periods=12) * 100

# 최근 데이터
recent = df.tail(12)

print("M2 통화량 전년동월대비 증가율:")
for _, row in recent.iterrows():
    if pd.notna(row['yoy_growth']):
        date_str = row['date'].strftime('%Y-%m')
        print(f"{date_str}: {row['yoy_growth']:.2f}%")
```

### 통화량 vs 물가 관계 분석

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# 데이터 조회
m2 = ecos.get_money_supply(indicator="M2", start_date="202001")
cpi = ecos.get_cpi(start_date="202001")

# M2 증가율 계산
m2['m2_growth'] = m2['value'].pct_change(periods=12) * 100

# 데이터 병합
merged = pd.merge(
    m2[['date', 'm2_growth']],
    cpi[['date', 'value']].rename(columns={'value': 'cpi'}),
    on='date'
)
merged = merged.dropna()

# 시각화
fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.plot(merged['date'], merged['m2_growth'], 'b-', label='M2 증가율')
ax1.set_xlabel('기간')
ax1.set_ylabel('M2 증가율 (%)', color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
ax2.plot(merged['date'], merged['cpi'], 'r-', label='CPI')
ax2.set_ylabel('CPI (%)', color='r')
ax2.tick_params(axis='y', labelcolor='r')

plt.title('M2 증가율 vs CPI')
plt.tight_layout()
plt.show()

# 상관관계
correlation = merged['m2_growth'].corr(merged['cpi'])
print(f"\nM2 증가율-CPI 상관계수: {correlation:.3f}")
```

### 가계부채 증가 추세 분석

```python
import ecos
import matplotlib.pyplot as plt

df = ecos.get_bank_lending(sector="household", start_date="201001")

# 조원 단위로 변환
df['value_trillion'] = df['value'] / 1000

# 전년동월대비 증가율
df['yoy_growth'] = df['value'].pct_change(periods=12) * 100

# 전월대비 증가액
df['mom_increase'] = df['value'].diff() / 1000  # 조원

# 시각화
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14))

# 잔액 추이
df.set_index('date')['value_trillion'].plot(
    ax=ax1,
    title='가계대출 잔액 추이',
    ylabel='잔액 (조원)',
    grid=True
)

# 증가율
df.set_index('date')['yoy_growth'].plot(
    ax=ax2,
    title='가계대출 전년동월대비 증가율',
    ylabel='증가율 (%)',
    grid=True,
    color='orange'
)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

# 월간 증가액
df.set_index('date')['mom_increase'].plot(
    ax=ax3,
    kind='bar',
    title='가계대출 월간 증가액',
    ylabel='증가액 (조원)',
    grid=True,
    color='green'
)
ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

plt.tight_layout()
plt.show()

# 최근 통계
recent = df.tail(6)
avg_increase = recent['mom_increase'].mean()
print(f"최근 6개월 평균 증가액: {avg_increase:.2f}조원/월")
```

### 가계부채 vs GDP 비율

```python
import ecos
import pandas as pd

# 데이터 조회
lending = ecos.get_bank_lending(sector="household", start_date="202001")
gdp_annual = ecos.get_gdp(frequency="A", basis="nominal", start_date="2020")

# 가계대출을 연간으로 집계 (연말 기준)
lending['year'] = lending['date'].dt.year
annual_lending = lending.groupby('year')['value'].last().reset_index()
annual_lending.columns = ['year', 'lending']

# GDP는 성장률이므로 절대값 추정 (2020년 기준)
# 실제로는 명목 GDP 절댓값이 필요하지만, 여기서는 추세 분석만 수행

print("연도별 가계대출 현황:")
for _, row in annual_lending.iterrows():
    year = row['year']
    lending_trillion = row['lending'] / 1000
    print(f"{year}년: {lending_trillion:.0f}조원")
```

### 신용 사이클 분석

```python
import ecos
import numpy as np

# 전체 대출 조회
df = ecos.get_bank_lending(sector="total", start_date="201001")

# 전년동월대비 증가율
df['yoy_growth'] = df['value'].pct_change(periods=12) * 100

# 이동평균으로 추세 파악
df['trend'] = df['yoy_growth'].rolling(window=12).mean()

# 신용 사이클 판단
df['cycle'] = np.where(df['yoy_growth'] > df['trend'], '확장', '수축')

# 최근 상황
recent = df.tail(12)
print("최근 12개월 신용 사이클:")
for _, row in recent.iterrows():
    if pd.notna(row['cycle']):
        date_str = row['date'].strftime('%Y-%m')
        print(f"{date_str}: {row['yoy_growth']:.2f}% ({row['cycle']})")
```

### 통화량 vs 대출 관계

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# 데이터 조회
m2 = ecos.get_money_supply(indicator="M2", start_date="202001")
lending = ecos.get_bank_lending(sector="total", start_date="202001")

# 조원 단위로 변환 및 병합
merged = pd.merge(
    m2[['date', 'value']].rename(columns={'value': 'M2'}),
    lending[['date', 'value']].rename(columns={'value': '대출'}),
    on='date'
)
merged[['M2', '대출']] = merged[['M2', '대출']] / 1000

# 대출/M2 비율
merged['ratio'] = (merged['대출'] / merged['M2']) * 100

# 시각화
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# 절댓값 비교
merged.set_index('date')[['M2', '대출']].plot(
    ax=ax1,
    title='M2 vs 은행 대출',
    ylabel='금액 (조원)',
    grid=True
)

# 비율
merged.set_index('date')['ratio'].plot(
    ax=ax2,
    title='은행 대출 / M2 비율',
    ylabel='비율 (%)',
    grid=True,
    color='purple'
)

plt.tight_layout()
plt.show()

print(f"현재 대출/M2 비율: {merged.iloc[-1]['ratio']:.1f}%")
```

## 다음 단계

- [고급 기능](advanced.md) - 캐시 관리, 에러 처리, 로깅 등
- [금리 지표](interest-rates.md) - 기준금리와 대출의 관계 분석
- [예제: 거시경제 대시보드](../examples/dashboard.md) - 통화와 다른 지표를 결합한 대시보드
