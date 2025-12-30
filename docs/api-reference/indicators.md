# 지표 함수

모든 지표 조회 함수의 상세 레퍼런스입니다.

## 금리 지표

### get_base_rate

한국은행 기준금리를 조회합니다.

```python
def get_base_rate(
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    ...
```

#### 매개변수

- `start_date` (str, optional): 시작일 (YYYYMM 형식)
- `end_date` (str, optional): 종료일 (YYYYMM 형식)

#### 반환값

- **타입**: `pd.DataFrame`
- **컬럼**:
    - `date` (datetime64): 적용 시작일
    - `value` (float64): 기준금리 (%)
    - `unit` (object): 단위

#### 예시

```python
import ecos

# 최근 데이터
df = ecos.get_base_rate()

# 특정 기간
df = ecos.get_base_rate(start_date="202001", end_date="202412")
```

### get_treasury_yield

국고채 수익률을 조회합니다.

```python
def get_treasury_yield(
    maturity: str,
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    ...
```

#### 매개변수

- `maturity` (str): 만기 (`1Y`, `3Y`, `5Y`, `10Y`, `20Y`, `30Y`)
- `start_date` (str, optional): 시작일 (YYYYMMDD 형식)
- `end_date` (str, optional): 종료일 (YYYYMMDD 형식)

#### 반환값

- **타입**: `pd.DataFrame`
- **컬럼**:
    - `date` (datetime64): 조회일
    - `value` (float64): 수익률 (%)
    - `unit` (object): 단위

#### 예시

```python
import ecos

# 국고채 3년물
df = ecos.get_treasury_yield(maturity="3Y")

# 국고채 10년물 (특정 기간)
df = ecos.get_treasury_yield(
    maturity="10Y",
    start_date="20240101",
    end_date="20241231"
)
```

### get_yield_spread

10년물과 3년물 국고채 수익률의 차이를 계산합니다.

```python
def get_yield_spread(
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    ...
```

#### 매개변수

- `start_date` (str, optional): 시작일 (YYYYMMDD 형식)
- `end_date` (str, optional): 종료일 (YYYYMMDD 형식)

#### 반환값

- **타입**: `pd.DataFrame`
- **컬럼**:
    - `date` (datetime64): 조회일
    - `long_yield` (float64): 10년물 수익률 (%)
    - `short_yield` (float64): 3년물 수익률 (%)
    - `spread` (float64): 금리차 (%p)
    - `unit` (object): 단위

#### 예시

```python
import ecos

# 최근 데이터
df = ecos.get_yield_spread()

# 특정 기간
df = ecos.get_yield_spread(start_date="20240101", end_date="20241231")
```

## 물가 지표

### get_cpi

소비자물가지수 전년동월대비 상승률을 조회합니다.

```python
def get_cpi(
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    ...
```

#### 매개변수

- `start_date` (str, optional): 시작일 (YYYYMM 형식)
- `end_date` (str, optional): 종료일 (YYYYMM 형식)

#### 반환값

- **타입**: `pd.DataFrame`
- **컬럼**:
    - `date` (datetime64): 조회 월
    - `value` (float64): 전년동월대비 상승률 (%)
    - `unit` (object): 단위

#### 예시

```python
import ecos

df = ecos.get_cpi(start_date="202301", end_date="202312")
```

### get_core_cpi

근원 소비자물가지수를 조회합니다.

```python
def get_core_cpi(
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    ...
```

#### 매개변수

- `start_date` (str, optional): 시작일 (YYYYMM 형식)
- `end_date` (str, optional): 종료일 (YYYYMM 형식)

#### 반환값

- **타입**: `pd.DataFrame`
- **컬럼**: `get_cpi()`와 동일

#### 예시

```python
import ecos

df = ecos.get_core_cpi(start_date="202301", end_date="202312")
```

### get_ppi

생산자물가지수 전년동월대비 상승률을 조회합니다.

```python
def get_ppi(
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    ...
```

#### 매개변수

- `start_date` (str, optional): 시작일 (YYYYMM 형식)
- `end_date` (str, optional): 종료일 (YYYYMM 형식)

#### 반환값

- **타입**: `pd.DataFrame`
- **컬럼**: `get_cpi()`와 동일

#### 예시

```python
import ecos

df = ecos.get_ppi(start_date="202301", end_date="202312")
```

## 성장 지표

### get_gdp

GDP 증가율을 조회합니다.

```python
def get_gdp(
    frequency: str = "Q",
    basis: str = "real",
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    ...
```

#### 매개변수

- `frequency` (str, optional): 주기 (`Q`: 분기, `A`: 연간) (기본값: `"Q"`)
- `basis` (str, optional): 기준 (`real`: 실질, `nominal`: 명목) (기본값: `"real"`)
- `start_date` (str, optional): 시작일 (분기: YYYYQN, 연간: YYYY)
- `end_date` (str, optional): 종료일 (분기: YYYYQN, 연간: YYYY)

#### 반환값

- **타입**: `pd.DataFrame`
- **컬럼**:
    - `date` (datetime64): 조회 분기/연도
    - `value` (float64): GDP 증가율 (%)
    - `unit` (object): 단위

#### 예시

```python
import ecos

# 분기별 실질 GDP
df = ecos.get_gdp(frequency="Q", basis="real")

# 연간 명목 GDP
df = ecos.get_gdp(frequency="A", basis="nominal")

# 특정 기간
df = ecos.get_gdp(
    frequency="Q",
    basis="real",
    start_date="2020Q1",
    end_date="2024Q4"
)
```

### get_gdp_deflator

GDP 디플레이터 변화율을 조회합니다.

```python
def get_gdp_deflator(
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    ...
```

#### 매개변수

- `start_date` (str, optional): 시작일 (YYYYQN 형식)
- `end_date` (str, optional): 종료일 (YYYYQN 형식)

#### 반환값

- **타입**: `pd.DataFrame`
- **컬럼**:
    - `date` (datetime64): 조회 분기
    - `value` (float64): 전년동기대비 변화율 (%)
    - `unit` (object): 단위

#### 예시

```python
import ecos

df = ecos.get_gdp_deflator(start_date="2020Q1", end_date="2024Q4")
```

## 통화 지표

### get_money_supply

통화량을 조회합니다.

```python
def get_money_supply(
    indicator: str,
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    ...
```

#### 매개변수

- `indicator` (str): 통화량 지표 (`M1`, `M2`, `Lf`)
- `start_date` (str, optional): 시작일 (YYYYMM 형식)
- `end_date` (str, optional): 종료일 (YYYYMM 형식)

#### 반환값

- **타입**: `pd.DataFrame`
- **컬럼**:
    - `date` (datetime64): 조회 월
    - `value` (float64): 통화량 (10억원)
    - `unit` (object): 단위

#### 예시

```python
import ecos

# M2 통화량
df = ecos.get_money_supply(indicator="M2")

# M1 (특정 기간)
df = ecos.get_money_supply(
    indicator="M1",
    start_date="202001",
    end_date="202412"
)
```

### get_bank_lending

은행 대출 잔액을 조회합니다.

```python
def get_bank_lending(
    sector: str,
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    ...
```

#### 매개변수

- `sector` (str): 부문 (`household`: 가계, `corporate`: 기업, `total`: 전체)
- `start_date` (str, optional): 시작일 (YYYYMM 형식)
- `end_date` (str, optional): 종료일 (YYYYMM 형식)

#### 반환값

- **타입**: `pd.DataFrame`
- **컬럼**:
    - `date` (datetime64): 조회 월
    - `value` (float64): 대출 잔액 (10억원)
    - `unit` (object): 단위

#### 예시

```python
import ecos

# 가계대출
df = ecos.get_bank_lending(sector="household")

# 기업대출
df = ecos.get_bank_lending(sector="corporate")

# 전체 대출 (특정 기간)
df = ecos.get_bank_lending(
    sector="total",
    start_date="202001",
    end_date="202412"
)
```

## 공통 사항

### 날짜 형식

| 주기 | 형식 | 예시 |
|-----|------|------|
| 일간 | YYYYMMDD | 20240101 |
| 월간 | YYYYMM | 202401 |
| 분기 | YYYYQN | 2024Q1 |
| 연간 | YYYY | 2024 |

### 예외 처리

모든 함수는 다음 예외를 발생시킬 수 있습니다:

- `EcosConfigError` - API 키 미설정
- `EcosNetworkError` - 네트워크 오류
- `EcosAPIError` - API 응답 오류

```python
import ecos
from ecos import EcosAPIError, EcosConfigError, EcosNetworkError

try:
    df = ecos.get_base_rate()
except EcosConfigError:
    print("API 키를 설정하세요")
except EcosNetworkError:
    print("네트워크 연결을 확인하세요")
except EcosAPIError as e:
    print(f"API 오류: {e.message}")
```

## 다음 페이지

- [예외 처리](exceptions.md) - 예외 클래스 상세 문서
- [클라이언트 API](client.md) - EcosClient 상세 문서
