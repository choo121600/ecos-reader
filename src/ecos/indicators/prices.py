"""
물가 지표 모듈

소비자물가지수(CPI), 생산자물가지수(PPI) 등 물가 관련 지표를 조회합니다.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from ..client import get_client
from ..constants import (
    ITEM_CORE_CPI,
    ITEM_CPI_TOTAL,
    ITEM_PPI_TOTAL,
    PERIOD_MONTHLY,
    STAT_CORE_CPI,
    STAT_CPI,
    STAT_PPI,
)
from ..parser import normalize_stat_result, parse_response


def _get_default_dates(months_back: int = 24) -> tuple[str, str]:
    """기본 조회 기간을 반환합니다 (기본 2년)."""
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


def get_cpi(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    소비자물가지수(CPI) 전년동월비를 조회합니다.

    한국은행 물가안정목표(2%)의 기준 지표입니다.

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
        - value: 전년동월비 (%)
        - unit: 단위

    Notes
    -----
    - CPI가 2%를 상회하면 인플레이션 압력이 있음을 의미
    - CPI가 2%를 하회하면 디플레이션 우려

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_cpi()
    >>> df.head()
            date  value unit
    0 2023-01-01   5.20    %
    """
    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_CPI,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
        item_code1=ITEM_CPI_TOTAL,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_core_cpi(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    근원 소비자물가지수(Core CPI)를 조회합니다.

    식료품과 에너지를 제외한 물가지수로, 일시적인 물가 변동 요인을
    제거한 기조적 인플레이션을 파악하는 데 활용됩니다.

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
        - value: 근원 CPI (%, 전년동월비)
        - unit: 단위

    Notes
    -----
    - 근원 CPI는 일시적 충격(유가, 농산물 가격)을 제외
    - 통화정책 결정 시 참고 지표로 중요하게 활용

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_core_cpi()
    >>> df.head()
    """
    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_CORE_CPI,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
        item_code1=ITEM_CORE_CPI,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_ppi(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    생산자물가지수(PPI) 전년동월비를 조회합니다.

    생산자물가는 소비자물가의 선행 지표로 활용됩니다.

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
        - value: 전년동월비 (%)
        - unit: 단위

    Notes
    -----
    - PPI 상승 → CPI 상승으로 이어지는 경향
    - 기업의 원가 부담을 나타내는 지표

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_ppi()
    >>> df.head()
    """
    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_PPI,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
        item_code1=ITEM_PPI_TOTAL,
    )

    df = parse_response(response)
    return normalize_stat_result(df)
