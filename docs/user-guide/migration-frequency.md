# frequency 표기 마이그레이션 (#20, #57)

이 문서는 `frequency` 인자 표기 변경(레거시 단일 문자 → 정식 풀네임)에 대한 안내입니다.
v0.4.0(#57)부터 레거시 단일 문자 표기는 **제거**되어 더 이상 허용되지 않습니다.

## 한눈에 보기

| 카테고리 | 함수 | 레거시(제거됨) | 정식(필수) |
|---|---|---|---|
| 성장 | `get_gdp`, `get_gdp_deflator` 등 | `Q`, `A` | `quarterly`, `annual` |
| 금리 | `get_base_rate` | `D`, `M` | `daily`, `monthly` |
| 주식 | `get_stock_index` | (없음) | `daily`, `monthly` |

## 권장 변경

```python
# Before (v0.3.x 이하, 이제 ValueError)
df = ecos.get_gdp(frequency="Q")

# After (정식)
df = ecos.get_gdp(frequency="quarterly")
```

## 동작/타임라인

- v0.2.2: 정식 어휘 도입. 레거시 단일 문자는 `EcosDeprecationWarning` 과 함께 계속 동작.
- **v0.4.0: 레거시 단일 문자 제거.** 이제 정식 어휘만 허용하며, 정식이 아닌
  값은 경고 없이 즉시 `ValueError` 입니다. frequency 전용 경고였던
  `EcosDeprecationWarning` 도 함께 제거되었습니다.

v0.4.0 변경 상세는 [v0.4.0 마이그레이션](migration-v0.4.0.md) 을 참고하세요.
