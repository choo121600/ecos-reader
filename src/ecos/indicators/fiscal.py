"""
재정 지표 모듈

통합재정수지 등 재정 관련 지표를 조회합니다.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from ..client import get_client
from ..constants import (
    ITEM_FISCAL_BALANCE,
    PERIOD_MONTHLY,
    STAT_FISCAL_BALANCE,
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


def get_fiscal_balance(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    통합재정수지를 조회합니다.

    통합재정수지는 중앙정부와 지방정부를 합한 일반정부의 재정수지로,
    정부의 재정건전성을 나타내는 핵심 지표입니다.

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
        - value: 통합재정수지 (조원)
        - unit: 단위

    Notes
    -----
    - 통합재정수지 = 총수입 - 총지출
    - 흑자(+): 재정 여력 있음
    - 적자(-): 재정 건전성 악화

    통합재정수지는 국가채무 증감과 직접적인 관련이 있으며,
    지속적인 적자는 국가 신용등급에 영향을 미칠 수 있습니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_fiscal_balance()
    >>> df.head()
            date  value unit
    0 2023-01-01   -5.2  조원
    1 2023-02-01   -3.8  조원

    >>> df = ecos.get_fiscal_balance(start_date="202301", end_date="202312")
    """
    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_FISCAL_BALANCE,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
        item_code1=ITEM_FISCAL_BALANCE,
    )

    df = parse_response(response)
    return normalize_stat_result(df)
