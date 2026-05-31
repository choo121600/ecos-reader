"""
환율 지표 모듈 (#106)

원/외화 환율(매매기준율)을 조회합니다. ECOS 통계표 ``731Y001``
(주요국 통화의 대원화환율, 일별)을 단일 진실원천으로 사용합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..client import get_client
from ..constants import EXCHANGE_RATE_ITEMS, STAT_EXCHANGE_RATE
from ..parser import normalize_stat_result, parse_response
from ._dates import default_daily

if TYPE_CHECKING:
    import pandas as pd


def get_exchange_rate(
    currency: Literal["USD", "JPY", "EUR", "CNY"] = "USD",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """원/외화 환율(매매기준율)을 조회합니다.

    ECOS 통계표 ``731Y001``(주요국 통화의 대원화환율, **일별**)을 사용합니다.
    이 표는 일별 종가의 정본이며, 통화별 매매기준율을 제공합니다.

    Parameters
    ----------
    currency : str
        통화 코드.
        - ``'USD'``: 원/미국달러 (기본값)
        - ``'JPY'``: 원/일본엔 — **100엔당** 환율입니다.
        - ``'EUR'``: 원/유로
        - ``'CNY'``: 원/위안 (2016-01-04~)
    start_date : str, optional
        조회 시작일 (``YYYYMMDD`` 형식), 기본값: 1년 전.
    end_date : str, optional
        조회 종료일 (``YYYYMMDD`` 형식), 기본값: 현재.

    Returns
    -------
    pd.DataFrame
        컬럼: ``date``, ``value``, ``unit``.
        - ``date``: 날짜 (datetime)
        - ``value``: 환율 (원). 환율은 영업일에만 갱신되어 결과가 sparse 합니다.
        - ``unit``: 단위 (원)

    Raises
    ------
    ValueError
        지원하지 않는 ``currency`` 일 때.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_exchange_rate("USD")
    >>> df.head(1)
            date   value unit
    0 2024-01-02  1289.4    원

    >>> # 기간 지정
    >>> df = ecos.get_exchange_rate("JPY", start_date="20240101", end_date="20241231")
    """
    if currency not in EXCHANGE_RATE_ITEMS:
        allowed = ", ".join(repr(c) for c in EXCHANGE_RATE_ITEMS)
        raise ValueError(
            f"get_exchange_rate(): currency는 {allowed} 중 하나여야 합니다. (받은 값: {currency!r})"
        )

    if start_date is None or end_date is None:
        default_start, default_end = default_daily(365)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_EXCHANGE_RATE,
        period="D",
        start_date=start_date,
        end_date=end_date,
        item_code1=EXCHANGE_RATE_ITEMS[currency],
    )

    df = parse_response(response)
    return normalize_stat_result(df)
