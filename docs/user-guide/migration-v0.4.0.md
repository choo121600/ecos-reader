# v0.4.0 마이그레이션 가이드

v0.4.0은 deprecation cycle이 만료된 항목을 제거하는 **BREAKING** 릴리스입니다.
v0.2.2(#20)에서 `EcosDeprecationWarning` 과 함께 deprecated 처리된 레거시
frequency 단일 문자 표기가 제거되었습니다.

## 무엇이 바뀌었나

- 레거시 frequency 단일 문자 표기(`"D"` / `"M"` / `"Q"` / `"A"`)가 **제거**되었습니다.
- 이제 정식(canonical) 어휘만 허용합니다.

  | 레거시 (제거됨) | 정식 어휘 |
  | :-------------- | :---------- |
  | `"D"`           | `"daily"`     |
  | `"M"`           | `"monthly"`   |
  | `"Q"`           | `"quarterly"` |
  | `"A"`           | `"annual"`    |

- 정식이 아닌 값은 경고 없이 **즉시 `ValueError`** 를 발생시킵니다.
  (이전에는 레거시 표기를 `EcosDeprecationWarning` 과 함께 통과시켰습니다.)
- frequency 전용 경고였던 `EcosDeprecationWarning` 클래스가 제거되어
  `ecos` 패키지에서 더 이상 export되지 않습니다.

## 영향을 받는 함수

frequency 인자를 받는 지표 함수들입니다.

- `get_gdp` 등 성장 지표: `"quarterly"` / `"annual"`
- `get_base_rate` 등 금리 지표: `"daily"` / `"monthly"`
- `get_stock_index` 등 주식 지표: `"daily"` / `"monthly"`

## 코드 변경 방법

레거시 단일 문자를 정식 어휘로 교체하세요.

```python
import ecos

# 이전 (v0.3.x 이하) — deprecated, v0.4.0에서 제거됨 (이제 ValueError)
df = ecos.get_gdp(frequency="Q")
df = ecos.get_base_rate(frequency="D")

# 이후 (v0.4.0+)
df = ecos.get_gdp(frequency="quarterly")
df = ecos.get_base_rate(frequency="daily")
```

`EcosDeprecationWarning` 을 직접 참조하던 코드가 있다면 제거하세요.

```python
# 이전 — 더 이상 동작하지 않음 (ImportError)
import warnings
from ecos import EcosDeprecationWarning
warnings.simplefilter("ignore", EcosDeprecationWarning)

# 이후 — 해당 경고가 제거되었으므로 이 코드는 불필요합니다.
```

## 참고

- `_registry.py` 의 `DateFormat = Literal["D", "M", "Q", "A"]` 는 ECOS API의
  내부 period 코드로, frequency 어휘와 무관하며 변경되지 않았습니다.
