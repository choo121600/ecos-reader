# ecos-reader
**한국은행 ECOS Open API Python 클라이언트**

한국은행 ECOS Open API를 Python에서 쉽고 일관된 방식으로 사용할 수 있는 라이브러리입니다.


## 설치

```bash
pip install ecos-reader
```

또는 개발 버전 설치:

```bash
git clone https://github.com/choo121600/ecos-reader.git
cd ecos-reader
pip install -e ".[dev]"
```

## API 키 설정

ECOS API를 사용하려면 한국은행에서 발급받은 API 키가 필요합니다.

[API 키 신청하기](https://ecos.bok.or.kr/api/)

### 방법 1: 환경 변수 (권장)

```bash
export ECOS_API_KEY="your_api_key"
```

또는 `.env` 파일 생성:

```
ECOS_API_KEY=your_api_key
```

> 참고: v0.1.0부터는 라이브러리 import 시점에 `.env`를 자동으로 로드하지 않습니다.
> `.env`를 사용하려면 아래처럼 `ecos.load_env()`를 한 번 호출하세요.

```python
import ecos

ecos.load_env()  # .env 로드 (명시적)
```

### 방법 2: 코드에서 직접 설정

```python
import ecos

ecos.set_api_key("your_api_key")
```

## 빠른 시작

```python
import ecos

# 한국은행 기준금리 조회
df = ecos.get_base_rate()
print(df)
#         date  value unit
# 0 2024-01-01   3.50    %
# 1 2024-02-01   3.50    %
# ...

# 소비자물가지수(CPI) 조회
df = ecos.get_cpi(start_date="202301", end_date="202312")
print(df)

# 국고채 수익률 조회
df = ecos.get_treasury_yield(maturity="10Y")
print(df)

# GDP 조회
df = ecos.get_gdp(frequency="Q", basis="real")
print(df)
```

## 지원 지표

### 금리 지표

| 함수 | 설명 |
|-----|------|
| `get_base_rate()` | 한국은행 기준금리 |
| `get_treasury_yield(maturity)` | 국고채 수익률 (1Y, 3Y, 5Y, 10Y, 20Y, 30Y) |
| `get_yield_spread()` | 장단기 금리차 |

### 물가 지표

| 함수 | 설명 |
|-----|------|
| `get_cpi()` | 소비자물가지수 전년동월비 |
| `get_core_cpi()` | 근원 CPI (식료품·에너지 제외) |
| `get_ppi()` | 생산자물가지수 전년동월비 |

### 성장 지표

| 함수 | 설명 |
|-----|------|
| `get_gdp(frequency, basis)` | GDP (분기/연간, 실질/명목) |
| `get_gdp_deflator()` | GDP 디플레이터 |

### 통화 지표

| 함수 | 설명 |
|-----|------|
| `get_money_supply(indicator)` | 통화량 (M1, M2, Lf) |
| `get_bank_lending(sector)` | 은행 대출 (가계/기업/전체) |

## 상세 사용법

### 기간 지정

```python
# 월간 데이터 (YYYYMM 형식)
df = ecos.get_base_rate(start_date="202001", end_date="202312")

# 일간 데이터 (YYYYMMDD 형식)
df = ecos.get_treasury_yield(maturity="3Y", start_date="20240101", end_date="20241231")

# 분기 데이터 (YYYYQN 형식)
df = ecos.get_gdp(frequency="Q", start_date="2020Q1", end_date="2024Q4")

# 연간 데이터 (YYYY 형식)
df = ecos.get_gdp(frequency="A", start_date="2015", end_date="2024")
```

### 캐시 관리

```python
import ecos

# 캐시 비활성화
ecos.disable_cache()

# 캐시 활성화
ecos.enable_cache()

# 캐시 초기화
ecos.clear_cache()
```

### 에러 처리

```python
import ecos
from ecos import EcosAPIError, EcosConfigError, EcosNetworkError

try:
    df = ecos.get_base_rate()
except EcosConfigError as e:
    print(f"API 키 설정 오류: {e}")
except EcosNetworkError as e:
    print(f"네트워크 오류: {e}")
except EcosAPIError as e:
    print(f"API 오류 [{e.code}]: {e.message}")
```

### 로깅 활성화(선택)

라이브러리는 import 시점에 로깅 핸들러를 자동으로 구성하지 않습니다. 필요 시 아래처럼 활성화하세요.

```python
import logging
import ecos

ecos.setup_logging(logging.INFO)
```

### 직접 클라이언트 사용

```python
from ecos import EcosClient

# 클라이언트 생성
client = EcosClient(
    api_key="your_api_key",
    timeout=60,
    max_retries=5,
    use_cache=True,
)

# 통계 데이터 조회
response = client.get_statistic_search(
    stat_code="722Y001",
    period="M",
    start_date="202401",
    end_date="202412",
    item_code1="0101000",
)

# 통계표 목록 조회
tables = client.get_statistic_table_list(start=1, end=10)

# 통계 세부항목 조회
items = client.get_statistic_item_list(stat_code="200Y101")

# 통계용어사전 검색
word_result = client.get_statistic_word(word="소비자물가지수")

# 100대 통계지표 조회
key_stats = client.get_key_statistic_list(start=1, end=10)

# 통계 메타데이터 조회
meta = client.get_statistic_meta(data_name="경제심리지수")
```

### 전역 기본 클라이언트 주입(선택)

indicator 함수들이 사용할 “기본 클라이언트”를 교체하고 싶다면 아래처럼 설정할 수 있습니다.

```python
import ecos
from ecos import EcosClient

custom = EcosClient(timeout=60, max_retries=5, use_cache=True)
ecos.set_client(custom)

df = ecos.get_cpi()  # custom 클라이언트 사용
```

## 테스트

```bash
# 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src/ecos

# 특정 테스트만 실행
pytest tests/test_config.py -v
```

## 프로젝트 구조

```
ecos-reader/
├── src/ecos/
│   ├── __init__.py          # Public API
│   ├── client.py            # API 클라이언트
│   ├── config.py            # 설정 관리
│   ├── cache.py             # 캐시 레이어
│   ├── parser.py            # 응답 파서
│   ├── exceptions.py        # 예외 클래스
│   ├── constants.py         # 상수 정의
│   └── indicators/          # 지표 모듈
│       ├── interest_rate.py # 금리
│       ├── prices.py        # 물가
│       ├── growth.py        # 성장
│       └── money.py         # 통화
├── tests/                   # 테스트 코드
├── examples/                # 예제 코드
├── docs/                    # 문서
├── pyproject.toml
└── README.md
```

## 문서

전체 문서는 [ecos-reader 공식 문서](https://choo121600.github.io/ecos-reader/)에서 확인할 수 있습니다.

### 로컬에서 문서 빌드

```bash
# 문서 도구 설치
pip install -e ".[docs]"

# 로컬 서버 실행
mkdocs serve

# 브라우저에서 http://127.0.0.1:8000 열기
```

# 라이센스
MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
