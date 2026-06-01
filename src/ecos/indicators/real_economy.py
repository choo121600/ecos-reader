"""
실물경기 지표 모듈 (#109)

산업생산지수·설비투자지수 등 실물 경기 동향 지표를 조회합니다.
- 산업생산지수: ECOS 통계표 ``901Y033``(전산업생산지수).
- 설비투자지수: ECOS 통계표 ``901Y066``.

두 표 모두 월별 지수(기준 2020=100)이며 원계열/계절조정 계열을 제공합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..client import get_client
from ..constants import (
    COMPOSITE_INDEX_ITEMS,
    ITEM_FACILITY_INVESTMENT,
    ITEM_FACILITY_INVESTMENT_SA,
    ITEM_INDUSTRIAL_ORIGINAL,
    ITEM_INDUSTRIAL_PRODUCTION,
    ITEM_INDUSTRIAL_SEASONAL,
    PERIOD_ANNUAL,
    PERIOD_MONTHLY,
    PERIOD_QUARTERLY,
    RETAIL_SALES_INDEX_ITEMS,
    STAT_COMPOSITE_INDEX,
    STAT_FACILITY_INVESTMENT,
    STAT_INDUSTRIAL_PRODUCTION,
    STAT_RETAIL_SALES,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_annual, default_monthly, default_quarterly
from ._frequency import normalize_frequency
from ._subcategory import select_subcategory

if TYPE_CHECKING:
    import pandas as pd


def get_industrial_production(
    start_date: str | None = None,
    end_date: str | None = None,
    seasonal: bool = False,
    frequency: Literal["monthly", "quarterly", "annual"] = "monthly",
) -> pd.DataFrame:
    """전산업생산지수를 조회합니다.

    ECOS 통계표 ``901Y033``(전산업생산지수, 농림어업 제외)을 사용합니다.
    월/분기/연별 지수(기준 2020=100)입니다. 2-축 구조(지수 × 계열)이므로 계열을
    원계열/계절조정 중 하나로 고정해 단일 시계열을 반환합니다.

    Parameters
    ----------
    start_date : str, optional
        조회 시작 시점. ``frequency`` 에 맞는 형식
        (월 ``YYYYMM`` / 분기 ``YYYYQn`` / 연 ``YYYY``). 기본값: 주기별 기본 범위.
    end_date : str, optional
        조회 종료 시점. (형식은 ``start_date`` 와 동일)
    seasonal : bool, default False
        ``True`` 면 계절조정 계열, ``False`` 면 원계열(기본).
    frequency : str
        조회 주기. ``'monthly'``(기본)/``'quarterly'``/``'annual'``.

    Returns
    -------
    pd.DataFrame
        컬럼: ``date``, ``value``, ``unit``. ``value`` 는 지수(2020=100).

    Raises
    ------
    ValueError
        지원하지 않는 ``frequency`` 일 때.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_industrial_production()                 # 원계열(월)
    >>> df = ecos.get_industrial_production(seasonal=True)    # 계절조정
    >>> df = ecos.get_industrial_production(frequency="annual")
    """
    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency,
        allowed=("monthly", "quarterly", "annual"),
        func_name="get_industrial_production",
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

    series = ITEM_INDUSTRIAL_SEASONAL if seasonal else ITEM_INDUSTRIAL_ORIGINAL
    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_INDUSTRIAL_PRODUCTION,
        period=period,
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
    frequency: Literal["monthly", "quarterly", "annual"] = "monthly",
) -> pd.DataFrame:
    """설비투자지수를 조회합니다.

    ECOS 통계표 ``901Y066``(설비투자지수)을 사용합니다. 월/분기/연별 지수(기준
    2020=100)이며, 원지수/계절조정지수 중 하나를 반환합니다.

    Parameters
    ----------
    start_date : str, optional
        조회 시작 시점. ``frequency`` 에 맞는 형식
        (월 ``YYYYMM`` / 분기 ``YYYYQn`` / 연 ``YYYY``). 기본값: 주기별 기본 범위.
    end_date : str, optional
        조회 종료 시점. (형식은 ``start_date`` 와 동일)
    seasonal : bool, default False
        ``True`` 면 계절조정지수, ``False`` 면 원지수(기본).
    frequency : str
        조회 주기. ``'monthly'``(기본)/``'quarterly'``/``'annual'``.

    Returns
    -------
    pd.DataFrame
        컬럼: ``date``, ``value``, ``unit``. ``value`` 는 지수(2020=100).

    Raises
    ------
    ValueError
        지원하지 않는 ``frequency`` 일 때.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_facility_investment()
    >>> df = ecos.get_facility_investment(frequency="annual")
    """
    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency,
        allowed=("monthly", "quarterly", "annual"),
        func_name="get_facility_investment",
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

    item = ITEM_FACILITY_INVESTMENT_SA if seasonal else ITEM_FACILITY_INVESTMENT
    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_FACILITY_INVESTMENT,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1=item,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_composite_index(
    index: Literal["leading", "coincident", "lagging"] = "coincident",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """경기종합지수(CI)를 조회합니다.

    ECOS 통계표 ``901Y067``(경기종합지수)의 선행/동행/후행 종합지수를
    조회합니다. 월별 지수(기준 2020=100)입니다.

    Parameters
    ----------
    index : str
        조회할 지수.
        - ``'coincident'``: 동행종합지수 (기본값)
        - ``'leading'``: 선행종합지수
        - ``'lagging'``: 후행종합지수
    start_date : str, optional
        조회 시작월 (``YYYYMM`` 형식). 기본값: 24개월 전.
    end_date : str, optional
        조회 종료월 (``YYYYMM`` 형식). 기본값: 현재.

    Returns
    -------
    pd.DataFrame
        컬럼: ``date``, ``value``, ``unit``. ``value`` 는 지수(2020=100).

    Raises
    ------
    ValueError
        지원하지 않는 ``index`` 일 때.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_composite_index("leading")
    """
    if index not in COMPOSITE_INDEX_ITEMS:
        allowed = ", ".join(repr(i) for i in COMPOSITE_INDEX_ITEMS)
        raise ValueError(
            f"get_composite_index(): index는 {allowed} 중 하나여야 합니다. (받은 값: {index!r})"
        )

    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_COMPOSITE_INDEX,
        period="M",
        start_date=start_date,
        end_date=end_date,
        item_code1=COMPOSITE_INDEX_ITEMS[index],
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_retail_sales(
    index: Literal["nominal", "real", "seasonal"] = "real",
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    frequency: Literal["monthly", "quarterly", "annual"] = "monthly",
) -> pd.DataFrame:
    """소매판매액지수를 상품군별로 조회합니다.

    ECOS 통계표 ``901Y100``(재별 및 상품군별 판매액지수)을 조회합니다. 2-축 구조
    (상품군 ``item_code1`` × 지수 계열 ``item_code2``)로, ``index`` 로 계열을 고정한 뒤
    partial-coverage 규약(#56)에 따라 ``sub_category`` 미지정 시 전체 상품군을
    long-format으로, 지정 시 해당 상품군 단일 시계열만 반환합니다. 기준 2020=100.

    Parameters
    ----------
    index : str
        지수 계열.
        - ``'real'``: 불변지수 (기본값, 물량 기준)
        - ``'nominal'``: 경상지수 (금액 기준)
        - ``'seasonal'``: 계절조정지수
    sub_category : str, optional
        상품군(분류명 또는 item_code1). 지정 시 해당 상품군 단일 시계열만,
        미지정 시 전체 상품군을 long-format으로 반환합니다.
        예) '총지수', '내구재', '음식료품', 또는 item_code 'G31'.
    start_date : str, optional
        조회 시작 시점. ``frequency`` 에 맞는 형식
        (월 ``YYYYMM`` / 분기 ``YYYYQn`` / 연 ``YYYY``). 기본값: 주기별 기본 범위.
    end_date : str, optional
        조회 종료 시점. (형식은 ``start_date`` 와 동일)
    frequency : str
        조회 주기. ``'monthly'``(기본)/``'quarterly'``/``'annual'``.

    Returns
    -------
    pd.DataFrame
        - ``sub_category`` 미지정: 컬럼 ``date, category_value, value, unit``
          (상품군별 long-format, ``category_value``=상품군명). 통계표는 계층형
          (총지수+내구재/준내구재/비내구재+세부품목)이라 단순 합산은 금지.
        - ``sub_category`` 지정: 컬럼 ``date, value, unit`` (단일 시계열).
        - value 는 지수(2020=100).

    Raises
    ------
    ValueError
        지원하지 않는 ``index``/``frequency`` 이거나 ``sub_category`` 가 없을 때.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_retail_sales()                          # 전체 상품군 long-format(불변지수, 월)
    >>> df = ecos.get_retail_sales(sub_category="총지수")       # 총지수 단일 시계열
    >>> df = ecos.get_retail_sales("nominal", sub_category="음식료품", frequency="annual")
    """
    if index not in RETAIL_SALES_INDEX_ITEMS:
        allowed = ", ".join(repr(i) for i in RETAIL_SALES_INDEX_ITEMS)
        raise ValueError(
            f"get_retail_sales(): index는 {allowed} 중 하나여야 합니다. (받은 값: {index!r})"
        )

    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency,
        allowed=("monthly", "quarterly", "annual"),
        func_name="get_retail_sales",
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

    # ECOS API는 item_code를 위치 기반으로 받아 item_code2 단독 필터가 불가하다.
    # bond_market과 동일하게 필터 없이 전량 조회 후, index(계열)를 item_code2로
    # client-side 고정한 뒤 상품군(item_code1)을 select_subcategory로 분류한다(#56 규약).
    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_RETAIL_SALES,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    df = parse_response(response)
    if "item_code2" in df.columns:
        df = df[df["item_code2"] == RETAIL_SALES_INDEX_ITEMS[index]]
    return select_subcategory(df, prefix="", sub_category=sub_category, context="get_retail_sales")
