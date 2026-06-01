# ECOS 통계 구현 현황

**마지막 업데이트**: 2026-06-01
**라이브러리 버전**: 0.6.0 (릴리스)

## 커버리지 모델 (v0.5.0~)

v0.5.0부터 커버리지를 **"구현된 표 N개 / 전체"** 비율이 아니라 **2계층**으로 본다.

1. **범용 접근 — ECOS 전체 도달 가능 (100%).** `ecos.get_series(stat_code, period, ...)`
   로 ECOS의 **어떤 통계표든** 직접 조회할 수 있다. 표 탐색은 동봉 카탈로그
   (`search_tables`/`list_tables`/`get_table_tree`)와 항목 탐색(`list_items`)으로
   네트워크 없이 수행한다. 즉 "라이브러리가 도달 못 하는 ECOS 통계는 없다."
2. **큐레이션 — 고가치 지표의 편의 함수.** 자주 쓰는 지표는 올바른
   `(stat_code, item_code, period)`를 검증해 도메인 함수로 노출한다. 아래 목록.

| 항목 | 수치 |
|------|------|
| **동봉 카탈로그 통계표** | 834개 (검색가능 `srch_yn=Y` **609개**) |
| **범용 접근 도달 가능** | 전체 100% (`get_series`) |
| **큐레이션 편의 함수** | 30+ 개 (아래) |

> 동봉 카탈로그 스냅샷은 `src/ecos/data/catalog.csv.gz`(834노드/검색가능 609)이며
> `scripts/audit_codes.py snapshot` 으로 재생성한다(#105). 과거 문서의 664/43 수치는
> v0.1.5 시절 기준으로 폐기되었다.

---

## 범용 접근 API (v0.5.0)

| 함수 | 설명 |
|------|------|
| `get_series(stat_code, period, *, item_code, start_date, end_date, tidy, max_rows, page_size)` | 임의 통계표 조회 → long-format tidy. 윈도우 초과 시 자동 페이지네이션. |
| `list_items(stat_code)` | 표의 세부 항목(item_code/cycle 등) 탐색. |
| `search_tables(keyword)` / `list_tables(parent)` / `get_table_tree()` | 동봉 카탈로그 오프라인 탐색. |
| `load_catalog()` | 카탈로그 전체 DataFrame. |
| `parse_response` / `normalize_stat_result` | 응답 파서 헬퍼(직접 가공용). |
| `RateLimiter` / `get_rate_limiter` · `DiskCache` / `get_disk_cache` | 대량수집 안전장치(선제 throttle + 영속 캐시). |

---

## 구현 완료 통계 목록

### 1. 통화/금융 (7개)

| 통계코드 | 통계명 | 주기 | 구현 함수 |
|---------|--------|------|----------|
| 161Y004 | M1 상품별 구성내역(말잔, 원계열) | 월 | `get_money_supply(indicator="M1")` |
| 161Y008 | M2 상품별 구성내역(말잔, 원계열) | 월 | `get_money_supply(indicator="M2")` |
| 171Y002 | Lf 상품별 구성내역(말잔, 원계열) | 월 | `get_money_supply(indicator="Lf")` |
| 104Y016 | 예금은행 대출금(말잔) | 월 | `get_bank_lending(sector="all")` |
| 151Y002 | 예금취급기관 가계대출(업권별, 월) | 월 | `get_bank_lending(sector="household")` |
| 722Y001 | 한국은행 기준금리 및 여수신금리 | 일 | `get_base_rate()` |
| 817Y002 | 시장금리(일별) | 일 | `get_treasury_yield()` |

### 2. 국민계정 (3개)

| 통계코드 | 통계명 | 주기 | 구현 함수 |
|---------|--------|------|----------|
| 200Y109 | 국내총생산에 대한 지출(원계열, 명목, 분기 및 연간) | 분기 | `get_gdp(basis="nominal")` |
| 200Y110 | 국내총생산에 대한 지출(원계열, 실질, 분기 및 연간) | 분기 | `get_gdp(basis="real")` |
| 200Y112 | 국내총생산에 대한 지출 디플레이터(분기 및 연간) | 분기 | `get_gdp_deflator()` |

### 3. 물가 (3개)

| 통계코드 | 통계명 | 주기 | 구현 함수 |
|---------|--------|------|----------|
| 404Y014 | 생산자물가지수(기본분류) | 월 | `get_ppi()` |
| 901Y009 | 소비자물가지수 | 월 | `get_cpi()` |
| 901Y010 | 소비자물가지수(특수분류) | 월 | `get_core_cpi()` |

### 4. 환율·국제수지·심리·실물경기 (v0.5.0 신규)

| 통계코드 | 통계명 | 주기 | 구현 함수 |
|---------|--------|------|----------|
| 731Y001 | 주요국 통화의 대원화환율 | 일 | `get_exchange_rate(currency=...)` |
| 301Y013 | 국제수지 | 월/분기/연 | `get_balance_of_payments(account=...)` |
| 512Y014 | 기업경기조사(업황전망BSI) | 월 | `get_business_sentiment(sector=...)` |
| 511Y002 | 소비자동향조사(CSI) | 월 | `get_consumer_sentiment()` |
| 901Y033 | 전산업생산지수 | 월 | `get_industrial_production(seasonal=...)` |
| 901Y066 | 설비투자지수 | 월 | `get_facility_investment(seasonal=...)` |

### 5. 무역·경기종합지수·소매판매 (v0.5.1 신규)

| 통계코드 | 통계명 | 주기 | 구현 함수 |
|---------|--------|------|----------|
| 901Y118 | 수출입 총괄 | 월/연 | `get_trade(flow=...)` (#127) |
| 901Y067 | 경기종합지수 | 월 | `get_composite_index(index=...)` (#127) |
| 901Y100 | 재별 및 상품군별 판매액지수(총지수) | 월/분기/연 | `get_retail_sales(index=...)` (#130) |

> 이 외 모든 통계표는 `get_series()` 로 도달 가능하다(범용 접근). 위 목록은
> 큐레이션된 편의 함수만 나열한다.

---

## 큐레이션 후보 (범용 접근으로는 이미 도달 가능)

아래 표들은 아직 **편의 함수**가 없을 뿐, `get_series()` 로 지금도 조회할 수 있다.
큐레이션 우선순위 참고용 목록이다.

> 참고: v0.1.5 문서에 있던 환율 `731Y003`/`731Y004`, 국제수지 `301Y017`, 설비투자
> `901Y049` 는 **잘못된 코드**였고 #67/#70/#72/#74에서 정정되었다(각각 731Y001 /
> 301Y013 / 901Y066). 환율·국제수지·BSI·CSI·산업생산·설비투자는 v0.5.0에서
> 큐레이션 완료되어 위 "구현 완료" 목록으로 이동했다.

### 🟢 사용 빈도가 높은 큐레이션 후보 통계

#### 금리 관련
| 통계코드 | 통계명 |
|---------|--------|
| 721Y001 | 시장금리(월, 분기, 년) |
| 121Y002 | 예금은행 수신금리(신규취급액 기준) |
| 121Y006 | 예금은행 대출금리(신규취급액 기준) |

#### 국민계정 관련
| 통계코드 | 통계명 |
|---------|--------|
| 200Y138 | 경제활동별 설비투자(명목, 연간) |
| 200Y140 | 가계의 목적별 최종소비지출(계절조정, 명목, 분기) |
| 200Y142 | 가계의 목적별 최종소비지출(원계열, 명목, 분기 및 연간) |

#### 물가 관련
| 통계코드 | 통계명 |
|---------|--------|
| 404Y015 | 생산자물가지수(특수분류) |
| 402Y014 | 수출물가지수(기본분류) |
| 401Y015 | 수입물가지수(기본분류) |

#### 무역 관련
| 통계코드 | 통계명 |
|---------|--------|
| 901Y119 | 대륙별 수출입 |
| 901Y121 | 국가별 수출입 |

> 수출입 총괄(901Y118)은 `get_trade()` 로 큐레이션 완료되어 위 "구현 완료" 목록으로 이동했다.

---

## 개발 로드맵

### v0.5.0 - 범용 접근 + 카탈로그 (Epic #98)
- [x] `get_series()` - 임의 통계표 범용 조회 (#100)
- [x] 자동 페이지네이션 (#101)
- [x] rate limiter + 디스크 캐시 (#102)
- [x] 카탈로그 스냅샷 + 탐색 API (#103) / 재생성 스크립트·CI (#105)
- [x] `list_items()` - 항목 탐색 (#104)

### v0.5.0 - 도메인 큐레이션 (Epic #98)
- [x] `get_exchange_rate()` - 주요 통화 환율 (731Y001, #106)
- [x] `get_balance_of_payments()` - 경상/자본/금융계정 (301Y013, #107)
- [x] `get_business_sentiment()` / `get_consumer_sentiment()` - BSI/CSI (#108)
- [x] `get_industrial_production()` / `get_facility_investment()` - 실물경기 (#109)

### v0.5.1 - 추가 도메인 큐레이션
- [x] `get_trade()` - 수출입 총괄 (901Y118, #127)
- [x] `get_composite_index()` - 경기종합지수 (901Y067, #127)
- [x] `get_retail_sales()` - 소매판매액지수 (901Y100, #130)

### 후속 (별도 이슈 분리)
- [ ] `get_effective_exchange_rate()` - 실효환율 (ECOS 원천 미확정, #71)
- [ ] 고용(고용률/실업률) 큐레이션
- [ ] 기업경영분석 지표

---

## 기여 가이드

### 새로운 지표 추가 방법

1. **통계코드 확인**
   ```python
   # ECOS에서 원하는 통계 찾기
   client = EcosClient(api_key="your_key")
   tables = client.get_statistic_table_list(start=1, end=100)
   ```

2. **constants.py에 추가**
   ```python
   # 통계코드 및 항목코드 정의
   STAT_NEW_INDICATOR = "XXX"
   ITEM_NEW_INDICATOR = "YYY"
   ```

3. **indicator 함수 구현**
   ```python
   # src/ecos/indicators/category.py
   def get_new_indicator(start_date=None, end_date=None):
       # 구현
       pass
   ```

4. **E2E 테스트 작성**
   ```python
   # tests/test_e2e_indicators.py
   def test_get_new_indicator(self):
       df = ecos.get_new_indicator()
       assert not df.empty
   ```

5. **Pull Request 제출**
   - 테스트 통과 확인
   - 문서 업데이트
   - PR 제출

---

## 참고 자료

- **동봉 카탈로그 스냅샷**: `src/ecos/data/catalog.csv.gz` (834표/검색가능 609).
  `ecos.search_tables()`/`list_tables()`/`get_table_tree()` 로 조회, `scripts/audit_codes.py snapshot` 으로 재생성.
- **범용 조회**: `ecos.get_series(stat_code, period, ...)` — 카탈로그의 어떤 표든 도달 가능.
- **ECOS Open API 공식 문서**: https://ecos.bok.or.kr/api/
- **GitHub Issues**: https://github.com/choo121600/ecos-reader/issues
