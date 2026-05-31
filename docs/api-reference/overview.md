# API 레퍼런스 개요

ecos-reader의 전체 API 문서입니다.

## 모듈 구조

```
ecos/
├── __init__.py          # Public API
├── access.py            # 범용 조회 (get_series, list_items)
├── catalog.py           # 통계표 카탈로그 탐색 (오프라인)
├── client.py            # API 클라이언트
├── config.py            # 설정 관리
├── cache.py             # 디스크 캐시
├── ratelimit.py         # rate limiter
├── metrics.py           # 호출 지표
├── parser.py            # 응답 파서
├── exceptions.py        # 예외 클래스
├── constants.py         # 통계코드 정의
├── data/catalog.csv.gz  # 동봉 카탈로그 스냅샷
└── indicators/          # 큐레이션 지표 모듈 (도메인별)
```

## Public API

ecos-reader는 두 진입점을 제공합니다. **범용 조회**(`get_series`)는 ECOS 전체에 도달하고,
**큐레이션 함수**(`get_*`)는 검증된 인자로 핵심 지표를 바로 노출합니다. 모든 함수는 정규화된
`pandas.DataFrame`을 반환합니다.

### 범용 조회 & 탐색

| 함수 | 설명 |
|-----|------|
| `get_series(stat_code, period, *, start_date, end_date, item_code=None, tidy=True, max_rows, page_size)` | 임의 통계표 조회 → long-format tidy. 윈도우 초과 시 자동 페이지네이션 |
| `list_items(stat_code)` | 표의 세부 항목(item_code/cycle) 탐색 |
| `search_tables(keyword, *, searchable_only=True)` | 카탈로그 키워드 검색 (오프라인) |
| `list_tables(parent=None)` | 부모 노드의 직계 자식 나열 (오프라인) |
| `get_table_tree()` | 전체 카탈로그를 중첩 트리로 반환 (오프라인) |
| `load_catalog()` | 카탈로그 전체 DataFrame |
| `parse_response`, `normalize_stat_result` | 응답 파서 헬퍼 (직접 가공용) |

자세한 사용법은 [범용 조회 & 탐색](../user-guide/universal-access.md) 가이드를 참고하세요.

### 설정 함수

| 함수 | 설명 |
|-----|------|
| `set_api_key(key)` | API 키 설정 |
| `get_api_key()` | 현재 API 키 조회 |
| `clear_api_key()` | API 키 해제 |
| `load_env()` | .env 파일에서 환경 변수 로드 |
| `set_client(client)` / `get_client()` / `reset_client()` | 전역 기본 클라이언트 관리 |
| `setup_logging(level)` | 로깅 설정 |

### 캐시·rate limit·지표

| 함수/클래스 | 설명 |
|-----|------|
| `enable_cache()` / `disable_cache()` | 캐시 활성화/비활성화 |
| `clear_cache()` | 캐시 초기화 |
| `DiskCache`, `get_disk_cache()` | 영속 디스크 캐시 |
| `RateLimiter`, `get_rate_limiter()` | 선제 throttle (대량 수집용) |
| `get_metrics_summary()`, `reset_metrics()` | API 호출 지표 |

### 큐레이션 지표 함수

도메인별 큐레이션 함수(37개)의 전체 목록과 시그니처는 [지표 함수](indicators.md)에서
자동 생성 docstring으로 확인할 수 있습니다. 도메인: 금리·물가·성장·통화/가계금융·실물경기·
심리·금융시장·환율·국제수지·무역·재정. 각 도메인의 활용법은 [사용자 가이드](../user-guide/basic-usage.md)를 참고하세요.

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

- `get_statistic_search(...)` - 통계 데이터 조회 (StatisticSearch)
- `get_statistic_item_list(...)` - 통계 세부항목 목록 (StatisticItemList)
- `get_statistic_table_list(...)` - 통계표 목록 (StatisticTableList)
- `get_statistic_word(...)` - 통계용어사전 검색 (StatisticWord)
- `get_key_statistic_list(...)` - 100대 통계지표 (KeyStatisticList)
- `get_statistic_meta(...)` - 통계 메타데이터 (StatisticMeta)

상세 시그니처는 [클라이언트 API](client.md)에서 확인하세요.

### 예외 클래스

7개 예외 클래스(`EcosError` 기반)가 있습니다. 전체 계층과 속성은
[예외 처리](exceptions.md)를 참고하세요. 아래는 자주 쓰는 세 가지입니다.

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
