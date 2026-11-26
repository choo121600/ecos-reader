# 하위호환·사용 중단(Deprecation) 정책

ecos-reader는 [Semantic Versioning 2.0.0](https://semver.org/lang/ko/)을 따릅니다.
이 문서는 무엇을 "공개 API"로 보장하고, 그것을 바꾸거나 없앨 때 어떤 절차를
거치는지 정합니다.

## 공개 API의 범위

다음은 하위호환 보장 대상입니다.

- `ecos.__all__`에 포함된 이름(함수·클래스·예외·상수)
- 위 함수의 **인자 이름, 기본값, 허용 값**(`Literal` 선택지 등)과 키워드 인자로 호출하는 방식
- 반환 DataFrame의 **컬럼 이름과 의미**
- 예외 클래스의 상속 구조(`except EcosAPIError:`가 잡는 범위 등)

다음은 보장 대상이 **아닙니다**.

- `_`로 시작하는 모듈·함수·속성, `ecos.__all__`에 없는 하위 모듈 내부 이름
- 경고·예외·로그 **메시지 문구**
- ECOS 원천 데이터의 변경: 값 수정, 항목 추가·삭제, 통계표 개편 (아래 "ECOS 측 변경" 참고)
- 성능 특성, 캐시 파일 형식

## 버전 번호 규칙

| 변경 | 1.0 이후 | 0.x 동안 |
|---|---|---|
| 하위호환을 깨는 변경(제거·이름 변경·의미 변경) | Major (`2.0.0`) | Minor (`0.9.0`) |
| 기능 추가, 사용 중단 예고(deprecation) | Minor (`1.1.0`) | Minor 또는 Patch |
| 버그 수정, 문서 | Patch (`1.0.1`) | Patch |

**Python 버전 지원**: 공식 지원이 끝난(EOL) Python 버전은 Minor 릴리스에서 지원을
중단할 수 있으며, 이를 하위호환을 깨는 변경으로 보지 않습니다. `requires-python`이
갱신되므로 구 Python 환경의 `pip`는 마지막 지원 버전을 자동으로 설치합니다.

## 사용 중단 절차

공개 API를 없애거나 바꿀 때는 **바로 제거하지 않고** 다음 순서를 따릅니다.

1. **예고 릴리스**: 기존 동작은 그대로 두고, 사용 시
   `ecos.EcosDeprecationWarning`을 발생시킵니다.
    - 메시지에 **대체 방법**과 **제거 예정 버전**을 적습니다.
    - 호출한 사용자 코드 위치가 표시되도록 `stacklevel`을 맞춥니다.
    - CHANGELOG의 `### Deprecated`와 해당 사용자 가이드에 기록합니다.
2. **유예 기간**: 예고 후 **최소 한 번의 Minor 릴리스**, 그리고 **최소 3개월**이
   지나야 제거할 수 있습니다. 둘 중 늦은 쪽을 따릅니다.
3. **제거 릴리스**: 위 버전 규칙에 맞는 릴리스(1.0 이후 Major)에서 제거하고,
   CHANGELOG의 `### Removed`와 마이그레이션 가이드에 적습니다.

```python
import warnings

from ecos.exceptions import EcosDeprecationWarning

warnings.warn(
    "get_foo()는 2.0.0에서 제거됩니다. get_bar()를 사용하세요.",
    EcosDeprecationWarning,
    stacklevel=2,
)
```

`EcosDeprecationWarning`은 `FutureWarning`을 상속하므로 별도 설정 없이 스크립트와
노트북에 표시됩니다. 경고를 오류로 바꿔 미리 점검하려면 다음처럼 실행합니다.

```bash
python -W error::FutureWarning your_script.py
```

## ECOS 측 변경

ECOS가 통계표나 항목을 없애거나 개편해 기존 함수가 더 이상 올바른 데이터를 돌려줄 수
없으면, 유예 기간 없이 다음 릴리스에서 동작을 바꾸거나 오류를 내도록 할 수 있습니다.
이 경우에도 CHANGELOG에 원인과 대체 방법을 적습니다.

## 기여자 체크리스트

공개 API를 바꾸는 PR은 다음을 확인합니다.

- [ ] 기존 호출이 계속 동작하며 `EcosDeprecationWarning`을 내는가
- [ ] 경고가 발생하는지 검증하는 테스트(`pytest.warns(EcosDeprecationWarning)`)가 있는가
- [ ] CHANGELOG `[Unreleased]`의 `### Deprecated`에 대체 방법과 제거 예정 버전을 적었는가
