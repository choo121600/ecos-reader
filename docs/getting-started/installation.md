# 설치

## 요구사항

- Python 3.10 이상
- pip 패키지 관리자

## pip를 통한 설치

가장 간단한 설치 방법은 pip를 사용하는 것입니다.

```bash
pip install ecos-reader
```

## 개발 버전 설치

최신 개발 버전을 설치하려면 GitHub 저장소에서 직접 설치할 수 있습니다.

```bash
git clone https://github.com/choo121600/ecos-reader.git
cd ecos-reader
pip install -e ".[dev]"
```

개발 버전에는 다음 도구들이 포함됩니다:

- pytest - 테스트 프레임워크
- pytest-cov - 코드 커버리지 측정
- ruff - 린터 및 포매터
- mypy - 정적 타입 체커
- responses - HTTP 요청 모킹
- pre-commit - Git 훅 관리

## 문서 빌드 도구 설치

문서를 로컬에서 빌드하고 미리보려면 문서 도구를 설치하세요.

```bash
pip install -e ".[docs]"
```

문서 도구 설치 후 로컬에서 문서를 실행할 수 있습니다:

```bash
mkdocs serve
```

브라우저에서 `http://127.0.0.1:8000`으로 접속하면 문서를 확인할 수 있습니다.

## API 키 발급

ecos-reader를 사용하려면 한국은행 ECOS API 키가 필요합니다.

### 1. 한국은행 ECOS 웹사이트 방문

[https://ecos.bok.or.kr/api/](https://ecos.bok.or.kr/api/)

### 2. 인증키 신청

1. 웹사이트 상단의 "인증키 신청" 버튼 클릭
2. 회원가입 또는 로그인
3. 신청 양식 작성
4. 신청 즉시 API 키 발급

### 3. API 키 설정

발급받은 API 키를 환경 변수로 설정합니다.

=== "Linux/macOS"

    ```bash
    export ECOS_API_KEY="your_api_key"
    ```

    영구적으로 설정하려면 `~/.bashrc` 또는 `~/.zshrc`에 추가:

    ```bash
    echo 'export ECOS_API_KEY="your_api_key"' >> ~/.bashrc
    source ~/.bashrc
    ```

=== "Windows (PowerShell)"

    ```powershell
    $env:ECOS_API_KEY="your_api_key"
    ```

    영구적으로 설정하려면 시스템 환경 변수에 추가하거나, PowerShell 프로필에 추가합니다.

=== ".env 파일"

    프로젝트 루트에 `.env` 파일을 생성:

    ```
    ECOS_API_KEY=your_api_key
    ```

    Python 코드에서 명시적으로 로드:

    ```python
    import ecos

    ecos.load_env()  # .env 파일 로드
    ```

!!! warning "주의사항"
    - API 키는 외부에 노출되지 않도록 주의하세요
    - `.env` 파일은 `.gitignore`에 추가하여 Git에 커밋되지 않도록 하세요
    - 공개 저장소에 API 키를 업로드하지 마세요

## 설치 확인

설치가 정상적으로 완료되었는지 확인합니다.

```python
import ecos

print(ecos.__version__)
```

API 키가 올바르게 설정되었는지 테스트:

```python
import ecos

# 간단한 API 호출로 테스트
try:
    df = ecos.get_base_rate()
    print("설치 및 API 키 설정이 정상적으로 완료되었습니다!")
    print(df.head())
except Exception as e:
    print(f"오류 발생: {e}")
```

## 다음 단계

설치가 완료되었다면 [빠른 시작](quickstart.md) 가이드를 통해 기본 사용법을 익혀보세요.
