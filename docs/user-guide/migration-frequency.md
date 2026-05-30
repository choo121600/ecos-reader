# frequency 어휘 통일 마이그레이션 (#20)

## 배경

과거 ecos-reader는 카테고리마다 `frequency` 파라미터의 표기가 달랐습니다.

- **성장 지표** (`growth.py`): `"Q"` (분기), `"A"` (연간)
- **금리 지표** (`interest_rate.py`): `"D"` (일), `"M"` (월)
- **주가 지표** (`stock.py`): `"daily"`, `"monthly"` (이미 풀네임 사용)

이 불일치를 해소하기 위해 이슈 #20에서 **풀네임 어휘**로 통일했습니다.

```
daily | monthly | quarterly | annual
```

## 레거시 → 정식 매핑

| 레거시 (구) | 정식 (신) | 설명 |
|------------|----------|------|
| `"D"` | `"daily"` | 일별 |
| `"M"` | `"monthly"` | 월별 |
| `"Q"` | `"quarterly"` | 분기별 |
| `"A"` | `"annual"` | 연간 |

## Deprecation 정책

레거시 단일 문자(`"D"`, `"M"`, `"Q"`, `"A"`)는 **당분간 계속 동작**하지만,
호출 시 `EcosDeprecationWarning`이 발생합니다.

- `EcosDeprecationWarning`은 `UserWarning`의 하위 클래스이며 기본 필터로도 표시됩니다.
- **v0.4.0**에서 레거시 단일 문자 지원이 완전히 제거될 예정입니다.

## Before / After 코드 예시

```python
# Before (레거시 — 동작하지만 경고 발생)
import ecos

df = ecos.get_gdp(frequency="Q")
df = ecos.get_gdp(frequency="A", basis="nominal")
df = ecos.get_base_rate(frequency="M")

# After (정식 — 권장)
df = ecos.get_gdp(frequency="quarterly")
df = ecos.get_gdp(frequency="annual", basis="nominal")
df = ecos.get_base_rate(frequency="monthly")
```

## 경고 끄는 법

마이그레이션 전까지 임시로 경고를 억제하려면:

```python
import warnings
from ecos import EcosDeprecationWarning

warnings.simplefilter("ignore", EcosDeprecationWarning)
```

## 영향 함수 목록

### `growth.py` — 6개 함수

| 함수 | 지원 frequency |
|------|---------------|
| `get_gdp()` | `quarterly`, `annual` |
| `get_gdp_deflator()` | `quarterly`, `annual` |
| `get_gdp_growth_rate()` | `quarterly`, `annual` |
| `get_gdp_by_industry()` | `quarterly`, `annual` |
| `get_gdp_by_expenditure()` | `quarterly`, `annual` |
| `get_gdp_deflator_by_industry()` | `quarterly`, `annual` |

### `interest_rate.py` — 1개 함수

| 함수 | 지원 frequency |
|------|---------------|
| `get_base_rate()` | `daily`, `monthly` |

### `stock.py` — 1개 함수 (이미 정식 어휘 사용)

| 함수 | 지원 frequency |
|------|---------------|
| `get_stock_index()` | `daily`, `monthly` |
