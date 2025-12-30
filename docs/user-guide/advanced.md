# 고급 기능

캐시 관리, 에러 처리, 로깅 등 ecos-reader의 고급 기능을 설명합니다.

## 캐시 관리

ecos-reader는 기본적으로 API 응답을 캐시하여 동일한 요청을 빠르게 처리합니다.

### 캐시 활성화/비활성화

```python
import ecos

# 캐시 비활성화
ecos.disable_cache()

# 이제 모든 요청이 실제 API를 호출합니다
df1 = ecos.get_base_rate()
df2 = ecos.get_base_rate()  # API 재호출

# 캐시 다시 활성화
ecos.enable_cache()

# 이제 동일한 요청은 캐시에서 가져옵니다
df3 = ecos.get_base_rate()  # API 호출
df4 = ecos.get_base_rate()  # 캐시에서 반환
```

### 캐시 초기화

```python
import ecos

# 캐시된 모든 데이터 삭제
ecos.clear_cache()

# 다음 요청은 반드시 API를 호출합니다
df = ecos.get_base_rate()
```

### 캐시 사용 시나리오

캐시를 **활성화**하는 경우:

- 동일한 데이터를 반복적으로 조회할 때
- 개발/테스트 중 API 호출을 줄이고 싶을 때
- 분석 스크립트에서 여러 번 같은 데이터를 사용할 때

캐시를 **비활성화**하는 경우:

- 실시간으로 최신 데이터가 필요할 때
- 장시간 실행되는 프로그램에서 오래된 데이터를 방지하고 싶을 때
- 프로덕션 환경에서 데이터 정확성이 중요할 때

### 클라이언트별 캐시 설정

```python
from ecos import EcosClient

# 캐시를 사용하지 않는 클라이언트
no_cache_client = EcosClient(use_cache=False)

# 캐시를 사용하는 클라이언트
cached_client = EcosClient(use_cache=True)
```

## 에러 처리

ecos-reader는 다양한 상황에 대한 명확한 예외 클래스를 제공합니다.

### 예외 클래스

- `EcosConfigError` - API 키 설정 오류
- `EcosNetworkError` - 네트워크 연결 오류
- `EcosAPIError` - API 응답 오류

### 기본 에러 처리

```python
import ecos
from ecos import EcosAPIError, EcosConfigError, EcosNetworkError

try:
    df = ecos.get_base_rate()
    print(df)
except EcosConfigError as e:
    print(f"API 키 설정 오류: {e}")
    print("ECOS_API_KEY 환경 변수를 설정하거나 ecos.set_api_key()를 호출하세요.")
except EcosNetworkError as e:
    print(f"네트워크 오류: {e}")
    print("인터넷 연결을 확인하세요.")
except EcosAPIError as e:
    print(f"API 오류 [{e.code}]: {e.message}")
    if e.code == "200":
        print("정상 응답이지만 데이터가 없을 수 있습니다.")
    elif e.code == "300":
        print("필수 파라미터가 누락되었습니다.")
```

### API 오류 코드

한국은행 ECOS API의 주요 오류 코드:

- `200` - 정상 (데이터가 없을 수 있음)
- `300` - 필수 파라미터 누락
- `310` - 통계코드 오류
- `311` - 주기 오류
- `500` - 서비스 오류
- `900` - 인증키 오류

### 재시도 로직

```python
from ecos import EcosClient, EcosNetworkError
import time

client = EcosClient(max_retries=3)

max_attempts = 3
for attempt in range(max_attempts):
    try:
        response = client.get_statistic_search(
            stat_code="722Y001",
            period="M",
            start_date="202401",
            end_date="202412",
            item_code1="0101000"
        )
        print("성공!")
        break
    except EcosNetworkError as e:
        if attempt < max_attempts - 1:
            wait_time = 2 ** attempt  # 지수 백오프
            print(f"재시도 {attempt + 1}/{max_attempts} ({wait_time}초 대기)")
            time.sleep(wait_time)
        else:
            print(f"최대 재시도 횟수 초과: {e}")
            raise
```

### 안전한 데이터 조회

```python
import ecos
from ecos import EcosAPIError

def safe_get_indicator(func, *args, **kwargs):
    """
    안전하게 지표를 조회하는 헬퍼 함수
    """
    try:
        return func(*args, **kwargs)
    except EcosAPIError as e:
        print(f"경고: {func.__name__} 조회 실패 - {e.message}")
        return None
    except Exception as e:
        print(f"오류: {func.__name__} - {str(e)}")
        return None

# 사용 예시
base_rate = safe_get_indicator(ecos.get_base_rate)
cpi = safe_get_indicator(ecos.get_cpi, start_date="202001")

if base_rate is not None:
    print(base_rate.tail())
if cpi is not None:
    print(cpi.tail())
```

## 로깅

디버깅과 모니터링을 위해 로깅을 활성화할 수 있습니다.

### 로깅 설정

```python
import logging
import ecos

# 로깅 활성화
ecos.setup_logging(logging.INFO)

# 이제 API 호출 시 로그가 출력됩니다
df = ecos.get_base_rate()
```

출력 예시:

```
INFO:ecos.client:Requesting statistic_search: stat_code=722Y001, period=M
INFO:ecos.client:Response received: 12 records
INFO:ecos.parser:Parsed 12 rows
```

### 로그 레벨

```python
import logging
import ecos

# DEBUG - 상세한 디버그 정보
ecos.setup_logging(logging.DEBUG)

# INFO - 일반 정보
ecos.setup_logging(logging.INFO)

# WARNING - 경고
ecos.setup_logging(logging.WARNING)

# ERROR - 에러만
ecos.setup_logging(logging.ERROR)
```

### 파일로 로그 저장

```python
import logging
import ecos

# 파일 핸들러 추가
file_handler = logging.FileHandler('ecos.log')
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)

# 로거 가져오기
logger = logging.getLogger('ecos')
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# 이제 로그가 파일에 저장됩니다
df = ecos.get_base_rate()
```

## 타임아웃 및 재시도 설정

### 커스텀 타임아웃

```python
from ecos import EcosClient

# 60초 타임아웃
client = EcosClient(timeout=60)

# 클라이언트로 직접 조회
response = client.get_statistic_search(
    stat_code="722Y001",
    period="M",
    start_date="202401",
    end_date="202412",
    item_code1="0101000"
)
```

### 재시도 횟수 설정

```python
from ecos import EcosClient

# 최대 5회 재시도
client = EcosClient(max_retries=5)
```

### 전역 클라이언트 설정

```python
import ecos
from ecos import EcosClient

# 커스텀 설정으로 클라이언트 생성
custom_client = EcosClient(
    timeout=60,
    max_retries=5,
    use_cache=True
)

# 전역 기본 클라이언트로 설정
ecos.set_client(custom_client)

# 이제 모든 지표 함수가 커스텀 설정을 사용합니다
df = ecos.get_base_rate()
```

## 직접 API 호출

저수준 API에 직접 접근이 필요한 경우:

```python
from ecos import EcosClient

client = EcosClient()

# 통계 조회
response = client.get_statistic_search(
    stat_code="722Y001",      # 통계코드
    period="M",               # 주기 (D: 일, M: 월, Q: 분기, A: 년)
    start_date="202401",      # 시작일
    end_date="202412",        # 종료일
    item_code1="0101000"      # 아이템코드1
)

# 응답 데이터는 딕셔너리 형태
print(response.keys())
```

### 통계 목록 조회

```python
from ecos import EcosClient

client = EcosClient()

# 특정 통계 정보 조회
stat_info = client.get_statistic_table_list(
    stat_code="722Y001"
)

print(stat_info)
```

## 환경별 설정

### 개발 환경

```python
import ecos
import logging

# 개발 시 유용한 설정
ecos.setup_logging(logging.DEBUG)  # 상세 로그
ecos.enable_cache()                # 빠른 테스트를 위한 캐시
```

### 프로덕션 환경

```python
import ecos
import logging
from ecos import EcosClient

# 프로덕션 설정
ecos.setup_logging(logging.WARNING)  # 경고 이상만 로그
ecos.disable_cache()                  # 항상 최신 데이터

# 타임아웃과 재시도 설정
production_client = EcosClient(
    timeout=30,
    max_retries=3,
    use_cache=False
)
ecos.set_client(production_client)
```

### 테스트 환경

```python
import ecos
from unittest.mock import Mock

# 테스트 시 실제 API 호출을 피하기 위한 모킹
def mock_get_base_rate(*args, **kwargs):
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=12, freq='MS'),
        'value': [3.5] * 12,
        'unit': ['%'] * 12
    })

# 원본 함수 저장
original_func = ecos.get_base_rate

# 모킹
ecos.get_base_rate = mock_get_base_rate

# 테스트 실행
df = ecos.get_base_rate()
assert len(df) == 12

# 복원
ecos.get_base_rate = original_func
```

## 성능 최적화

### 배치 조회

여러 지표를 한 번에 조회할 때:

```python
import ecos
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

def fetch_indicator(func, *args, **kwargs):
    """지표를 조회하는 헬퍼 함수"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error in {func.__name__}: {e}")
        return None

# 병렬 조회
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        'base_rate': executor.submit(ecos.get_base_rate),
        'cpi': executor.submit(ecos.get_cpi),
        'gdp': executor.submit(ecos.get_gdp, "Q", "real"),
        'm2': executor.submit(ecos.get_money_supply, "M2")
    }

    results = {
        name: future.result()
        for name, future in futures.items()
    }

# 결과 사용
if results['base_rate'] is not None:
    print("기준금리:", results['base_rate'].tail())
```

### 데이터 전처리 파이프라인

```python
import ecos
import pandas as pd

def create_macro_dataset(start_date="202001"):
    """
    여러 지표를 하나의 데이터셋으로 통합
    """
    # 데이터 조회
    base_rate = ecos.get_base_rate(start_date=start_date)
    cpi = ecos.get_cpi(start_date=start_date)
    m2 = ecos.get_money_supply("M2", start_date=start_date)

    # 월 기준으로 통합
    base_rate['month'] = base_rate['date'].dt.to_period('M')
    cpi['month'] = cpi['date'].dt.to_period('M')
    m2['month'] = m2['date'].dt.to_period('M')

    # 기준금리 월별 전파
    base_rate_monthly = base_rate.groupby('month')['value'].last()

    # 병합
    dataset = cpi.set_index('month')[['value']].rename(columns={'value': 'cpi'})
    dataset['base_rate'] = base_rate_monthly
    dataset['m2'] = m2.set_index('month')['value']

    # 결측치 처리
    dataset['base_rate'] = dataset['base_rate'].fillna(method='ffill')

    return dataset.reset_index()

# 사용
df = create_macro_dataset()
print(df.head())
```

## 다음 단계

- [API 레퍼런스](../api-reference/overview.md) - 전체 API 문서
- [예제](../examples/basic.md) - 실전 예제 코드
