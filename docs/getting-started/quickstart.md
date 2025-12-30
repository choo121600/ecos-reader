# 빠른 시작

이 가이드는 ecos-reader의 기본 사용법을 빠르게 익힐 수 있도록 돕습니다.

## API 키 설정

먼저 한국은행에서 발급받은 API 키를 설정합니다.

```python
import ecos

# 방법 1: 환경 변수 사용 (권장)
# export ECOS_API_KEY="your_api_key"

# 방법 2: 코드에서 직접 설정
ecos.set_api_key("your_api_key")

# 방법 3: .env 파일 사용
ecos.load_env()  # .env 파일 로드
```

!!! tip "권장 방법"
    환경 변수를 사용하는 방법이 가장 안전하고 권장됩니다.

## 기본 사용법

### 금리 지표 조회

```python
import ecos

# 한국은행 기준금리
df = ecos.get_base_rate()
print(df)
```

```
        date  value unit
0 2024-01-01   3.50    %
1 2024-02-01   3.50    %
...
```

### 국고채 수익률 조회

```python
# 국고채 3년물
df = ecos.get_treasury_yield(maturity="3Y")
print(df.tail())

# 국고채 10년물
df = ecos.get_treasury_yield(maturity="10Y")
print(df.tail())
```

### 물가 지표 조회

```python
# 소비자물가지수 (CPI)
df = ecos.get_cpi()
print(df.tail())

# 근원 CPI (식료품·에너지 제외)
df = ecos.get_core_cpi()
print(df.tail())

# 생산자물가지수 (PPI)
df = ecos.get_ppi()
print(df.tail())
```

### GDP 조회

```python
# 분기별 실질 GDP
df = ecos.get_gdp(frequency="Q", basis="real")
print(df.tail())

# 연간 명목 GDP
df = ecos.get_gdp(frequency="A", basis="nominal")
print(df.tail())
```

### 통화 지표 조회

```python
# M2 통화량
df = ecos.get_money_supply(indicator="M2")
print(df.tail())

# 가계대출
df = ecos.get_bank_lending(sector="household")
print(df.tail())

# 기업대출
df = ecos.get_bank_lending(sector="corporate")
print(df.tail())
```

## 기간 지정

모든 함수는 `start_date`와 `end_date` 매개변수를 지원합니다.

### 월간 데이터

```python
# YYYYMM 형식
df = ecos.get_base_rate(
    start_date="202001",
    end_date="202312"
)
```

### 일간 데이터

```python
# YYYYMMDD 형식
df = ecos.get_treasury_yield(
    maturity="3Y",
    start_date="20240101",
    end_date="20241231"
)
```

### 분기 데이터

```python
# YYYYQN 형식
df = ecos.get_gdp(
    frequency="Q",
    start_date="2020Q1",
    end_date="2024Q4"
)
```

### 연간 데이터

```python
# YYYY 형식
df = ecos.get_gdp(
    frequency="A",
    start_date="2015",
    end_date="2024"
)
```

## DataFrame 활용

반환된 DataFrame은 pandas의 모든 기능을 사용할 수 있습니다.

```python
import ecos
import matplotlib.pyplot as plt

# 기준금리 조회
df = ecos.get_base_rate(start_date="202001", end_date="202412")

# 날짜를 인덱스로 설정
df.set_index('date', inplace=True)

# 차트 그리기
df['value'].plot(
    title='한국은행 기준금리',
    ylabel='금리 (%)',
    figsize=(12, 6)
)
plt.show()

# 통계 정보
print(df.describe())

# 최댓값, 최솟값
print(f"최고 금리: {df['value'].max()}%")
print(f"최저 금리: {df['value'].min()}%")
```

## 에러 처리

API 호출 시 발생할 수 있는 에러를 처리합니다.

```python
from ecos import EcosAPIError, EcosConfigError, EcosNetworkError
import ecos

try:
    df = ecos.get_base_rate()
    print(df)
except EcosConfigError as e:
    print(f"API 키 설정 오류: {e}")
except EcosNetworkError as e:
    print(f"네트워크 오류: {e}")
except EcosAPIError as e:
    print(f"API 오류 [{e.code}]: {e.message}")
```

## 캐시 관리

기본적으로 캐시가 활성화되어 있어 동일한 요청을 반복할 때 빠르게 응답합니다.

```python
import ecos

# 캐시 비활성화
ecos.disable_cache()

# 캐시 활성화
ecos.enable_cache()

# 캐시 초기화
ecos.clear_cache()
```

## 로깅 설정

디버깅이나 모니터링을 위해 로깅을 활성화할 수 있습니다.

```python
import logging
import ecos

# 로깅 활성화
ecos.setup_logging(logging.INFO)

# 이제 API 호출 시 로그가 출력됩니다
df = ecos.get_base_rate()
```

로그 레벨:

- `logging.DEBUG` - 상세한 디버그 정보
- `logging.INFO` - 일반 정보
- `logging.WARNING` - 경고
- `logging.ERROR` - 에러

## 다음 단계

- [기본 사용법](../user-guide/basic-usage.md) - 더 자세한 사용법
- [금리 지표](../user-guide/interest-rates.md) - 금리 지표 활용
- [물가 지표](../user-guide/prices.md) - 물가 지표 활용
- [예제](../examples/basic.md) - 실전 예제 코드
