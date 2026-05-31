"""
국제수지(BoP) 지표 모듈 (#107)

경상수지/자본수지/금융계정 등 국제수지 주요 시계열을 조회합니다.
ECOS 통계표 ``301Y013``(국제수지, 경상·자본·금융계정 전체)을 단일
진실원천으로 사용합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..client import get_client
from ..constants import (
    BOP_ACCOUNT_ITEMS,
    PERIOD_ANNUAL,
    PERIOD_MONTHLY,
    PERIOD_QUARTERLY,
    STAT_BOP,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_annual, default_monthly, default_quarterly
from ._frequency import normalize_frequency

if TYPE_CHECKING:
    import pandas as pd


def get_balance_of_payments(
    account: Literal["current", "capital", "financial"] = "current",
    start_date: str | None = None,
    end_date: str | None = None,
    frequency: Literal["monthly", "quarterly", "annual"] = "monthly",
) -> pd.DataFrame:
    """국제수지(BoP) 주요 계정 시계열을 조회합니다.

    ECOS 통계표 ``301Y013``(국제수지)을 사용합니다. 단위는 백만달러이며,
    월/분기/연 주기를 지원합니다.

    Parameters
    ----------
    account : str
        조회할 계정.
        - ``'current'``: 경상수지 (기본값)
        - ``'capital'``: 자본수지
        - ``'financial'``: 금융계정
    start_date : str, optional
        조회 시작 시점. ``frequency`` 에 맞는 형식
        (월 ``YYYYMM`` / 분기 ``YYYYQn`` / 연 ``YYYY``). 기본값: 주기별 기본 범위.
    end_date : str, optional
        조회 종료 시점. (형식은 ``start_date`` 와 동일)
    frequency : str
        조회 주기.
        - ``'monthly'``: 월별 (기본값)
        - ``'quarterly'``: 분기별
        - ``'annual'``: 연별

    Returns
    -------
    pd.DataFrame
        컬럼: ``date``, ``value``, ``unit``.
        - ``value``: 수지 (백만달러). 흑자는 양수, 적자는 음수.

    Raises
    ------
    ValueError
        지원하지 않는 ``account`` 또는 ``frequency`` 일 때.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_balance_of_payments("current")  # 월별 경상수지
    >>> df = ecos.get_balance_of_payments("financial", frequency="annual")
    """
    if account not in BOP_ACCOUNT_ITEMS:
        allowed = ", ".join(repr(a) for a in BOP_ACCOUNT_ITEMS)
        raise ValueError(
            f"get_balance_of_payments(): account는 {allowed} 중 하나여야 합니다. "
            f"(받은 값: {account!r})"
        )

    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency,
        allowed=("monthly", "quarterly", "annual"),
        func_name="get_balance_of_payments",
    )

    period = {
        "monthly": PERIOD_MONTHLY,
        "quarterly": PERIOD_QUARTERLY,
        "annual": PERIOD_ANNUAL,
    }[frequency]

    if start_date is None or end_date is None:
        if frequency == "monthly":
            default_start, default_end = default_monthly(24)
        elif frequency == "quarterly":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_BOP,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1=BOP_ACCOUNT_ITEMS[account],
    )

    df = parse_response(response)
    return normalize_stat_result(df)
