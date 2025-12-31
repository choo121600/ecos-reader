"""
주식시장 지표 모듈

주가지수, 투자자별 거래 등 주식시장 관련 지표를 조회합니다.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

import pandas as pd

from ..client import get_client
from ..constants import (
    PERIOD_DAILY,
    PERIOD_MONTHLY,
    STAT_INVESTOR_TRADING,
    STAT_STOCK_DAILY,
    STAT_STOCK_MONTHLY,
)
from ..parser import normalize_stat_result, parse_response


def _get_default_dates_daily(days_back: int = 365) -> tuple[str, str]:
    """기본 조회 기간을 반환합니다 (일별)."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    return start_str, end_str


def _get_default_dates_monthly(months_back: int = 24) -> tuple[str, str]:
    """기본 조회 기간을 반환합니다 (월별)."""
    end_date = datetime.now()

    # 총 개월 수 계산
    total_months = end_date.year * 12 + end_date.month
    start_total_months = total_months - months_back

    # 연도와 월 계산
    start_year = (start_total_months - 1) // 12
    start_month = (start_total_months - 1) % 12 + 1

    start_str = f"{start_year}{start_month:02d}"
    end_str = f"{end_date.year}{end_date.month:02d}"

    return start_str, end_str


def get_stock_index(
    frequency: Literal["daily", "monthly"] = "daily",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    주가지수를 조회합니다.

    KOSPI(종합주가지수)를 일별 또는 월별로 조회할 수 있습니다.

    Parameters
    ----------
    frequency : str
        조회 주기
        - 'daily': 일별 (기본값)
        - 'monthly': 월별
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
        - value: 주가지수
        - unit: 단위 (포인트)

    Notes
    -----
    - KOSPI(Korea Composite Stock Price Index)는 한국거래소 유가증권시장의 대표 지수
    - 1980년 1월 4일 기준시점 100포인트
    - 시가총액 가중 방식으로 계산

    주가지수는 경기 선행지표로 활용되며, 투자심리와 경제 전망을 반영합니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_stock_index()  # 일별 KOSPI
    >>> df.head()
            date    value     unit
    0 2024-01-02  2655.28  포인트
    1 2024-01-03  2627.94  포인트

    >>> df = ecos.get_stock_index(frequency="monthly")  # 월별 KOSPI
    """
    if frequency not in ["daily", "monthly"]:
        raise ValueError("frequency는 'daily' 또는 'monthly' 중 하나여야 합니다.")

    # 주기별 stat_code 및 period 선택
    if frequency == "daily":
        stat_code = STAT_STOCK_DAILY
        period = PERIOD_DAILY
        item_code = "0001000"  # KOSPI지수 (일별)
        # 기본 날짜 설정 (일별)
        if start_date is None or end_date is None:
            default_start, default_end = _get_default_dates_daily(365)
            start_date = start_date or default_start
            end_date = end_date or default_end
    else:  # monthly
        stat_code = STAT_STOCK_MONTHLY
        period = PERIOD_MONTHLY
        item_code = "1010000"  # KOSPI 회사수 (월별)
        # 기본 날짜 설정 (월별)
        if start_date is None or end_date is None:
            default_start, default_end = _get_default_dates_monthly(24)
            start_date = start_date or default_start
            end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1=item_code,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_investor_trading(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    투자자별 주식거래를 조회합니다.

    개인, 외국인, 기관 투자자별 순매수/순매도 금액을 제공합니다.

    Parameters
    ----------
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 2년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 거래금액
        - unit: 단위

    Notes
    -----
    - 외국인 순매수: 외국인 투자자의 매수 - 매도
    - 기관 순매수: 기관 투자자의 매수 - 매도
    - 개인 순매수: 개인 투자자의 매수 - 매도

    외국인과 기관의 순매수/순매도는 주가 방향성의 중요한 신호로 활용됩니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_investor_trading()
    >>> df.head()
            date   value    unit
    0 2024-01-01  1250.5  십억원
    1 2024-02-01  -850.3  십억원

    >>> df = ecos.get_investor_trading(start_date="202301", end_date="202312")
    """
    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates_monthly(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_INVESTOR_TRADING,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
        item_code1="S22AF",  # 기타법인(매도)
    )

    df = parse_response(response)
    return normalize_stat_result(df)
