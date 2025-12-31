"""
채권시장 지표 모듈

국채 및 회사채 수익률 등 채권시장 관련 지표를 조회합니다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import pandas as pd

from ..client import get_client
from ..constants import (
    PERIOD_MONTHLY,
    STAT_BOND_MARKET,
    STAT_BOND_YIELD_TYPE,
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


def get_bond_yield(
    bond_type: Literal["종류별", "시장별"] = "종류별",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    채권 수익률을 조회합니다.

    국채, 회사채 등 채권 종류별 또는 시장별 거래 정보를 제공합니다.

    Parameters
    ----------
    bond_type : str
        채권 분류 기준
        - '종류별': 국채, 회사채 등 채권 종류별 (기본값)
        - '시장별': 채권 시장별 거래
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 2년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 채권 거래액 또는 수익률
        - unit: 단위

    Notes
    -----
    - 국채: 정부가 발행하는 채권, 가장 안전한 자산
    - 회사채: 기업이 발행하는 채권, 신용등급에 따라 수익률 차이
    - 채권 수익률 상승 = 채권 가격 하락

    채권 수익률은 금리 정책과 밀접한 관련이 있으며,
    경기 전망과 인플레이션 기대를 반영합니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_bond_yield()  # 종류별 채권 거래
    >>> df.head()
            date  value    unit
    0 2024-01-01   45.2  조원
    1 2024-02-01   38.7  조원

    >>> df = ecos.get_bond_yield(bond_type="시장별")  # 시장별 채권 거래
    """
    if bond_type not in ["종류별", "시장별"]:
        raise ValueError("bond_type은 '종류별' 또는 '시장별' 중 하나여야 합니다.")

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 채권 분류에 따른 stat_code 및 item_code 선택
    if bond_type == "종류별":
        stat_code = STAT_BOND_YIELD_TYPE
        item_code = "1"  # 합계
    else:  # 시장별
        stat_code = STAT_BOND_MARKET
        item_code = "AMT"  # 거래대금

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
        item_code1=item_code,
    )

    df = parse_response(response)
    return normalize_stat_result(df)
