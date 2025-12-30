# 물가 지표

소비자물가지수(CPI), 생산자물가지수(PPI) 등 물가 관련 지표를 조회하는 방법을 설명합니다.

## 소비자물가지수 (CPI)

소비자가 구입하는 상품과 서비스의 가격 변동을 나타내는 지표입니다.

### 기본 사용법

```python
import ecos

# CPI 전년동월비 조회
df = ecos.get_cpi()
print(df.tail())
```

### 기간 지정

```python
# 2023년 전체 데이터
df = ecos.get_cpi(
    start_date="202301",
    end_date="202312"
)
```

!!! info "날짜 형식"
    CPI는 월간 데이터이므로 `YYYYMM` 형식을 사용합니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 전년동월대비 상승률 (%) |
| `unit` | str | 단위 (%) |

### 활용 예시

```python
import ecos
import matplotlib.pyplot as plt

# 최근 5년 CPI 추이
df = ecos.get_cpi(start_date="202001")

# 시각화
df.set_index('date')['value'].plot(
    title='소비자물가 상승률 추이',
    ylabel='전년동월비 (%)',
    figsize=(12, 6),
    grid=True
)

# 한국은행 물가안정목표 (2%) 표시
plt.axhline(y=2.0, color='red', linestyle='--', label='물가안정목표 (2%)')
plt.legend()
plt.show()

# 통계
print(f"현재 상승률: {df.iloc[-1]['value']}%")
print(f"평균 상승률: {df['value'].mean():.2f}%")
print(f"최고 상승률: {df['value'].max()}%")
print(f"최저 상승률: {df['value'].min()}%")
```

## 근원 CPI

식료품 및 에너지 가격을 제외한 근원 소비자물가지수입니다.

### 기본 사용법

```python
import ecos

# 근원 CPI 조회
df = ecos.get_core_cpi()
print(df.tail())
```

### 기간 지정

```python
df = ecos.get_core_cpi(
    start_date="202301",
    end_date="202312"
)
```

### CPI vs 근원 CPI 비교

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# 두 지표 조회
cpi = ecos.get_cpi(start_date="202001")
core_cpi = ecos.get_core_cpi(start_date="202001")

# 데이터 병합
merged = pd.merge(
    cpi[['date', 'value']].rename(columns={'value': 'CPI'}),
    core_cpi[['date', 'value']].rename(columns={'value': 'Core CPI'}),
    on='date'
)

# 시각화
merged.set_index('date').plot(
    title='CPI vs 근원 CPI',
    ylabel='전년동월비 (%)',
    figsize=(12, 6),
    grid=True
)
plt.axhline(y=2.0, color='red', linestyle='--', alpha=0.5, label='물가안정목표')
plt.legend()
plt.show()

# 차이 분석
merged['diff'] = merged['CPI'] - merged['Core CPI']
print(f"평균 차이: {merged['diff'].mean():.2f}%p")
print(f"최대 차이: {merged['diff'].max():.2f}%p")
```

## 생산자물가지수 (PPI)

생산자가 판매하는 상품과 서비스의 가격 변동을 나타내는 지표입니다.

### 기본 사용법

```python
import ecos

# PPI 전년동월비 조회
df = ecos.get_ppi()
print(df.tail())
```

### 기간 지정

```python
df = ecos.get_ppi(
    start_date="202301",
    end_date="202312"
)
```

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 월 |
| `value` | float | 전년동월대비 상승률 (%) |
| `unit` | str | 단위 (%) |

### PPI vs CPI 비교

PPI는 CPI의 선행 지표로 간주됩니다.

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# 두 지표 조회
ppi = ecos.get_ppi(start_date="202001")
cpi = ecos.get_cpi(start_date="202001")

# 데이터 병합
merged = pd.merge(
    ppi[['date', 'value']].rename(columns={'value': 'PPI'}),
    cpi[['date', 'value']].rename(columns={'value': 'CPI'}),
    on='date'
)

# 시각화
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# 추이 비교
merged.set_index('date')[['PPI', 'CPI']].plot(
    ax=ax1,
    title='생산자물가 vs 소비자물가',
    ylabel='전년동월비 (%)',
    grid=True
)

# 차이 시각화
merged['spread'] = merged['PPI'] - merged['CPI']
merged.set_index('date')['spread'].plot(
    ax=ax2,
    title='PPI - CPI 스프레드',
    ylabel='차이 (%p)',
    grid=True,
    color='purple'
)
ax2.axhline(y=0, color='black', linestyle='--', linewidth=0.5)

plt.tight_layout()
plt.show()
```

## 실전 활용 예제

### 인플레이션 압력 분석

```python
import ecos

# 최근 데이터 조회
cpi = ecos.get_cpi()
core_cpi = ecos.get_core_cpi()
ppi = ecos.get_ppi()

# 최신 값
latest_cpi = cpi.iloc[-1]['value']
latest_core = core_cpi.iloc[-1]['value']
latest_ppi = ppi.iloc[-1]['value']

print("=== 인플레이션 현황 ===")
print(f"CPI: {latest_cpi:.2f}%")
print(f"근원 CPI: {latest_core:.2f}%")
print(f"PPI: {latest_ppi:.2f}%")

# 분석
if latest_cpi > 3.0:
    print("\n⚠️ 높은 인플레이션 압력")
elif latest_cpi > 2.0:
    print("\n⚡ 물가안정목표 초과")
else:
    print("\n✅ 안정적 물가 수준")

# 추세 분석
cpi_trend = cpi.tail(3)['value'].mean()
if latest_cpi > cpi_trend:
    print("📈 상승 추세")
elif latest_cpi < cpi_trend:
    print("📉 하락 추세")
else:
    print("➡️ 보합 추세")
```

### 물가 목표 달성률 분석

```python
import ecos

df = ecos.get_cpi(start_date="202001")

# 물가안정목표 (2%) 대비 분석
df['deviation'] = df['value'] - 2.0
df['target_met'] = df['deviation'].abs() <= 0.5  # ±0.5%p 허용

# 통계
total_months = len(df)
months_met = df['target_met'].sum()
success_rate = (months_met / total_months) * 100

print(f"물가목표 달성 분석 (±0.5%p):")
print(f"전체 기간: {total_months}개월")
print(f"목표 달성: {months_met}개월")
print(f"달성률: {success_rate:.1f}%")
print(f"\n평균 괴리도: {df['deviation'].abs().mean():.2f}%p")
```

### 물가 상승 가속도 분석

```python
import ecos

df = ecos.get_cpi(start_date="202001")

# 변화율 계산
df['mom_change'] = df['value'].diff()  # 전월 대비 변화
df['acceleration'] = df['mom_change'].diff()  # 가속도

# 최근 추세
recent = df.tail(6)

print("최근 6개월 물가 추이:")
for _, row in recent.iterrows():
    date_str = row['date'].strftime('%Y-%m')
    value = row['value']
    change = row['mom_change']

    if pd.notna(change):
        trend = "↑" if change > 0 else "↓" if change < 0 else "→"
        print(f"{date_str}: {value:.2f}% ({trend} {abs(change):.2f}%p)")
    else:
        print(f"{date_str}: {value:.2f}%")
```

### 물가와 금리 관계 분석

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# 데이터 조회
cpi = ecos.get_cpi(start_date="202001")
base_rate = ecos.get_base_rate(start_date="202001")

# 월 단위로 맞추기 (기준금리는 변경 시점만 기록되므로)
base_rate['year_month'] = base_rate['date'].dt.to_period('M')
cpi['year_month'] = cpi['date'].dt.to_period('M')

# 기준금리를 월별로 전파
base_rate_monthly = base_rate.groupby('year_month')['value'].last()
merged = pd.merge(
    cpi.set_index('year_month')[['value']].rename(columns={'value': 'cpi'}),
    base_rate_monthly.rename('rate'),
    left_index=True,
    right_index=True,
    how='left'
)
merged['rate'] = merged['rate'].fillna(method='ffill')

# 상관관계 분석
correlation = merged['cpi'].corr(merged['rate'])
print(f"CPI-금리 상관계수: {correlation:.3f}")

# 시각화
fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.plot(merged.index.astype(str), merged['cpi'], 'b-', label='CPI')
ax1.set_xlabel('기간')
ax1.set_ylabel('CPI (%)', color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
ax2.plot(merged.index.astype(str), merged['rate'], 'r-', label='기준금리')
ax2.set_ylabel('기준금리 (%)', color='r')
ax2.tick_params(axis='y', labelcolor='r')

# x축 레이블 회전
plt.xticks(rotation=45)
plt.title('CPI vs 기준금리')
plt.tight_layout()
plt.show()
```

## 다음 단계

- [금리 지표](interest-rates.md) - 기준금리, 국고채 수익률 등
- [성장 지표](growth.md) - GDP 등 성장 지표 활용
- [통화 지표](money.md) - 통화량, 은행 대출 등
