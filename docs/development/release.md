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

### 1. 버전 업데이트

```bash
# pyproject.toml의 버전 업데이트
version = "0.1.2"  # 예시
```

### 2. CHANGELOG 업데이트

`CHANGELOG.md`에 변경사항 추가:

```markdown
## [0.1.2] - 2024-12-31

### Added
- 새로운 기능 설명

### Changed
- 변경된 사항

### Fixed
- 버그 수정

[0.1.2]: https://github.com/choo121600/ecos-reader/compare/v0.1.1...v0.1.2
```

### 3. 테스트 실행

```bash
# 모든 테스트 통과 확인
pytest

# 코드 품질 검사
ruff check src tests
mypy src
```

### 4. 커밋 및 태그

```bash
# 변경사항 커밋
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.1.2"

# 태그 생성
git tag -a v0.1.2 -m "Release v0.1.2"

# 푸시
git push origin main
git push origin v0.1.2
```

### 5. 자동 배포 확인

태그를 푸시하면 GitHub Actions가 자동으로:

1. 패키지 빌드
2. PyPI에 배포
3. GitHub Release 생성 (CHANGELOG 내용 포함)

진행 상황은 GitHub Actions 탭에서 확인할 수 있습니다.

## 버전 번호 규칙

[Semantic Versioning](https://semver.org/)을 따릅니다:

- **Major (X.0.0)**: 호환성이 깨지는 변경
- **Minor (0.X.0)**: 하위 호환 가능한 기능 추가
- **Patch (0.0.X)**: 하위 호환 가능한 버그 수정

예시:
- `0.1.0` → `0.1.1`: 버그 수정, 문서 업데이트
- `0.1.1` → `0.2.0`: 새로운 지표 추가
- `0.2.0` → `1.0.0`: API 변경으로 하위 호환성 깨짐

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
- [ ] CHANGELOG 업데이트
- [ ] 버전 번호 업데이트
- [ ] 문서 업데이트
- [ ] 예제 코드 동작 확인
- [ ] 로컬에서 빌드 테스트
- [ ] Git 태그 생성 및 푸시

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
