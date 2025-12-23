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

__version__ = "0.1.0"
__author__ = "yeonguk"

# Config API
# Cache API
from .cache import clear_cache, disable_cache, enable_cache

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
)

# Indicator APIs
from .indicators import (
    get_bank_lending,
    # 금리 지표
    get_base_rate,
    get_core_cpi,
    # 물가 지표
    get_cpi,
    # 성장 지표
    get_gdp,
    get_gdp_deflator,
    # 통화 지표
    get_money_supply,
    get_ppi,
    get_treasury_yield,
    get_yield_spread,
)

# Logging API
from .logging import setup_logging

# Metrics API
from .metrics import get_metrics_summary, reset_metrics

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
    # Exceptions
    "EcosError",
    "EcosAPIError",
    "EcosConfigError",
    "EcosNetworkError",
    "EcosRateLimitError",
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
    # Metrics
    "get_metrics_summary",
    "reset_metrics",
    # Logging
    "setup_logging",
]
