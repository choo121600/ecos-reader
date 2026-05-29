"""
물가 지표 모듈

소비자물가지수(CPI), 생산자물가지수(PPI) 등 물가 관련 지표를 조회합니다.
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

from ..client import get_client
from ..constants import (
    CPI_CATEGORY_CODES,
    PERIOD_MONTHLY,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_monthly
from ._deprecations import warn_partial_coverage as _warn_partial_coverage
from ._registry import get_indicator


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
    # 선언적 레지스트리(#16)에 위임하는 얇은 alias.
    return get_indicator("cpi", start_date=start_date, end_date=end_date)


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
    # 선언적 레지스트리(#16)에 위임하는 얇은 alias.
    return get_indicator("core_cpi", start_date=start_date, end_date=end_date)


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
    # 선언적 레지스트리(#16)에 위임하는 얇은 alias.
    return get_indicator("ppi", start_date=start_date, end_date=end_date)


def get_cpi_monthly(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    CPI 월별 원지수를 조회합니다.

    전년동월비가 아닌 원지수(index)를 제공합니다.

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
        - value: CPI 원지수
        - unit: 단위

    Warnings
    --------
    DeprecationWarning
        현재 단일 항목(`item_code1="0"`, 전체(미확인))만 반환하며 함수명이 시사하는
        전체 CPI 시리즈를 다루지 않습니다. v0.3.0에서 시그니처가 변경될 예정이며,
        현재 동작에 의존한다면 `EcosClient.get_statistic_search`로 직접 item_code1을
        전달하는 방식으로 마이그레이션하세요. (이슈 #8)

    Notes
    -----
    - 원지수는 기준년도(2020=100)를 100으로 한 지수값
    - 전년동월비는 get_cpi() 함수 사용

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_cpi_monthly()
    >>> df.head()
            date   value  unit
    0 2023-01-01  105.20  지수
    """
    # 부분 커버리지 경고는 이 함수의 고유 동작이므로 alias 위임 전에 유지.
    _warn_partial_coverage("get_cpi_monthly", "0", "총지수")

    # 선언적 레지스트리(#16)에 위임하는 얇은 alias.
    return get_indicator("cpi_monthly", start_date=start_date, end_date=end_date)


def get_cpi_by_category(
    category: Literal[
        "전체",
        "상품",
        "서비스",
        "식품_에너지제외",
        "농산물_석유제외",
        "식료품_비주류음료",
        "주거_수도_전기",
        "교통",
    ] = "전체",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    CPI 세부 항목별 지수를 조회합니다.

    상품, 서비스, 식품 등 세부 항목별 물가지수를 제공합니다.

    Parameters
    ----------
    category : str
        CPI 세부 항목
        - '전체': 소비자물가지수 (기본값)
        - '상품': 상품 물가지수
        - '서비스': 서비스 물가지수
        - '식품_에너지제외': 식품 및 에너지 제외 지수
        - '농산물_석유제외': 농산물 및 석유류 제외 지수
        - '식료품_비주류음료': 식료품 및 비주류음료
        - '주거_수도_전기': 주거, 수도, 전기 및 연료
        - '교통': 교통
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 2년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: CPI 카테고리별 지수
        - unit: 단위

    Notes
    -----
    - 각 카테고리별로 물가 변동을 세부적으로 파악 가능
    - '식품_에너지제외'는 근원 물가와 유사한 개념
    - 상품과 서비스 물가의 괴리는 수요 구조 변화를 반영
    - 특수분류(전체/상품/서비스/제외 시리즈)는 stat_code 901Y010,
      COICOP 1단계(식료품/주거/교통 등)는 stat_code 901Y009를 사용

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_cpi_by_category(category="식품_에너지제외")
    >>> df.head()
            date   value  unit
    0 2023-01-01  103.50  지수

    >>> df = ecos.get_cpi_by_category(category="교통")
    >>> df.head()
    """
    if category not in CPI_CATEGORY_CODES:
        raise ValueError(f"category는 {list(CPI_CATEGORY_CODES.keys())} 중 하나여야 합니다.")

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    stat_code, item_code = CPI_CATEGORY_CODES[category]

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
