# 재정 지표

한국 정부의 재정 수지 등 재정 관련 지표를 조회하는 방법을 설명합니다.

## 통합재정수지

정부의 통합재정수지 데이터를 조회합니다. 통합재정수지는 중앙정부와 지방정부를 합친 재정수지로, 국가의 재정 건전성을 나타내는 핵심 지표입니다.

### 기본 사용법

```python
import ecos

# 통합재정수지 조회
df = ecos.get_fiscal_balance()
print(df.tail())
```

### 기간 지정

```python
# 2020년 1월부터 2024년 12월까지
df = ecos.get_fiscal_balance(
    start_date="202001",
    end_date="202412"
)
```

!!! info "날짜 형식"
    재정수지는 월간 데이터이므로 `YYYYMM` 형식을 사용합니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 재정수지 (10억원) |
| `unit` | str | 단위 (십억원) |

### 시각화

```python
import ecos
import matplotlib.pyplot as plt

# 통합재정수지 추이
df = ecos.get_fiscal_balance(start_date="202001")

# 조원 단위로 변환
df['value_trillion'] = df['value'] / 1000

# 그래프
df.set_index('date')['value_trillion'].plot(
    kind='bar',
    title='통합재정수지 추이',
    ylabel='재정수지 (조원)',
    figsize=(14, 6),
    grid=True,
    color=['red' if x < 0 else 'blue' for x in df['value_trillion']]
)
plt.axhline(y=0, color='black', linestyle='-', linewidth=1)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

## 실전 활용 예제

### 재정수지 누적 분석

```python
import ecos

df = ecos.get_fiscal_balance(start_date="202001")

# 조원 단위로 변환
df['value_trillion'] = df['value'] / 1000

# 연도별 누적 재정수지 계산
df['year'] = df['date'].dt.year
annual_balance = df.groupby('year')['value_trillion'].sum().reset_index()
annual_balance.columns = ['연도', '누적수지']

print("연도별 통합재정수지 누적:")
print(annual_balance)

# 시각화
import matplotlib.pyplot as plt

annual_balance.plot(
    x='연도',
    y='누적수지',
    kind='bar',
    title='연도별 통합재정수지 누적',
    ylabel='누적 재정수지 (조원)',
    figsize=(10, 6),
    grid=True,
    legend=False,
    color=['red' if x < 0 else 'blue' for x in annual_balance['누적수지']]
)
plt.axhline(y=0, color='black', linestyle='-', linewidth=1)
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()
```

### 재정 건전성 평가

```python
import ecos

df = ecos.get_fiscal_balance(start_date="202001")

# 조원 단위로 변환
df['value_trillion'] = df['value'] / 1000

# 통계 분석
total_surplus = df[df['value_trillion'] > 0]['value_trillion'].sum()
total_deficit = df[df['value_trillion'] < 0]['value_trillion'].sum()
net_balance = df['value_trillion'].sum()

surplus_months = (df['value_trillion'] > 0).sum()
deficit_months = (df['value_trillion'] < 0).sum()

print("재정 건전성 분석:")
print(f"총 흑자: {total_surplus:.2f}조원 ({surplus_months}개월)")
print(f"총 적자: {total_deficit:.2f}조원 ({deficit_months}개월)")
print(f"순 재정수지: {net_balance:.2f}조원")
print(f"평균 월간 수지: {df['value_trillion'].mean():.2f}조원")

# 건전성 판단
if net_balance > 0:
    print("\n✅ 재정 흑자 상태")
elif net_balance > -10:
    print("\n⚠️ 소폭 재정 적자 상태")
else:
    print("\n❌ 대규모 재정 적자 상태")
```

### 계절성 분석

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

df = ecos.get_fiscal_balance(start_date="201001")

# 조원 단위로 변환
df['value_trillion'] = df['value'] / 1000

# 월별 평균 계산
df['month'] = df['date'].dt.month
monthly_avg = df.groupby('month')['value_trillion'].mean().reset_index()
monthly_avg.columns = ['월', '평균수지']

# 시각화
monthly_avg.plot(
    x='월',
    y='평균수지',
    kind='bar',
    title='월별 평균 재정수지 (계절성)',
    ylabel='평균 재정수지 (조원)',
    figsize=(12, 6),
    grid=True,
    legend=False,
    color=['red' if x < 0 else 'blue' for x in monthly_avg['평균수지']]
)
plt.axhline(y=0, color='black', linestyle='-', linewidth=1)
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()

print("\n월별 평균 재정수지:")
print(monthly_avg.to_string(index=False))
```

### 재정수지 vs GDP

```python
import ecos
import pandas as pd

# 데이터 조회
fiscal = ecos.get_fiscal_balance(start_date="202001")
gdp = ecos.get_gdp(frequency="Q", basis="nominal", start_date="2020Q1")

# 조원 단위로 변환
fiscal['value_trillion'] = fiscal['value'] / 1000

# 분기별 재정수지 합계
fiscal['year_quarter'] = fiscal['date'].dt.to_period('Q')
quarterly_fiscal = fiscal.groupby('year_quarter')['value_trillion'].sum().reset_index()
quarterly_fiscal.columns = ['분기', '재정수지']

print("분기별 재정수지:")
print(quarterly_fiscal)

# GDP 대비 재정수지 비율 분석 (개념적 예시)
# 주의: GDP는 성장률이므로 실제로는 GDP 절댓값이 필요함
print("\n참고: GDP 대비 재정수지 비율 계산을 위해서는")
print("      명목 GDP 절댓값이 필요합니다.")
```

## 다음 단계

- [금융시장 지표](financial-markets.md) - 주식, 채권 등 금융시장 지표
- [성장 지표](growth.md) - GDP 등 경제성장 지표
- [예제: 거시경제 대시보드](../examples/dashboard.md) - 재정과 다른 지표를 결합한 대시보드
