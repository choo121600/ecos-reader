"""
성장 지표 모듈

GDP(국내총생산), GDP 디플레이터 등 성장 관련 지표를 조회합니다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import pandas as pd

from ..client import get_client
from ..constants import (
    ITEM_GDP,
    ITEM_GDP_DEFLATOR,
    PERIOD_ANNUAL,
    PERIOD_QUARTERLY,
    STAT_GDP_DEFLATOR,
    STAT_GDP_NOMINAL,
    STAT_GDP_REAL,
)
from ..parser import normalize_stat_result, parse_response


def _get_default_dates_quarterly(years_back: int = 5) -> tuple[str, str]:
    """기본 조회 기간을 반환합니다 (분기)."""
    end_date = datetime.now()
    start_year = end_date.year - years_back
    current_quarter = (end_date.month - 1) // 3 + 1

    start_str = f"{start_year}Q1"
    end_str = f"{end_date.year}Q{current_quarter}"

    return start_str, end_str


def _get_default_dates_annual(years_back: int = 10) -> tuple[str, str]:
    """기본 조회 기간을 반환합니다 (연간)."""
    end_date = datetime.now()
    start_year = end_date.year - years_back

    return str(start_year), str(end_date.year)


def get_gdp(
    frequency: Literal["Q", "A"] = "Q",
    basis: Literal["real", "nominal"] = "real",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    국내총생산(GDP)을 조회합니다.

    Parameters
    ----------
    frequency : str
        조회 주기
        - 'Q': 분기 (기본값)
        - 'A': 연간
    basis : str
        GDP 기준
        - 'real': 실질 GDP (기본값)
        - 'nominal': 명목 GDP
    start_date : str, optional
        조회 시작일
        - 분기: YYYYQN 형식 (예: 2020Q1)
        - 연간: YYYY 형식 (예: 2020)
    end_date : str, optional
        조회 종료일

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: GDP (조원)
        - unit: 단위

    Notes
    -----
    - 실질 GDP: 물가 변동을 제외한 실제 생산량 변화
    - 명목 GDP: 당해 연도 가격 기준 GDP

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_gdp()  # 분기별 실질 GDP
    >>> df.head()

    >>> df = ecos.get_gdp(frequency="A", basis="nominal")  # 연간 명목 GDP
    """
    # 통계코드 선택
    stat_code = STAT_GDP_REAL if basis == "real" else STAT_GDP_NOMINAL

    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "Q" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "Q":
            default_start, default_end = _get_default_dates_quarterly(5)
        else:
            default_start, default_end = _get_default_dates_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1=ITEM_GDP,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_gdp_deflator(
    frequency: Literal["Q", "A"] = "Q",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    GDP 디플레이터를 조회합니다.

    GDP 디플레이터는 명목 GDP와 실질 GDP의 비율로 계산되는
    종합 물가지수입니다.

    Parameters
    ----------
    frequency : str
        조회 주기
        - 'Q': 분기 (기본값)
        - 'A': 연간
    start_date : str, optional
        조회 시작일
    end_date : str, optional
        조회 종료일

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: GDP 디플레이터
        - unit: 단위

    Notes
    -----
    - GDP 디플레이터 = (명목 GDP / 실질 GDP) × 100
    - CPI보다 포괄적인 물가 지표
    - 국내에서 생산된 모든 재화와 서비스의 가격 변화 반영

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_gdp_deflator()
    >>> df.head()
    """
    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "Q" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "Q":
            default_start, default_end = _get_default_dates_quarterly(5)
        else:
            default_start, default_end = _get_default_dates_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_GDP_DEFLATOR,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1=ITEM_GDP_DEFLATOR,
    )

    df = parse_response(response)
    return normalize_stat_result(df)
