"""
ecos-reader: 한국은행 ECOS Open API Python 클라이언트

한국은행 ECOS Open API를 Python에서 쉽고 일관된 방식으로 사용할 수 있는 라이브러리입니다.

Examples
--------
>>> import ecos
>>> ecos.set_api_key("your_api_key")

# 기준금리 조회
>>> df = ecos.get_base_rate()
>>> df.head()
        date  value unit
0 2024-01-01   3.50    %

# 소비자물가지수 조회
>>> df = ecos.get_cpi(start_date="202301", end_date="202312")
"""

from __future__ import annotations

__version__ = "0.4.0"
__author__ = "yeonguk"

# 범용 조회 API (#100)
from .access import get_series

# Config API
# Cache API
from .cache import clear_cache, disable_cache, enable_cache

# 카탈로그 탐색 API (#103)
from .catalog import get_table_tree, list_tables, load_catalog, search_tables

# Client
from .client import EcosClient, get_client, reset_client, set_client
from .config import clear_api_key, get_api_key, load_env, set_api_key

# Exceptions
from .exceptions import (
    EcosAPIError,
    EcosConfigError,
    EcosError,
    EcosNetworkError,
    EcosRateLimitError,
    EcosServerError,
    EcosValidationError,
)

# Indicator APIs
from .indicators import (
    INDICATORS,
    IndicatorSpec,
    get_bank_deposit_rate,
    get_bank_lending,
    get_bank_lending_rate,
    # 금리 지표
    get_base_rate,
    # 채권시장 지표
    get_bond_yield,
    get_borrower_loan,
    get_core_cpi,
    # 물가 지표
    get_cpi,
    get_cpi_by_category,
    get_cpi_monthly,
    # 재정 지표
    get_fiscal_balance,
    # 성장 지표
    get_gdp,
    get_gdp_by_expenditure,
    get_gdp_by_industry,
    get_gdp_deflator,
    get_gdp_deflator_by_industry,
    get_gdp_growth_rate,
    get_household_credit,
    get_household_lending_detail,
    # 선언적 레지스트리 (#16)
    get_indicator,
    get_investor_trading,
    get_m1_variants,
    get_m2_by_holder,
    get_m2_variants,
    # 통화 지표
    get_money_supply,
    get_ppi,
    # 주식시장 지표
    get_stock_index,
    get_treasury_yield,
    get_yield_spread,
    list_indicators,
)

# Logging API
from .logging import setup_logging

# Metrics API
from .metrics import get_metrics_summary, reset_metrics

# 파서 헬퍼 (#100): 범용 조회 결과를 직접 가공할 때 사용
from .parser import normalize_stat_result, parse_response

__all__ = [
    # Version
    "__version__",
    # Config
    "set_api_key",
    "get_api_key",
    "clear_api_key",
    "load_env",
    # Cache
    "clear_cache",
    "disable_cache",
    "enable_cache",
    # Client
    "EcosClient",
    "get_client",
    "set_client",
    "reset_client",
    # 범용 조회 API (#100)
    "get_series",
    "parse_response",
    "normalize_stat_result",
    # 카탈로그 탐색 API (#103)
    "search_tables",
    "list_tables",
    "get_table_tree",
    "load_catalog",
    # Exceptions
    "EcosError",
    "EcosAPIError",
    "EcosConfigError",
    "EcosNetworkError",
    "EcosRateLimitError",
    "EcosServerError",
    "EcosValidationError",
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
    # 선언적 레지스트리 (#16)
    "get_indicator",
    "list_indicators",
    "INDICATORS",
    "IndicatorSpec",
    # Metrics
    "get_metrics_summary",
    "reset_metrics",
    # Logging
    "setup_logging",
]
