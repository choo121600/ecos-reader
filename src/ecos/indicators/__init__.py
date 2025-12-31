"""
ecos-reader 지표 모듈

각종 거시경제 지표 조회 함수를 제공합니다.
"""

from __future__ import annotations

# 재정·금융시장 지표
from .bond import get_bond_yield
from .fiscal import get_fiscal_balance

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
from .stock import get_investor_trading, get_stock_index

__all__ = [
    # 재정 지표
    "get_fiscal_balance",
    # 주식시장 지표
    "get_stock_index",
    "get_investor_trading",
    # 채권시장 지표
    "get_bond_yield",
    # 금리 지표
    "get_base_rate",
    "get_treasury_yield",
    "get_yield_spread",
    "get_bank_deposit_rate",
    "get_bank_lending_rate",
    # 물가 지표
    "get_cpi",
    "get_core_cpi",
    "get_ppi",
    "get_cpi_monthly",
    "get_cpi_by_category",
    # 성장 지표
    "get_gdp",
    "get_gdp_deflator",
    "get_gdp_growth_rate",
    "get_gdp_by_industry",
    "get_gdp_by_expenditure",
    "get_gdp_deflator_by_industry",
    # 통화 지표
    "get_money_supply",
    "get_bank_lending",
    "get_m1_variants",
    "get_m2_variants",
    "get_m2_by_holder",
    "get_household_credit",
    "get_household_lending_detail",
    "get_borrower_loan",
]
