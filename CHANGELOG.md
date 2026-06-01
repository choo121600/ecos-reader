# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Tests
- 매핑 정합성 가드를 **주기(period)·구조 차원**으로 확장 (오프라인, 매 PR). 새 스냅샷
  `tests/fixtures/ecos_table_structure.json`(통계표별 제공 주기·항목 축 수)를 추가하고,
  ① 함수가 호출에 쓰는 `period` 가 해당 통계표에 실제 존재하는지(없으면 빈 응답 silent
  실패) ② 사용 stat_code 가 모두 구조 스냅샷에 존재하는지 검증한다. 라이브 전수 검사로
  현재 주기 매핑이 전부 유효함을 확인(회귀 방지용 가드). `scripts/snapshot_item_units.py`
  가 두 스냅샷을 함께 재생성/`--check` 하고 야간 e2e CI가 drift 를 감시한다.
- `scripts/audit_endpoints_live.py` 추가 — 실제 키로 전 엔드포인트(92 변종)를 라이브
  호출해 단위·값범위·계열정합성·파라미터효과(변종 구분)를 1:1 대조하는 재실행 가능한
  FM 전수 감사 하니스 (#151). 도메인별 배치(`--group`)·결과표(`--report`) 지원.

## [0.5.3] - 2026-06-01

> 지표 매핑 정확성 패치. 전수 조사로 발견한 stat/item·단위 오매핑 6건을 정정하고,
> 인플레이션율(전년동월비) 조회와 재발 방지 가드를 추가합니다. 대부분 비파괴적이나
> **`get_m2_by_holder()` 기본 반환 형태가 단일 시계열 → long-format 으로 변경**되었으니
> 해당 함수를 쓰던 코드는 확인하세요(#141). `get_bond_yield()` 는 deprecation alias 로
> 계속 동작합니다(#140).

### Added
- `get_cpi()` / `get_core_cpi()` / `get_ppi()` 에 `measure` 파라미터 추가 (#139).
  `measure='index'`(기본값, 지수 2020=100) / `'yoy'`(전년동월비 %, 인플레이션율) /
  `'mom'`(전월비 %). 변화율은 지수에서 파생 계산하며 lookback 을 시차만큼 앞으로 확장해
  요청 구간 첫 달부터 값이 나오도록 한다. **기본값이 'index' 라 기존 동작은 불변.**

### Changed
- `get_bond_yield()` 를 `get_bond_market()` 으로 이름 변경 (#140). 이 함수는 이름과 달리
  채권 수익률(%)이 아니라 **채권시장 거래통계**(거래대금/거래량/상장잔액/상장종목수)를
  반환했다. `get_bond_yield()` 는 `DeprecationWarning` 을 내는 alias로 유지되며 다음 마이너
  릴리스에서 제거된다. 채권 수익률(연%)은 `get_treasury_yield()` 를 사용한다.
- `get_m2_by_holder()` 가 실제로 경제주체별 분해를 제공하도록 재설계 (#141). 과거엔 holder
  선택 인자가 없고 M2 총계 항목만 가리켜 `get_m2_variants()` 와 동일값을 반환했다. 이제
  partial-coverage 규약(#56)에 따라 `sub_category` 미지정 시 전체 경제주체(가계·비금융기업·
  보험기관·연금기금 등)를 long-format(`date, category_value, value, unit`)으로, 지정 시 해당
  주체 단일 시계열을 반환한다. **기본 호출의 반환 형태가 단일 시계열 → long-format으로 변경됨.**

### Fixed
- `get_cpi()` / `get_core_cpi()` / `get_ppi()` 의 docstring·registry 메타데이터가 실제 반환값과
  불일치하던 문제 정정. 이 함수들은 전년동월비(%)가 아니라 **지수(2020=100)** 를 반환하며,
  문서/registry `unit` 을 실제 값(`"2020=100"`)에 맞췄다. **반환 데이터 자체는 변경 없음**
  (비파괴적, 문서·메타데이터만 정정). 인플레이션율이 필요하면 지수에서 직접 계산. (#136)
- 금액 지표 다수의 docstring·registry 단위가 `조원` 으로 선언됐으나 ECOS 실제 반환은
  `십억원` (1000배 오라벨) 인 문제 정정 — `get_fiscal_balance`, `get_money_supply`,
  `get_m1_variants`, `get_m2_variants`, `get_m2_by_holder`, `get_household_credit`,
  `get_gdp`. **반환 데이터 변경 없음**(문서·메타데이터만 정정). `get_fiscal_balance` 의
  허구 Examples 값과 registry `unit`, 관련 문서 표기도 `십억원` 으로 정정. (#142)

- registry `base_rate` 단위 `"%"` → `"연%"` 로 정정 (ECOS 실제 단위와 일치). 신규 매핑 가드가 발견.

### Tests
- e2e 회귀 가드 추가: 물가지수 함수들이 `unit == "2020=100"` 의 지수 레벨을 반환하고
  전년동월비(%)가 아님을 검증.
- e2e 회귀 가드 추가: 금액 지표(fiscal_balance/money_supply/gdp/household_credit)가
  `unit == "십억원"` 을 반환함을 검증 (#142).
- **오프라인 매핑 정합성 가드 추가** (`tests/test_mapping_consistency.py`, API 불필요,
  매 PR 실행) — 라이브러리가 참조하는 (stat_code, item_code) 를 커밋된 ECOS 항목 스냅샷
  (`tests/fixtures/ecos_item_catalog.json`) 과 대조해 ① item_code 실존 여부와 ② 선언 단위
  ↔ 실제 단위 일치를 검증. #133/#134/#136/#142 부류(잘못된 계열·단위 오라벨)를 머지 전에
  차단한다. 스냅샷은 `scripts/snapshot_item_units.py` 로 재생성하고 야간 e2e CI가 라이브
  drift 를 감시.

## [0.5.2] - 2026-06-01

> 지표 매핑 정확성 패치. `get_core_cpi`/`get_gdp_growth_rate` 가 엉뚱한 계열을
> 반환하던 버그를 정정합니다. 두 함수의 반환 **값/단위가 바뀌므로** 해당 지표를
> 쓰던 코드는 결과를 재확인하세요.

### Fixed
- `get_core_cpi()` 가 근원CPI 대신 헤드라인 CPI(총지수)를 반환하던 버그 수정. `ITEM_CORE_CPI`
  를 `"00"`(총지수) → `"DB"`(식료품·에너지제외)로 정정. 이제 `get_cpi` 와 다른 값을 반환한다. (#133)
- `get_gdp_growth_rate()` 가 성장률(%) 대신 GDP 금액 레벨(십억원)을 반환하던 버그 수정.
  과거 매핑 `200Y104`/`200Y106` 표는 전 항목이 금액 레벨이라 성장률 항목이 없었고 item
  `"1101"`(농림어업) 금액을 반환했다. `902Y015`(국제 주요국 경제성장률, OECD) 한국(`KOR`)
  계열로 재매핑해 분기 QoQ·연간 YoY 성장률(%)을 반환한다. (#134)

### Tests
- e2e 시맨틱 회귀 가드 추가: 근원CPI≠헤드라인 검증, GDP 성장률 단위(`%`)·범위 검증.
  계열을 잘못 가리키는 매핑 버그가 "비어있지 않음" 검사를 통과해도 즉시 감지된다.

## [0.5.1] - 2026-06-01

> v0.5.0 이후 추가된 도메인 큐레이션과 정적 분석 보강을 묶은 패치 릴리스.
> 비파괴적(추가/수정만)입니다.

### Added
- **무역** `get_trade(flow, frequency)` — 수출입 금액(`901Y118`). export/import, 월/연. (#127)
- **경기종합지수** `get_composite_index(index)` — 선행/동행/후행 종합지수(`901Y067`), 월. (#127)
- **소매판매** `get_retail_sales(index, frequency)` — 소매판매액지수 총지수(`901Y100`).
  경상/불변/계절조정 계열, 월/분기/연.

### Fixed
- `STAT_RETAIL_SALES` 상수가 실제로는 "건축허가현황"(`901Y037`)을 가리키던 오라벨을
  올바른 소매판매액지수(`901Y100`)로 정정.
- CodeQL `py/clear-text-logging-sensitive-data` 오탐 근본 차단 — 로깅용 URL을 실제
  요청 URL과 코드 경로까지 분리해 평문 인증키가 로그 데이터 흐름에 등장하지 않도록 함.
  마스킹 동작/로그 포맷(`/***/`)은 동일. (#125)

## [0.5.0] - 2026-05-31

> Epic #98(Full ECOS Coverage)의 기능 릴리스. 범용 조회 `get_series` 로 ECOS
> 전체 통계표에 도달 가능해졌고, 오프라인 카탈로그 탐색·항목 탐색·대량수집
> 안전장치·주요 도메인 큐레이션이 추가되었습니다. 기존 도메인 함수 API는
> 변경되지 않았습니다(비파괴적, 추가만).

### Added
- **범용 조회** `get_series(stat_code, period, *, item_code, start_date, end_date, tidy, max_rows, page_size)`
  — 임의 통계표를 long-format tidy로 조회. period 어휘(정식 + 반기/반월 + 원시코드
  passthrough), 다축 항목코드, 윈도우 초과 시 자동 페이지네이션. (#99, #100, #101)
- **항목 탐색** `list_items(stat_code)` — 표의 세부 항목/주기 탐색. (#104)
- **카탈로그 탐색(오프라인)** `search_tables` / `list_tables` / `get_table_tree` /
  `load_catalog` — 패키지 동봉 스냅샷(834표/검색가능 609) 기반, 네트워크 불필요.
  재생성 스크립트(`scripts/audit_codes.py snapshot`)·CI 포함. (#103, #105)
- **대량수집 안전장치** — 선제 rate limiter(`RateLimiter` / `get_rate_limiter`,
  300 calls/3분 sliding window, 기본 on) + opt-in 디스크 캐시(`DiskCache` /
  `get_disk_cache`, `EcosClient(disk_cache=True)`). (#102)
- **도메인 큐레이션** — `get_exchange_rate`(#106), `get_balance_of_payments`(#107),
  `get_business_sentiment` / `get_consumer_sentiment`(#108),
  `get_industrial_production` / `get_facility_investment`(#109).
- **파서 헬퍼 export** `parse_response` / `normalize_stat_result`. (#100)
- 범용 조회 & 탐색 가이드 문서, 커버리지 검증 테스트, 설계 ADR(0001). (#99, #111)

## [0.4.0] - 2026-05-31

> Epic #57(Deprecation 정리)의 **BREAKING** 릴리스. v0.2.2(#20)에서
> `EcosDeprecationWarning` 과 함께 deprecated 처리됐던 레거시 frequency
> 단일 문자 표기를 제거합니다. 마이그레이션: 사용자 가이드 > v0.4.0 마이그레이션.

### Removed (BREAKING)
- 레거시 `frequency` 단일 문자 표기(`"D"`/`"M"`/`"Q"`/`"A"`) 제거. 이제 정식
  어휘(`"daily"`/`"monthly"`/`"quarterly"`/`"annual"`)만 허용하며, 정식이 아닌
  값은 경고 없이 즉시 `ValueError` 를 발생시킵니다. (#65)
- `EcosDeprecationWarning` 클래스 및 공개 export 제거. frequency 단일 문자
  표기 전용 경고였으며, 해당 표기 제거와 함께 더 이상 노출되지 않습니다. (#65)

### Added
- v0.4.0 마이그레이션 가이드(사용자 가이드). (#66)

## [0.3.0] - 2026-05-31

> Epic #56(Partial-coverage 재설계)의 **BREAKING** 릴리스. 함수명이 전체 시리즈를
> 시사하지만 단일 ECOS 항목만 반환하던 함수들을 전체 시리즈 long-format +
> `sub_category` 선택으로 재설계했습니다. 마이그레이션: 사용자 가이드 > v0.3.0 마이그레이션.

### Changed (BREAKING)
- partial-coverage 함수들의 기본 반환이 **단일 시계열 → 전체 분류 long-format**
  (`date, category_value, value, unit`)으로 변경. 단일 시계열은 `sub_category` 로 선택.
  - `get_gdp_by_industry` / `get_gdp_by_expenditure` / `get_gdp_deflator_by_industry` — PR #85 (#59)
  - `get_stock_index(monthly)`(item_code 1010000 회사수 → 1070000 KOSPI 종가 정정) /
    `get_investor_trading`(`action`·`metric` 인자 추가) — PR #86 (#60)
  - `get_cpi_monthly` — PR #87 (#61)
  - `get_household_lending_detail` — PR #88 (#62)
  - `get_bond_yield`(`measure` 인자 추가, 종류별/시장별 분류) — PR #89 (#63)
- 공통 헬퍼 `select_subcategory` 도입(규약: 개발 > Partial-coverage 재설계 규약). PR #68 (#58).

### Removed (BREAKING)
- `EcosPartialCoverageWarning` 클래스 및 내부 `ecos.indicators._deprecations` 모듈 제거.
  모든 partial-coverage 함수가 재설계되어 더 이상 경고를 내지 않습니다. (#64)

### Added
- v0.3.0 마이그레이션 가이드(사용자 가이드). (#64)

## [0.2.2] - 2026-05-30

> Epic #3(Extensibility & Long-term Design)의 하위 작업을 정리한 릴리스.
> 모든 변경이 하위호환이라, `0.3.0`(시그니처 breaking 재설계용 예약)을 침범하지
> 않도록 patch(0.2.2) 로 릴리스합니다.

### Added
- `frequency` 어휘를 풀네임으로 통일: `daily` / `monthly` / `quarterly` / `annual`.
  카테고리마다 달랐던 표기(`growth` 의 `Q`/`A`, `interest_rate` 의 `D`/`M`,
  `stock` 의 `daily`/`monthly`)를 정식 어휘로 일원화. PR #51 (#20).
- `EcosDeprecationWarning` 공개 export (`from ecos import EcosDeprecationWarning`).
  레거시 입력값 사용 시 발생하며, 기본 경고 필터에서도 보이도록 `UserWarning` 기반.
- `mkdocstrings` 도입으로 indicator/클라이언트/예외 API 문서를 docstring 기반
  자동 생성. PR #53 (#18).

### Deprecated
- 레거시 단일 문자 `frequency`(`"D"`/`"M"`/`"Q"`/`"A"`). 당분간 동작하되
  `EcosDeprecationWarning` 을 발생시키며 **v0.4.0** 에서 제거 예정. 정식 어휘로
  마이그레이션하세요(문서: 사용자 가이드 > frequency 마이그레이션). PR #51 (#20).

### Changed
- `mypy strict` 모드 적용 — `py.typed` 광고와 실제 타입 안전성을 일치. CI 의
  `mypy src/ecos` 가 strict 를 강제. PR #52 (#17).
- `mkdocs build --strict` 적용 — 깨진 링크/누락 페이지를 빌드 실패로 검출,
  PR 에서도 docs 빌드 검증. PR #53 (#18).

### Internal
- 보안/유지보수 자동화: `dependabot`(pip·github-actions), `CodeQL`(Python),
  `pip-audit`(주간), `CODEOWNERS` 추가. `ruff` 규칙에 `S`(bandit)/`RUF`/`PT`/
  `TC`/`N` 추가. PR #50 (#19).

## [0.2.1] - 2026-05-29

> 0.3.0 은 시그니처 breaking 재설계(epic #3)를 위해 예약돼 있어, 본 하위호환
> 기능 추가는 patch(0.2.1) 로 릴리스합니다.

### Added
- `get_base_rate` 에 `frequency` 파라미터 추가 (`"M"` 기본 / `"D"`). ECOS 통계표
  `722Y001` 은 일별 원천이라 `frequency="D"` 로 변경일 단위(sparse) 시계열을
  조회할 수 있습니다. `"D"` 지정 시 날짜 형식은 `YYYYMMDD`, 기본 조회기간도
  일별 포맷으로 산출합니다. 기본값 `"M"` 으로 기존 동작은 그대로 유지(하위호환).

### Notes
- M2 평잔·계절조정(`161Y005`/`BBHS00`) 시계열은 기존
  `get_m2_variants(variant="평잔_계절조정")` 로 이미 제공됩니다 (별도 추가 없음).

## [0.2.0] - 2026-05-29

v0.1.6 라이브 e2e 검증에서 드러난 follow-up(#2 Reliability epic)을 정리한 릴리스.
모든 변경은 실제 ECOS API 키로 라이브 검증했습니다.

### Changed
- **BREAKING** `get_borrower_loan` 시그니처 재설계. ECOS 실제 구조(stat_code는
  신규 `181Y001`/잔액 `181Y002` 2개뿐, 모든 분류축은 `item_code1` prefix로 표현)에
  맞춰 다음과 같이 변경. PR #37 (#29).
  - `category`: `전체`/`성별`/`연령별`/`지역별`/`업권별`/`담보유형별`/`다중대출별`
    (각 축은 `item_code1` prefix `0000`/`B`/`C`/`D`/`E`/`F`/`G`로 필터링)
  - `sub_category` 파라미터 추가 — 미지정 시 분류축 전체를 long-format
    (`date, category_value, value, unit`)으로, 지정 시 단일 시계열로 반환
  - 없는 `sub_category`는 사용 가능한 항목 목록과 함께 `ValueError`
  - 구 `STAT_BORROWER_LOAN_NEW/BALANCE`(181Y001~016 가정) 매핑 제거 →
    `BORROWER_LOAN_STAT_CODES` / `BORROWER_LOAN_CATEGORY_PREFIX`
  - v0.1.6에서 빈 응답을 막기 위해 차단했던 7개 조합이 정상 데이터를 반환

### Added
- `Cache`를 나머지 5개 client 엔드포인트(`get_statistic_item_list`,
  `get_statistic_table_list`, `get_statistic_word`, `get_key_statistic_list`,
  `get_statistic_meta`)로 확장. 공통 `_cached_request` 헬퍼로 6개 메서드가
  동일한 캐시 키 규칙(service, api_key, lang, format, 페이지 범위, path 인자)을
  공유하며 `get_statistic_search` 동작/키는 호환 유지. PR #36 (#31).
- v0.1.6 데이터 매핑 수정에 대한 회귀 e2e 가드(`TestE2ERegressionV016`): GDP 연간
  fallback, m2 말잔, CPI 8개 카테고리, 채권 월별 1행, borrower 분류축 등. PR #39 (#30).

### Fixed
- `get_cpi_monthly`가 존재하지 않는 stat_code `901Y001`로 빈 응답을 반환하던 문제
  수정 → `get_cpi`와 동일한 소비자물가지수 `901Y009` 총지수(item `0`) 사용. PR #35 (#32).

## [0.1.6] - 2026-05-29

### Security
- DEBUG/WARNING/ERROR 로그에서 raw API 키 노출을 차단 (`mask_api_key` 적용 +
  `urllib3` 디버그 로거 가드). PR #23.

### Added
- CI 워크플로우 신설 (`.github/workflows/ci.yml`): Python 3.10/3.11/3.12 매트릭스,
  ruff/mypy/pytest 강제. PR #21.
- `publish.yml`에 `needs: [ci]` 게이트 추가 — 테스트/lint/type 통과 후에만
  PyPI 배포. PR #26.
- `ecos.EcosPartialCoverageWarning` (`UserWarning` 서브클래스) — 단일
  `item_code1`만 반환하는 7개 indicator helper가 기본 필터에서도 보이는
  경고를 발화. PR #25.
- CHANGELOG 추출 로직 강화 (`awk` 기반) — 마지막 버전 섹션 잘림 버그 해결. PR #26.

### Fixed
- `Cache` was effectively a no-op since the initial release because
  `if self._cache and self.use_cache:` evaluated to `False` whenever the cache
  was empty (`Cache` defines `__len__` but not `__bool__`). Switched to
  `is not None`; the in-memory cache now actually works (~10× speedup on
  repeated `get_statistic_search` calls). PR #24.
- `EcosClient.get_statistic_search` cache key now includes the page range
  (`start`/`end`), the resolved API key, language and format. Prior key
  collided across pages and across tenants. PR #24.
- `get_cpi_by_category`: prior `stat_code` mapping (`901Y001~008`) did not exist
  on the ECOS API and returned empty DataFrames for every category. Re-mapped
  to the real stat codes (`901Y010` for 특수분류, `901Y009` for COICOP categories)
  with verified `item_code1` values.
- `get_bond_yield(bond_type="종류별")`: the prior call omitted `item_code2`,
  so the response mixed four different measures (상장종목수 / 상장잔액 / 거래량
  / 거래대금) under one `value` column. Now pins `item_code2="2040000"` (거래대금)
  so the returned series is internally consistent.
- `get_gdp_by_expenditure(frequency="A")`: previously mapped only to 계절조정
  stat codes (`200Y107/108`) which are quarterly-only, returning empty for
  annual. Now falls back to 원계열 codes (`200Y109/110`) when `frequency="A"`.
- `get_gdp_growth_rate(frequency="A")`: same issue — `200Y104` is 계절조정+분기
  only. Now uses `200Y106` (원계열, 분기/연간) for annual.
- `get_m2_by_holder(variant="말잔_계절조정"|"말잔_원계열")`: prior item codes
  (`BBHB00S` / `BBHB00`) did not exist on stat `161Y011` / `161Y012`. Re-mapped
  to the real codes `BBGS00` / `BBGA00` discovered via `get_statistic_item_list`.

### Changed
- `get_gdp_by_industry(seasonal_adj=True, frequency="A")`: now raises
  `ValueError` instead of silently returning empty. ECOS does not publish
  계절조정 GDP for annual frequency.
- `get_borrower_loan`: 7 `(loan_type, category)` combinations
  (`{신규,잔액} × {연령별, 지역별, 업권별}` + `신규 × 담보유형별`) previously
  returned empty DataFrames because the function assumed each category had
  its own stat code while ECOS uses a single stat (`181Y001`/`181Y002`) with
  category-as-item_code1. These combinations now raise `ValueError` with a
  message pointing at the direct `EcosClient.get_statistic_search` call.
  The full function will be redesigned in v0.2.0.

### Known Limitations
- `get_gdp_by_industry`, `get_gdp_by_expenditure`, `get_gdp_deflator_by_industry`,
  `get_stock_index(frequency="monthly")`, `get_investor_trading`, `get_bond_yield`,
  `get_household_lending_detail`, `get_borrower_loan`, `get_cpi_monthly`
  currently return a single ECOS `item_code1` value rather
  than the full series implied by their docstrings. Each emits a
  `ecos.EcosPartialCoverageWarning` (a `UserWarning` subclass, so visible under
  Python's default filter) at call time. The signature/behavior will be
  redesigned in v0.3.0; see issue #8 and the v0.3.0 epic #3.
  Silence with:
  ```python
  import warnings, ecos
  warnings.simplefilter("ignore", ecos.EcosPartialCoverageWarning)
  ```

## [0.1.5] - 2025-12-31

## [0.1.4] - 2025-12-31

### Added - 30개 신규 함수

**재정 지표 (1개)**
- `get_fiscal_balance()` - 통합재정수지

**금융시장 지표 (5개)**
- `get_stock_index(frequency)` - 주가지수 KOSPI (일별/월별)
- `get_investor_trading()` - 투자자별 주식거래
- `get_bond_yield(bond_type)` - 채권 수익률 (종류별/시장별)

**금리 지표 (2개)**
- `get_bank_deposit_rate(basis)` - 예금은행 수신금리 (신규/잔액)
- `get_bank_lending_rate(basis)` - 예금은행 대출금리 (신규/잔액)

**통화·금융 지표 (13개)**
- `get_m1_variants(variant)` - M1 평잔/말잔, 계절조정/원계열
- `get_m2_variants(variant)` - M2 평잔/말잔, 계절조정/원계열
- `get_m2_by_holder(variant)` - M2 경제주체별
- `get_household_credit(category)` - 가계신용 업권별/용도별
- `get_household_lending_detail()` - 예금취급기관 가계대출 용도별
- `get_borrower_loan(loan_type)` - 차주별 가계대출 신규/잔액

**성장 지표 (9개)**
- `get_gdp_growth_rate(frequency)` - 실질 GDP 성장률
- `get_gdp_by_industry(basis, seasonal_adj, frequency)` - 산업별 GDP
- `get_gdp_by_expenditure(basis, frequency)` - 지출항목별 GDP
- `get_gdp_deflator_by_industry(frequency)` - 산업별 GDP 디플레이터

### Changed
- 모든 stat_code의 item_code를 ECOS API와 검증하여 수정
- Constants 모듈 확장 (30개 새 stat_code 및 매핑 추가)

### Fixed
- 조건부 item_code 선택 구현 (일별/월별, 신규/잔액 등)

## [0.1.3] - 2025-12-30

### Fixed
- **통계코드 및 항목코드 수정**: 실제 ECOS API와 일치하도록 모든 지표의 stat_code와 item_code 수정
  - 근원 CPI: 항목코드 `AA0000` → `00`
  - 생산자물가지수(PPI): 항목코드 `A00` → `*AA`
  - 실질 GDP: 통계코드 `200Y001` → `200Y110`, 항목코드 `10101` → `10601`
  - 명목 GDP: 통계코드 `200Y002` → `200Y109`, 항목코드 `10101` → `10601`
  - GDP 디플레이터: 통계코드 `200Y004` → `200Y112`, 항목코드 `10101` → `10601`
  - M1 통화량: 통계코드 `101Y018`/항목 `BBLS00` → `161Y004`/`BBKA00`
  - M2 통화량: 별도 통계코드 `161Y008` 사용
  - Lf 통화량: 별도 통계코드 `171Y002` 사용
- **통화 지표 구조 개선**: 각 통화량 지표(M1, M2, Lf)가 올바른 통계코드를 사용하도록 수정
- **은행 대출 함수 개선**: 가계대출 지원 추가, 기업대출은 별도 통계표 필요로 제거

### Added
- **E2E 테스트 확대**: 모든 High-Level 지표 함수에 대한 18개의 E2E 테스트 추가
  - 금리 지표: 기준금리, 국고채 수익률, 장단기 금리차
  - 물가 지표: CPI, 근원 CPI, PPI
  - 성장 지표: GDP(분기/연간, 실질/명목), GDP 디플레이터
  - 통화 지표: M1/M2/Lf, 은행 대출(전체/가계)
  - 통합 워크플로우 및 캐시 기능 테스트

### Changed
- `constants.py`: 모든 통계코드와 항목코드를 실제 API 응답과 일치하도록 업데이트
- `money.py`: 통화량 조회 시 지표별로 다른 통계코드를 사용하도록 리팩토링
- `test_e2e_indicators.py`: 실제 API 응답에 맞춰 테스트 기대값 수정

## [0.1.2] - 2025-12-30

### Added
- **완전한 ECOS API 지원**: 누락되었던 3개의 API 엔드포인트 추가
  - `get_statistic_word()` - 통계용어사전 조회
  - `get_key_statistic_list()` - 100대 통계지표 조회
  - `get_statistic_meta()` - 통계메타DB 조회
- **확장된 주기 지원**: 반년(S), 반월(SM) 주기 타입 추가
- **향상된 날짜 파싱**: 모든 ECOS 날짜 형식 지원
  - 연간 (YYYY)
  - 반년 (YYYYSN)
  - 분기 (YYYYQN)
  - 월간 (YYYYMM)
  - 반월 (YYYYMMSMN)
  - 일간 (YYYYMMDD)
- **포괄적인 E2E 테스트**: 실제 API를 사용한 13개의 통합 테스트 추가
- **완전한 API 필드 매핑**: 모든 API 응답 필드에 대한 파서 지원

### Changed
- `EcosService` 타입에 `StatisticMeta` 추가
- `Period` 타입 확장: `D`, `M`, `Q`, `A`, `S`, `SM` 모두 지원
- 파서 컬럼 매핑 확장: StatisticWord, KeyStatisticList, StatisticMeta, StatisticTableList의 모든 필드 포함

### Fixed
- 공식 ECOS API 가이드와 완전히 일치하도록 코드 리팩토링
- URL 구성 및 파라미터 처리 개선

## [0.1.1] - 2025-12-30

### Added
- 완전한 MkDocs 문서 사이트
  - 설치 가이드 및 빠른 시작
  - 사용자 가이드 (기본 사용법, 금리/물가/성장/통화 지표, 고급 기능)
  - API 레퍼런스 (클라이언트, 지표 함수, 예외 처리)
  - 실전 예제 (기본 사용법, 거시경제 대시보드)
  - 기여 가이드
- GitHub Actions 워크플로우를 통한 문서 자동 배포
- `docs` optional dependency 추가 (mkdocs, mkdocs-material)

### Changed
- README에 문서 링크 추가
- pyproject.toml의 Documentation URL을 GitHub Pages로 업데이트

## [0.1.0] - 2025-12-30

### Added
- 초기 릴리스
- 한국은행 ECOS Open API 클라이언트 구현
- 금리 지표 조회
  - 한국은행 기준금리 (`get_base_rate`)
  - 국고채 수익률 (`get_treasury_yield`)
  - 장단기 금리차 (`get_yield_spread`)
- 물가 지표 조회
  - 소비자물가지수 (`get_cpi`)
  - 근원 CPI (`get_core_cpi`)
  - 생산자물가지수 (`get_ppi`)
- 성장 지표 조회
  - GDP (`get_gdp`)
  - GDP 디플레이터 (`get_gdp_deflator`)
- 통화 지표 조회
  - 통화량 (`get_money_supply`)
  - 은행 대출 (`get_bank_lending`)
- API 키 설정 기능
  - 환경 변수 지원
  - `.env` 파일 지원
  - 코드에서 직접 설정
- 자동 캐싱 기능
- 에러 처리
  - `EcosConfigError` - 설정 오류
  - `EcosNetworkError` - 네트워크 오류
  - `EcosAPIError` - API 응답 오류
- 로깅 지원
- 타입 힌팅
- 단위 테스트 및 커버리지
- 예제 코드
  - 기본 사용법 (`examples/basic_usage.py`)
  - 거시경제 대시보드 (`examples/macro_dashboard.py`)

[0.5.1]: https://github.com/choo121600/ecos-reader/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/choo121600/ecos-reader/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/choo121600/ecos-reader/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/choo121600/ecos-reader/compare/v0.2.2...v0.3.0
[0.1.2]: https://github.com/choo121600/ecos-reader/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/choo121600/ecos-reader/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/choo121600/ecos-reader/releases/tag/v0.1.0
