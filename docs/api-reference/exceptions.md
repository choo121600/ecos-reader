# 예외 처리

ecos-reader가 제공하는 예외 클래스 레퍼런스입니다.

## 예외 계층 구조

```
Exception
└── EcosError (기본 예외)
    ├── EcosConfigError
    ├── EcosNetworkError
    └── EcosAPIError
```

## EcosError

모든 ecos-reader 예외의 기본 클래스입니다.

```python
class EcosError(Exception):
    """Base exception for ecos-reader"""
    pass
```

### 사용

```python
from ecos import EcosError

try:
    df = ecos.get_base_rate()
except EcosError as e:
    # 모든 ecos-reader 예외를 잡습니다
    print(f"ECOS 오류: {e}")
```

## EcosConfigError

설정 관련 오류입니다. 주로 API 키가 설정되지 않았을 때 발생합니다.

```python
class EcosConfigError(EcosError):
    """Configuration error"""
    pass
```

### 발생 조건

- API 키가 설정되지 않은 경우
- 잘못된 설정 값을 사용한 경우

### 예시

```python
import ecos
from ecos import EcosConfigError

try:
    # API 키가 설정되지 않은 상태
    df = ecos.get_base_rate()
except EcosConfigError as e:
    print(f"설정 오류: {e}")
    print("해결 방법:")
    print("1. 환경 변수 설정: export ECOS_API_KEY='your_key'")
    print("2. 코드에서 설정: ecos.set_api_key('your_key')")
```

### 해결 방법

1. 환경 변수 설정

```bash
export ECOS_API_KEY="your_api_key"
```

2. 코드에서 설정

```python
import ecos
ecos.set_api_key("your_api_key")
```

3. .env 파일 사용

```python
import ecos
ecos.load_env()
```

## EcosNetworkError

네트워크 연결 오류입니다.

```python
class EcosNetworkError(EcosError):
    """Network error"""
    pass
```

### 발생 조건

- 인터넷 연결이 끊긴 경우
- ECOS 서버에 접속할 수 없는 경우
- 타임아웃이 발생한 경우
- DNS 오류

### 예시

```python
import ecos
from ecos import EcosNetworkError

try:
    df = ecos.get_base_rate()
except EcosNetworkError as e:
    print(f"네트워크 오류: {e}")
    print("인터넷 연결을 확인하세요.")
```

### 재시도 패턴

```python
import ecos
from ecos import EcosNetworkError
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        df = ecos.get_base_rate()
        print("성공!")
        break
    except EcosNetworkError as e:
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt
            print(f"재시도 {attempt + 1}/{max_retries} ({wait_time}초 대기)")
            time.sleep(wait_time)
        else:
            print("최대 재시도 횟수 초과")
            raise
```

## EcosAPIError

ECOS API 응답 오류입니다.

```python
class EcosAPIError(EcosError):
    """API error"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")
```

### 속성

- `code` (str): API 오류 코드
- `message` (str): 오류 메시지

### 발생 조건

- API가 오류 응답을 반환한 경우
- 잘못된 파라미터를 사용한 경우
- 데이터가 존재하지 않는 경우

### 주요 오류 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | 정상 | 요청은 성공했으나 데이터가 없을 수 있음 |
| 300 | 파라미터 오류 | 필수 파라미터 누락 |
| 310 | 통계코드 오류 | 잘못된 통계코드 |
| 311 | 주기 오류 | 잘못된 주기 값 |
| 320 | 기간 오류 | 잘못된 날짜 형식 |
| 500 | 서버 오류 | ECOS 서버 내부 오류 |
| 900 | 인증 오류 | 잘못된 API 키 |

### 예시

```python
import ecos
from ecos import EcosAPIError

try:
    df = ecos.get_base_rate()
except EcosAPIError as e:
    print(f"API 오류 코드: {e.code}")
    print(f"오류 메시지: {e.message}")

    if e.code == "900":
        print("해결: API 키가 잘못되었습니다. 키를 확인하세요.")
    elif e.code == "300":
        print("해결: 필수 파라미터를 확인하세요.")
    elif e.code == "500":
        print("해결: ECOS 서버 문제입니다. 잠시 후 다시 시도하세요.")
```

### 오류 코드별 처리

```python
import ecos
from ecos import EcosAPIError

def handle_api_error(e: EcosAPIError):
    """API 오류 코드에 따른 처리"""
    error_handlers = {
        "200": lambda: print("데이터가 없습니다."),
        "300": lambda: print("파라미터를 확인하세요."),
        "310": lambda: print("통계코드가 잘못되었습니다."),
        "500": lambda: print("서버 오류입니다. 나중에 다시 시도하세요."),
        "900": lambda: print("API 키가 잘못되었습니다."),
    }

    handler = error_handlers.get(e.code, lambda: print(f"알 수 없는 오류: {e.message}"))
    handler()

try:
    df = ecos.get_base_rate()
except EcosAPIError as e:
    handle_api_error(e)
```

## 모든 예외 처리

```python
import ecos
from ecos import EcosAPIError, EcosConfigError, EcosNetworkError, EcosError

try:
    df = ecos.get_base_rate()
    print(df)
except EcosConfigError as e:
    print(f"❌ 설정 오류: {e}")
    print("💡 API 키를 설정하세요.")
except EcosNetworkError as e:
    print(f"❌ 네트워크 오류: {e}")
    print("💡 인터넷 연결을 확인하세요.")
except EcosAPIError as e:
    print(f"❌ API 오류 [{e.code}]: {e.message}")
    if e.code == "900":
        print("💡 API 키를 확인하세요.")
    elif e.code == "500":
        print("💡 잠시 후 다시 시도하세요.")
except EcosError as e:
    # 기타 ecos 관련 오류
    print(f"❌ ECOS 오류: {e}")
except Exception as e:
    # 예상하지 못한 오류
    print(f"❌ 예상치 못한 오류: {e}")
```

## 로깅과 함께 사용

```python
import logging
import ecos
from ecos import EcosAPIError, EcosNetworkError, EcosConfigError

# 로깅 설정
ecos.setup_logging(logging.INFO)
logger = logging.getLogger(__name__)

try:
    df = ecos.get_base_rate()
except EcosConfigError as e:
    logger.error(f"Configuration error: {e}")
    raise
except EcosNetworkError as e:
    logger.warning(f"Network error: {e}")
    # 재시도 로직 등
except EcosAPIError as e:
    logger.error(f"API error [{e.code}]: {e.message}")
    # 오류 코드별 처리
```

## Best Practices

### 1. 구체적인 예외부터 처리

```python
try:
    df = ecos.get_base_rate()
except EcosConfigError:
    # 설정 오류 처리
    pass
except EcosNetworkError:
    # 네트워크 오류 처리
    pass
except EcosAPIError:
    # API 오류 처리
    pass
except EcosError:
    # 기타 ecos 오류 처리
    pass
```

### 2. 사용자에게 친화적인 메시지 제공

```python
try:
    df = ecos.get_base_rate()
except EcosConfigError:
    print("⚙️ API 키를 설정해주세요.")
    print("   https://ecos.bok.or.kr/api/ 에서 키를 발급받을 수 있습니다.")
except EcosNetworkError:
    print("🌐 인터넷 연결을 확인해주세요.")
except EcosAPIError as e:
    print(f"📊 데이터 조회 중 오류가 발생했습니다: {e.message}")
```

### 3. 적절한 로깅

```python
import logging
from ecos import EcosError

logger = logging.getLogger(__name__)

try:
    df = ecos.get_base_rate()
except EcosError as e:
    logger.exception("Failed to fetch base rate")
    # 상세 스택 트레이스와 함께 로깅됨
    raise
```

## 다음 페이지

- [클라이언트 API](client.md) - EcosClient 상세 문서
- [지표 함수](indicators.md) - 모든 지표 함수 상세 문서
