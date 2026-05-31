# ecos-reader

**한국은행 ECOS Open API Python 클라이언트**

ecos-reader는 한국은행 ECOS Open API를 Python에서 쉽고 일관된 방식으로 사용할 수 있는 라이브러리입니다.

## 두 가지 사용 방식

ecos-reader는 동등한 두 진입점을 제공합니다. 둘 다 정규화된 pandas DataFrame을 반환합니다.

| | 큐레이션 함수 | 범용 조회 |
|---|---|---|
| **함수** | `get_base_rate()`, `get_cpi()`, `get_gdp()` … (37개) | `get_series(stat_code, period, …)` |
| **언제** | 자주 쓰는 고가치 지표를 검증된 인자로 바로 | ECOS의 **어떤 통계표든** 직접 |
| **탐색** | 함수 시그니처가 곧 옵션 | `search_tables()` / `list_tables()` / `list_items()` (오프라인 카탈로그) |
| **도달 범위** | 큐레이션된 핵심 지표 | ECOS 전체 (도달 못 하는 통계 없음) |

> 큐레이션 함수는 범용 조회 위에 올바른 `(stat_code, item_code, period)`를 검증해 얹은
> 편의 계층입니다. 도메인 함수가 없는 통계는 `get_series` 로 도달하세요.

## 주요 특징

- **두 진입점**: 큐레이션 함수 + `get_series` 범용 조회로 ECOS 전체 도달
- **타입 안전성**: 완전한 타입 힌팅 지원으로 IDE 자동완성 활용
- **pandas 통합**: 모든 데이터를 long-format tidy DataFrame으로 반환
- **오프라인 탐색**: 통계표 카탈로그를 패키지에 동봉 — 네트워크 없이 검색
- **자동 캐싱·rate limit**: 반복 요청 캐싱 + 대량 수집용 선제 throttle
- **에러 처리**: 명확한 예외 클래스로 안정적인 에러 핸들링

## 빠른 시작

### 설치

```bash
pip install ecos-reader
```

### API 키 설정

한국은행에서 발급받은 API 키를 환경 변수로 설정합니다.

```bash
export ECOS_API_KEY="your_api_key"
```

!!! info "API 키 발급"
    API 키는 [한국은행 ECOS](https://ecos.bok.or.kr/api/)에서 무료로 발급받을 수 있습니다.

### 첫 번째 코드

```python
import ecos

# 한국은행 기준금리 조회
df = ecos.get_base_rate()
print(df)
```

출력 예시:

```
        date  value unit
0 2024-01-01   3.50    %
1 2024-02-01   3.50    %
2 2024-03-01   3.50    %
...
```

큐레이션 함수가 없는 통계는 `get_series` 로 직접 조회합니다.

```python
import ecos

# 통계표 찾기 → 임의 시계열 조회 (네트워크 없이 검색)
hits = ecos.search_tables("소비자물가")          # 오프라인 카탈로그 검색
df = ecos.get_series(
    "901Y009", "monthly",
    start_date="202401", end_date="202412",
)
```

자세한 범용 조회·탐색은 [범용 조회 & 탐색](user-guide/universal-access.md) 가이드를 참고하세요.

## 커버리지

ECOS 전체 통계는 `get_series` 로 100% 도달할 수 있고, 그 위에 **큐레이션 편의 함수 37개**가
도메인별로 제공됩니다. 통계표 카탈로그(834노드, 검색가능 609개)는 패키지에 동봉되어 오프라인으로
탐색합니다. 표별 상세 현황은 [구현 현황](https://github.com/choo121600/ecos-reader/blob/main/IMPLEMENTATION_STATUS.md)을 참고하세요.

### 큐레이션 함수 도메인 (37개)

| 도메인 | 함수 |
|--------|------|
| 금리 (5) | `get_base_rate`, `get_treasury_yield`, `get_yield_spread`, `get_bank_deposit_rate`, `get_bank_lending_rate` |
| 물가 (5) | `get_cpi`, `get_core_cpi`, `get_ppi`, `get_cpi_monthly`, `get_cpi_by_category` |
| 성장 (6) | `get_gdp`, `get_gdp_deflator`, `get_gdp_growth_rate`, `get_gdp_by_industry`, `get_gdp_by_expenditure`, `get_gdp_deflator_by_industry` |
| 통화·가계금융 (8) | `get_money_supply`, `get_bank_lending`, `get_m1_variants`, `get_m2_variants`, `get_m2_by_holder`, `get_household_credit`, `get_household_lending_detail`, `get_borrower_loan` |
| 실물경기 (4) | `get_industrial_production`, `get_facility_investment`, `get_composite_index`, `get_retail_sales` |
| 심리 (2) | `get_business_sentiment`, `get_consumer_sentiment` |
| 금융시장 (3) | `get_stock_index`, `get_investor_trading`, `get_bond_yield` |
| 환율 (1) | `get_exchange_rate` |
| 국제수지 (1) | `get_balance_of_payments` |
| 무역 (1) | `get_trade` |
| 재정 (1) | `get_fiscal_balance` |

## 다음 단계

- [설치 가이드](getting-started/installation.md) - 자세한 설치 방법
- [빠른 시작](getting-started/quickstart.md) - 기본 사용법 익히기
- [범용 조회 & 탐색](user-guide/universal-access.md) - `get_series`로 ECOS 전체 도달
- [사용자 가이드](user-guide/basic-usage.md) - 심화 사용법
- [API 레퍼런스](api-reference/overview.md) - 전체 API 문서
- [예제](examples/basic.md) - 실전 예제 코드

## 라이센스

MIT License - 자세한 내용은 [LICENSE](https://github.com/choo121600/ecos-reader/blob/main/LICENSE) 파일을 참조하세요.
