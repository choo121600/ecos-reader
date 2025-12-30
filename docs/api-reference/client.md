# EcosClient

API 클라이언트 클래스입니다.

## 클래스 정의

```python
from ecos import EcosClient

class EcosClient:
    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
        use_cache: bool = True
    ):
        ...
```

## 생성자 매개변수

### api_key

- **타입**: `str | None`
- **기본값**: `None`
- **설명**: ECOS API 키. `None`이면 환경 변수 `ECOS_API_KEY`에서 읽어옵니다.

```python
# 환경 변수 사용
client = EcosClient()

# 직접 지정
client = EcosClient(api_key="your_api_key")
```

### timeout

- **타입**: `int`
- **기본값**: `30`
- **단위**: 초
- **설명**: HTTP 요청 타임아웃

```python
# 60초 타임아웃
client = EcosClient(timeout=60)
```

### max_retries

- **타입**: `int`
- **기본값**: `3`
- **설명**: 네트워크 오류 시 최대 재시도 횟수

```python
# 5회까지 재시도
client = EcosClient(max_retries=5)
```

### use_cache

- **타입**: `bool`
- **기본값**: `True`
- **설명**: API 응답 캐싱 여부

```python
# 캐시 비활성화
client = EcosClient(use_cache=False)
```

## 메서드

### get_statistic_search

통계 데이터를 조회합니다.

```python
def get_statistic_search(
    self,
    stat_code: str,
    period: str,
    start_date: str,
    end_date: str,
    item_code1: str = "?",
    item_code2: str = "?",
    item_code3: str = "?",
    item_code4: str = "?"
) -> dict:
    ...
```

#### 매개변수

- `stat_code` (str): 통계표 코드
- `period` (str): 주기 (`D`, `M`, `Q`, `A`)
- `start_date` (str): 시작일
- `end_date` (str): 종료일
- `item_code1` (str, optional): 아이템코드1 (기본값: `"?"`)
- `item_code2` (str, optional): 아이템코드2 (기본값: `"?"`)
- `item_code3` (str, optional): 아이템코드3 (기본값: `"?"`)
- `item_code4` (str, optional): 아이템코드4 (기본값: `"?"`)

#### 반환값

- **타입**: `dict`
- **설명**: ECOS API 응답 데이터

#### 예시

```python
from ecos import EcosClient

client = EcosClient()

response = client.get_statistic_search(
    stat_code="722Y001",
    period="M",
    start_date="202401",
    end_date="202412",
    item_code1="0101000"
)

print(response)
```

#### 예외

- `EcosConfigError` - API 키가 설정되지 않은 경우
- `EcosNetworkError` - 네트워크 오류
- `EcosAPIError` - API 응답 오류

### get_statistic_table_list

통계표 목록을 조회합니다.

```python
def get_statistic_table_list(
    self,
    stat_code: str = "",
    start: int = 1,
    end: int = 10000
) -> dict:
    ...
```

#### 매개변수

- `stat_code` (str, optional): 통계표 코드 (기본값: `""`)
- `start` (int, optional): 시작 건수 (기본값: `1`)
- `end` (int, optional): 종료 건수 (기본값: `10000`)

#### 반환값

- **타입**: `dict`
- **설명**: 통계표 목록 정보

#### 예시

```python
from ecos import EcosClient

client = EcosClient()

# 전체 통계표 목록 조회
tables = client.get_statistic_table_list(start=1, end=10)
print(tables)

# 특정 통계표 필터링
info = client.get_statistic_table_list(stat_code="722Y001")
print(info)
```

### get_statistic_item_list

통계표의 세부 항목 목록을 조회합니다.

```python
def get_statistic_item_list(
    self,
    stat_code: str,
    start: int = 1,
    end: int = 10000
) -> dict:
    ...
```

#### 매개변수

- `stat_code` (str): 통계표 코드
- `start` (int, optional): 시작 건수 (기본값: `1`)
- `end` (int, optional): 종료 건수 (기본값: `10000`)

#### 반환값

- **타입**: `dict`
- **설명**: 통계 세부항목 목록

#### 예시

```python
from ecos import EcosClient

client = EcosClient()

items = client.get_statistic_item_list(stat_code="200Y101", start=1, end=10)
print(items)
```

### get_statistic_word

통계용어사전을 검색합니다.

```python
def get_statistic_word(
    self,
    word: str,
    start: int = 1,
    end: int = 10
) -> dict:
    ...
```

#### 매개변수

- `word` (str): 검색할 통계 용어
- `start` (int, optional): 시작 건수 (기본값: `1`)
- `end` (int, optional): 종료 건수 (기본값: `10`)

#### 반환값

- **타입**: `dict`
- **설명**: 용어 검색 결과

#### 예시

```python
from ecos import EcosClient

client = EcosClient()

# 용어 검색
result = client.get_statistic_word(word="소비자물가지수")
print(result)

# GDP 검색
result = client.get_statistic_word(word="GDP")
print(result)
```

### get_key_statistic_list

한국은행이 선정한 100대 통계지표를 조회합니다.

```python
def get_key_statistic_list(
    self,
    start: int = 1,
    end: int = 100
) -> dict:
    ...
```

#### 매개변수

- `start` (int, optional): 시작 건수 (기본값: `1`)
- `end` (int, optional): 종료 건수 (기본값: `100`)

#### 반환값

- **타입**: `dict`
- **설명**: 주요 통계지표 목록

#### 예시

```python
from ecos import EcosClient

client = EcosClient()

# 처음 10개 조회
stats = client.get_key_statistic_list(start=1, end=10)
print(stats)

# 전체 100개 조회
all_stats = client.get_key_statistic_list(start=1, end=100)
print(all_stats)
```

### get_statistic_meta

통계 메타데이터를 조회합니다.

```python
def get_statistic_meta(
    self,
    data_name: str,
    start: int = 1,
    end: int = 10
) -> dict:
    ...
```

#### 매개변수

- `data_name` (str): 조회할 데이터명
- `start` (int, optional): 시작 건수 (기본값: `1`)
- `end` (int, optional): 종료 건수 (기본값: `10`)

#### 반환값

- **타입**: `dict`
- **설명**: 통계 메타데이터

#### 예시

```python
from ecos import EcosClient

client = EcosClient()

meta = client.get_statistic_meta(data_name="경제심리지수")
print(meta)
```

## 사용 예제

### 기본 사용

```python
from ecos import EcosClient

# 클라이언트 생성
client = EcosClient()

# 데이터 조회
response = client.get_statistic_search(
    stat_code="722Y001",
    period="M",
    start_date="202401",
    end_date="202412",
    item_code1="0101000"
)

# 응답 확인
if 'StatisticSearch' in response:
    rows = response['StatisticSearch']['row']
    for row in rows:
        print(f"{row['TIME']}: {row['DATA_VALUE']}")
```

### 커스텀 설정

```python
from ecos import EcosClient

# 프로덕션 환경 설정
client = EcosClient(
    api_key="your_api_key",
    timeout=60,
    max_retries=5,
    use_cache=False
)

# 사용
response = client.get_statistic_search(
    stat_code="722Y001",
    period="M",
    start_date="202401",
    end_date="202412",
    item_code1="0101000"
)
```

### 에러 처리

```python
from ecos import EcosClient, EcosAPIError, EcosNetworkError

client = EcosClient()

try:
    response = client.get_statistic_search(
        stat_code="722Y001",
        period="M",
        start_date="202401",
        end_date="202412",
        item_code1="0101000"
    )
except EcosNetworkError as e:
    print(f"네트워크 오류: {e}")
except EcosAPIError as e:
    print(f"API 오류 [{e.code}]: {e.message}")
```

### 전역 클라이언트로 설정

```python
import ecos
from ecos import EcosClient

# 커스텀 클라이언트 생성
custom_client = EcosClient(
    timeout=60,
    max_retries=5
)

# 전역 기본 클라이언트로 설정
ecos.set_client(custom_client)

# 이제 모든 지표 함수가 이 클라이언트를 사용
df = ecos.get_base_rate()
```

## 내부 동작

### 캐싱 메커니즘

`use_cache=True`인 경우, 동일한 요청은 메모리에 캐시됩니다:

1. 요청 매개변수로 캐시 키 생성
2. 캐시에 키가 있으면 즉시 반환
3. 없으면 API 호출 후 결과를 캐시에 저장

### 재시도 로직

네트워크 오류 시 지수 백오프(exponential backoff)로 재시도:

1. 첫 번째 재시도: 1초 대기
2. 두 번째 재시도: 2초 대기
3. 세 번째 재시도: 4초 대기
4. ...

### HTTP 세션

내부적으로 `requests.Session`을 사용하여 연결을 재사용합니다.

## 다음 페이지

- [지표 함수](indicators.md) - 모든 지표 함수 상세 문서
- [예외 처리](exceptions.md) - 예외 클래스 상세 문서
