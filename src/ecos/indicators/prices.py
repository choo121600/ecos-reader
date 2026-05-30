"""
물가 지표 모듈

소비자물가지수(CPI), 생산자물가지수(PPI) 등 물가 관련 지표를 조회합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..client import get_client
from ..constants import (
    CPI_CATEGORY_CODES,
    PERIOD_MONTHLY,
    STAT_CPI_MONTHLY,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_monthly
from ._registry import get_indicator
from ._subcategory import select_subcategory

if TYPE_CHECKING:
    import pandas as pd


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
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    CPI 월별 원지수를 품목/분류별로 조회합니다.

    전년동월비가 아닌 원지수(index)를 COICOP 품목 분류 전체로 제공합니다.
    partial-coverage 재설계 규약(#56)을 따릅니다 — ``sub_category`` 미지정 시
    전체 품목을 long-format으로, 지정 시 해당 품목 단일 시계열만 반환합니다.

    Parameters
    ----------
    sub_category : str, optional
        세부 품목/분류(항목명 또는 item_code1). 지정 시 해당 품목 단일 시계열만
        반환합니다. 미지정 시 전체 품목을 long-format으로 반환합니다.
        예) '총지수', '식료품 및 비주류음료', '쌀', 또는 item_code 'A01101'
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 2년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        - ``sub_category`` 미지정: 컬럼 ``date, category_value, value, unit``
          (각 품목이 행으로 포함된 long-format, ``category_value``=품목명)
        - ``sub_category`` 지정: 컬럼 ``date, value, unit`` (단일 시계열)

    Raises
    ------
    ValueError
        지정한 ``sub_category`` 가 존재하지 않는 경우 (사용 가능 항목을 함께 안내).

    Notes
    -----
    - 원지수는 기준년도(2020=100)를 100으로 한 지수값
    - 전년동월비는 get_cpi() 함수 사용
    - CPI 통계표(901Y009)는 계층형입니다 — long-format에는 총지수(item_code '0'),
      COICOP 대분류(A=식료품 등), 중·소분류, 개별 품목(쌀 등)이 모두 포함됩니다.
      특정 시계열이 필요하면 ``sub_category`` 로 선택하세요(축 간 단순 합산 금지).
    - 특수분류(상품/서비스/근원 등) 선택은 ``get_cpi_by_category`` 를 사용하세요.

    Examples
    --------
    >>> import ecos
    >>> # 전체 품목 long-format
    >>> df = ecos.get_cpi_monthly()
    >>> df.head()
            date category_value   value unit

    >>> # 총지수만
    >>> df = ecos.get_cpi_monthly(sub_category="총지수")

    >>> # 쌀 가격지수 (item_code도 허용)
    >>> df = ecos.get_cpi_monthly(sub_category="쌀")
    """
    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(24)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # item_code1 미지정 → 전체 품목 수신 후 select_subcategory로 분류(#58 규약).
    # 901Y009는 단일 분류축(item_code1)이라 prefix="" 로 전량 분류한다.
    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_CPI_MONTHLY,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
    )

    df = parse_response(response)
    return select_subcategory(df, prefix="", sub_category=sub_category, context="get_cpi_monthly")


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
