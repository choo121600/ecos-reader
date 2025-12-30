# 성장 지표

GDP, GDP 디플레이터 등 경제 성장 관련 지표를 조회하는 방법을 설명합니다.

## GDP (국내총생산)

한국의 국내총생산(Gross Domestic Product) 데이터를 조회합니다.

### 매개변수

- `frequency`: 조회 빈도
    - `"Q"` - 분기별 (기본값)
    - `"A"` - 연간
- `basis`: 기준
    - `"real"` - 실질 GDP (기본값)
    - `"nominal"` - 명목 GDP

### 분기별 실질 GDP

```python
import ecos

# 분기별 실질 GDP (전년동기대비)
df = ecos.get_gdp(frequency="Q", basis="real")
print(df.tail())
```

### 기간 지정

```python
# 2020년 1분기부터 2024년 4분기까지
df = ecos.get_gdp(
    frequency="Q",
    basis="real",
    start_date="2020Q1",
    end_date="2024Q4"
)
```

!!! info "날짜 형식"
    분기 데이터는 `YYYYQN` 형식 (예: 2024Q1, 2024Q2)을 사용합니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 분기/연도 |
| `value` | float | GDP 증가율 (%) |
| `unit` | str | 단위 (%) |

### 시각화

```python
import ecos
import matplotlib.pyplot as plt

# 분기별 실질 GDP
df = ecos.get_gdp(frequency="Q", start_date="2015Q1")

# 그래프
df.set_index('date')['value'].plot(
    kind='bar',
    title='분기별 실질 GDP 성장률',
    ylabel='전년동기대비 (%)',
    figsize=(14, 6),
    grid=True
)
plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

## 연간 GDP

### 연간 실질 GDP

```python
import ecos

# 연간 실질 GDP
df = ecos.get_gdp(frequency="A", basis="real")
print(df)
```

### 기간 지정

```python
# 2015년부터 2024년까지
df = ecos.get_gdp(
    frequency="A",
    basis="real",
    start_date="2015",
    end_date="2024"
)
```

!!! info "날짜 형식"
    연간 데이터는 `YYYY` 형식을 사용합니다.

### 연간 명목 GDP

```python
import ecos

# 연간 명목 GDP
df = ecos.get_gdp(frequency="A", basis="nominal")
print(df)
```

## 실질 vs 명목 GDP 비교

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# 두 지표 조회
real = ecos.get_gdp(frequency="A", basis="real", start_date="2010")
nominal = ecos.get_gdp(frequency="A", basis="nominal", start_date="2010")

# 데이터 병합
merged = pd.merge(
    real[['date', 'value']].rename(columns={'value': '실질 GDP'}),
    nominal[['date', 'value']].rename(columns={'value': '명목 GDP'}),
    on='date'
)

# 시각화
merged.set_index('date').plot(
    kind='bar',
    title='실질 GDP vs 명목 GDP 성장률',
    ylabel='전년대비 (%)',
    figsize=(12, 6),
    grid=True
)
plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
plt.xticks(rotation=45)
plt.legend(['실질 GDP', '명목 GDP'])
plt.tight_layout()
plt.show()

# 차이 분석 (명목 - 실질 = 대략적인 인플레이션 효과)
merged['차이'] = merged['명목 GDP'] - merged['실질 GDP']
print("\n명목-실질 GDP 차이 (인플레이션 효과):")
print(merged[['date', '차이']])
```

## GDP 디플레이터

GDP 디플레이터는 명목 GDP와 실질 GDP의 비율로, 전반적인 물가 수준을 나타냅니다.

### 기본 사용법

```python
import ecos

# GDP 디플레이터 조회
df = ecos.get_gdp_deflator()
print(df.tail())
```

### 기간 지정

```python
# 분기별 데이터
df = ecos.get_gdp_deflator(
    start_date="2020Q1",
    end_date="2024Q4"
)
```

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 분기 |
| `value` | float | 전년동기대비 변화율 (%) |
| `unit` | str | 단위 (%) |

### GDP 디플레이터 vs CPI 비교

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# GDP 디플레이터 (분기)
deflator = ecos.get_gdp_deflator(start_date="2020Q1")

# CPI (월간 데이터를 분기로 변환)
cpi = ecos.get_cpi(start_date="202001")
cpi['quarter'] = cpi['date'].dt.to_period('Q')
cpi_quarterly = cpi.groupby('quarter')['value'].mean().reset_index()
cpi_quarterly['date'] = cpi_quarterly['quarter'].dt.to_timestamp()

# 데이터 병합
merged = pd.merge(
    deflator[['date', 'value']].rename(columns={'value': 'GDP 디플레이터'}),
    cpi_quarterly[['date', 'value']].rename(columns={'value': 'CPI'}),
    on='date',
    how='inner'
)

# 시각화
merged.set_index('date').plot(
    title='GDP 디플레이터 vs CPI',
    ylabel='전년동기대비 (%)',
    figsize=(12, 6),
    grid=True
)
plt.legend(['GDP 디플레이터', 'CPI'])
plt.tight_layout()
plt.show()
```

## 실전 활용 예제

### 경기 사이클 분석

```python
import ecos
import numpy as np

df = ecos.get_gdp(frequency="Q", start_date="2010Q1")

# 이동 평균으로 추세 파악
df['MA4'] = df['value'].rolling(window=4).mean()  # 4분기 이동평균

# 경기 국면 판단
df['cycle'] = np.where(df['value'] > df['MA4'], '확장', '수축')

# 최근 상황
recent = df.tail(8)
print("최근 8분기 경기 국면:")
for _, row in recent.iterrows():
    date_str = row['date'].strftime('%Y-Q%q')
    print(f"{date_str}: {row['value']:.2f}% ({row['cycle']})")
```

### 잠재성장률 대비 분석

한국의 잠재성장률을 약 2.0%로 가정하고 분석합니다.

```python
import ecos
import matplotlib.pyplot as plt

df = ecos.get_gdp(frequency="Q", start_date="2015Q1")

# 잠재성장률 설정
POTENTIAL_GROWTH = 2.0

# 산출갭 추정 (실제 성장률 - 잠재성장률)
df['output_gap'] = df['value'] - POTENTIAL_GROWTH

# 시각화
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# GDP 성장률
df.set_index('date')['value'].plot(ax=ax1, label='실제 성장률')
ax1.axhline(y=POTENTIAL_GROWTH, color='red', linestyle='--', label='잠재성장률')
ax1.set_title('GDP 성장률')
ax1.set_ylabel('전년동기대비 (%)')
ax1.legend()
ax1.grid(True)

# 산출갭
df.set_index('date')['output_gap'].plot(ax=ax2, color='purple')
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.fill_between(
    df.set_index('date').index,
    df.set_index('date')['output_gap'],
    0,
    where=(df.set_index('date')['output_gap'] > 0),
    color='green',
    alpha=0.3,
    label='양의 갭 (과열)'
)
ax2.fill_between(
    df.set_index('date').index,
    df.set_index('date')['output_gap'],
    0,
    where=(df.set_index('date')['output_gap'] < 0),
    color='red',
    alpha=0.3,
    label='음의 갭 (침체)'
)
ax2.set_title('산출갭 (실제 - 잠재)')
ax2.set_ylabel('갭 (%p)')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()
```

### 성장률 변동성 분석

```python
import ecos

df = ecos.get_gdp(frequency="Q", start_date="2010Q1")

# 기간별 분석
periods = [
    ("2010Q1", "2014Q4", "2010-2014"),
    ("2015Q1", "2019Q4", "2015-2019"),
    ("2020Q1", "2024Q4", "2020-2024")
]

print("기간별 GDP 성장률 분석:")
print("-" * 60)

for start, end, label in periods:
    period_data = df[
        (df['date'] >= start) &
        (df['date'] <= end)
    ]['value']

    print(f"\n{label}:")
    print(f"  평균: {period_data.mean():.2f}%")
    print(f"  표준편차: {period_data.std():.2f}%")
    print(f"  최댓값: {period_data.max():.2f}%")
    print(f"  최솟값: {period_data.min():.2f}%")
```

### 코로나19 영향 분석

```python
import ecos

df = ecos.get_gdp(frequency="Q", start_date="2019Q1")

# 코로나 이전/이후 구분
pre_covid = df[df['date'] < '2020-03-01']['value']
covid = df[
    (df['date'] >= '2020-03-01') &
    (df['date'] < '2022-01-01')
]['value']
post_covid = df[df['date'] >= '2022-01-01']['value']

print("코로나19 전후 GDP 성장률 비교:")
print(f"코로나 이전 (2019-2020Q1): {pre_covid.mean():.2f}%")
print(f"코로나 기간 (2020Q2-2021): {covid.mean():.2f}%")
print(f"코로나 이후 (2022-): {post_covid.mean():.2f}%")

# 최대 충격
min_covid = covid.min()
min_date = df[df['value'] == min_covid]['date'].iloc[0]
print(f"\n최대 충격: {min_covid:.2f}% ({min_date.strftime('%Y-Q%q')})")
```

## 다음 단계

- [물가 지표](prices.md) - CPI, PPI 등
- [통화 지표](money.md) - 통화량, 은행 대출 등
- [예제: 거시경제 대시보드](../examples/dashboard.md) - 성장과 다른 지표를 결합한 대시보드
