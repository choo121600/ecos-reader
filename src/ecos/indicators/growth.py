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
from ._frequency import normalize_frequency
from ._subcategory import select_subcategory

if TYPE_CHECKING:
    import pandas as pd


def get_gdp(
    frequency: Literal["quarterly", "annual", "Q", "A"] = "quarterly",
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
        - 'quarterly': 분기 (기본값)
        - 'annual': 연간

        레거시 'Q'/'A'도 당분간 허용되나 EcosDeprecationWarning과 함께
        deprecated이며 v0.4.0에서 제거됩니다.
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

    >>> df = ecos.get_gdp(frequency="annual", basis="nominal")  # 연간 명목 GDP
    """
    frequency = normalize_frequency(frequency, allowed=("quarterly", "annual"), func_name="get_gdp")  # type: ignore[assignment]

    # 통계코드 선택
    stat_code = STAT_GDP_REAL if basis == "real" else STAT_GDP_NOMINAL

    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "quarterly" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "quarterly":
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
    frequency: Literal["quarterly", "annual", "Q", "A"] = "quarterly",
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
        - 'quarterly': 분기 (기본값)
        - 'annual': 연간

        레거시 'Q'/'A'도 당분간 허용되나 EcosDeprecationWarning과 함께
        deprecated이며 v0.4.0에서 제거됩니다.
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
    frequency = normalize_frequency(
        frequency, allowed=("quarterly", "annual"), func_name="get_gdp_deflator"
    )  # type: ignore[assignment]

    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "quarterly" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "quarterly":
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
    frequency: Literal["quarterly", "annual", "Q", "A"] = "quarterly",
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
        - 'quarterly': 분기 (기본값)
        - 'annual': 연간

        레거시 'Q'/'A'도 당분간 허용되나 EcosDeprecationWarning과 함께
        deprecated이며 v0.4.0에서 제거됩니다.
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
    frequency = normalize_frequency(
        frequency, allowed=("quarterly", "annual"), func_name="get_gdp_growth_rate"
    )  # type: ignore[assignment]

    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "quarterly" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "quarterly":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 계절조정 시리즈(200Y104)는 분기만 — 연간 조회 시 원계열(200Y106)로 fallback.
    stat_code = STAT_GDP_GROWTH_RATE if frequency == "quarterly" else STAT_GDP_GROWTH_RATE_ANNUAL

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
    frequency: Literal["quarterly", "annual", "Q", "A"] = "quarterly",
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    경제활동별(산업별) GDP를 조회합니다.

    농림어업, 광공업, 서비스업 등 경제활동별 부가가치 전체 시리즈를 제공합니다.
    partial-coverage 재설계 규약(#56)을 따릅니다 — ``sub_category`` 미지정 시
    전체 산업을 long-format으로, 지정 시 해당 산업 단일 시계열만 반환합니다.

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
        - 'quarterly': 분기 (기본값)
        - 'annual': 연간

        레거시 'Q'/'A'도 당분간 허용되나 EcosDeprecationWarning과 함께
        deprecated이며 v0.4.0에서 제거됩니다.
    sub_category : str, optional
        세부 산업(항목명 또는 item_code1). 지정 시 해당 산업 단일 시계열만
        반환합니다. 미지정 시 전체 산업을 long-format으로 반환합니다.
    start_date : str, optional
        조회 시작일
    end_date : str, optional
        조회 종료일

    Returns
    -------
    pd.DataFrame
        - ``sub_category`` 미지정: 컬럼 ``date, category_value, value, unit``
          (각 산업이 행으로 포함된 long-format, ``category_value``=산업명)
        - ``sub_category`` 지정: 컬럼 ``date, value, unit`` (단일 시계열)

    Raises
    ------
    ValueError
        지원하지 않는 basis/seasonal_adj/frequency 조합이거나, 지정한
        ``sub_category`` 가 존재하지 않는 경우 (사용 가능 항목을 함께 안내).

    Notes
    -----
    - 계절조정: 계절적 요인 제거
    - 원계열: 계절조정하지 않은 원자료

    산업별 GDP는 경제 구조와 각 산업의 기여도를 파악하는 데 활용됩니다.

    Examples
    --------
    >>> import ecos
    >>> # 전체 산업 long-format
    >>> df = ecos.get_gdp_by_industry()
    >>> df.head()
            date category_value     value   unit

    >>> # 제조업 단일 시계열
    >>> df = ecos.get_gdp_by_industry(sub_category="제조업")

    >>> df = ecos.get_gdp_by_industry(basis="nominal", seasonal_adj=False)
    """
    frequency = normalize_frequency(
        frequency, allowed=("quarterly", "annual"), func_name="get_gdp_by_industry"
    )  # type: ignore[assignment]

    # 계절조정 시리즈는 ECOS에서 분기만 제공 — 연간 조회는 데이터 없음.
    if seasonal_adj and frequency == "annual":
        raise ValueError(
            "seasonal_adj=True와 frequency='annual' 조합은 ECOS에서 제공되지 않습니다. "
            "연간 데이터가 필요하면 seasonal_adj=False(원계열)로 호출하세요."
        )

    # basis와 seasonal_adj 조합으로 stat_code 선택
    variant_key = (
        f"{'계절조정' if seasonal_adj else '원계열'}_{'실질' if basis == 'real' else '명목'}"
    )

    if variant_key not in GDP_BY_INDUSTRY_VARIANTS:
        raise ValueError(f"지원하지 않는 조합입니다: basis={basis}, seasonal_adj={seasonal_adj}")

    stat_code = GDP_BY_INDUSTRY_VARIANTS[variant_key]

    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "quarterly" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "quarterly":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 이 통계표는 분류축이 item_code1 하나뿐이라 prefix="" 로 전체 항목을 분류한다
    # (money.py의 다축 prefix 필터와 달리 단일 축이므로 필터 없이 전량 long-format화, #58 규약).
    # 주의: 통계표에 총계/소계 행이 있으면 long-format에 함께 포함된다 → 라이브 e2e 검증 필요.
    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    df = parse_response(response)
    return select_subcategory(
        df, prefix="", sub_category=sub_category, context="get_gdp_by_industry"
    )


def get_gdp_by_expenditure(
    basis: Literal["real", "nominal"] = "real",
    frequency: Literal["quarterly", "annual", "Q", "A"] = "quarterly",
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    지출항목별 GDP를 조회합니다.

    민간소비, 정부소비, 투자, 수출입 등 지출항목별 GDP 전체 시리즈를 제공합니다.
    partial-coverage 재설계 규약(#56)을 따릅니다 — ``sub_category`` 미지정 시
    전체 지출항목을 long-format으로, 지정 시 해당 항목 단일 시계열만 반환합니다.

    Parameters
    ----------
    basis : str
        GDP 기준
        - 'real': 실질 GDP (기본값)
        - 'nominal': 명목 GDP
    frequency : str
        조회 주기
        - 'quarterly': 분기 (기본값)
        - 'annual': 연간

        레거시 'Q'/'A'도 당분간 허용되나 EcosDeprecationWarning과 함께
        deprecated이며 v0.4.0에서 제거됩니다.
    sub_category : str, optional
        세부 지출항목(항목명 또는 item_code1). 지정 시 해당 항목 단일 시계열만
        반환합니다. 미지정 시 전체 지출항목을 long-format으로 반환합니다.
    start_date : str, optional
        조회 시작일
    end_date : str, optional
        조회 종료일

    Returns
    -------
    pd.DataFrame
        - ``sub_category`` 미지정: 컬럼 ``date, category_value, value, unit``
          (각 지출항목이 행으로 포함된 long-format, ``category_value``=항목명)
        - ``sub_category`` 지정: 컬럼 ``date, value, unit`` (단일 시계열)

    Raises
    ------
    ValueError
        지원하지 않는 basis 조합이거나, 지정한 ``sub_category`` 가 존재하지
        않는 경우 (사용 가능 항목을 함께 안내).

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
    >>> # 전체 지출항목 long-format
    >>> df = ecos.get_gdp_by_expenditure()
    >>> df.head()

    >>> # 민간소비 단일 시계열
    >>> df = ecos.get_gdp_by_expenditure(sub_category="민간소비지출")

    >>> df = ecos.get_gdp_by_expenditure(basis="nominal")
    """
    frequency = normalize_frequency(
        frequency, allowed=("quarterly", "annual"), func_name="get_gdp_by_expenditure"
    )  # type: ignore[assignment]

    # 계절조정 시리즈(200Y107/108)는 분기만 — 연간 조회 시 원계열(200Y109/110)로 fallback.
    season = "계절조정" if frequency == "quarterly" else "원계열"
    variant_key = f"{season}_{'실질' if basis == 'real' else '명목'}"

    if variant_key not in GDP_BY_EXPENDITURE_VARIANTS:
        raise ValueError(f"지원하지 않는 조합입니다: basis={basis}")

    stat_code = GDP_BY_EXPENDITURE_VARIANTS[variant_key]

    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "quarterly" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "quarterly":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 이 통계표는 분류축이 item_code1 하나뿐이라 prefix="" 로 전체 항목을 분류한다
    # (money.py의 다축 prefix 필터와 달리 단일 축이므로 필터 없이 전량 long-format화, #58 규약).
    # 주의: 통계표에 총계/소계 행이 있으면 long-format에 함께 포함된다 → 라이브 e2e 검증 필요.
    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    df = parse_response(response)
    return select_subcategory(
        df, prefix="", sub_category=sub_category, context="get_gdp_by_expenditure"
    )


def get_gdp_deflator_by_industry(
    frequency: Literal["quarterly", "annual", "Q", "A"] = "quarterly",
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    경제활동별(산업별) GDP 디플레이터를 조회합니다.

    산업별 물가 변화를 나타내는 GDP 디플레이터 전체 시리즈를 제공합니다.
    partial-coverage 재설계 규약(#56)을 따릅니다 — ``sub_category`` 미지정 시
    전체 산업을 long-format으로, 지정 시 해당 산업 단일 시계열만 반환합니다.

    Parameters
    ----------
    frequency : str
        조회 주기
        - 'quarterly': 분기 (기본값)
        - 'annual': 연간

        레거시 'Q'/'A'도 당분간 허용되나 EcosDeprecationWarning과 함께
        deprecated이며 v0.4.0에서 제거됩니다.
    sub_category : str, optional
        세부 산업(항목명 또는 item_code1). 지정 시 해당 산업 단일 시계열만
        반환합니다. 미지정 시 전체 산업을 long-format으로 반환합니다.
    start_date : str, optional
        조회 시작일
    end_date : str, optional
        조회 종료일

    Returns
    -------
    pd.DataFrame
        - ``sub_category`` 미지정: 컬럼 ``date, category_value, value, unit``
          (각 산업이 행으로 포함된 long-format, ``category_value``=산업명)
        - ``sub_category`` 지정: 컬럼 ``date, value, unit`` (단일 시계열)

    Raises
    ------
    ValueError
        지정한 ``sub_category`` 가 존재하지 않는 경우 (사용 가능 항목을 함께 안내).

    Notes
    -----
    - GDP 디플레이터 = (명목 GDP / 실질 GDP) × 100
    - 각 산업별로 물가 변화를 측정

    산업별 GDP 디플레이터는 산업별 물가 동향을 파악하는 데 활용됩니다.

    Examples
    --------
    >>> import ecos
    >>> # 전체 산업 long-format
    >>> df = ecos.get_gdp_deflator_by_industry()
    >>> df.head()

    >>> # 제조업 단일 시계열
    >>> df = ecos.get_gdp_deflator_by_industry(sub_category="제조업")

    >>> df = ecos.get_gdp_deflator_by_industry(frequency="annual")
    """
    frequency = normalize_frequency(
        frequency, allowed=("quarterly", "annual"), func_name="get_gdp_deflator_by_industry"
    )  # type: ignore[assignment]

    # 주기 코드
    period = PERIOD_QUARTERLY if frequency == "quarterly" else PERIOD_ANNUAL

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "quarterly":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 이 통계표는 분류축이 item_code1 하나뿐이라 prefix="" 로 전체 항목을 분류한다
    # (money.py의 다축 prefix 필터와 달리 단일 축이므로 필터 없이 전량 long-format화, #58 규약).
    # 주의: 통계표에 총계/소계 행이 있으면 long-format에 함께 포함된다 → 라이브 e2e 검증 필요.
    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_GDP_DEFLATOR_BY_INDUSTRY,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    df = parse_response(response)
    return select_subcategory(
        df, prefix="", sub_category=sub_category, context="get_gdp_deflator_by_industry"
    )
