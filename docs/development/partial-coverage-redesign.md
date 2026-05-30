# Partial-coverage 재설계 규약

> v0.3.0 마일스톤(epic [#56](https://github.com/choo121600/ecos-reader/issues/56))의 공통 설계 규약입니다. 카테고리별 하위 이슈(#59~#63)는 모두 이 규약을 따릅니다.

## 배경

일부 지표 함수는 함수명이 **전체 시리즈**(예: "산업별 GDP", "투자자별 거래")를 시사하지만, 실제로는 ECOS `item_code1` 단일 항목만 조회해 반환합니다. 이들은 `EcosPartialCoverageWarning`([#8](https://github.com/choo121600/ecos-reader/issues/8))과 함께 동작하며, v0.3.0 에서 함수 시그니처를 바꿔 전체 시리즈 또는 sub-category 선택을 제공하도록 재설계됩니다.

레퍼런스는 v0.2.0 의 [`get_borrower_loan`](https://github.com/choo121600/ecos-reader/pull/29) 재설계입니다. 이 규약은 그 패턴을 일반화한 것입니다.

## 핵심 사실: ECOS `item_code1` 은 정확 일치 필터

ECOS 의 한 통계표(`stat_code`)는 여러 세부 항목을 `item_code1` 으로 묶어 제공합니다. 분류축(연령·지역·업권 등)은 별도 `stat_code` 가 아니라 `item_code1` **prefix** 로 표현되는 경우가 많습니다.

ECOS API 의 `item_code1` 파라미터는 *정확 일치* 만 지원하므로 prefix 조회가 불가능합니다. 따라서 재설계 함수는 **`item_code1` 필터 없이 통계표 전량을 받아 client-side 에서 분류축을 필터링**합니다.

## 규약

1. **입력 검증** — 허용되지 않는 인자는 사용 가능 목록과 함께 `ValueError`. 검증은 네트워크 호출 전에 수행합니다.
2. **전량 조회** — `client.get_statistic_search(...)` 를 `item_code1` 없이 호출합니다.
3. **분류축 필터 + 형식 결정** — `parse_response` 결과를 [`select_subcategory`](#select_subcategory)에 넘깁니다.
    - `sub_category` **미지정**: 분류축 전체를 long-format(`date, category_value, value, unit`)으로 반환하며 `category_value` 컬럼에 세부 항목명을 담습니다.
    - `sub_category` **지정**: 해당 세부 항목 단일 시계열(`date, value, unit`)만 반환합니다. 항목명(`item_name1`)과 `item_code1` 둘 다 허용합니다.
4. **친절한 에러** — 존재하지 않는 `sub_category` 는 **사용 가능한 항목 목록과 함께** `ValueError` 를 던집니다.

## `select_subcategory`

공통 선택 로직은 `ecos.indicators._subcategory.select_subcategory` 에 있습니다.

```python
from ecos.indicators._subcategory import select_subcategory

def get_something(sub_category=None, start_date=None, end_date=None):
    # 1) 입력 검증 + 기본 날짜 (생략)
    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_SOMETHING,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
    )  # item_code1 미지정 → 전량 수신
    df = parse_response(response)
    return select_subcategory(
        df,
        prefix=PREFIX,    # 분류축 item_code1 prefix
        exact=False,      # 단일 코드 정확 일치가 필요하면 True
        sub_category=sub_category,
        context="<함수 맥락 설명>",  # ValueError 메시지에 포함
    )
```

| 인자 | 의미 |
| --- | --- |
| `prefix` | 분류축 `item_code1` prefix (또는 `exact=True` 일 때 정확코드) |
| `exact` | `True` → `item_code1 == prefix` 정확 일치 / `False` → `startswith` 매칭 |
| `sub_category` | 세부 항목명 또는 `item_code1`. 미지정 시 long-format |
| `context` | `ValueError` 메시지에 포함할 호출 맥락 (예: `"category='연령별'"`) |

분류축 메타데이터(`{분류축: prefix}` 매핑 등)는 함수가 속한 카테고리 모듈 또는 `constants.py` 에 선언합니다. 레퍼런스: `constants.BORROWER_LOAN_CATEGORY_PREFIX`.

### 경계 동작 (하위 이슈가 지켜야 할 계약)

- **빈 결과**: 매칭되는 항목이 없으면 빈 DataFrame 을 반환합니다. 컬럼 구성은 보장하지 않으므로 호출자는 `.empty` 로 판별합니다.
- **항목명 중복**: `item_name1` 은 분류축 내에서 유일하지 않을 수 있습니다. 이름이 겹치는 통계표라면 사용자가 `item_code1` 으로 단일 시계열을 선택할 수 있도록 안내하고, 가능하면 docstring 의 사용 가능 항목 예시에 코드를 함께 노출합니다.
- **항목명 결측**: `item_name1` 이 결측인 행은 long-format 의 `category_value` 가 결측으로 남습니다. 그대로 두는 것이 기본이며, 결측이 잦은 통계표는 함수 단에서 보정합니다.

## 마이그레이션 영향

이 재설계는 **BREAKING** 변경입니다. 단일 시계열을 반환하던 함수가 기본적으로 long-format 을 반환하게 됩니다. 기존 동작을 원하는 호출자는 `sub_category` 를 명시하거나 `EcosClient.get_statistic_search` 를 직접 사용해야 합니다. 전체 함수별 변경 내역과 마이그레이션 가이드는 [#64](https://github.com/choo121600/ecos-reader/issues/64) cleanup 에서 정리합니다.
