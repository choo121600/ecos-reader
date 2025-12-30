# 기여하기

ecos-reader 프로젝트에 기여해주셔서 감사합니다!

## 개발 환경 설정

### 1. 저장소 포크 및 클론

```bash
# 포크 후 클론
git clone https://github.com/your-username/ecos-reader.git
cd ecos-reader

# 업스트림 추가
git remote add upstream https://github.com/choo121600/ecos-reader.git
```

### 2. 개발 의존성 설치

```bash
# 개발 도구 포함 설치
pip install -e ".[dev]"

# pre-commit 설정
pre-commit install
```

### 3. API 키 설정

```bash
# .env 파일 생성
echo "ECOS_API_KEY=your_api_key" > .env
```

## 개발 워크플로우

### 1. 브랜치 생성

```bash
# 최신 코드 가져오기
git checkout main
git pull upstream main

# 기능 브랜치 생성
git checkout -b feature/your-feature-name
```

### 2. 코드 작성

#### 코드 스타일

프로젝트는 다음 도구를 사용합니다:

- **ruff**: 린팅 및 포매팅
- **mypy**: 타입 체킹

```bash
# 린팅
ruff check src tests

# 포매팅
ruff format src tests

# 타입 체킹
mypy src
```

#### 타입 힌팅

모든 public 함수와 메서드에 타입 힌팅을 추가하세요:

```python
def get_base_rate(
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    """
    한국은행 기준금리를 조회합니다.

    Parameters
    ----------
    start_date : str, optional
        시작일 (YYYYMM 형식)
    end_date : str, optional
        종료일 (YYYYMM 형식)

    Returns
    -------
    pd.DataFrame
        기준금리 데이터
    """
    ...
```

### 3. 테스트 작성

모든 새로운 기능에는 테스트를 작성해야 합니다.

```bash
# 모든 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src/ecos --cov-report=html

# 특정 테스트만 실행
pytest tests/test_config.py -v
```

#### 테스트 예시

```python
import pytest
from ecos import get_base_rate

def test_get_base_rate():
    """기준금리 조회 테스트"""
    df = get_base_rate()

    # DataFrame 반환 확인
    assert df is not None
    assert len(df) > 0

    # 필수 컬럼 확인
    assert 'date' in df.columns
    assert 'value' in df.columns
    assert 'unit' in df.columns

def test_get_base_rate_with_date_range():
    """기간 지정 기준금리 조회 테스트"""
    df = get_base_rate(start_date="202001", end_date="202012")

    assert len(df) == 12  # 12개월
```

### 4. 문서 작성

새로운 기능을 추가할 때는 문서도 함께 업데이트하세요.

```bash
# 문서 빌드
cd docs
mkdocs serve

# 브라우저에서 http://127.0.0.1:8000 열기
```

#### Docstring 스타일

NumPy 스타일을 사용합니다:

```python
def get_treasury_yield(
    maturity: str,
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    """
    국고채 수익률을 조회합니다.

    Parameters
    ----------
    maturity : str
        만기 (1Y, 3Y, 5Y, 10Y, 20Y, 30Y)
    start_date : str, optional
        시작일 (YYYYMMDD 형식)
    end_date : str, optional
        종료일 (YYYYMMDD 형식)

    Returns
    -------
    pd.DataFrame
        국고채 수익률 데이터

    Raises
    ------
    EcosConfigError
        API 키가 설정되지 않은 경우
    EcosAPIError
        API 응답 오류

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_treasury_yield(maturity="3Y")
    >>> print(df.head())
    """
    ...
```

### 5. 커밋

```bash
# 변경사항 스테이징
git add .

# 커밋 (pre-commit 훅이 자동 실행됨)
git commit -m "Add feature: your feature description"
```

#### 커밋 메시지 가이드

- 명령형으로 작성: "Add feature" (O), "Added feature" (X)
- 첫 줄은 50자 이내
- 필요시 상세 설명 추가

```
Add support for exchange rate indicators

- Add get_exchange_rate() function
- Add tests for exchange rate
- Update documentation
```

### 6. Pull Request 생성

```bash
# 원격 저장소에 푸시
git push origin feature/your-feature-name
```

GitHub에서 Pull Request를 생성합니다.

#### PR 체크리스트

- [ ] 모든 테스트 통과
- [ ] 코드 커버리지 유지 또는 증가
- [ ] 린팅 및 포매팅 통과
- [ ] 타입 체킹 통과
- [ ] 문서 업데이트
- [ ] CHANGELOG 업데이트 (주요 변경사항)

## 프로젝트 구조

```
ecos-reader/
├── src/ecos/
│   ├── __init__.py          # Public API
│   ├── client.py            # API 클라이언트
│   ├── config.py            # 설정 관리
│   ├── parser.py            # 응답 파서
│   ├── exceptions.py        # 예외 클래스
│   ├── constants.py         # 상수 정의
│   └── indicators/          # 지표 모듈
│       ├── __init__.py
│       ├── interest_rate.py
│       ├── prices.py
│       ├── growth.py
│       └── money.py
├── tests/                   # 테스트 코드
│   ├── conftest.py          # pytest 설정
│   ├── test_client.py
│   ├── test_config.py
│   └── indicators/
│       ├── test_interest_rate.py
│       ├── test_prices.py
│       ├── test_growth.py
│       └── test_money.py
├── docs/                    # 문서
├── examples/                # 예제 코드
├── pyproject.toml           # 프로젝트 설정
└── README.md
```

## 이슈 리포팅

버그를 발견하거나 기능 제안이 있으면 [GitHub Issues](https://github.com/choo121600/ecos-reader/issues)에 등록해주세요.

### 버그 리포트

다음 정보를 포함해주세요:

- ecos-reader 버전
- Python 버전
- OS 및 버전
- 재현 단계
- 예상 동작
- 실제 동작
- 에러 메시지 (있는 경우)

### 기능 제안

다음 정보를 포함해주세요:

- 제안 배경
- 기대 효과
- 사용 예시 코드

## 코드 리뷰

모든 PR은 코드 리뷰를 거칩니다. 리뷰어의 피드백에 열린 마음으로 응해주세요.

### 리뷰 기준

- 코드 품질
- 테스트 커버리지
- 문서화
- 성능
- 보안

## 릴리스 프로세스

1. 버전 업데이트 (`pyproject.toml`)
2. CHANGELOG 업데이트
3. Git 태그 생성
4. PyPI 배포

## 행동 강령

- 존중과 배려
- 건설적인 피드백
- 포용적인 언어 사용

## 질문이나 도움이 필요하신가요?

- [GitHub Discussions](https://github.com/choo121600/ecos-reader/discussions)에 질문을 올려주세요
- 또는 [Issues](https://github.com/choo121600/ecos-reader/issues)를 생성해주세요

감사합니다!
