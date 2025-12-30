# 기본 사용법 예제

ecos-reader의 기본 사용법을 실전 예제로 배워봅니다.

## 준비

```python
import ecos

# API 키 설정 (환경 변수가 설정되어 있으면 생략 가능)
# ecos.set_api_key("your_api_key")
```

## 1. 금리 지표 조회

### 한국은행 기준금리

```python
import ecos

print("=" * 60)
print("1. 한국은행 기준금리")
print("=" * 60)

# 기준금리 조회 (최근 1년)
df_base_rate = ecos.get_base_rate()
print(df_base_rate)
print()

# 특정 기간 조회
df_base_rate_period = ecos.get_base_rate(start_date="202001", end_date="202312")
print(f"조회 건수: {len(df_base_rate_period)}개")
print()
```

출력 예시:

```
============================================================
1. 한국은행 기준금리
============================================================
        date  value unit
0 2024-01-01   3.50    %
1 2024-02-01   3.50    %
...

조회 건수: 48개
```

### 국고채 수익률

```python
import ecos

print("=" * 60)
print("2. 국고채 수익률")
print("=" * 60)

# 국고채 3년물
df_treasury_3y = ecos.get_treasury_yield(maturity="3Y")
print("국고채 3년물:")
print(df_treasury_3y.tail())
print()

# 국고채 10년물
df_treasury_10y = ecos.get_treasury_yield(maturity="10Y")
print("국고채 10년물:")
print(df_treasury_10y.tail())
print()
```

### 장단기 금리차

```python
import ecos

print("=" * 60)
print("3. 장단기 금리차 (10Y - 3Y)")
print("=" * 60)

# 장단기 금리차 계산
df_spread = ecos.get_yield_spread()
print(df_spread.tail())
print()
```

## 2. 물가 지표 조회

### 소비자물가지수 (CPI)

```python
import ecos

print("=" * 60)
print("4. 소비자물가지수 (CPI)")
print("=" * 60)

# CPI 조회
df_cpi = ecos.get_cpi()
print(df_cpi.tail())
print()

# 근원 CPI
df_core_cpi = ecos.get_core_cpi()
print("근원 CPI:")
print(df_core_cpi.tail())
print()
```

### 생산자물가지수 (PPI)

```python
import ecos

print("=" * 60)
print("5. 생산자물가지수 (PPI)")
print("=" * 60)

df_ppi = ecos.get_ppi()
print(df_ppi.tail())
print()
```

## 3. 성장 지표 조회

### GDP

```python
import ecos

print("=" * 60)
print("6. GDP")
print("=" * 60)

# 분기별 실질 GDP
df_gdp_q = ecos.get_gdp(frequency="Q", basis="real")
print("분기별 실질 GDP:")
print(df_gdp_q.tail())
print()

# 연간 명목 GDP
df_gdp_a = ecos.get_gdp(frequency="A", basis="nominal")
print("연간 명목 GDP:")
print(df_gdp_a.tail())
print()
```

## 4. 통화 지표 조회

### 통화량 (M2)

```python
import ecos

print("=" * 60)
print("7. 통화량 (M2)")
print("=" * 60)

df_m2 = ecos.get_money_supply(indicator="M2")
print(df_m2.tail())
print()
```

### 은행 대출

```python
import ecos

print("=" * 60)
print("8. 은행 대출")
print("=" * 60)

# 가계대출
df_household = ecos.get_bank_lending(sector="household")
print("가계대출:")
print(df_household.tail())
print()

# 기업대출
df_corporate = ecos.get_bank_lending(sector="corporate")
print("기업대출:")
print(df_corporate.tail())
print()

print("=" * 60)
print("예제 완료!")
print("=" * 60)
```

## 5. 데이터 시각화

### 기준금리 추이

```python
import ecos
import matplotlib.pyplot as plt

# 데이터 조회
df = ecos.get_base_rate(start_date="202001")

# 시각화
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['value'], marker='o', linewidth=2)
plt.title('한국은행 기준금리 추이', fontsize=14)
plt.xlabel('날짜')
plt.ylabel('금리 (%)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

### CPI vs 기준금리 비교

```python
import ecos
import pandas as pd
import matplotlib.pyplot as plt

# 데이터 조회
cpi = ecos.get_cpi(start_date="202001")
base_rate = ecos.get_base_rate(start_date="202001")

# 월 단위로 맞추기
base_rate['month'] = base_rate['date'].dt.to_period('M')
cpi['month'] = cpi['date'].dt.to_period('M')
base_rate_monthly = base_rate.groupby('month')['value'].last()

# 병합
merged = pd.merge(
    cpi.set_index('month')[['value']].rename(columns={'value': 'cpi'}),
    base_rate_monthly.rename('rate'),
    left_index=True,
    right_index=True,
    how='left'
)
merged['rate'] = merged['rate'].fillna(method='ffill')
merged = merged.reset_index()

# 이중 축 그래프
fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.plot(merged['month'].astype(str), merged['cpi'], 'b-', label='CPI', linewidth=2)
ax1.set_xlabel('기간')
ax1.set_ylabel('CPI (%)', color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
ax2.plot(merged['month'].astype(str), merged['rate'], 'r-', label='기준금리', linewidth=2)
ax2.set_ylabel('기준금리 (%)', color='r')
ax2.tick_params(axis='y', labelcolor='r')

plt.title('CPI vs 기준금리')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

## 6. 에러 처리

### 안전한 데이터 조회

```python
import ecos
from ecos import EcosAPIError, EcosConfigError, EcosNetworkError

def safe_fetch(func, *args, **kwargs):
    """안전하게 데이터를 조회하는 헬퍼 함수"""
    try:
        return func(*args, **kwargs)
    except EcosConfigError as e:
        print(f"❌ API 키 설정 오류: {e}")
        return None
    except EcosNetworkError as e:
        print(f"❌ 네트워크 오류: {e}")
        return None
    except EcosAPIError as e:
        print(f"❌ API 오류 [{e.code}]: {e.message}")
        return None
    except Exception as e:
        print(f"❌ 알 수 없는 오류: {e}")
        return None

# 사용 예시
base_rate = safe_fetch(ecos.get_base_rate)
if base_rate is not None:
    print("✅ 기준금리 조회 성공")
    print(base_rate.tail())
else:
    print("⚠️ 기준금리 조회 실패")

cpi = safe_fetch(ecos.get_cpi, start_date="202001")
if cpi is not None:
    print("✅ CPI 조회 성공")
    print(cpi.tail())
```

## 7. 여러 지표 동시 조회

```python
import ecos
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def fetch_all_indicators():
    """여러 지표를 병렬로 조회"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            'base_rate': executor.submit(ecos.get_base_rate),
            'cpi': executor.submit(ecos.get_cpi),
            'gdp': executor.submit(ecos.get_gdp, "Q", "real"),
            'm2': executor.submit(ecos.get_money_supply, "M2")
        }

        results = {}
        for name, future in futures.items():
            try:
                results[name] = future.result()
                print(f"✅ {name} 조회 완료")
            except Exception as e:
                print(f"❌ {name} 조회 실패: {e}")
                results[name] = None

        return results

# 실행
data = fetch_all_indicators()

# 결과 확인
for name, df in data.items():
    if df is not None:
        print(f"\n{name}:")
        print(df.tail())
```

## 8. 데이터 저장

### CSV 파일로 저장

```python
import ecos

# 데이터 조회
df = ecos.get_base_rate(start_date="202001")

# CSV 저장
df.to_csv('base_rate.csv', index=False, encoding='utf-8-sig')
print("✅ base_rate.csv 저장 완료")

# 읽기
df_loaded = pd.read_csv('base_rate.csv')
print(df_loaded.head())
```

### Excel 파일로 저장

```python
import ecos
import pandas as pd

# 여러 지표 조회
base_rate = ecos.get_base_rate(start_date="202001")
cpi = ecos.get_cpi(start_date="202001")
gdp = ecos.get_gdp(frequency="Q", start_date="2020Q1")

# Excel 저장 (여러 시트)
with pd.ExcelWriter('macro_indicators.xlsx', engine='openpyxl') as writer:
    base_rate.to_excel(writer, sheet_name='기준금리', index=False)
    cpi.to_excel(writer, sheet_name='CPI', index=False)
    gdp.to_excel(writer, sheet_name='GDP', index=False)

print("✅ macro_indicators.xlsx 저장 완료")
```

## 전체 예제 코드

완전한 예제 코드는 [GitHub 저장소의 examples 디렉토리](https://github.com/choo121600/ecos-reader/tree/main/examples)에서 확인할 수 있습니다.

- `basic_usage.py` - 기본 사용법
- `macro_dashboard.py` - 거시경제 대시보드

## 다음 단계

- [거시경제 대시보드 예제](dashboard.md) - 실전 대시보드 구축
- [사용자 가이드](../user-guide/basic-usage.md) - 심화 사용법
