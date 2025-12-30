# 기여 가이드 (Contributing Guide)

ecos-reader 프로젝트에 기여해주셔서 감사합니다!
이 문서는 프로젝트에 기여하는 방법을 안내합니다.

## 목차

1. [시작하기](#시작하기)
2. [개발 환경 설정](#개발-환경-설정)
3. [코드 작성 가이드](#코드-작성-가이드)
4. [새로운 지표 추가하기](#새로운-지표-추가하기)
5. [테스트 작성](#테스트-작성)
6. [Pull Request 제출](#pull-request-제출)
7. [코드 리뷰 프로세스](#코드-리뷰-프로세스)

---

## 시작하기

### 기여할 수 있는 방법

- **버그 리포트**: [Issues](https://github.com/choo121600/ecos-reader/issues)에서 버그 제보
- **기능 제안**: 새로운 지표나 기능 제안
- **문서 개선**: 오타 수정, 예제 추가, 설명 개선
- **코드 기여**: 새로운 지표 구현, 버그 수정, 성능 개선
- **테스트 추가**: 테스트 커버리지 향상

### 기여 전 확인사항

1. [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)에서 구현 현황 확인
2. [Issues](https://github.com/choo121600/ecos-reader/issues)에서 중복 여부 확인
3. 작업하고 싶은 내용이 있다면 Issue를 먼저 생성하여 논의

---

## 개발 환경 설정

### 1. Repository Fork 및 Clone

```bash
# Repository Fork (GitHub에서)
# https://github.com/choo121600/ecos-reader -> Fork 버튼 클릭

# Clone
git clone https://github.com/YOUR_USERNAME/ecos-reader.git
cd ecos-reader

# Upstream 설정
git remote add upstream https://github.com/choo121600/ecos-reader.git
```

### 2. Python 환경 설정

**필수 요구사항**: Python 3.10 이상

```bash
# Virtual environment 생성
python -m venv .venv

# Activate
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 개발 의존성 설치
pip install -e ".[dev]"
```

### 3. Pre-commit Hooks 설정

```bash
# Pre-commit hooks 설치
pre-commit install

# 수동으로 실행해보기
pre-commit run --all-files
```

Pre-commit hooks는 다음을 자동으로 체크합니다:
- 코드 포맷팅 (ruff-format)
- 린팅 (ruff)
- 타입 체킹 (mypy)
- 파일 끝 공백 제거
- YAML/TOML 문법 체크

### 4. ECOS API 키 설정

```bash
# .env 파일 생성
echo "ECOS_API_KEY=your_api_key_here" > .env

# 또는 환경 변수로 설정
export ECOS_API_KEY="your_api_key_here"
```

API 키 발급: https://ecos.bok.or.kr/api/

---

## 코드 작성 가이드

### 프로젝트 구조

```
ecos-reader/
├── src/ecos/
│   ├── __init__.py          # Public API
│   ├── client.py            # ECOS API 클라이언트
│   ├── config.py            # 설정 관리
│   ├── cache.py             # 캐싱 레이어
│   ├── parser.py            # 응답 파싱
│   ├── constants.py         # 통계코드 상수
│   ├── exceptions.py        # 예외 클래스
│   └── indicators/          # 지표 모듈
│       ├── __init__.py
│       ├── interest_rate.py # 금리 지표
│       ├── prices.py        # 물가 지표
│       ├── growth.py        # 성장 지표
│       └── money.py         # 통화 지표
├── tests/
│   ├── test_client.py
│   ├── test_e2e.py          # Low-level API E2E 테스트
│   └── test_e2e_indicators.py # High-level 지표 E2E 테스트
└── docs/                    # 문서
```

### 코드 스타일

프로젝트는 다음 도구들을 사용합니다:

- **ruff**: 린팅 및 포맷팅
- **mypy**: 정적 타입 체킹
- **pytest**: 테스팅

#### Type Hints

모든 함수에 타입 힌트를 추가해야 합니다:

```python
from __future__ import annotations

import pandas as pd

def get_indicator(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    지표를 조회합니다.

    Parameters
    ----------
    start_date : str, optional
        조회 시작일
    end_date : str, optional
        조회 종료일

    Returns
    -------
    pd.DataFrame
        조회된 데이터
    """
    pass
```

#### Docstrings

NumPy 스타일 docstring을 사용합니다:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    간단한 함수 설명 (한 줄)

    더 자세한 설명이 필요하면 여기에 작성합니다.

    Parameters
    ----------
    param1 : str
        첫 번째 파라미터 설명
    param2 : int
        두 번째 파라미터 설명

    Returns
    -------
    bool
        반환값 설명

    Examples
    --------
    >>> result = function_name("test", 42)
    >>> print(result)
    True

    Notes
    -----
    추가 참고사항이 있으면 여기에 작성
    """
    pass
```

---

## 새로운 지표 추가하기

### Step 1: ECOS에서 통계코드 찾기

```python
import ecos

# API 키 설정
ecos.set_api_key("your_api_key")

# 통계표 목록 조회
client = ecos.EcosClient()
tables = client.get_statistic_table_list(start=1, end=1000)

# 원하는 통계 검색
# 예: "환율" 검색
import pandas as pd
df = ecos.parser.parse_response(tables)
exchange_rate = df[df['stat_name'].str.contains('환율', na=False)]
print(exchange_rate[['stat_code', 'stat_name']])

# 항목 코드 확인
items = client.get_statistic_item_list(stat_code='731Y003')
df_items = ecos.parser.parse_response(items)
print(df_items[['item_code', 'item_name']].head())
```

### Step 2: constants.py에 추가

`src/ecos/constants.py`에 통계코드와 항목코드를 추가합니다:

```python
# ============================================================================
# 환율 지표 (forex)
# ============================================================================

STAT_EXCHANGE_RATE = "731Y003"

# 통화별 항목코드
EXCHANGE_RATE_ITEMS: dict[str, str] = {
    "USD": "0000001",  # 원/달러
    "JPY": "0000002",  # 원/100엔
    "EUR": "0000003",  # 원/유로
    "CNY": "0000053",  # 원/위안
}
```

### Step 3: 지표 함수 구현

적절한 카테고리 파일에 함수를 추가합니다 (예: `src/ecos/indicators/forex.py`):

```python
"""
환율 지표 모듈

주요 통화의 환율 정보를 조회합니다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import pandas as pd

from ..client import get_client
from ..constants import (
    EXCHANGE_RATE_ITEMS,
    PERIOD_DAILY,
    STAT_EXCHANGE_RATE,
)
from ..parser import normalize_stat_result, parse_response


def get_exchange_rate(
    currency: Literal["USD", "JPY", "EUR", "CNY"] = "USD",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    주요 통화의 환율을 조회합니다.

    Parameters
    ----------
    currency : str
        조회할 통화
        - 'USD': 미국 달러 (기본값)
        - 'JPY': 일본 엔
        - 'EUR': 유럽 유로
        - 'CNY': 중국 위안
    start_date : str, optional
        조회 시작일 (YYYYMMDD 형식), 기본값: 1년 전
    end_date : str, optional
        조회 종료일 (YYYYMMDD 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 환율
        - unit: 단위

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_exchange_rate(currency="USD")
    >>> df.head()
            date    value  unit
    0 2024-01-01  1200.5  원/USD

    >>> df = ecos.get_exchange_rate(currency="JPY")
    """
    if currency not in EXCHANGE_RATE_ITEMS:
        raise ValueError(
            f"currency는 {list(EXCHANGE_RATE_ITEMS.keys())} 중 하나여야 합니다."
        )

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        end_dt = datetime.now()
        start_dt = datetime(end_dt.year - 1, end_dt.month, end_dt.day)
        start_date = start_date or start_dt.strftime("%Y%m%d")
        end_date = end_date or end_dt.strftime("%Y%m%d")

    item_code = EXCHANGE_RATE_ITEMS[currency]

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_EXCHANGE_RATE,
        period=PERIOD_DAILY,
        start_date=start_date,
        end_date=end_date,
        item_code1=item_code,
    )

    df = parse_response(response)
    return normalize_stat_result(df)
```

### Step 4: __init__.py에 추가

`src/ecos/indicators/__init__.py`:

```python
from .forex import get_exchange_rate

__all__ = [
    # ... 기존 함수들
    "get_exchange_rate",
]
```

`src/ecos/__init__.py`:

```python
from .indicators import (
    # ... 기존 함수들
    get_exchange_rate,
)

__all__ = [
    # ... 기존 함수들
    "get_exchange_rate",
]
```

---

## 테스트 작성

### Unit Test

`tests/test_forex.py` 생성:

```python
"""환율 지표 유닛 테스트"""

import pandas as pd
import pytest

from ecos.indicators.forex import get_exchange_rate


class TestExchangeRate:
    """환율 조회 테스트"""

    def test_get_exchange_rate_usd(self, mock_client):
        """USD 환율 조회"""
        df = get_exchange_rate(currency="USD")

        assert isinstance(df, pd.DataFrame)
        assert "date" in df.columns
        assert "value" in df.columns

    def test_invalid_currency(self):
        """잘못된 통화 코드"""
        with pytest.raises(ValueError, match="currency는"):
            get_exchange_rate(currency="INVALID")
```

### E2E Test

`tests/test_e2e_indicators.py`에 추가:

```python
class TestE2EForexIndicators:
    """환율 지표 E2E 테스트"""

    def test_get_exchange_rate_usd(self):
        """USD 환율 조회"""
        df = ecos.get_exchange_rate(
            currency="USD",
            start_date="20230101",
            end_date="20231231"
        )

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_exchange_rate_jpy(self):
        """JPY 환율 조회"""
        df = ecos.get_exchange_rate(currency="JPY")

        assert not df.empty
        assert len(df) > 0
```

### 테스트 실행

```bash
# 전체 테스트
pytest

# 특정 파일만
pytest tests/test_forex.py -v

# E2E 테스트 (API 키 필요)
export ECOS_API_KEY="your_key"
pytest tests/test_e2e_indicators.py::TestE2EForexIndicators -v

# 커버리지 확인
pytest --cov=src/ecos --cov-report=html
```

---

## Pull Request 제출

### 1. Branch 생성

```bash
# Main branch를 최신으로 업데이트
git checkout main
git pull upstream main

# Feature branch 생성
git checkout -b feature/add-exchange-rate-indicator
```

Branch 이름 규칙:
- `feature/`: 새로운 기능
- `fix/`: 버그 수정
- `docs/`: 문서 개선
- `test/`: 테스트 추가/수정
- `refactor/`: 리팩토링

### 2. 변경사항 커밋

```bash
# 변경된 파일 확인
git status

# 파일 추가
git add src/ecos/indicators/forex.py
git add src/ecos/constants.py
git add tests/test_e2e_indicators.py

# 커밋 (pre-commit hooks가 자동 실행됨)
git commit -m "Add exchange rate indicator (get_exchange_rate)"
```

### 3. Push 및 PR 생성

```bash
# Fork한 repository에 push
git push origin feature/add-exchange-rate-indicator
```

GitHub에서:
1. Fork한 repository로 이동
2. "Compare & pull request" 버튼 클릭
3. PR 템플릿에 따라 설명 작성:

```markdown
## 변경 내용
환율 지표 조회 기능을 추가했습니다.

## 구현 사항
- [ ] `get_exchange_rate()` 함수 구현
- [ ] USD, JPY, EUR, CNY 지원
- [ ] E2E 테스트 추가
- [ ] 문서 업데이트

## 테스트
- [x] Unit tests 통과
- [x] E2E tests 통과
- [x] Pre-commit hooks 통과

## 관련 Issue
Closes #123

## 스크린샷
```python
>>> df = ecos.get_exchange_rate(currency="USD")
>>> df.head()
        date    value  unit
0 2024-01-01  1200.5  원/USD
```

### 4. PR 체크리스트

제출 전 확인:
- [ ] 모든 테스트 통과 (`pytest`)
- [ ] 타입 체크 통과 (`mypy src/ecos`)
- [ ] 린팅 통과 (`ruff check src/ecos`)
- [ ] 포맷팅 적용 (`ruff format src/ecos`)
- [ ] Docstring 작성 (NumPy 스타일)
- [ ] E2E 테스트 추가
- [ ] `__all__` 업데이트
- [ ] CHANGELOG.md 업데이트 (메인테이너가 할 수도 있음)

---

## 자주 묻는 질문

### Q: 어떤 지표를 먼저 구현해야 하나요?

A: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)의 우선순위를 참고하세요:
- 🔴 우선순위 1: 환율 및 국제수지
- 🟡 우선순위 2: 실물경제 및 심리지표
- 🟢 우선순위 3: 기타 중요 통계

### Q: API 키가 없어도 기여할 수 있나요?

A: 네! 다음 방법으로 기여 가능합니다:
- 문서 개선
- 코드 리팩토링
- 타입 힌트 추가
- Unit test 작성 (mock 사용)

### Q: 버그를 발견했는데 고치는 방법을 모르겠어요.

A: Issue를 생성해주세요! 버그 리포트만으로도 큰 도움이 됩니다.

### Q: 통계코드를 찾는 방법이 어렵습니다.

A: 다음 도구를 활용하세요:
1. `ecos_all_statistics.csv` 파일 참조
2. ECOS 공식 홈페이지에서 검색
3. Issue에 질문 남기기

---

## 도움 받기

- **질문**: [GitHub Discussions](https://github.com/choo121600/ecos-reader/discussions)
- **버그**: [GitHub Issues](https://github.com/choo121600/ecos-reader/issues)
- **기타**: Repository 메인테이너에게 연락

---
