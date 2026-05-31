"""
실물경기 지표 모듈 (#109)

산업생산지수·설비투자지수 등 실물 경기 동향 지표를 조회합니다.
- 산업생산지수: ECOS 통계표 ``901Y033``(전산업생산지수).
- 설비투자지수: ECOS 통계표 ``901Y066``.

두 표 모두 월별 지수(기준 2020=100)이며 원계열/계절조정 계열을 제공합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..client import get_client
from ..constants import (
    ITEM_FACILITY_INVESTMENT,
    ITEM_FACILITY_INVESTMENT_SA,
    ITEM_INDUSTRIAL_ORIGINAL,
    ITEM_INDUSTRIAL_PRODUCTION,
    ITEM_INDUSTRIAL_SEASONAL,
    STAT_FACILITY_INVESTMENT,
    STAT_INDUSTRIAL_PRODUCTION,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_monthly

if TYPE_CHECKING:
    import pandas as pd


def get_industrial_production(
    start_date: str | None = None,
    end_date: str | None = None,
    seasonal: bool = False,
) -> pd.DataFrame:
    """전산업생산지수를 조회합니다.

    ECOS 통계표 ``901Y033``(전산업생산지수, 농림어업 제외)을 사용합니다.
    월별 지수(기준 2020=100)입니다. 2-축 구조(지수 × 계열)이므로 계열을
    원계열/계절조정 중 하나로 고정해 단일 시계열을 반환합니다.

    Parameters
    ----------
    start_date : str, optional
        조회 시작월 (``YYYYMM`` 형식). 기본값: 24개월 전.
    end_date : str, optional
        조회 종료월 (``YYYYMM`` 형식). 기본값: 현재.
    seasonal : bool, default False
        ``True`` 면 계절조정 계열, ``False`` 면 원계열(기본).

    Returns
    -------
    pd.DataFrame
        컬럼: ``date``, ``value``, ``unit``. ``value`` 는 지수(2020=100).

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_industrial_production()                 # 원계열
    >>> df = ecos.get_industrial_production(seasonal=True)    # 계절조정
    """
    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    series = ITEM_INDUSTRIAL_SEASONAL if seasonal else ITEM_INDUSTRIAL_ORIGINAL
    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_INDUSTRIAL_PRODUCTION,
        period="M",
        start_date=start_date,
        end_date=end_date,
        item_code1=ITEM_INDUSTRIAL_PRODUCTION,
        item_code2=series,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_facility_investment(
    start_date: str | None = None,
    end_date: str | None = None,
    seasonal: bool = False,
) -> pd.DataFrame:
    """설비투자지수를 조회합니다.

    ECOS 통계표 ``901Y066``(설비투자지수)을 사용합니다. 월별 지수(기준
    2020=100)이며, 원지수/계절조정지수 중 하나를 반환합니다.

    Parameters
    ----------
    start_date : str, optional
        조회 시작월 (``YYYYMM`` 형식). 기본값: 24개월 전.
    end_date : str, optional
        조회 종료월 (``YYYYMM`` 형식). 기본값: 현재.
    seasonal : bool, default False
        ``True`` 면 계절조정지수, ``False`` 면 원지수(기본).

    Returns
    -------
    pd.DataFrame
        컬럼: ``date``, ``value``, ``unit``. ``value`` 는 지수(2020=100).

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_facility_investment()
    """
    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    item = ITEM_FACILITY_INVESTMENT_SA if seasonal else ITEM_FACILITY_INVESTMENT
    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_FACILITY_INVESTMENT,
        period="M",
        start_date=start_date,
        end_date=end_date,
        item_code1=item,
    )

    df = parse_response(response)
    return normalize_stat_result(df)
