"""
ecos-reader 지표 모듈

각종 거시경제 지표 조회 함수를 제공합니다.
"""

from __future__ import annotations

from .growth import get_gdp, get_gdp_deflator
from .interest_rate import get_base_rate, get_treasury_yield, get_yield_spread
from .money import get_bank_lending, get_money_supply
from .prices import get_core_cpi, get_cpi, get_ppi

__all__ = [
    # 금리 지표
    "get_base_rate",
    "get_treasury_yield",
    "get_yield_spread",
    # 물가 지표
    "get_cpi",
    "get_core_cpi",
    "get_ppi",
    # 성장 지표
    "get_gdp",
    "get_gdp_deflator",
    # 통화 지표
    "get_money_supply",
    "get_bank_lending",
]
