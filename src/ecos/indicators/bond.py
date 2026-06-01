"""
채권시장 지표 모듈

국채 및 회사채 수익률 등 채권시장 관련 지표를 조회합니다.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Literal

from ..client import get_client
from ..constants import (
    BOND_MARKET_MEASURE_CODE,
    BOND_YIELD_TYPE_MEASURE_CODE,
    PERIOD_MONTHLY,
    STAT_BOND_MARKET,
    STAT_BOND_YIELD_TYPE,
)
from ..parser import parse_response
from ._dates import default_monthly
from ._subcategory import select_subcategory

if TYPE_CHECKING:
    import pandas as pd


def get_bond_market(
    bond_type: Literal["종류별", "시장별"] = "종류별",
    measure: Literal["거래대금", "거래량", "상장잔액", "상장종목수"] = "거래대금",
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    채권시장 거래통계를 종류별 또는 시장별로 조회합니다.

    국채/회사채 등 채권 종류별, 또는 국채전문/일반채권 등 시장별 거래대금·거래량·
    상장잔액·상장종목수를 제공합니다. partial-coverage 재설계 규약(#56)을 따릅니다 —
    ``sub_category`` 미지정 시 전체 분류를 long-format으로, 지정 시 해당 분류 단일
    시계열만 반환합니다.

    .. note::
       이 함수는 **채권 수익률(%)이 아니라 채권시장 거래통계**를 반환합니다.
       채권/국고채 수익률(연%)은 :func:`get_treasury_yield` 를 사용하세요.

    Parameters
    ----------
    bond_type : str
        채권 분류 기준
        - '종류별': 합계/국채/지방채/특수채/회사채/외국채 (기본값, 901Y015)
        - '시장별': 합계/국채전문/일반채권/소액채권/신고매매 (901Y120)
    measure : str
        측정 지표 (한 차원을 이 값으로 고정한 뒤 분류축을 분류합니다)
        - '거래대금' (기본값), '거래량'
        - '상장잔액', '상장종목수' (``bond_type='종류별'`` 에서만 지원)
    sub_category : str, optional
        세부 분류(분류명 또는 item_code). 지정 시 해당 분류 단일 시계열만
        반환합니다. 미지정 시 전체 분류를 long-format으로 반환합니다.
        예) 종류별: '국채' 또는 '4' / 시장별: '국채전문 유통시장' 또는 '0202'
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 2년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        - ``sub_category`` 미지정: 컬럼 ``date, category_value, value, unit``
          (각 분류가 행으로 포함된 long-format, ``category_value``=분류명)
        - ``sub_category`` 지정: 컬럼 ``date, value, unit`` (단일 시계열)

    Raises
    ------
    ValueError
        bond_type/measure가 허용 값이 아니거나, 지정한 ``sub_category`` 가
        존재하지 않는 경우 (사용 가능 항목을 함께 안내).

    Notes
    -----
    - 국채: 정부가 발행하는 채권, 가장 안전한 자산
    - 회사채: 기업이 발행하는 채권, 신용등급에 따라 수익률 차이
    - 두 통계표 모두 분류축에 '합계' 행이 포함되므로 long-format을 단순 합산하면
      중복 집계됩니다. 특정 시계열은 ``sub_category`` 로 선택하세요.

    채권 거래 동향은 금리 정책·경기 전망·인플레이션 기대를 반영합니다.

    Examples
    --------
    >>> import ecos
    >>> # 종류별 거래대금 전체 (long-format)
    >>> df = ecos.get_bond_market()
    >>> df.head()
            date category_value  value unit

    >>> # 국채만
    >>> df = ecos.get_bond_market(sub_category="국채")

    >>> # 시장별 거래량
    >>> df = ecos.get_bond_market(bond_type="시장별", measure="거래량")
    """
    if bond_type not in ("종류별", "시장별"):
        raise ValueError("bond_type은 '종류별' 또는 '시장별' 중 하나여야 합니다.")

    # 입력 검증은 네트워크 호출 전에 수행한다 (잘못된 measure는 즉시 ValueError).
    # 두 통계표는 measure가 놓인 축이 다르다:
    #   종류별(901Y015): measure=item_code2, 분류축=item_code1(채권종류)
    #   시장별(901Y120): measure=item_code1, 분류축=item_code2(시장)
    if bond_type == "종류별":
        stat_code = STAT_BOND_YIELD_TYPE
        measure_map = BOND_YIELD_TYPE_MEASURE_CODE
    else:
        stat_code = STAT_BOND_MARKET
        measure_map = BOND_MARKET_MEASURE_CODE
    if measure not in measure_map:
        raise ValueError(f"{bond_type} measure는 {list(measure_map.keys())} 중 하나여야 합니다.")
    measure_code = measure_map[measure]

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
    )
    df = parse_response(response)

    # measure로 한 차원을 고정한 뒤 분류축(category_value)을 select_subcategory로 분류한다.
    if bond_type == "종류별":
        if "item_code2" in df.columns:
            df = df[df["item_code2"] == measure_code]
    else:  # 시장별: measure로 item_code1을 고정한 뒤 시장 축(item_code2)을 item_code1로 승격.
        if "item_code1" in df.columns:
            df = df[df["item_code1"] == measure_code]
        df = df.drop(columns=["item_code1", "item_name1"], errors="ignore").rename(
            columns={"item_code2": "item_code1", "item_name2": "item_name1"}
        )

    return select_subcategory(
        df, prefix="", sub_category=sub_category, context=f"bond_type='{bond_type}'"
    )


def get_bond_yield(
    bond_type: Literal["종류별", "시장별"] = "종류별",
    measure: Literal["거래대금", "거래량", "상장잔액", "상장종목수"] = "거래대금",
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """``get_bond_market`` 의 deprecated alias (#140).

    이 함수는 이름과 달리 수익률(%)이 아니라 채권시장 거래통계를 반환했습니다.
    이름을 :func:`get_bond_market` 으로 정정했으며, 본 alias 는 다음 마이너
    릴리스에서 제거됩니다. 채권 수익률은 :func:`get_treasury_yield` 를 사용하세요.
    """
    warnings.warn(
        "get_bond_yield()는 get_bond_market()으로 이름이 변경되었습니다 "
        "(수익률이 아닌 채권시장 거래통계 반환). get_bond_market()을 사용하세요. "
        "채권 수익률(%)은 get_treasury_yield()를 사용하세요. "
        "이 alias는 다음 마이너 릴리스에서 제거됩니다.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_bond_market(
        bond_type=bond_type,
        measure=measure,
        sub_category=sub_category,
        start_date=start_date,
        end_date=end_date,
    )
