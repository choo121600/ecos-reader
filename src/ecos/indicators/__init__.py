"""
ecos-reader 지표 모듈

각종 거시경제 지표 조회 함수를 제공합니다.
"""

from __future__ import annotations

# 선언적 레지스트리 (#16) — 단일 엔트리 조회 및 지표 메타데이터.
from ._registry import INDICATORS, IndicatorSpec, get_indicator, list_indicators

# 재정·금융시장 지표
from .bond import get_bond_yield

# 국제수지 지표 (#107)
from .bop import get_balance_of_payments
from .fiscal import get_fiscal_balance

# 환율 지표 (#106)
from .forex import get_exchange_rate

# 성장 지표
from .growth import (
    get_gdp,
    get_gdp_by_expenditure,
    get_gdp_by_industry,
    get_gdp_deflator,
    get_gdp_deflator_by_industry,
    get_gdp_growth_rate,
)

# 금리 지표
from .interest_rate import (
    get_bank_deposit_rate,
    get_bank_lending_rate,
    get_base_rate,
    get_treasury_yield,
    get_yield_spread,
)

# 통화 지표
from .money import (
    get_bank_lending,
    get_borrower_loan,
    get_household_credit,
    get_household_lending_detail,
    get_m1_variants,
    get_m2_by_holder,
    get_m2_variants,
    get_money_supply,
)

# 물가 지표
from .prices import (
    get_core_cpi,
    get_cpi,
    get_cpi_by_category,
    get_cpi_monthly,
    get_ppi,
)

# 실물경기 지표 (#109)
from .real_economy import get_facility_investment, get_industrial_production

# 심리 지표 (#108)
from .sentiment import get_business_sentiment, get_consumer_sentiment
from .stock import get_investor_trading, get_stock_index

# ``__all__`` 자동 생성 (#16): 이 모듈로 import 된 모든 공개 ``get_*`` 조회 함수와
# 레지스트리 공개 심볼을 수집합니다. 새 지표 함수를 추가/이동해도 수동 동기화가
# 필요 없습니다.
_REGISTRY_EXPORTS = ["INDICATORS", "IndicatorSpec", "list_indicators"]

__all__ = sorted(
    {name for name, obj in list(globals().items()) if name.startswith("get_") and callable(obj)}
    | set(_REGISTRY_EXPORTS)
)
