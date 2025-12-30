# 기본 사용법

이 페이지에서는 ecos-reader의 기본적인 사용 방법과 패턴을 설명합니다.

## 라이브러리 임포트

```python
import ecos
```

## API 키 설정 방법

ecos-reader는 여러 가지 방법으로 API 키를 설정할 수 있습니다.

### 방법 1: 환경 변수 (권장)

가장 안전하고 권장되는 방법입니다.

```bash
export ECOS_API_KEY="your_api_key"
```

환경 변수가 설정되어 있으면 라이브러리가 자동으로 읽어옵니다:

```python
import ecos

# API 키가 자동으로 로드됨
df = ecos.get_base_rate()
```

### 방법 2: 코드에서 직접 설정

```python
import ecos

ecos.set_api_key("your_api_key")

df = ecos.get_base_rate()
```

!!! warning "주의"
    이 방법은 코드에 API 키가 노출될 수 있으므로 주의해서 사용하세요.

### 방법 3: .env 파일 사용

프로젝트 루트에 `.env` 파일 생성:

```
ECOS_API_KEY=your_api_key
```

Python 코드에서 명시적으로 로드:

```python
import ecos

ecos.load_env()  # .env 파일을 읽어서 환경 변수 설정

df = ecos.get_base_rate()
```

!!! info "버전 정보"
    v0.1.0부터는 라이브러리 import 시점에 `.env`를 자동으로 로드하지 않습니다.
    `.env`를 사용하려면 `ecos.load_env()`를 명시적으로 호출해야 합니다.

## 데이터 조회 기본 패턴

### 기본 조회

매개변수 없이 호출하면 최근 데이터를 반환합니다:

```python
import ecos

df = ecos.get_base_rate()
print(df)
```

### 기간 지정 조회

`start_date`와 `end_date`를 사용하여 특정 기간의 데이터를 조회할 수 있습니다:

```python
df = ecos.get_base_rate(
    start_date="202001",
    end_date="202312"
)
```

## 날짜 형식

지표의 빈도에 따라 적절한 날짜 형식을 사용해야 합니다.

### 월간 데이터

`YYYYMM` 형식 사용:

```python
df = ecos.get_cpi(
    start_date="202301",
    end_date="202312"
)
```

### 일간 데이터

`YYYYMMDD` 형식 사용:

```python
df = ecos.get_treasury_yield(
    maturity="3Y",
    start_date="20240101",
    end_date="20241231"
)
```

### 분기 데이터

`YYYYQN` 형식 사용 (Q1, Q2, Q3, Q4):

```python
df = ecos.get_gdp(
    frequency="Q",
    start_date="2020Q1",
    end_date="2024Q4"
)
```

### 연간 데이터

`YYYY` 형식 사용:

```python
df = ecos.get_gdp(
    frequency="A",
    start_date="2015",
    end_date="2024"
)
```

## DataFrame 구조

모든 지표 함수는 pandas DataFrame을 반환하며, 일반적으로 다음 컬럼을 포함합니다:

- `date`: 날짜 (datetime 타입)
- `value`: 지표 값 (float 타입)
- `unit`: 단위 (%, 조원 등)

예시:

```python
import ecos

df = ecos.get_base_rate()
print(df.dtypes)
```

```
date     datetime64[ns]
value           float64
unit             object
dtype: object
```

## 데이터 후처리

### 날짜 인덱스 설정

```python
df = ecos.get_base_rate()
df.set_index('date', inplace=True)
print(df)
```

### 특정 기간 필터링

```python
df = ecos.get_base_rate()

# 2024년 데이터만 추출
df_2024 = df[df['date'].dt.year == 2024]
```

### 통계 계산

```python
df = ecos.get_cpi(start_date="202001", end_date="202412")

# 기술 통계
print(df['value'].describe())

# 평균, 최댓값, 최솟값
print(f"평균: {df['value'].mean():.2f}")
print(f"최댓값: {df['value'].max():.2f}")
print(f"최솟값: {df['value'].min():.2f}")
```

### 데이터 시각화

```python
import ecos
import matplotlib.pyplot as plt

df = ecos.get_base_rate(start_date="202001")
df.set_index('date', inplace=True)

df['value'].plot(
    title='한국은행 기준금리 추이',
    ylabel='금리 (%)',
    figsize=(12, 6),
    grid=True
)
plt.show()
```

## 클라이언트 커스터마이징

기본 설정을 변경하려면 커스텀 클라이언트를 생성할 수 있습니다.

### 커스텀 클라이언트 생성

```python
from ecos import EcosClient

client = EcosClient(
    api_key="your_api_key",
    timeout=60,          # 타임아웃 (초)
    max_retries=5,       # 최대 재시도 횟수
    use_cache=True       # 캐시 사용 여부
)

# 직접 API 호출
response = client.get_statistic_search(
    stat_code="722Y001",
    period="M",
    start_date="202401",
    end_date="202412",
    item_code1="0101000"
)
```

### 전역 기본 클라이언트 교체

```python
import ecos
from ecos import EcosClient

# 커스텀 클라이언트 생성
custom_client = EcosClient(
    timeout=60,
    max_retries=5,
    use_cache=True
)

# 전역 기본 클라이언트로 설정
ecos.set_client(custom_client)

# 이제 모든 지표 함수가 커스텀 클라이언트를 사용
df = ecos.get_cpi()
```

## 여러 지표 동시 조회

여러 지표를 한 번에 조회하여 분석할 수 있습니다:

```python
import ecos
import pandas as pd

# 여러 지표 조회
base_rate = ecos.get_base_rate(start_date="202001", end_date="202412")
cpi = ecos.get_cpi(start_date="202001", end_date="202412")
gdp = ecos.get_gdp(frequency="Q", start_date="2020Q1", end_date="2024Q4")

# 데이터 병합 (날짜 기준)
merged = pd.merge(
    base_rate[['date', 'value']].rename(columns={'value': 'base_rate'}),
    cpi[['date', 'value']].rename(columns={'value': 'cpi'}),
    on='date',
    how='outer'
)

print(merged)
```

## 다음 단계

각 지표별 자세한 사용법은 다음 페이지를 참고하세요:

- [금리 지표](interest-rates.md) - 기준금리, 국고채 수익률 등
- [물가 지표](prices.md) - CPI, PPI 등
- [성장 지표](growth.md) - GDP, GDP 디플레이터 등
- [통화 지표](money.md) - 통화량, 은행 대출 등
- [고급 기능](advanced.md) - 캐시 관리, 에러 처리, 로깅 등
