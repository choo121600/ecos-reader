"""
무역 지표 모듈 (#127)

수출입 금액(통관 기준)을 조회합니다. ECOS 통계표 ``901Y118``
(수출입 총괄)을 사용합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..client import get_client
from ..constants import PERIOD_ANNUAL, PERIOD_MONTHLY, STAT_TRADE, TRADE_FLOW_ITEMS
from ..parser import normalize_stat_result, parse_response
from ._dates import default_annual, default_monthly
from ._frequency import normalize_frequency

if TYPE_CHECKING:
    import pandas as pd


def get_trade(
    flow: Literal["export", "import"] = "export",
    start_date: str | None = None,
    end_date: str | None = None,
    frequency: Literal["monthly", "annual"] = "monthly",
) -> pd.DataFrame:
    """수출입 금액(통관 기준)을 조회합니다.

    ECOS 통계표 ``901Y118``(수출입 총괄)을 사용합니다. 단위는 천불(천 USD)이며
    월/연 주기를 지원합니다.

    Parameters
    ----------
    flow : str
        조회 항목.
        - ``'export'``: 수출금액 (기본값)
        - ``'import'``: 수입금액
    start_date : str, optional
        조회 시작 시점. ``frequency`` 에 맞는 형식(월 ``YYYYMM`` / 연 ``YYYY``).
        기본값: 주기별 기본 범위.
    end_date : str, optional
        조회 종료 시점. (형식은 ``start_date`` 와 동일)
    frequency : str
        조회 주기. ``'monthly'``(기본) 또는 ``'annual'``.

    Returns
    -------
    pd.DataFrame
        컬럼: ``date``, ``value``, ``unit``. ``value`` 는 금액(천불).

    Raises
    ------
    ValueError
        지원하지 않는 ``flow`` 또는 ``frequency`` 일 때.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_trade("export")                       # 월별 수출금액
    >>> df = ecos.get_trade("import", frequency="annual")   # 연별 수입금액
    """
    if flow not in TRADE_FLOW_ITEMS:
        allowed = ", ".join(repr(f) for f in TRADE_FLOW_ITEMS)
        raise ValueError(f"get_trade(): flow는 {allowed} 중 하나여야 합니다. (받은 값: {flow!r})")

    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency, allowed=("monthly", "annual"), func_name="get_trade"
    )
    period = PERIOD_MONTHLY if frequency == "monthly" else PERIOD_ANNUAL

    if start_date is None or end_date is None:
        if frequency == "monthly":
            default_start, default_end = default_monthly(24)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_TRADE,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1=TRADE_FLOW_ITEMS[flow],
    )

    df = parse_response(response)
    return normalize_stat_result(df)
