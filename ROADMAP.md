# ecos-reader v0.1.0 로드맵

> 📅 최종 수정: 2025년 12월
> 📌 버전: v0.1.0 (Initial Release)

---

## 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [릴리즈 목표](#릴리즈-목표)
3. [Phase 0: 프로젝트 기반 구축](#phase-0-프로젝트-기반-구축)
4. [Phase 1: 코어 인프라](#phase-1-코어-인프라)
5. [Phase 2: 핵심 거시 지표 API](#phase-2-핵심-거시-지표-api)
6. [Phase 3: 금융시장 지표](#phase-3-금융시장-지표)
7. [Phase 4: 경기 판단 보조 지표](#phase-4-경기-판단-보조-지표)
8. [릴리즈 기준](#릴리즈-기준-definition-of-done)
9. [프로젝트 구조](#프로젝트-구조)
10. [의존성](#의존성)
11. [향후 계획](#향후-계획)

---

## 프로젝트 개요

**ecos-reader**는 한국은행 ECOS Open API를 Python에서 쉽고 일관된 방식으로 사용할 수 있도록 만든 라이브러리입니다.

### 핵심 가치

| 가치 | 설명 |
|-----|------|
| **간결함** | 한 줄의 코드로 거시경제 데이터 조회 |
| **일관성** | 모든 결과를 pandas DataFrame으로 반환 |
| **신뢰성** | 견고한 에러 처리와 재시도 로직 |
| **확장성** | 모듈화된 설계로 새 지표 추가 용이 |

### 타겟 사용자

- 거시경제·금융 데이터 분석가
- 퀀트 리서처 및 투자 전략가
- 경제 리포트 자동화를 원하는 개발자
- 학술 연구자

---

## 릴리즈 목표

v0.1.0은 **안정적인 코어 인프라 구축**과 **핵심 거시 지표 API 제공**에 집중합니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                        v0.1.0 스코프                             │
├─────────────────────────────────────────────────────────────────┤
│  [필수] Phase 0: 프로젝트 기반 구축                               │
│  [필수] Phase 1: 코어 인프라                                     │
│  [필수] Phase 2: 핵심 거시 지표 (금리, 물가, 성장, 통화)            │
│  [선택] Phase 3: 금융시장 지표 (환율, 국제수지)                    │
│  [선택] Phase 4: 경기 판단 보조 지표 (실물, 심리)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: 프로젝트 기반 구축

### 목표
개발 환경과 프로젝트 구조를 설정하여 안정적인 개발 기반을 마련합니다.

### 작업 항목

| 작업 | 설명 | 산출물 |
|-----|------|--------|
| 프로젝트 구조 설계 | src 레이아웃 기반 패키지 구조 | `src/ecos/` 디렉토리 |
| pyproject.toml 설정 | 패키지 메타데이터 및 의존성 정의 | `pyproject.toml` |
| 개발 도구 설정 | 린터, 포매터, 테스트 도구 설정 | `ruff.toml`, `pytest.ini` |
| Git 설정 | .gitignore, pre-commit hooks | `.gitignore`, `.pre-commit-config.yaml` |
| CI/CD 설정 | GitHub Actions 워크플로우 | `.github/workflows/` |

### pyproject.toml 핵심 설정

```toml
[project]
name = "ecos-reader"
version = "0.1.0"
description = "한국은행 ECOS Open API Python 클라이언트"
requires-python = ">=3.10"
dependencies = [
    "requests>=2.28.0",
    "pandas>=2.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
```

---

## Phase 1: 코어 인프라

### 목표
ECOS API와 통신하는 핵심 인프라를 구축합니다. 이 레이어는 모든 지표 API의 기반이 됩니다.

### 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         Public API                              │
│                   (ecos.get_base_rate() 등)                     │
├─────────────────────────────────────────────────────────────────┤
│                      Indicator Modules                          │
│         (interest_rate.py, prices.py, growth.py 등)             │
├─────────────────────────────────────────────────────────────────┤
│                        Core Layer                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ EcosClient│ │  Config  │ │  Cache   │ │ Response Parser  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Error Handler                         │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                      ECOS Open API                              │
│                  (https://ecos.bok.or.kr)                       │
└─────────────────────────────────────────────────────────────────┘
```

### 1.1 Config Manager (`config.py`)

API Key 및 기본 설정을 관리합니다.

**기능 요구사항:**
- [ ] 환경 변수(`ECOS_API_KEY`)에서 API Key 로드
- [ ] `set_api_key()` 함수로 런타임에 API Key 설정
- [ ] `get_api_key()` 함수로 현재 API Key 조회
- [ ] API Key 미설정 시 명확한 에러 메시지

**API 설계:**
```python
# 환경 변수 방식
import ecos
# ECOS_API_KEY 환경 변수 자동 로드

# 직접 설정 방식
ecos.set_api_key("your_api_key")

# 조회
api_key = ecos.get_api_key()
```

### 1.2 API Client (`client.py`)

ECOS API와 HTTP 통신을 담당하는 핵심 클라이언트입니다.

**기능 요구사항:**
- [ ] ECOS API 엔드포인트 관리
- [ ] HTTP GET 요청 처리
- [ ] 요청 파라미터 구성 및 URL 인코딩
- [ ] 재시도 로직 (최대 3회, exponential backoff)
- [ ] 요청 타임아웃 설정 (기본 30초)
- [ ] Rate Limiting 준수 (분당 요청 수 제한)

**ECOS API 엔드포인트:**
```
Base URL: https://ecos.bok.or.kr/api/
서비스명:
  - StatisticSearch: 통계 조회
  - StatisticTableList: 통계표 목록
  - StatisticItemList: 통계 항목 목록
  - StatisticWord: 통계 용어 사전
  - KeyStatisticList: 주요 통계 지표
```

**요청 URL 포맷 (예: `StatisticItemList`)**

- **URL 규칙**: `https://ecos.bok.or.kr/api/{service}/{api_key}/{format}/{lang}/{start}/{end}/{stat_code}/`
- **테스트 URL 예시**: `https://ecos.bok.or.kr/api/StatisticItemList/sample/xml/kr/1/10/043Y070/`
  - `sample` 위치에 실제 **인증키(api_key)** 를 넣어 테스트

**요청 인자 (StatisticItemList)**

| 항목명(국문) | 필수여부 | 예시 | 설명 |
| --- | --- | --- | --- |
| 서비스명 | Y | `StatisticItemList` | API 서비스명 |
| 인증키 | Y | `sample` | 한국은행에서 발급받은 오픈API 인증키 |
| 요청유형 | Y | `xml` | 결과 파일 형식 (`xml`, `json`) |
| 언어구분 | Y | `kr` | 결과 언어 (`kr`, `en`) |
| 요청시작건수 | Y | `1` | 전체 결과값 중 시작 번호 |
| 요청종료건수 | Y | `10` | 전체 결과값 중 끝 번호 |
| 통계표코드 | Y | `601Y002` | 통계표코드 |

**출력 필드 (StatisticItemList)**

| 항목명(국문) | 항목명(영문) | 예시 | 설명 |
| --- | --- | --- | --- |
| 통계표코드 | `STAT_CODE` | `601Y002` | 통계표코드 |
| 통계명 | `STAT_NAME` | `7.5.2. ...` | 통계명 |
| 항목그룹코드 | `GRP_CODE` | `Group1` | 통계항목그룹코드 |
| 항목그룹명 | `GRP_NAME` | `지역코드` | 통계항목그룹명 |
| 통계항목코드 | `ITEM_CODE` | `A` | 통계항목코드 |
| 통계항목명 | `ITEM_NAME` | `서울` | 통계항목명 |
| 상위통계항목코드 | `P_ITEM_CODE` | `null` | 상위통계항목코드 |
| 상위통계항목명 | `P_ITEM_NAME` | `null` | 상위통계항목명 |
| 주기 | `CYCLE` | `M` | 주기 |
| 수록시작일자 | `START_TIME` | `200912` | 수록시작일자 |
| 수록종료일자 | `END_TIME` | `202112` | 수록종료일자 |
| 자료수 | `DATA_CNT` | `145` | 자료수 |
| 단위 | `UNIT_NAME` | `십억원` | 단위 |
| 가중치 | `WEIGHT` | `null` | 가중치 |

**클래스 설계:**
```python
class EcosClient:
    BASE_URL = "https://ecos.bok.or.kr/api/"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_api_key()
        self.session = requests.Session()

    def get(
        self,
        service: str,
        stat_code: str,
        period: str,
        start_date: str,
        end_date: str,
        item_code1: str = "",
        item_code2: str = "",
        item_code3: str = "",
    ) -> dict:
        """ECOS API 호출"""
        ...
```

### 1.3 Response Parser (`parser.py`)

ECOS API 응답을 pandas DataFrame으로 변환합니다.

**기능 요구사항:**
- [ ] JSON 응답 파싱
- [ ] DataFrame 컬럼명 정규화 (영문 snake_case)
- [ ] 날짜 컬럼 자동 파싱
- [ ] 수치 컬럼 타입 변환
- [ ] 빈 응답 처리 (빈 DataFrame 반환)

**컬럼 매핑:**
```python
COLUMN_MAP = {
    "STAT_CODE": "stat_code",
    "STAT_NAME": "stat_name",
    "ITEM_CODE1": "item_code1",
    "ITEM_NAME1": "item_name1",
    "TIME": "time",
    "DATA_VALUE": "value",
    "UNIT_NAME": "unit",
}
```

### 1.4 Error Handler (`exceptions.py`)

ECOS API 에러 및 라이브러리 예외를 처리합니다.

**예외 클래스 계층:**
```python
class EcosError(Exception):
    """ecos-reader 기본 예외"""
    pass

class EcosAPIError(EcosError):
    """ECOS API 호출 에러"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")

class EcosConfigError(EcosError):
    """설정 관련 에러 (API Key 등)"""
    pass

class EcosNetworkError(EcosError):
    """네트워크 연결 에러"""
    pass

class EcosRateLimitError(EcosError):
    """Rate Limit 초과"""
    pass
```

**ECOS 에러 코드 매핑:**
| 타입 | 코드 | 설명 | 처리 방안 |
| --- | --- | --- | --- |
| 정보 | `100` | 인증키가 유효하지 않습니다. 인증키를 확인하십시오! 인증키가 없는 경우 인증키를 신청하십시오! | `EcosConfigError` 발생 |
| 정보 | `200` | 해당하는 데이터가 없습니다. | **빈 DataFrame 반환** (예외 대신 정상 흐름) |
| 에러 | `100` | 필수 값이 누락되어 있습니다. 필수 값을 확인하십시오! | `EcosAPIError` 발생 (입력 검증/요청 구성 오류) |
| 에러 | `101` | 주기와 다른 형식의 날짜 형식입니다. | `EcosAPIError` 발생 (입력 검증) |
| 에러 | `200` | 파일타입 값이 누락 혹은 유효하지 않습니다. | `EcosAPIError` 발생 |
| 에러 | `300` | 조회건수 값이 누락되어 있습니다. | `EcosAPIError` 발생 |
| 에러 | `301` | 조회건수 값의 타입이 유효하지 않습니다. 정수를 입력하세요. | `EcosAPIError` 발생 |
| 에러 | `400` | 검색범위가 적정범위를 초과하여 60초 TIMEOUT이 발생하였습니다. | `EcosAPIError` 발생 (필요 시 범위 축소 가이드) |
| 에러 | `500` | 서버 오류입니다. 해당 서비스를 찾을 수 없습니다. | `EcosAPIError` 발생, **재시도 대상** |
| 에러 | `600` | DB Connection 오류입니다. | `EcosAPIError` 발생, **재시도 대상** |
| 에러 | `601` | SQL 오류입니다. | `EcosAPIError` 발생 |
| 에러 | `602` | 과도한 OpenAPI 호출로 이용이 제한되었습니다. | `EcosRateLimitError` 발생, **백오프 후 재시도** |

> 참고: 문서에 `100` 코드가 **정보/에러**로 모두 등장하므로, 구현 시에는 응답에서 제공되는 **메시지 타입(정보/에러) + 코드** 조합(또는 원문 메시지)을 함께 사용해 분기합니다.

### 1.5 Cache Layer (`cache.py`)

동일 요청에 대한 응답을 캐싱하여 API 호출을 최소화합니다.

**기능 요구사항:**
- [ ] 인메모리 LRU 캐시
- [ ] TTL(Time-To-Live) 기반 만료 (기본 1시간)
- [ ] 캐시 키 생성 (요청 파라미터 해시)
- [ ] 캐시 무효화 API
- [ ] 캐시 비활성화 옵션

**설계:**
```python
class Cache:
    def __init__(self, ttl: int = 3600, maxsize: int = 100):
        self.ttl = ttl
        self.maxsize = maxsize
        self._cache: dict[str, CacheEntry] = {}

    def get(self, key: str) -> dict | None: ...
    def set(self, key: str, value: dict) -> None: ...
    def clear(self) -> None: ...
    def invalidate(self, key: str) -> None: ...
```

---

## Phase 2: 핵심 거시 지표 API

### 목표
투자 분석과 경제 리서치에 가장 핵심적인 거시 지표 API를 구현합니다.

### 2.1 금리 지표 (`indicators/interest_rate.py`)

> 🎯 **우선순위: 최상**
> 금리는 모든 자산 가격의 기준이므로 가장 먼저 구현합니다.

#### `get_base_rate()`
한국은행 기준금리를 조회합니다.

```python
def get_base_rate(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    한국은행 기준금리 조회

    Parameters
    ----------
    start_date : str, optional
        조회 시작일 (YYYYMMDD), 기본값: 1년 전
    end_date : str, optional
        조회 종료일 (YYYYMMDD), 기본값: 오늘

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_base_rate()
    >>> df.head()
            date  value unit
    0 2024-01-01   3.50    %
    1 2024-02-01   3.50    %
    """
    ...
```

**ECOS 코드:**
- 통계코드: `722Y001`
- 항목코드: `0101000`

#### `get_treasury_yield()`
국고채 수익률을 조회합니다.

```python
def get_treasury_yield(
    maturity: Literal["1Y", "3Y", "5Y", "10Y", "20Y", "30Y"] = "3Y",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    국고채 수익률 조회

    Parameters
    ----------
    maturity : str
        만기 (1Y, 3Y, 5Y, 10Y, 20Y, 30Y)
    """
    ...
```

**ECOS 코드:**
- 통계코드: `817Y002`
- 항목코드: 만기별 상이

#### `get_yield_spread()`
장단기 금리차(10Y - 3Y)를 계산합니다.

```python
def get_yield_spread(
    long_maturity: str = "10Y",
    short_maturity: str = "3Y",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    국고채 장단기 금리차 (경기 침체 신호 지표)

    음수 전환 시 경기 침체 가능성 시사
    """
    ...
```

### 2.2 물가 지표 (`indicators/prices.py`)

> 🎯 **우선순위: 상**
> 물가는 통화정책 결정의 핵심 지표입니다.

#### `get_cpi()`
소비자물가지수 전년동월비를 조회합니다.

```python
def get_cpi(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    소비자물가지수(CPI) 전년동월비

    한국은행 물가안정목표(2%)의 기준 지표
    """
    ...
```

**ECOS 코드:**
- 통계코드: `901Y009`
- 항목코드: `0`

#### `get_core_cpi()`
근원 소비자물가지수(식료품·에너지 제외)를 조회합니다.

```python
def get_core_cpi(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    근원 CPI (식료품·에너지 제외)

    일시적 물가 변동 요인을 제거한 기조적 인플레이션
    """
    ...
```

#### `get_ppi()`
생산자물가지수 전년동월비를 조회합니다.

```python
def get_ppi(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    생산자물가지수(PPI) 전년동월비

    CPI의 선행 지표로 활용
    """
    ...
```

### 2.3 성장 지표 (`indicators/growth.py`)

> 🎯 **우선순위: 상**
> GDP는 경제 규모와 성장을 판단하는 핵심 지표입니다.

#### `get_gdp()`
국내총생산(GDP)을 조회합니다.

```python
def get_gdp(
    frequency: Literal["Q", "A"] = "Q",
    basis: Literal["real", "nominal"] = "real",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    국내총생산(GDP) 조회

    Parameters
    ----------
    frequency : str
        'Q': 분기, 'A': 연간
    basis : str
        'real': 실질 GDP, 'nominal': 명목 GDP

    Returns
    -------
    pd.DataFrame
        컬럼: period, value, yoy, qoq (분기인 경우)
    """
    ...
```

**ECOS 코드:**
- 실질 GDP: `200Y001`
- 명목 GDP: `200Y002`

#### `get_gdp_deflator()`
GDP 디플레이터를 조회합니다.

```python
def get_gdp_deflator(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    GDP 디플레이터

    실질 GDP와 명목 GDP의 비율로 계산되는 종합 물가지수
    """
    ...
```

### 2.4 통화 지표 (`indicators/money.py`)

> 🎯 **우선순위: 중**
> 유동성과 신용 사이클을 파악하는 지표입니다.

#### `get_money_supply()`
통화량을 조회합니다.

```python
def get_money_supply(
    indicator: Literal["M1", "M2", "Lf"] = "M2",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    통화량 조회

    Parameters
    ----------
    indicator : str
        'M1': 협의통화
        'M2': 광의통화 (가장 많이 사용)
        'Lf': 금융기관유동성
    """
    ...
```

**ECOS 코드:**
- 통계코드: `101Y018`

#### `get_bank_lending()`
은행 대출 증가율을 조회합니다.

```python
def get_bank_lending(
    sector: Literal["household", "corporate", "all"] = "all",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    은행 대출 증가율

    Parameters
    ----------
    sector : str
        'household': 가계대출
        'corporate': 기업대출
        'all': 전체
    """
    ...
```

---

## Phase 3: 금융시장 지표

### 목표
환율과 국제수지 등 금융시장에 직접 영향을 미치는 지표를 구현합니다.

### 3.1 환율 (`indicators/forex.py`)

#### `get_exchange_rate()`
원화 환율을 조회합니다.

```python
def get_exchange_rate(
    currency: Literal["USD", "JPY", "EUR", "CNY"] = "USD",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    원화 환율 조회

    Parameters
    ----------
    currency : str
        'USD': 원/달러
        'JPY': 원/100엔
        'EUR': 원/유로
        'CNY': 원/위안
    """
    ...
```

**ECOS 코드:**
- 통계코드: `731Y003`

#### `get_effective_exchange_rate()`
실효환율을 조회합니다.

```python
def get_effective_exchange_rate(
    basis: Literal["nominal", "real"] = "real",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    실효환율 조회

    교역 상대국 통화 대비 원화의 종합적인 가치
    """
    ...
```

### 3.2 국제수지 (`indicators/bop.py`)

#### `get_current_account()`
경상수지를 조회합니다.

```python
def get_current_account(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    경상수지 조회

    환율의 중장기 방향을 결정하는 핵심 지표
    """
    ...
```

#### `get_capital_flow()`
자본 유출입을 조회합니다.

```python
def get_capital_flow(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    자본수지 및 금융계정 조회

    외국인 자금 흐름과 금융시장 변동성 분석
    """
    ...
```

---

## Phase 4: 경기 판단 보조 지표

### 목표
경기 국면 분석에 활용되는 실물 및 심리 지표를 구현합니다.

### 4.1 실물 지표 (`indicators/real_economy.py`)

#### `get_industrial_production()`
산업생산지수를 조회합니다.

```python
def get_industrial_production(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    산업생산지수

    경기 동행 지표
    """
    ...
```

#### `get_facility_investment()`
설비투자지수를 조회합니다.

```python
def get_facility_investment(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    설비투자지수

    경기 선행 지표
    """
    ...
```

#### `get_retail_sales()`
소매판매지수를 조회합니다.

```python
def get_retail_sales(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    소매판매지수

    민간 소비 흐름 파악
    """
    ...
```

### 4.2 심리 지표 (`indicators/sentiment.py`)

#### `get_bsi()`
기업경기실사지수를 조회합니다.

```python
def get_bsi(
    sector: Literal["manufacturing", "non_manufacturing", "all"] = "all",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    기업경기실사지수(BSI)

    100 이상: 경기 호전 전망 우세
    100 미만: 경기 악화 전망 우세
    """
    ...
```

#### `get_csi()`
소비자심리지수를 조회합니다.

```python
def get_csi(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    소비자심리지수(CSI)

    100 이상: 소비 심리 긍정적
    100 미만: 소비 심리 부정적
    """
    ...
```

---

## 릴리즈 기준 (Definition of Done)

v0.1.0 릴리즈를 위해 아래 기준을 충족해야 합니다.

### 필수 요건

| 항목 | 기준 | 상태 |
|-----|------|------|
| 코어 인프라 | Phase 1 전체 완료 | ⬜ |
| 핵심 지표 | Phase 2 전체 완료 | ⬜ |
| 테스트 커버리지 | 80% 이상 | ⬜ |
| 타입 힌트 | 전체 public API 적용 | ⬜ |
| 문서화 | 모든 public API docstring | ⬜ |
| 예제 코드 | 각 지표별 사용 예시 | ⬜ |
| PyPI 배포 | `pip install ecos-reader` 가능 | ⬜ |

### 권장 요건

| 항목 | 기준 | 상태 |
|-----|------|------|
| 금융시장 지표 | Phase 3 완료 | ⬜ |
| 경기 판단 지표 | Phase 4 완료 | ⬜ |
| CI/CD | GitHub Actions 구축 | ⬜ |
| 문서 사이트 | mkdocs 기반 문서 | ⬜ |

---

## 프로젝트 구조

```
ecos-reader/
├── src/
│   └── ecos/
│       ├── __init__.py              # Public API export
│       ├── client.py                # EcosClient 클래스
│       ├── config.py                # 설정 관리
│       ├── cache.py                 # 캐시 레이어
│       ├── exceptions.py            # 커스텀 예외
│       ├── parser.py                # 응답 파서
│       ├── constants.py             # 상수 정의 (ECOS 코드 등)
│       └── indicators/              # 지표별 모듈
│           ├── __init__.py
│           ├── interest_rate.py     # 금리 (기준금리, 국채, 금리차)
│           ├── prices.py            # 물가 (CPI, 근원CPI, PPI)
│           ├── growth.py            # 성장 (GDP, GDP 디플레이터)
│           ├── money.py             # 통화 (M2, 대출)
│           ├── forex.py             # 환율 (원/달러, 실효환율)
│           ├── bop.py               # 국제수지 (경상수지, 자본)
│           ├── real_economy.py      # 실물 (산업생산, 설비투자, 소매)
│           └── sentiment.py         # 심리 (BSI, CSI)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # pytest fixtures
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_cache.py
│   ├── test_parser.py
│   └── indicators/
│       ├── test_interest_rate.py
│       ├── test_prices.py
│       └── ...
├── docs/
│   ├── index.md
│   ├── quickstart.md
│   ├── api/
│   └── examples/
├── examples/
│   ├── basic_usage.py
│   ├── macro_dashboard.py
│   └── ...
├── .github/
│   └── workflows/
│       ├── test.yml
│       └── publish.yml
├── pyproject.toml
├── README.md
├── ROADMAP.md
├── CHANGELOG.md
└── LICENSE
```

---

## 의존성

### 런타임 의존성

| 패키지 | 버전 | 용도 |
|-------|------|------|
| `requests` | >=2.28.0 | HTTP 클라이언트 |
| `pandas` | >=2.0.0 | 데이터 처리 |
| `python-dotenv` | >=1.0.0 | 환경 변수 관리 |

### 개발 의존성

| 패키지 | 버전 | 용도 |
|-------|------|------|
| `pytest` | >=7.0.0 | 테스트 프레임워크 |
| `pytest-cov` | >=4.0.0 | 커버리지 측정 |
| `ruff` | >=0.1.0 | 린터 & 포매터 |
| `mypy` | >=1.0.0 | 타입 체커 |
| `responses` | >=0.23.0 | HTTP 목킹 |

---

## 향후 계획

### v0.2.0 (예정)

- [ ] 비동기 API 지원 (`aiohttp` 기반)
- [ ] 데이터 시각화 유틸리티
- [ ] 지표 간 비교/분석 기능
- [ ] 더 많은 ECOS 통계 지표 추가

### v0.3.0 (예정)

- [ ] 데이터 캐싱 영속화 (SQLite/Redis)
- [ ] 자동 데이터 업데이트 스케줄러
- [ ] Jupyter Notebook 위젯

---

## 참고 자료

- [한국은행 ECOS Open API](https://ecos.bok.or.kr/api/)
- [ECOS Open API 개발 가이드](https://ecos.bok.or.kr/api/#/)
- [한국은행 경제통계시스템](https://ecos.bok.or.kr/)

---

> 📝 이 문서는 프로젝트 진행에 따라 지속적으로 업데이트됩니다.
