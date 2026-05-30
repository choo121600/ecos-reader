"""
성장 지표 모듈

GDP(국내총생산), GDP 디플레이터 등 성장 관련 지표를 조회합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..client import get_client
from ..constants import (
    GDP_BY_EXPENDITURE_VARIANTS,
    GDP_BY_INDUSTRY_VARIANTS,
    ITEM_GDP,
    ITEM_GDP_DEFLATOR,
    ITEM_GDP_GROWTH_RATE,
    PERIOD_ANNUAL,
    PERIOD_QUARTERLY,
    STAT_GDP_DEFLATOR,
    STAT_GDP_DEFLATOR_BY_INDUSTRY,
    STAT_GDP_GROWTH_RATE,
    STAT_GDP_GROWTH_RATE_ANNUAL,
    STAT_GDP_NOMINAL,
    STAT_GDP_REAL,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_annual, default_quarterly
from ._deprecations import warn_partial_coverage as _warn_partial_coverage

if TYPE_CHECKING:
    import pandas as pd


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
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
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
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
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


def get_gdp_growth_rate(
    frequency: Literal["Q", "A"] = "Q",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    실질 GDP 성장률을 조회합니다.

    전기비 또는 전년동기비 실질 GDP 성장률을 제공합니다.

    Parameters
    ----------
    frequency : str
        조회 주기
        - 'Q': 분기 (기본값)
        - 'A': 연간
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
        - value: GDP 성장률 (%)
        - unit: 단위

    Notes
    -----
    - 전기비: 직전 분기/년 대비 성장률
    - 전년동기비: 전년 같은 분기/년 대비 성장률

    GDP 성장률은 경제 성장의 속도를 나타내는 가장 핵심적인 지표입니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_gdp_growth_rate()
    >>> df.head()
            date  value unit
    0 2024-01-01   2.3    %
    """
    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "Q" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "Q":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 계절조정 시리즈(200Y104)는 분기만 — 연간 조회 시 원계열(200Y106)로 fallback.
    stat_code = STAT_GDP_GROWTH_RATE if frequency == "Q" else STAT_GDP_GROWTH_RATE_ANNUAL

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1=ITEM_GDP_GROWTH_RATE,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_gdp_by_industry(
    basis: Literal["real", "nominal"] = "real",
    seasonal_adj: bool = True,
    frequency: Literal["Q", "A"] = "Q",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    경제활동별(산업별) GDP를 조회합니다.

    농림어업, 광공업, 서비스업 등 경제활동별 부가가치를 제공합니다.

    Parameters
    ----------
    basis : str
        GDP 기준
        - 'real': 실질 GDP (기본값)
        - 'nominal': 명목 GDP
    seasonal_adj : bool
        계절조정 여부 (기본값: True)
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
        - value: 산업별 GDP (조원)
        - unit: 단위

    Warnings
    --------
    DeprecationWarning
        현재 단일 항목(`item_code1="1101"`, 농림어업)만 반환하며 함수명이 시사하는
        전체 산업 시리즈를 다루지 않습니다. v0.3.0에서 시그니처가 변경될 예정이며,
        현재 동작에 의존한다면 `EcosClient.get_statistic_search`로 직접 item_code1을
        전달하는 방식으로 마이그레이션하세요. (이슈 #8)

    Notes
    -----
    - 계절조정: 계절적 요인 제거
    - 원계열: 계절조정하지 않은 원자료

    산업별 GDP는 경제 구조와 각 산업의 기여도를 파악하는 데 활용됩니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_gdp_by_industry()
    >>> df.head()

    >>> df = ecos.get_gdp_by_industry(basis="nominal", seasonal_adj=False)
    """
    # 계절조정 시리즈는 ECOS에서 분기만 제공 — 연간 조회는 데이터 없음.
    if seasonal_adj and frequency == "A":
        raise ValueError(
            "seasonal_adj=True와 frequency='A' 조합은 ECOS에서 제공되지 않습니다. "
            "연간 데이터가 필요하면 seasonal_adj=False(원계열)로 호출하세요."
        )

    # basis와 seasonal_adj 조합으로 stat_code 선택
    variant_key = (
        f"{'계절조정' if seasonal_adj else '원계열'}_{'실질' if basis == 'real' else '명목'}"
    )

    if variant_key not in GDP_BY_INDUSTRY_VARIANTS:
        raise ValueError(f"지원하지 않는 조합입니다: basis={basis}, seasonal_adj={seasonal_adj}")

    _warn_partial_coverage("get_gdp_by_industry", "1101", "농림어업")

    stat_code = GDP_BY_INDUSTRY_VARIANTS[variant_key]

    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "Q" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "Q":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1="1101",  # 농림어업
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_gdp_by_expenditure(
    basis: Literal["real", "nominal"] = "real",
    frequency: Literal["Q", "A"] = "Q",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    지출항목별 GDP를 조회합니다.

    민간소비, 정부소비, 투자, 수출입 등 지출항목별 GDP를 제공합니다.

    Parameters
    ----------
    basis : str
        GDP 기준
        - 'real': 실질 GDP (기본값)
        - 'nominal': 명목 GDP
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
        - value: 지출항목별 GDP (조원)
        - unit: 단위

    Warnings
    --------
    DeprecationWarning
        현재 단일 항목(`item_code1="10601"`, 지출항목별 전체(미확인))만 반환하며 함수명이
        시사하는 전체 지출 시리즈를 다루지 않습니다. v0.3.0에서 시그니처가 변경될 예정이며,
        현재 동작에 의존한다면 `EcosClient.get_statistic_search`로 직접 item_code1을
        전달하는 방식으로 마이그레이션하세요. (이슈 #8)

    Notes
    -----
    GDP 지출항목:
    - 민간소비: 가계의 소비지출
    - 정부소비: 정부의 소비지출
    - 총고정자본형성: 기업 및 정부의 투자
    - 수출 - 수입: 순수출

    지출항목별 GDP는 경제 성장의 원천을 파악하는 데 활용됩니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_gdp_by_expenditure()
    >>> df.head()

    >>> df = ecos.get_gdp_by_expenditure(basis="nominal")
    """
    # 계절조정 시리즈(200Y107/108)는 분기만 — 연간 조회 시 원계열(200Y109/110)로 fallback.
    season = "계절조정" if frequency == "Q" else "원계열"
    variant_key = f"{season}_{'실질' if basis == 'real' else '명목'}"

    if variant_key not in GDP_BY_EXPENDITURE_VARIANTS:
        raise ValueError(f"지원하지 않는 조합입니다: basis={basis}")

    _warn_partial_coverage("get_gdp_by_expenditure", "10601", "지출항목별 전체(미확인)")

    stat_code = GDP_BY_EXPENDITURE_VARIANTS[variant_key]

    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "Q" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "Q":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1="10601",  # 지출항목별 전체 (StatisticItemList로 확인 필요)
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_gdp_deflator_by_industry(
    frequency: Literal["Q", "A"] = "Q",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    경제활동별(산업별) GDP 디플레이터를 조회합니다.

    산업별 물가 변화를 나타내는 GDP 디플레이터를 제공합니다.

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

    Warnings
    --------
    DeprecationWarning
        현재 단일 항목(`item_code1="1101"`, 농림어업)만 반환하며 함수명이 시사하는
        전체 산업 시리즈를 다루지 않습니다. v0.3.0에서 시그니처가 변경될 예정이며,
        현재 동작에 의존한다면 `EcosClient.get_statistic_search`로 직접 item_code1을
        전달하는 방식으로 마이그레이션하세요. (이슈 #8)

    Notes
    -----
    - GDP 디플레이터 = (명목 GDP / 실질 GDP) × 100
    - 각 산업별로 물가 변화를 측정

    산업별 GDP 디플레이터는 산업별 물가 동향을 파악하는 데 활용됩니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_gdp_deflator_by_industry()
    >>> df.head()

    >>> df = ecos.get_gdp_deflator_by_industry(frequency="A")
    """
    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "Q" else PERIOD_ANNUAL

    _warn_partial_coverage("get_gdp_deflator_by_industry", "1101", "농림어업")

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "Q":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_GDP_DEFLATOR_BY_INDUSTRY,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1="1101",  # 농림어업
    )

    df = parse_response(response)
    return normalize_stat_result(df)
