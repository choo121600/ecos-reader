"""
통화 지표 모듈

통화량(M1, M2, Lf), 은행 대출 등 통화 관련 지표를 조회합니다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import pandas as pd

from ..client import get_client
from ..constants import (
    BANK_LENDING_ITEMS,
    MONEY_SUPPLY_ITEMS,
    MONEY_SUPPLY_STAT_CODES,
    PERIOD_MONTHLY,
    STAT_BANK_LENDING,
    STAT_HOUSEHOLD_LENDING,
)
from ..parser import normalize_stat_result, parse_response


def _get_default_dates(months_back: int = 36) -> tuple[str, str]:
    """기본 조회 기간을 반환합니다 (기본 3년)."""
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


def get_money_supply(
    indicator: Literal["M1", "M2", "Lf"] = "M2",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    통화량을 조회합니다.

    Parameters
    ----------
    indicator : str
        통화 지표
        - 'M1': 협의통화 (현금 + 요구불예금)
        - 'M2': 광의통화 (기본값, 가장 많이 사용)
        - 'Lf': 금융기관유동성
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 3년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 통화량 (조원)
        - unit: 단위

    Notes
    -----
    - M1 (협의통화): 즉시 사용 가능한 화폐
    - M2 (광의통화): M1 + 저축성 예금, 시장형 금융상품 등
    - Lf (금융기관유동성): M2 + 생명보험 계약 준비금 등

    통화량 증가율은 인플레이션 및 자산 가격에 영향을 미칩니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_money_supply()  # M2 기본
    >>> df.head()

    >>> df = ecos.get_money_supply(indicator="M1")
    """
    if indicator not in MONEY_SUPPLY_ITEMS:
        raise ValueError(f"indicator는 {list(MONEY_SUPPLY_ITEMS.keys())} 중 하나여야 합니다.")

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates(36)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 각 지표마다 다른 stat code 사용
    stat_code = MONEY_SUPPLY_STAT_CODES[indicator]
    item_code = MONEY_SUPPLY_ITEMS[indicator]

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


def get_bank_lending(
    sector: Literal["household", "all"] = "all",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    은행 대출금을 조회합니다.

    Parameters
    ----------
    sector : str
        대출 부문
        - 'all': 예금은행 전체 대출금 (기본값)
        - 'household': 예금취급기관 가계대출
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 3년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 대출금 (조원 또는 십억원)
        - unit: 단위

    Notes
    -----
    - 가계대출 증가: 소비 증가 및 부동산 가격 상승 요인
    - 기업대출은 별도 통계표 (산업별대출금 등) 사용 필요

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_bank_lending()
    >>> df.head()

    >>> df = ecos.get_bank_lending(sector="household")  # 가계대출
    """
    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates(36)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # sector에 따라 다른 stat code와 item code 사용
    if sector == "all":
        stat_code = STAT_BANK_LENDING
        item_code = BANK_LENDING_ITEMS["all"]
    elif sector == "household":
        stat_code = STAT_HOUSEHOLD_LENDING
        item_code = "1110000"  # 예금취급기관
    else:
        raise ValueError("sector는 'all' 또는 'household' 중 하나여야 합니다.")

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
