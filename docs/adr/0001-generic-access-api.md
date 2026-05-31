# ADR 0001 — 공개 범용 조회 API 설계

- **상태(Status):** Accepted
- **결정일:** 2026-05-31
- **관련:** Epic #98 (v0.5.0 Full ECOS Coverage), #99(본 ADR), #100(`get_series` 구현), #103(정적 카탈로그), #104(`list_items`)
- **마일스톤:** v0.5.0 — Full ECOS Coverage

---

## 1. 맥락 (Context)

`ecos-reader`는 현재 두 계층으로 구성된다.

1. **L0 클라이언트** — `EcosClient`가 ECOS Open API의 6개 서비스를 모두 래핑한다
   (`get_statistic_search` / `get_statistic_item_list` / `get_statistic_table_list` /
   `get_statistic_word` / `get_key_statistic_list` / `get_statistic_meta`). 응답 파서
   `parse_response`는 테이블에 무관하게 범용으로 동작한다.
2. **L2 도메인 지표 함수** — `get_base_rate`, `get_cpi`, `get_gdp` 등 큐레이션된
   고수준 함수. 각 함수는 특정 `(stat_code, item_code, period)` 조합을 내부에 고정한다.

"ECOS의 모든 통계를 받을 수 있게 한다"는 목표는 700여 개 통계표마다 도메인 함수를
손으로 만드는 문제가 **아니다**. 이미 범용 엔진(`EcosClient._cached_request` →
`get_statistic_search`)이 존재하므로, 빠진 것은 **임의의 `(stat_code, item_code,
period)`를 받아 tidy DataFrame을 돌려주는 공개 함수 하나**다. 이 키스톤이 `get_series`이며,
구현(#100)에 앞서 시그니처·출력 스키마·period 어휘·에러 의미를 **설계 게이트**로 먼저
확정한다(본 ADR).

### 제약과 기존 자산

- `EcosClient.get_statistic_search(stat_code, period, start_date, end_date, item_code1..4,
  start, end)`가 이미 4축 항목코드와 페이지네이션(`start`/`end`)을 지원한다.
- `parser.parse_time_column`은 ECOS의 6가지 시간 표기를 모두 datetime으로 변환한다:
  연(`YYYY`) / 반기(`YYYYSN`) / 분기(`YYYYQN`) / 월(`YYYYMM`) / 반월(`YYYYMMSMN`) / 일(`YYYYMMDD`).
- `parser.normalize_stat_result(df, columns=, date_col=)`는 임의 컬럼 집합을 선택·정렬하는
  범용 정규화기다. `columns` 인자로 항목 차원을 보존할 수 있다.
- v0.4.0(#57)에서 도메인 함수의 `frequency`는 정식 풀네임 어휘
  (`daily`/`monthly`/`quarterly`/`annual`)만 허용하도록 정리되었다. 그러나 이 4단어로는
  ECOS의 반기/반월 주기를 표현할 수 없다.
- ECOS는 300 calls / 3분의 rate limit이 있다(코드 미반영, #102에서 명문화 예정).

---

## 2. 결정 (Decision)

### 2.1 시그니처

```python
def get_series(
    stat_code: str,
    period: str,
    *,
    start_date: str,
    end_date: str,
    item_code: str | list[str] | None = None,
    tidy: bool = True,
    client: EcosClient | None = None,
) -> pd.DataFrame:
    ...
```

| 인자 | 의미 |
|------|------|
| `stat_code` | ECOS 통계표코드(예: `"722Y001"`). 필수, 위치 인자. |
| `period` | 조회 주기. 정식 어휘 / 원시 코드 / 반기·반월 확장을 모두 수용(§2.3). 필수, 위치 인자. |
| `start_date` | 조회 시작 시점. ECOS 표기(`period`에 맞는 `YYYY`/`YYYYMM`/`YYYYMMDD` 등). 키워드 전용. |
| `end_date` | 조회 종료 시점. 키워드 전용. |
| `item_code` | 항목코드 선택자. `None`(전체), 단일 문자열, 또는 길이 ≤ 4 리스트(다축). 키워드 전용. |
| `tidy` | `True`(기본)면 long-format tidy 스키마로 정규화(§2.2). `False`면 `parse_response` 원본 컬럼을 그대로 반환(이스케이프 해치). |
| `client` | 사용할 `EcosClient`. 생략 시 전역 클라이언트(`get_client()`). |

**설계 근거**

- `stat_code`, `period`는 ECOS의 모든 조회에서 필수이므로 위치 인자로 둔다.
- `start_date`/`end_date`/`item_code`는 키워드 전용으로 강제해, 항목코드 다축이 늘어나도
  호출부가 위치 의존성에서 안전하다(`get_statistic_search`의 `item_code1..4` 위치 인자가
  겪던 가독성 문제를 답습하지 않는다).
- `item_code`는 `str | list[str] | None`으로 받아 내부에서 `item_code1..4`에 매핑한다.
  리스트 길이가 4를 초과하면 즉시 `ValueError`.
- `tidy=False` 이스케이프 해치를 둬, 비표준 응답(메타·잔여 컬럼 필요)도 막다른 길이 되지
  않게 한다.

`get_series`는 신규 모듈 `src/ecos/access.py`(가칭)의 공개 함수로 두고 `ecos.__init__`에서
re-export한다. L2 도메인 함수의 의존 대상은 아니며(도메인 함수는 기존 경로 유지), 범용
접근의 단일 진입점이다.

### 2.2 출력 스키마 — long-format tidy

`tidy=True`(기본)일 때 반환 DataFrame은 **long-format tidy**다. 한 행 = 한 (시점 × 항목조합)
관측치이며, 다음 컬럼 중 **응답에 실제로 존재하고 비어있지 않은 축만** 포함한다.

| 컬럼 | dtype | 출처(`COLUMN_MAP`) | 비고 |
|------|-------|--------------------|------|
| `date` | `datetime64[ns]` | `TIME` → `parse_time_column` | 항상 포함. 오름차순 정렬. |
| `value` | `float64` | `DATA_VALUE` | 항상 포함. 숫자 변환 실패 시 `NaN`. |
| `unit` | `object`(str) | `UNIT_NAME` | 응답에 있으면 포함. |
| `item_code1..4` | `object`(str) | `ITEM_CODE1..4` | **비어있지 않은 축만** 포함. |
| `item_name1..4` | `object`(str) | `ITEM_NAME1..4` | 대응 `item_code{n}`가 포함될 때 함께 포함. |

- **항목 차원 보존:** 단일 시리즈로 평탄화하지 않는다. `item_code`로 다축을 조회하면
  각 항목조합이 별도 행으로 유지된다(따라서 long-format). 단일 항목/단일 축이면 자연히
  `date, value, unit` 중심의 좁은 표가 된다.
- **비어있는 축 제거:** ECOS는 사용하지 않는 항목축을 빈 문자열로 채워 보낸다. 모두 빈 축
  컬럼은 스키마에서 제외해 잡음을 없앤다(`normalize_stat_result`의 "존재하는 컬럼만 선택"
  규칙을 항목축까지 확장).
- **구현 재사용:** `normalize_stat_result(df, columns=[...], date_col="time")`에 위 컬럼
  목록을 전달해 생성한다. 새 파싱 로직을 만들지 않는다.
- `tidy=False`면 `parse_response(response)` 결과(snake_case 정규화된 원본 전 컬럼)를
  그대로 반환한다.

빈 결과는 빈 `DataFrame`(컬럼 없음)을 반환한다 — §2.4 참고.

### 2.3 period 어휘

`period` 인자는 세 표기를 모두 수용하며, 내부에서 ECOS 원시 코드로 정규화한 뒤
`get_statistic_search`에 넘긴다.

| 정식 어휘(canonical) | 원시 코드(passthrough) | ECOS 시간 표기 | 비고 |
|----------------------|------------------------|----------------|------|
| `daily` | `D` | `YYYYMMDD` | |
| `monthly` | `M` | `YYYYMM` | |
| `quarterly` | `Q` | `YYYYQN` | |
| `annual` | `A` | `YYYY` | |
| `semiannual` | `S` | `YYYYSN` | v0.4.0 4단어에 없던 **반기** 확장 |
| `semimonthly` | `SM` | `YYYYMMSMN` | **반월** 확장 |

- **정식 어휘**: v0.4.0 도메인 함수와 일관된 풀네임. 신규로 `semiannual`/`semimonthly`를
  추가해 ECOS 6주기를 모두 표현한다.
- **원시 코드 passthrough**: `D`/`M`/`Q`/`A`/`S`/`SM`을 그대로 전달하면 매핑 없이 통과한다.
  카탈로그(#103)나 ECOS 문서에서 얻은 원시 코드를 가공 없이 쓸 수 있게 한다.
- 정규화는 대소문자를 구분하지 않는다(`"Daily"`, `"sm"` 허용). 매핑표에 없는 값은 경고 없이
  즉시 `ValueError`(허용 목록을 메시지에 포함). 이는 v0.4.0 `normalize_frequency`의
  fail-fast 정책과 일치한다.
- 주의: 이 어휘는 **L0/범용 계층(`get_series`)** 전용이다. L2 도메인 함수의 `frequency`
  어휘(정식 풀네임만)는 그대로 두며 본 ADR로 바뀌지 않는다.

### 2.4 에러 의미 (Error semantics)

| 상황 | 동작 |
|------|------|
| 존재하지 않는 `stat_code` | ECOS가 `ERROR-*` 비즈니스 코드를 반환 → 기존 `_check_error_response`가 `EcosAPIError`로 변환. `get_series`는 이를 그대로 전파한다. |
| 존재하지 않는 `item_code` | ECOS는 보통 빈 결과(`INFO-200`)를 반환 → 빈 DataFrame. (별도 검증/조회를 하지 않는다.) |
| 빈 결과(`INFO-200`, 데이터 없음) | **에러 아님.** 빈 `DataFrame`을 반환한다(기존 `_check_error_response`가 `INFO-200`을 정상 처리). |
| 페이지 초과(`start`/`end`가 범위 밖) | 빈 결과로 간주 → 빈 DataFrame. v0.5.0 시점에는 단일 페이지(`start=1, end=100000`) 기본값으로 호출하며, 다중 페이지 자동 순회는 후속(#101 페이지네이션)로 미룬다. |
| 잘못된 `period` | 매핑 실패 → `ValueError`(네트워크 호출 전, §2.3). |
| `item_code` 리스트 길이 > 4 | `ValueError`(네트워크 호출 전). |
| Rate limit 초과 | 기존 `EcosRateLimitError` 전파. rate limiter 도입은 #102. |

원칙: **"데이터 없음"은 빈 DataFrame, "잘못된 요청/응답"은 예외.** 빈 결과를 예외로 바꾸지
않으며(호출부가 `try/except` 없이 `.empty`로 분기), 입력 검증 오류는 네트워크 비용 이전에
`ValueError`로 빠르게 실패시킨다.

---

## 3. 대안 (Alternatives considered)

- **`item_code`를 위치 인자 `item_code1..4`로 노출** — `get_statistic_search`와 동일.
  거부: 4축 위치 인자는 호출부 가독성이 나쁘고, 단일/다축 케이스를 한 인자로 자연스럽게
  표현하지 못한다.
- **wide-format(시점 인덱스 × 항목 컬럼) 기본 반환** — 거부: 항목 수가 가변(수백 개 가능)이라
  컬럼 폭발이 발생하고, 단위(`unit`)가 항목별로 다를 때 표현이 깨진다. tidy long-format은
  pandas pivot으로 언제든 wide 변환이 가능하므로 long을 정본으로 둔다.
- **`period`를 정식 어휘만 허용(원시 코드 거부)** — 거부: 카탈로그/ECOS 원문이 제공하는
  원시 코드를 매번 변환하게 강제하면 범용 접근의 마찰이 커진다. passthrough로 둘 다 수용한다.
- **빈 결과를 예외로 처리** — 거부: "조회는 성공했고 데이터가 없음"은 정상 흐름이다.
  기존 `INFO-200` 처리 관례와도 일치한다.

---

## 4. 결과 (Consequences)

**긍정**

- 단 하나의 공개 함수로 ECOS 700여 통계표 전체가 도달 가능해진다("전부 도달 가능" 충족).
- 기존 엔진(`_cached_request`, `parse_response`, `normalize_stat_result`,
  `parse_time_column`)을 재사용 — 신규 파싱/캐시/재시도 로직이 없다.
- L2 도메인 함수와 출력 형태(tidy)·에러 정책이 일관된다.

**부정 / 후속 과제**

- 단일 페이지 기본 호출이라 매우 큰 시리즈는 잘릴 수 있다 → 다중 페이지 자동 순회는 #101.
- rate limit 보호 장치 없음 → #102.
- `item_code` 다축의 축 의미(어느 stat_code에서 item_code1이 무엇인지)는 사용자가 알아야
  한다 → 정적 카탈로그(#103)와 `list_items`(#104)가 탐색을 보조한다.
- period 어휘가 L0(`get_series`, 6주기)와 L2(`frequency`, 4단어)에서 다르다는 점을
  문서로 명확히 구분해야 한다.

---

## 5. 완료 기준 (이슈 #99)

- [x] `get_series` 시그니처/인자 의미 확정 (§2.1)
- [x] 출력 스키마 = long-format tidy 확정 (§2.2)
- [x] period 어휘(정식 + 반기/반월 + 원시 코드 passthrough) 매핑표 확정 (§2.3)
- [x] 에러 의미(없는 stat_code/item, 빈 결과, 페이지 초과) 정의 (§2.4)

본 ADR이 머지되면 #100(`get_series` 구현)의 설계 게이트가 해제된다.
