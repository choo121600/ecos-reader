"""
주식시장 지표 모듈

주가지수, 투자자별 거래 등 주식시장 관련 지표를 조회합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..client import get_client
from ..constants import (
    INVESTOR_TRADING_ACTION_PREFIX,
    INVESTOR_TRADING_METRIC_CODE,
    ITEM_STOCK_INDEX_DAILY,
    ITEM_STOCK_INDEX_MONTHLY,
    PERIOD_ANNUAL,
    PERIOD_DAILY,
    PERIOD_MONTHLY,
    STAT_INVESTOR_TRADING,
    STAT_STOCK_DAILY,
    STAT_STOCK_MONTHLY,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_annual, default_daily, default_monthly
from ._frequency import normalize_frequency
from ._subcategory import select_subcategory

if TYPE_CHECKING:
    import pandas as pd


def get_stock_index(
    frequency: Literal["daily", "monthly"] = "daily",
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    주가지수를 조회합니다.

    KOSPI 종합주가지수를 일별 또는 월별로 조회합니다. ``sub_category`` 를 지정하면
    같은 주식시장 통계표의 다른 항목(시가총액·거래량·KOSDAQ 지수 등)을 선택할 수
    있습니다.

    Parameters
    ----------
    frequency : str
        조회 주기
        - 'daily': 일별 (기본값) — KOSPI 지수
        - 'monthly': 월별 — KOSPI 종가(지수)
    sub_category : str, optional
        주식시장 통계표의 다른 항목(항목명 또는 item_code1)을 선택합니다.
        미지정 시 KOSPI 지수를 반환합니다.
        예) 월별: 'KOSPI_시가총액', 'KOSPI_거래대금', 'KOSDAQ_종가'
    start_date : str, optional
        조회 시작일
        - daily: YYYYMMDD 형식 (예: 20240101)
        - monthly: YYYYMM 형식 (예: 202401)
        기본값: 1년 전(일별) 또는 2년 전(월별)
    end_date : str, optional
        조회 종료일 (형식은 start_date와 동일)

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 주가지수(기본) 또는 선택한 항목 값
        - unit: 단위 (포인트 등)

    Raises
    ------
    ValueError
        지정한 ``sub_category`` 가 존재하지 않는 경우 (사용 가능 항목을 함께 안내).

    Notes
    -----
    - KOSPI(Korea Composite Stock Price Index)는 한국거래소 유가증권시장의 대표 지수
    - 1980년 1월 4일 기준시점 100포인트
    - 시가총액 가중 방식으로 계산
    - v0.3.0(#60): 월별 기본값이 `1010000`(KOSPI 회사수, 오류)에서
      `1070000`(KOSPI 종가, 지수)로 정정되었습니다.

    주가지수는 경기 선행지표로 활용되며, 투자심리와 경제 전망을 반영합니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_stock_index()  # 일별 KOSPI 지수
    >>> df.head()
            date    value     unit
    0 2024-01-02  2655.28  포인트

    >>> df = ecos.get_stock_index(frequency="monthly")  # 월별 KOSPI 종가(지수)

    >>> # 월별 KOSPI 시가총액
    >>> df = ecos.get_stock_index(frequency="monthly", sub_category="KOSPI_시가총액")
    """
    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency, allowed=("daily", "monthly"), func_name="get_stock_index"
    )

    # 주기별 stat_code / period / 기본 지수 item_code 및 기본 날짜 선택
    if frequency == "daily":
        stat_code = STAT_STOCK_DAILY
        period = PERIOD_DAILY
        default_item = ITEM_STOCK_INDEX_DAILY  # 0001000 KOSPI지수
        if start_date is None or end_date is None:
            default_start, default_end = default_daily(365)
            start_date = start_date or default_start
            end_date = end_date or default_end
    else:  # monthly
        stat_code = STAT_STOCK_MONTHLY
        period = PERIOD_MONTHLY
        default_item = ITEM_STOCK_INDEX_MONTHLY  # 1070000 KOSPI 종가 (#60 정정)
        if start_date is None or end_date is None:
            default_start, default_end = default_monthly(24)
            start_date = start_date or default_start
            end_date = end_date or default_end

    client = get_client()

    # 기본(sub_category 미지정): KOSPI 지수 단일 항목을 직접 조회.
    if sub_category is None:
        response = client.get_statistic_search(
            stat_code=stat_code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            item_code1=default_item,
        )
        return normalize_stat_result(parse_response(response))

    # sub_category 지정: 통계표 전량 수신 후 해당 항목 단일 시계열 선택(#58 규약).
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )
    return select_subcategory(
        parse_response(response),
        prefix="",
        sub_category=sub_category,
        context=f"get_stock_index({frequency})",
    )


def get_investor_trading(
    action: Literal["순매수", "매수", "매도"] = "순매수",
    metric: Literal["거래대금", "거래량"] = "거래대금",
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    frequency: Literal["monthly", "annual"] = "monthly",
) -> pd.DataFrame:
    """
    투자자별 주식거래를 조회합니다.

    기관·개인·외국인 등 투자자별 매도/매수/순매수를 거래대금 또는 거래량 기준으로
    제공합니다. partial-coverage 재설계 규약(#56)을 따릅니다 — ``sub_category``
    미지정 시 전체 투자자를 long-format으로, 지정 시 해당 투자자 단일 시계열만
    반환합니다.

    Parameters
    ----------
    action : str
        거래 행위
        - '순매수': 순매수(매수-매도) (기본값)
        - '매수': 매수
        - '매도': 매도
    metric : str
        측정 지표
        - '거래대금': 금액 기준 (기본값)
        - '거래량': 수량 기준
    sub_category : str, optional
        특정 투자자(항목명 또는 item_code1)를 선택합니다. 지정 시 해당 투자자
        단일 시계열만 반환합니다. 미지정 시 전체 투자자를 long-format으로
        반환합니다. 항목명은 ECOS 라벨(예: '개인(순매수)')을 따르며, 안정적
        선택을 위해 item_code(예: 'S22CB')도 허용합니다.
    start_date : str, optional
        조회 시작 시점. ``frequency`` 에 맞는 형식
        (월 ``YYYYMM`` / 연 ``YYYY``). 기본값: 주기별 기본 범위.
    end_date : str, optional
        조회 종료 시점. (형식은 ``start_date`` 와 동일)
    frequency : str
        조회 주기. ``'monthly'``(기본)/``'annual'``.
        이 통계표(``901Y055``)는 월·연 자료만 제공합니다.

    Returns
    -------
    pd.DataFrame
        - ``sub_category`` 미지정: 컬럼 ``date, category_value, value, unit``
          (투자자별 long-format, ``category_value``=투자자명). 전체 합계행은 제외.
        - ``sub_category`` 지정: 컬럼 ``date, value, unit`` (단일 시계열)

    Raises
    ------
    ValueError
        action/metric/frequency가 허용 값이 아니거나, 지정한 ``sub_category`` 가
        존재하지 않는 경우 (사용 가능 항목을 함께 안내).

    Notes
    -----
    - 외국인 순매수: 외국인 투자자의 매수 - 매도
    - 기관 순매수: 기관 투자자의 매수 - 매도
    - 개인 순매수: 개인 투자자의 매수 - 매도
    - ``category_value`` 는 ECOS 원본 라벨이라 각주 표식이 붙을 수 있습니다
      (예: ``'외국인(순매수) 3)'``). 정확한 이름 매칭이 까다로우므로 단일 투자자
      선택은 item_code(예: ``'S22CC'``)를 권장합니다.

    외국인과 기관의 순매수/순매도는 주가 방향성의 중요한 신호로 활용됩니다.

    Examples
    --------
    >>> import ecos
    >>> # 투자자별 순매수 거래대금 (long-format)
    >>> df = ecos.get_investor_trading()
    >>> df.head()
            date  category_value   value unit

    >>> # 외국인 순매수만
    >>> df = ecos.get_investor_trading(sub_category="S22CC")

    >>> # 투자자별 매수 거래량
    >>> df = ecos.get_investor_trading(action="매수", metric="거래량")

    >>> # 연간 투자자별 순매수
    >>> df = ecos.get_investor_trading(frequency="annual")
    """
    if action not in INVESTOR_TRADING_ACTION_PREFIX:
        raise ValueError(
            f"action은 {list(INVESTOR_TRADING_ACTION_PREFIX.keys())} 중 하나여야 합니다."
        )
    if metric not in INVESTOR_TRADING_METRIC_CODE:
        raise ValueError(
            f"metric은 {list(INVESTOR_TRADING_METRIC_CODE.keys())} 중 하나여야 합니다."
        )

    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency,
        allowed=("monthly", "annual"),
        func_name="get_investor_trading",
    )
    period = PERIOD_MONTHLY if frequency == "monthly" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "monthly":
            default_start, default_end = default_monthly(24)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    prefix = INVESTOR_TRADING_ACTION_PREFIX[action]
    metric_code = INVESTOR_TRADING_METRIC_CODE[metric]

    # item_code1 미지정 → 전량 수신. item_code2(지표)로 먼저 거른 뒤
    # 행위 prefix로 분류한다(#58 규약). prefix 정확일치 행은 전체 합계이므로 제외.
    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_INVESTOR_TRADING,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    df = parse_response(response)
    if "item_code2" in df.columns:
        df = df[df["item_code2"] == metric_code]
    if "item_code1" in df.columns:
        df = df[df["item_code1"] != prefix]  # 활성 prefix의 합계행(예: S22C) 제외

    return select_subcategory(
        df, prefix=prefix, sub_category=sub_category, context=f"action='{action}'"
    )
