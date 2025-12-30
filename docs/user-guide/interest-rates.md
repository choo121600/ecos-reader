# 금리 지표

한국은행 기준금리와 국고채 수익률 등 금리 관련 지표를 조회하는 방법을 설명합니다.

## 한국은행 기준금리

한국은행 금융통화위원회에서 결정하는 기준금리를 조회합니다.

### 기본 사용법

```python
import ecos

# 최근 기준금리 조회
df = ecos.get_base_rate()
print(df)
```

### 기간 지정

```python
# 2020년 1월부터 2024년 12월까지
df = ecos.get_base_rate(
    start_date="202001",
    end_date="202412"
)
```

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 적용 시작일 |
| `value` | float | 기준금리 (%) |
| `unit` | str | 단위 (%) |

### 활용 예시

```python
import ecos
import matplotlib.pyplot as plt

# 최근 5년 기준금리 추이
df = ecos.get_base_rate(start_date="202001")

# 시각화
df.set_index('date')['value'].plot(
    title='한국은행 기준금리 추이',
    ylabel='금리 (%)',
    figsize=(12, 6),
    grid=True
)
plt.show()

# 통계
print(f"현재 금리: {df.iloc[-1]['value']}%")
print(f"평균 금리: {df['value'].mean():.2f}%")
print(f"최고 금리: {df['value'].max()}%")
print(f"최저 금리: {df['value'].min()}%")
```

## 국고채 수익률

국고채 각 만기별 수익률을 조회합니다.

### 지원 만기

- `1Y` - 국고채 1년
- `3Y` - 국고채 3년
- `5Y` - 국고채 5년
- `10Y` - 국고채 10년
- `20Y` - 국고채 20년
- `30Y` - 국고채 30년

### 기본 사용법

```python
import ecos

# 국고채 3년물
df = ecos.get_treasury_yield(maturity="3Y")
print(df.tail())

# 국고채 10년물
df = ecos.get_treasury_yield(maturity="10Y")
print(df.tail())
```

### 기간 지정

```python
# 2024년 데이터만 조회
df = ecos.get_treasury_yield(
    maturity="10Y",
    start_date="20240101",
    end_date="20241231"
)
```

!!! info "날짜 형식"
    국고채 수익률은 일간 데이터이므로 `YYYYMMDD` 형식을 사용합니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회일 |
| `value` | float | 수익률 (%) |
| `unit` | str | 단위 (%) |

### 여러 만기 비교

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# 여러 만기 조회
y3 = ecos.get_treasury_yield(maturity="3Y", start_date="20240101")
y5 = ecos.get_treasury_yield(maturity="5Y", start_date="20240101")
y10 = ecos.get_treasury_yield(maturity="10Y", start_date="20240101")

# 데이터 병합
merged = pd.merge(
    y3[['date', 'value']].rename(columns={'value': '3Y'}),
    y5[['date', 'value']].rename(columns={'value': '5Y'}),
    on='date'
)
merged = pd.merge(
    merged,
    y10[['date', 'value']].rename(columns={'value': '10Y'}),
    on='date'
)

# 수익률 곡선 시각화
merged.set_index('date').plot(
    title='국고채 수익률 추이',
    ylabel='수익률 (%)',
    figsize=(12, 6),
    grid=True
)
plt.legend(['3년', '5년', '10년'])
plt.show()
```

## 장단기 금리차

10년물과 3년물 국고채 수익률의 차이를 계산합니다.

### 기본 사용법

```python
import ecos

# 장단기 금리차 조회
df = ecos.get_yield_spread()
print(df.tail())
```

### 기간 지정

```python
df = ecos.get_yield_spread(
    start_date="20240101",
    end_date="20241231"
)
```

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회일 |
| `long_yield` | float | 10년물 수익률 (%) |
| `short_yield` | float | 3년물 수익률 (%) |
| `spread` | float | 금리차 (%p) |
| `unit` | str | 단위 (%p) |

### 금리 역전 감지

금리 역전(yield curve inversion)은 경기 침체의 선행 지표로 알려져 있습니다.

```python
import ecos

df = ecos.get_yield_spread()

# 최근 금리차
latest = df.iloc[-1]
spread = latest['spread']

# 금리 역전 여부 확인
if spread < 0:
    print(f"⚠️ 금리 역전 발생! ({spread:.2f}%p)")
    print("경기 침체 가능성에 주의하세요.")
elif spread < 0.5:
    print(f"⚡ 금리차 축소 ({spread:.2f}%p)")
    print("금리 역전 가능성을 모니터링하세요.")
else:
    print(f"✅ 정상 수익률 곡선 ({spread:.2f}%p)")
```

### 금리차 추이 시각화

```python
import ecos
import matplotlib.pyplot as plt

df = ecos.get_yield_spread(start_date="20200101")

# 그래프 생성
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# 수익률 추이
df.set_index('date')[['long_yield', 'short_yield']].plot(
    ax=ax1,
    title='국고채 수익률 추이',
    ylabel='수익률 (%)',
    grid=True
)
ax1.legend(['10년물', '3년물'])

# 금리차 추이
spread_plot = df.set_index('date')['spread'].plot(
    ax=ax2,
    title='장단기 금리차',
    ylabel='금리차 (%p)',
    grid=True,
    color='green'
)

# 0선 표시 (금리 역전 기준선)
ax2.axhline(y=0, color='red', linestyle='--', linewidth=1, label='역전 기준선')
ax2.fill_between(
    df.set_index('date').index,
    df.set_index('date')['spread'],
    0,
    where=(df.set_index('date')['spread'] < 0),
    color='red',
    alpha=0.3,
    label='역전 구간'
)
ax2.legend()

plt.tight_layout()
plt.show()
```

## 실전 활용 예제

### 금리 변동성 분석

```python
import ecos
import numpy as np

df = ecos.get_base_rate(start_date="202001")

# 금리 변화 계산
df['change'] = df['value'].diff()

# 변동성 통계
print("금리 변동 통계:")
print(f"평균 변화: {df['change'].mean():.4f}%p")
print(f"표준편차: {df['change'].std():.4f}%p")
print(f"최대 인상: {df['change'].max():.2f}%p")
print(f"최대 인하: {df['change'].min():.2f}%p")

# 인상/인하 횟수
raises = (df['change'] > 0).sum()
cuts = (df['change'] < 0).sum()
holds = (df['change'] == 0).sum()

print(f"\n금리 조정 현황:")
print(f"인상: {raises}회")
print(f"인하: {cuts}회")
print(f"동결: {holds}회")
```

### 금리 사이클 분석

```python
import ecos

df = ecos.get_base_rate(start_date="201001")

# 금리 피크와 저점 찾기
peak_value = df['value'].max()
trough_value = df['value'].min()

peak_date = df.loc[df['value'] == peak_value, 'date'].iloc[0]
trough_date = df.loc[df['value'] == trough_value, 'date'].iloc[0]

print(f"금리 사이클 분석:")
print(f"최고점: {peak_value}% ({peak_date.strftime('%Y-%m-%d')})")
print(f"최저점: {trough_value}% ({trough_date.strftime('%Y-%m-%d')})")
print(f"사이클 범위: {peak_value - trough_value}%p")
```

## 다음 단계

- [물가 지표](prices.md) - CPI, PPI 등 물가 지표 활용
- [성장 지표](growth.md) - GDP 등 성장 지표 활용
- [예제: 거시경제 대시보드](../examples/dashboard.md) - 금리와 다른 지표를 결합한 대시보드
