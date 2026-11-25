# 릴리스 가이드

ecos-reader의 새 버전을 릴리스하는 방법을 설명합니다.

## 사전 준비

### PyPI Trusted Publishers 설정 (최초 1회)

PyPI Trusted Publishers를 사용하면 API 토큰 없이 GitHub Actions에서 안전하게 배포할 수 있습니다.

#### 1. PyPI 웹사이트에서 설정

1. [PyPI](https://pypi.org/)에 로그인
2. ecos-reader 프로젝트 페이지로 이동
3. **Settings** → **Publishing** 클릭
4. **Add a new publisher** 클릭
5. 다음 정보 입력:
   - **PyPI Project Name**: `ecos-reader`
   - **Owner**: `choo121600`
   - **Repository name**: `ecos-reader`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
6. **Add** 클릭

#### 2. GitHub Repository 설정

1. GitHub 저장소로 이동
2. **Settings** → **Environments** 클릭
3. **New environment** 클릭
4. Environment name: `pypi`
5. **Configure environment** 클릭
6. (선택사항) **Deployment protection rules** 설정
   - **Required reviewers** 추가 (릴리스 전 승인 필요)
7. **Save protection rules** 클릭

## 릴리스 프로세스

버전의 **단일 출처는 git 태그**입니다. `pyproject.toml`에는 버전을 적지 않고
(`dynamic = ["version"]`), [hatch-vcs](https://github.com/ofek/hatch-vcs)가 빌드 시점에
태그 `vX.Y.Z`에서 버전을 계산합니다. `ecos.__version__`은 설치된 패키지 메타데이터
(`importlib.metadata`)에서 읽습니다. 따라서 버전을 바꾸려고 파일을 고칠 필요가 없고,
태그와 배포 버전이 어긋날 수 없습니다.

태그가 없는 커밋에서 빌드하면 `0.8.1.dev3+g1a2b3c4` 같은 개발 버전(PEP 440)이 됩니다.

### 1. CHANGELOG 정리 (PR)

[Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따릅니다. 평소에는
`## [Unreleased]` 아래에 변경사항을 쌓고, 릴리스 PR에서 헤더를 버전으로 바꾼 뒤
하단 비교 링크를 갱신합니다.

```markdown
## [Unreleased]

## [0.9.0] - 2026-12-31

### Added
- 새로운 기능 설명

...

[Unreleased]: https://github.com/choo121600/ecos-reader/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/choo121600/ecos-reader/compare/v0.8.0...v0.9.0
```

### 2. 테스트 실행

```bash
uv run pytest
uv run ruff check src tests
uv run mypy src
```

### 3. 태그 및 푸시

CHANGELOG PR이 `main`에 머지된 뒤, 그 머지 커밋에 **주석 태그**를 답니다.

```bash
git switch main && git pull --ff-only
git tag -a v0.9.0 -m "Release v0.9.0"
git push origin v0.9.0
```

태그 이름은 반드시 `v` + SemVer(`vX.Y.Z`)입니다.

### 4. 자동 배포 확인

태그를 푸시하면 `publish.yml`이 자동으로:

1. CI 게이트(lint, type-check, 테스트) 통과 확인
2. 패키지 빌드 후 산출물 버전이 태그와 같은지 검증
3. PyPI에 배포 (Trusted Publishing)
4. GitHub Release 생성 (CHANGELOG 해당 섹션 포함)

진행 상황은 GitHub Actions 탭에서 확인할 수 있습니다.

## 버전 번호 규칙

[Semantic Versioning 2.0.0](https://semver.org/lang/ko/)을 따릅니다:

- **Major (X.0.0)**: 호환성이 깨지는 변경
- **Minor (0.X.0)**: 하위 호환 가능한 기능 추가
- **Patch (0.0.X)**: 하위 호환 가능한 버그 수정

1.0.0 이전(0.x)에는 공개 API가 안정되지 않았다는 뜻이므로, 호환성이 깨지는 변경은
**Minor**를 올리고 그 외는 Patch를 올립니다(예: Python 3.10 지원 중단 → 0.7.0 → 0.8.0).

## 수동 배포 (비상시)

GitHub Actions가 작동하지 않을 경우:

```bash
# 빌드
python -m build

# PyPI 업로드 (API 토큰 필요)
python -m twine upload dist/ecos_reader-X.Y.Z*
```

## 롤백

잘못된 버전을 배포한 경우:

1. PyPI에서는 같은 버전을 덮어쓸 수 없음
2. 버전을 올려서 핫픽스 배포
3. 잘못된 버전은 PyPI에서 "Yank" 처리

```bash
# 잘못된 버전 Yank (PyPI 웹에서)
# Settings → Manage → Options → Yank release
```

## 체크리스트

릴리스 전 확인사항:

- [ ] 모든 테스트 통과
- [ ] CHANGELOG 업데이트 (`[Unreleased]` → 버전 헤더, 하단 비교 링크)
- [ ] 문서 업데이트
- [ ] 예제 코드 동작 확인
- [ ] 로컬에서 빌드 테스트
- [ ] `vX.Y.Z` 주석 태그 생성 및 푸시

## 트러블슈팅

### "Trusted publishing exchange failure"

- PyPI Trusted Publishers 설정 확인
- Workflow name, Environment name 정확한지 확인
- Repository owner/name 정확한지 확인

### "Release already exists"

- 이미 같은 태그가 존재하는 경우
- `git tag -d v0.1.2` 로컬 태그 삭제
- `git push origin :v0.1.2` 원격 태그 삭제
- 수정 후 다시 태그 생성

### 패키지 빌드 실패

- `pyproject.toml` 문법 확인
- 필수 파일 존재 확인 (README.md, LICENSE 등)
- 로컬에서 `python -m build` 테스트
- 버전이 `0.0.0` 또는 `.dev`로 나오면 태그가 없는 것: `git fetch --tags` 후 다시 빌드
