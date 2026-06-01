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
from ._subcategory import select_subcategory

#: CSI 인구통계 축(item_code2)의 '전체'. 구성지표 선택 시 이 축을 전체로 고정한다.
_CSI_ALL_DEMO = "99988"

if TYPE_CHECKING:
    import pandas as pd


def get_business_sentiment(
    sector: Literal[
        "all",
        "manufacturing",
        "heavy_chemical",
        "light",
        "large",
        "sme",
        "export",
        "domestic",
        "non_manufacturing",
        "service",
    ] = "all",
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
        조회 업종 (전 부문 라이브 검증, #154).
        - ``'all'``: 전산업 (기본값)
        - ``'manufacturing'``: 제조업 / ``'heavy_chemical'``: 중화학공업 / ``'light'``: 경공업
        - ``'large'``: 대기업 / ``'sme'``: 중소기업 / ``'export'``: 수출기업 / ``'domestic'``: 내수기업
        - ``'non_manufacturing'``: 비제조업 / ``'service'``: 서비스업
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
    sub_category: str | None = None,
) -> pd.DataFrame:
    """소비자심리지수(CSI)를 조회합니다.

    ECOS 통계표 ``511Y002``(소비자동향조사)를 조회합니다. 월별 지수이며, 100을
    기준으로 그 이상이면 소비 심리가 낙관적임을 뜻합니다. 기본은 종합 소비자심리
    지수(``FME``)이며, ``sub_category`` 로 구성지표(생활형편전망·소비지출전망 등)를
    선택할 수 있습니다. 인구통계 축(item_code2)은 '전체'로 고정합니다.

    Parameters
    ----------
    start_date : str, optional
        조회 시작월 (``YYYYMM`` 형식). 기본값: 24개월 전.
    end_date : str, optional
        조회 종료월 (``YYYYMM`` 형식). 기본값: 현재.
    sub_category : str, optional
        구성지표(분류명 또는 item_code1). 미지정 시 종합 소비자심리지수(FME).
        예) '소비지출전망CSI', '생활형편전망CSI', 또는 item_code 'FMCB'.

    Returns
    -------
    pd.DataFrame
        컬럼: ``date``, ``value``, ``unit``. ``value`` 는 지수(기준 100).
        (단일 시계열 — 종합 또는 선택한 구성지표 1개)

    Notes
    -----
    511Y002는 2-축 구조(구성지표 × 인구통계)입니다. 이 함수는 인구통계를 '전체'로
    고정합니다. 성별·연령·소득 등 인구통계별 세부는
    ``ecos.get_series("511Y002", "M", item_code=[code1, demo], ...)`` 로 조회하세요.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_consumer_sentiment()                          # 종합 CSI
    >>> df = ecos.get_consumer_sentiment(sub_category="소비지출전망CSI")
    """
    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    if sub_category is None:
        # 종합 소비자심리지수(FME) — 전체 인구통계 단일 시계열 (기존 동작, 하위호환).
        response = client.get_statistic_search(
            stat_code=STAT_CSI,
            period="M",
            start_date=start_date,
            end_date=end_date,
            item_code1=ITEM_CSI,
        )
        return normalize_stat_result(parse_response(response))

    # 구성지표 선택: 필터 없이 조회 → 인구통계를 '전체'로 client-side 고정 후
    # 구성지표(item_code1)를 select_subcategory로 선택(#56 규약, 단일 시계열 반환).
    response = client.get_statistic_search(
        stat_code=STAT_CSI,
        period="M",
        start_date=start_date,
        end_date=end_date,
    )
    df = parse_response(response)
    if "item_code2" in df.columns:
        df = df[df["item_code2"] == _CSI_ALL_DEMO]
    return select_subcategory(
        df, prefix="", sub_category=sub_category, context="get_consumer_sentiment"
    )
