"""
채권시장 지표 모듈

국채 및 회사채 수익률 등 채권시장 관련 지표를 조회합니다.
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

from ..client import get_client
from ..constants import (
    PERIOD_MONTHLY,
    STAT_BOND_MARKET,
    STAT_BOND_YIELD_TYPE,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_monthly
from ._deprecations import warn_partial_coverage as _warn_partial_coverage


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

    Warnings
    --------
    EcosPartialCoverageWarning
        두 분기 모두 단일 항목만 반환합니다.
        - `bond_type="종류별"`: 채권종류별 통계(901Y015)에서 `item_code1="1"`(합계),
          `item_code2="2040000"`(거래대금)으로 고정. 다른 종목 분류(국채/회사채 등)나
          다른 measure(상장종목수/잔액/거래량)는 v0.1.6에서 직접 노출되지 않습니다.
        - `bond_type="시장별"`: 채권시장별 통계(901Y120)에서 `item_code1="AMT"`
          (거래대금)으로 고정.
        함수명이 시사하는 전체 채권 시리즈를 다루지 않습니다. v0.3.0에서 시그니처가
        변경될 예정이며, 현재 동작에 의존한다면 `EcosClient.get_statistic_search`로
        직접 item_code를 지정해 호출하세요. (이슈 #8)

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
        default_start, default_end = default_monthly(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 채권 분류에 따른 stat_code 및 item_code 선택
    # 종류별(901Y015)은 item_code1만 지정하면 item_code2 차원(상장종목수/잔액/거래량/거래대금)이
    # 모두 섞여 반환되어 value 컬럼이 의미 불명이 된다. v0.1.6에서는 거래대금 한 measure로
    # 고정해 일관된 시계열을 반환.
    item_code2 = ""
    if bond_type == "종류별":
        stat_code = STAT_BOND_YIELD_TYPE
        item_code = "1"  # 합계
        item_code2 = "2040000"  # 거래대금 measure만 선택
        _warn_partial_coverage("get_bond_yield(종류별)", "1/2040000", "합계 거래대금")
    else:  # 시장별
        stat_code = STAT_BOND_MARKET
        item_code = "AMT"  # 거래대금
        item_code2 = "020101"  # 시장 합계만 (국채전문/일반/소액/신고매매 분리는 제외)
        _warn_partial_coverage("get_bond_yield(시장별)", "AMT/020101", "거래대금 합계")

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
        item_code1=item_code,
        item_code2=item_code2,
    )

    df = parse_response(response)
    return normalize_stat_result(df)
