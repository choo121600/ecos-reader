# API 레퍼런스 개요

ecos-reader의 전체 API 문서입니다.

## 모듈 구조

```
ecos/
├── __init__.py          # Public API
├── client.py            # API 클라이언트
├── config.py            # 설정 관리
├── parser.py            # 응답 파서
├── exceptions.py        # 예외 클래스
├── constants.py         # 상수 정의
└── indicators/          # 지표 모듈
    ├── interest_rate.py
    ├── prices.py
    ├── growth.py
    └── money.py
```

## Public API

### 설정 함수

| 함수 | 설명 |
|-----|------|
| `set_api_key(key)` | API 키 설정 |
| `load_env()` | .env 파일에서 환경 변수 로드 |
| `set_client(client)` | 전역 기본 클라이언트 설정 |
| `setup_logging(level)` | 로깅 설정 |

### 캐시 관리

| 함수 | 설명 |
|-----|------|
| `enable_cache()` | 캐시 활성화 |
| `disable_cache()` | 캐시 비활성화 |
| `clear_cache()` | 캐시 초기화 |

### 금리 지표

| 함수 | 설명 |
|-----|------|
| `get_base_rate(start_date, end_date)` | 한국은행 기준금리 |
| `get_treasury_yield(maturity, start_date, end_date)` | 국고채 수익률 |
| `get_yield_spread(start_date, end_date)` | 장단기 금리차 |

### 물가 지표

| 함수 | 설명 |
|-----|------|
| `get_cpi(start_date, end_date)` | 소비자물가지수 |
| `get_core_cpi(start_date, end_date)` | 근원 CPI |
| `get_ppi(start_date, end_date)` | 생산자물가지수 |

### 성장 지표

| 함수 | 설명 |
|-----|------|
| `get_gdp(frequency, basis, start_date, end_date)` | GDP |
| `get_gdp_deflator(start_date, end_date)` | GDP 디플레이터 |

### 통화 지표

| 함수 | 설명 |
|-----|------|
| `get_money_supply(indicator, start_date, end_date)` | 통화량 |
| `get_bank_lending(sector, start_date, end_date)` | 은행 대출 |

## 클래스

### EcosClient

API 클라이언트 클래스

```python
from ecos import EcosClient

client = EcosClient(
    api_key=None,        # API 키 (기본값: 환경 변수)
    timeout=30,          # 타임아웃 (초)
    max_retries=3,       # 최대 재시도 횟수
    use_cache=True       # 캐시 사용 여부
)
```

#### 메서드

- `get_statistic_search(...)` - 통계 데이터 조회
- `get_statistic_table_list(...)` - 통계 목록 조회

### 예외 클래스

#### EcosConfigError

설정 관련 오류 (예: API 키 미설정)

```python
from ecos import EcosConfigError

try:
    df = ecos.get_base_rate()
except EcosConfigError as e:
    print(f"설정 오류: {e}")
```

#### EcosNetworkError

네트워크 연결 오류

```python
from ecos import EcosNetworkError

try:
    df = ecos.get_base_rate()
except EcosNetworkError as e:
    print(f"네트워크 오류: {e}")
```

#### EcosAPIError

API 응답 오류

```python
from ecos import EcosAPIError

try:
    df = ecos.get_base_rate()
except EcosAPIError as e:
    print(f"API 오류 [{e.code}]: {e.message}")
```

## 타입

모든 지표 함수는 `pandas.DataFrame`을 반환합니다.

### DataFrame 스키마

#### 기본 스키마

```python
{
    'date': datetime64[ns],  # 날짜
    'value': float64,        # 지표 값
    'unit': object           # 단위
}
```

#### 장단기 금리차 스키마

```python
{
    'date': datetime64[ns],     # 날짜
    'long_yield': float64,      # 10년물 수익률
    'short_yield': float64,     # 3년물 수익률
    'spread': float64,          # 금리차
    'unit': object              # 단위
}
```

## 상수

### 통계 코드

ecos-reader 내부에서 사용하는 통계 코드는 `ecos.constants` 모듈에 정의되어 있습니다.

### 날짜 형식

| 주기 | 형식 | 예시 |
|-----|------|------|
| 일간 | YYYYMMDD | 20240101 |
| 월간 | YYYYMM | 202401 |
| 분기 | YYYYQN | 2024Q1 |
| 연간 | YYYY | 2024 |

## 버전 정보

```python
import ecos

print(ecos.__version__)
```

## 다음 페이지

- [클라이언트 API](client.md) - EcosClient 상세 문서
- [지표 함수](indicators.md) - 모든 지표 함수 상세 문서
- [예외 처리](exceptions.md) - 예외 클래스 상세 문서
