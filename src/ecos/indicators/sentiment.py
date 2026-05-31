"""
심리 지표 모듈 (#108)

기업경기실사지수(BSI)와 소비자심리지수(CSI)를 조회합니다.
- BSI: ECOS 통계표 ``512Y014``(기업경기조사, 전망). 헤드라인은 업황전망BSI.
- CSI: ECOS 통계표 ``511Y002``(소비자동향조사). 소비자심리지수.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..client import get_client
from ..constants import (
    BSI_SECTOR_ITEMS,
    ITEM_BSI_OUTLOOK,
    ITEM_CSI,
    STAT_BSI,
    STAT_CSI,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_monthly

if TYPE_CHECKING:
    import pandas as pd


def get_business_sentiment(
    sector: Literal["manufacturing", "non_manufacturing", "all"] = "all",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """기업경기실사지수(BSI) — 업황전망BSI를 조회합니다.

    ECOS 통계표 ``512Y014``(기업경기조사, 전망)의 **업황전망BSI**(헤드라인)를
    업종별로 조회합니다. 월별 지수이며, 100을 기준으로 그 이상이면 경기를
    긍정적으로 보는 기업이 더 많음을 뜻합니다.

    Parameters
    ----------
    sector : str
        조회 업종.
        - ``'all'``: 전산업 (기본값)
        - ``'manufacturing'``: 제조업
        - ``'non_manufacturing'``: 비제조업
    start_date : str, optional
        조회 시작월 (``YYYYMM`` 형식). 기본값: 24개월 전.
    end_date : str, optional
        조회 종료월 (``YYYYMM`` 형식). 기본값: 현재.

    Returns
    -------
    pd.DataFrame
        컬럼: ``date``, ``value``, ``unit``.
        - ``value``: 업황전망BSI (지수, 기준 100)

    Raises
    ------
    ValueError
        지원하지 않는 ``sector`` 일 때.

    Notes
    -----
    512Y014는 2-축 구조(업종 × 설문항목)입니다. 이 함수는 설문항목을 업황전망
    BSI(``BA``)로 고정합니다. 매출/생산/자금사정 등 세부 항목은
    ``ecos.get_series("512Y014", "M", item_code=[sector, code2], ...)`` 로 조회하세요.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_business_sentiment("manufacturing")
    """
    if sector not in BSI_SECTOR_ITEMS:
        allowed = ", ".join(repr(s) for s in BSI_SECTOR_ITEMS)
        raise ValueError(
            f"get_business_sentiment(): sector는 {allowed} 중 하나여야 합니다. "
            f"(받은 값: {sector!r})"
        )

    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_BSI,
        period="M",
        start_date=start_date,
        end_date=end_date,
        item_code1=BSI_SECTOR_ITEMS[sector],
        item_code2=ITEM_BSI_OUTLOOK,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_consumer_sentiment(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """소비자심리지수(CSI)를 조회합니다.

    ECOS 통계표 ``511Y002``(소비자동향조사)의 소비자심리지수(``FME``)를
    조회합니다. 월별 지수이며, 100을 기준으로 그 이상이면 소비 심리가
    낙관적임을 뜻합니다.

    Parameters
    ----------
    start_date : str, optional
        조회 시작월 (``YYYYMM`` 형식). 기본값: 24개월 전.
    end_date : str, optional
        조회 종료월 (``YYYYMM`` 형식). 기본값: 현재.

    Returns
    -------
    pd.DataFrame
        컬럼: ``date``, ``value``, ``unit``.
        - ``value``: 소비자심리지수 (지수, 기준 100)

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_consumer_sentiment(start_date="202301", end_date="202312")
    """
    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_CSI,
        period="M",
        start_date=start_date,
        end_date=end_date,
        item_code1=ITEM_CSI,
    )

    df = parse_response(response)
    return normalize_stat_result(df)
