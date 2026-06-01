"""
통화 지표 모듈

통화량(M1, M2, Lf), 은행 대출 등 통화 관련 지표를 조회합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..client import get_client
from ..constants import (
    BANK_LENDING_ITEMS,
    BORROWER_LOAN_CATEGORY_PREFIX,
    BORROWER_LOAN_STAT_CODES,
    M1_ITEMS,
    M1_VARIANTS,
    M2_HOLDER_VARIANTS,
    M2_ITEMS,
    M2_VARIANTS,
    MONEY_SUPPLY_ITEMS,
    MONEY_SUPPLY_STAT_CODES,
    PERIOD_ANNUAL,
    PERIOD_MONTHLY,
    PERIOD_QUARTERLY,
    STAT_BANK_LENDING,
    STAT_HOUSEHOLD_CREDIT_PURPOSE,
    STAT_HOUSEHOLD_CREDIT_SECTOR,
    STAT_HOUSEHOLD_LENDING,
    STAT_HOUSEHOLD_LENDING_PURPOSE,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_annual, default_monthly, default_quarterly
from ._frequency import normalize_frequency
from ._subcategory import select_subcategory

if TYPE_CHECKING:
    import pandas as pd


def get_money_supply(
    indicator: Literal["M1", "M2", "Lf"] = "M2",
    start_date: str | None = None,
    end_date: str | None = None,
    frequency: Literal["monthly", "quarterly", "annual"] = "monthly",
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
        조회 시작 시점. ``frequency`` 에 맞는 형식
        (월 ``YYYYMM`` / 분기 ``YYYYQn`` / 연 ``YYYY``). 기본값: 주기별 기본 범위.
    end_date : str, optional
        조회 종료 시점. (형식은 ``start_date`` 와 동일)
    frequency : str
        조회 주기. ``'monthly'``(기본)/``'quarterly'``/``'annual'``.

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 통화량 (십억원)
        - unit: 단위

    Raises
    ------
    ValueError
        지원하지 않는 ``indicator``/``frequency`` 일 때.

    Notes
    -----
    - M1 (협의통화): 즉시 사용 가능한 화폐
    - M2 (광의통화): M1 + 저축성 예금, 시장형 금융상품 등
    - Lf (금융기관유동성): M2 + 생명보험 계약 준비금 등

    통화량 증가율은 인플레이션 및 자산 가격에 영향을 미칩니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_money_supply()  # M2 기본(월)
    >>> df.head()

    >>> df = ecos.get_money_supply(indicator="M1")
    >>> df = ecos.get_money_supply(frequency="annual")
    """
    if indicator not in MONEY_SUPPLY_ITEMS:
        raise ValueError(f"indicator는 {list(MONEY_SUPPLY_ITEMS.keys())} 중 하나여야 합니다.")

    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency,
        allowed=("monthly", "quarterly", "annual"),
        func_name="get_money_supply",
    )
    period = {
        "monthly": PERIOD_MONTHLY,
        "quarterly": PERIOD_QUARTERLY,
        "annual": PERIOD_ANNUAL,
    }[frequency]

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "monthly":
            default_start, default_end = default_monthly(36)
        elif frequency == "quarterly":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 각 지표마다 다른 stat code 사용
    stat_code = MONEY_SUPPLY_STAT_CODES[indicator]
    item_code = MONEY_SUPPLY_ITEMS[indicator]

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
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
    frequency: Literal["monthly", "quarterly", "annual"] = "monthly",
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
        조회 시작 시점. ``frequency`` 에 맞는 형식
        (월 ``YYYYMM`` / 분기 ``YYYYQn`` / 연 ``YYYY``). 기본값: 주기별 기본 범위.
    end_date : str, optional
        조회 종료 시점. (형식은 ``start_date`` 와 동일)
    frequency : str
        조회 주기. ``'monthly'``(기본)/``'quarterly'``/``'annual'``.

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 대출금 (십억원)
        - unit: 단위

    Raises
    ------
    ValueError
        지원하지 않는 ``sector``/``frequency`` 일 때.

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
    >>> df = ecos.get_bank_lending(frequency="annual")
    """
    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency,
        allowed=("monthly", "quarterly", "annual"),
        func_name="get_bank_lending",
    )
    period = {
        "monthly": PERIOD_MONTHLY,
        "quarterly": PERIOD_QUARTERLY,
        "annual": PERIOD_ANNUAL,
    }[frequency]

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "monthly":
            default_start, default_end = default_monthly(36)
        elif frequency == "quarterly":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
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
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1=item_code,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_m1_variants(
    variant: Literal["평잔_계절조정", "평잔_원계열", "말잔_계절조정"] = "말잔_계절조정",
    start_date: str | None = None,
    end_date: str | None = None,
    frequency: Literal["monthly", "quarterly", "annual"] = "monthly",
) -> pd.DataFrame:
    """
    M1 세부 데이터를 조회합니다.

    평잔/말잔, 계절조정/원계열 등 M1 통화량의 다양한 변형을 제공합니다.

    Parameters
    ----------
    variant : str
        M1 변형 종류
        - '평잔_계절조정': 평잔 계절조정 계열
        - '평잔_원계열': 평잔 원계열
        - '말잔_계절조정': 말잔 계절조정 계열 (기본값)
    start_date : str, optional
        조회 시작 시점. ``frequency`` 에 맞는 형식
        (월 ``YYYYMM`` / 분기 ``YYYYQn`` / 연 ``YYYY``). 기본값: 주기별 기본 범위.
    end_date : str, optional
        조회 종료 시점. (형식은 ``start_date`` 와 동일)
    frequency : str
        조회 주기. ``'monthly'``(기본)/``'quarterly'``/``'annual'``.

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: M1 (십억원)
        - unit: 단위

    Raises
    ------
    ValueError
        지원하지 않는 ``variant``/``frequency`` 일 때.

    Notes
    -----
    - 평잔: 기간 중 평균 잔액
    - 말잔: 기말 잔액
    - 계절조정: 계절적 요인 제거

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_m1_variants()
    >>> df.head()

    >>> df = ecos.get_m1_variants(variant="평잔_원계열")
    >>> df = ecos.get_m1_variants(frequency="annual")
    """
    if variant not in M1_VARIANTS:
        raise ValueError(f"variant는 {list(M1_VARIANTS.keys())} 중 하나여야 합니다.")

    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency,
        allowed=("monthly", "quarterly", "annual"),
        func_name="get_m1_variants",
    )
    period = {
        "monthly": PERIOD_MONTHLY,
        "quarterly": PERIOD_QUARTERLY,
        "annual": PERIOD_ANNUAL,
    }[frequency]

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "monthly":
            default_start, default_end = default_monthly(36)
        elif frequency == "quarterly":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    stat_code = M1_VARIANTS[variant]
    item_code = M1_ITEMS[variant]

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1=item_code,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_m2_variants(
    variant: Literal["평잔_계절조정", "평잔_원계열", "말잔_계절조정"] = "말잔_계절조정",
    start_date: str | None = None,
    end_date: str | None = None,
    frequency: Literal["monthly", "quarterly", "annual"] = "monthly",
) -> pd.DataFrame:
    """
    M2 세부 데이터를 조회합니다.

    평잔/말잔, 계절조정/원계열 등 M2 통화량의 다양한 변형을 제공합니다.

    Parameters
    ----------
    variant : str
        M2 변형 종류
        - '평잔_계절조정': 평잔 계절조정 계열
        - '평잔_원계열': 평잔 원계열
        - '말잔_계절조정': 말잔 계절조정 계열 (기본값)
    start_date : str, optional
        조회 시작 시점. ``frequency`` 에 맞는 형식
        (월 ``YYYYMM`` / 분기 ``YYYYQn`` / 연 ``YYYY``). 기본값: 주기별 기본 범위.
    end_date : str, optional
        조회 종료 시점. (형식은 ``start_date`` 와 동일)
    frequency : str
        조회 주기. ``'monthly'``(기본)/``'quarterly'``/``'annual'``.

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: M2 (십억원)
        - unit: 단위

    Raises
    ------
    ValueError
        지원하지 않는 ``variant``/``frequency`` 일 때.

    Notes
    -----
    - 평잔: 기간 중 평균 잔액
    - 말잔: 기말 잔액
    - 계절조정: 계절적 요인 제거

    M2 변형 데이터는 통화량 추세 분석에 유용합니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_m2_variants()
    >>> df.head()

    >>> df = ecos.get_m2_variants(variant="평잔_원계열")
    >>> df = ecos.get_m2_variants(frequency="annual")
    """
    if variant not in M2_VARIANTS:
        raise ValueError(f"variant는 {list(M2_VARIANTS.keys())} 중 하나여야 합니다.")

    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency,
        allowed=("monthly", "quarterly", "annual"),
        func_name="get_m2_variants",
    )
    period = {
        "monthly": PERIOD_MONTHLY,
        "quarterly": PERIOD_QUARTERLY,
        "annual": PERIOD_ANNUAL,
    }[frequency]

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "monthly":
            default_start, default_end = default_monthly(36)
        elif frequency == "quarterly":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    stat_code = M2_VARIANTS[variant]
    item_code = M2_ITEMS[variant]

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
        start_date=start_date,
        end_date=end_date,
        item_code1=item_code,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_m2_by_holder(
    variant: Literal[
        "평잔_계절조정", "평잔_원계열", "말잔_계절조정", "말잔_원계열"
    ] = "말잔_원계열",
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    frequency: Literal["monthly", "quarterly", "annual"] = "monthly",
) -> pd.DataFrame:
    """
    M2 경제주체별 보유 현황을 조회합니다.

    가계 및 비영리단체, 비금융기업, 보험기관, 연금기금 등 경제주체별 M2
    보유액을 제공합니다. partial-coverage 재설계 규약(#56)을 따릅니다 —
    ``sub_category`` 미지정 시 전체 경제주체를 long-format으로, 지정 시 해당
    주체 단일 시계열만 반환합니다.

    Parameters
    ----------
    variant : str
        M2 변형 종류
        - '평잔_계절조정': 평잔 계절조정 계열
        - '평잔_원계열': 평잔 원계열
        - '말잔_계절조정': 말잔 계절조정 계열
        - '말잔_원계열': 말잔 원계열 (기본값)
    sub_category : str, optional
        경제주체(항목명 또는 item_code1). 지정 시 해당 주체 단일 시계열만,
        미지정 시 전체 주체를 long-format으로 반환합니다.
        예) '가계 및 비영리단체', '비금융기업', 또는 item_code 'BBGAJ1'.
    start_date : str, optional
        조회 시작 시점. ``frequency`` 에 맞는 형식
        (월 ``YYYYMM`` / 분기 ``YYYYQn`` / 연 ``YYYY``). 기본값: 주기별 기본 범위.
    end_date : str, optional
        조회 종료 시점. (형식은 ``start_date`` 와 동일)
    frequency : str
        조회 주기. ``'monthly'``(기본)/``'quarterly'``/``'annual'``.

    Returns
    -------
    pd.DataFrame
        - ``sub_category`` 미지정: 컬럼 ``date, category_value, value, unit``
          (각 경제주체가 행으로 포함된 long-format, ``category_value``=주체명).
          이 통계표에는 총계(M2 전체)와 주체별 항목이 함께 포함되므로 주체 간
          단순 합산은 금지합니다.
        - ``sub_category`` 지정: 컬럼 ``date, value, unit`` (단일 시계열).
        - value 단위: 십억원

    Raises
    ------
    ValueError
        지원하지 않는 ``variant``/``frequency`` 이거나 ``sub_category`` 가 없을 때.

    Notes
    -----
    경제주체별 M2 보유 현황은 자금 흐름과 유동성 분포를 파악하는 데
    중요한 지표입니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_m2_by_holder()  # 전체 주체 long-format
    >>> df = ecos.get_m2_by_holder(sub_category="가계 및 비영리단체")  # 단일 주체
    >>> df = ecos.get_m2_by_holder(variant="평잔_계절조정")
    >>> df = ecos.get_m2_by_holder(frequency="annual")
    """
    if variant not in M2_HOLDER_VARIANTS:
        raise ValueError(f"variant는 {list(M2_HOLDER_VARIANTS.keys())} 중 하나여야 합니다.")

    frequency = normalize_frequency(  # type: ignore[assignment]
        frequency,
        allowed=("monthly", "quarterly", "annual"),
        func_name="get_m2_by_holder",
    )
    period = {
        "monthly": PERIOD_MONTHLY,
        "quarterly": PERIOD_QUARTERLY,
        "annual": PERIOD_ANNUAL,
    }[frequency]

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        if frequency == "monthly":
            default_start, default_end = default_monthly(36)
        elif frequency == "quarterly":
            default_start, default_end = default_quarterly(5)
        else:
            default_start, default_end = default_annual(10)
        start_date = start_date or default_start
        end_date = end_date or default_end

    stat_code = M2_HOLDER_VARIANTS[variant]

    # 보유주체별 통계표는 분류축이 item_code1 하나뿐(총계 BBxA00 + 주체별 BBxAJn).
    # item_code1 필터 없이 전량을 조회해 select_subcategory로 분류한다(#58 규약).
    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    df = parse_response(response)
    return select_subcategory(df, prefix="", sub_category=sub_category, context="get_m2_by_holder")


def get_household_credit(
    category: Literal["업권별", "용도별"] = "업권별",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    가계신용(분기)을 조회합니다.

    업권별 또는 용도별 가계신용 잔액을 제공합니다.

    Parameters
    ----------
    category : str
        가계신용 분류
        - '업권별': 은행, 비은행 등 업권별 (기본값)
        - '용도별': 주택담보대출, 기타대출 등 용도별
    start_date : str, optional
        조회 시작일 (YYYYQN 형식, 예: 2024Q1), 기본값: 5년 전
    end_date : str, optional
        조회 종료일 (YYYYQN 형식), 기본값: 현재 분기

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 가계신용 (십억원)
        - unit: 단위

    Notes
    -----
    가계신용 = 가계대출 + 판매신용

    가계신용 증가율은 가계부채 건전성과 소비 여력을 판단하는
    중요한 지표입니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_household_credit()
    >>> df.head()

    >>> df = ecos.get_household_credit(category="용도별")
    """
    if category not in ["업권별", "용도별"]:
        raise ValueError("category는 '업권별' 또는 '용도별' 중 하나여야 합니다.")

    # 기본 날짜 설정 (분기)
    if start_date is None or end_date is None:
        default_start, default_end = default_quarterly(5)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 카테고리에 따른 stat_code 및 item_code 선택
    if category == "업권별":
        stat_code = STAT_HOUSEHOLD_CREDIT_SECTOR
        item_code = "1110000"  # 예금취급기관
    else:  # 용도별
        stat_code = STAT_HOUSEHOLD_CREDIT_PURPOSE
        item_code = "1000000"  # 가계신용

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=PERIOD_QUARTERLY,
        start_date=start_date,
        end_date=end_date,
        item_code1=item_code,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_household_lending_detail(
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    예금취급기관 가계대출(용도별)을 조회합니다.

    주택관련대출/기타대출을 기관(예금취급기관/예금은행/비은행)별로 제공합니다.
    partial-coverage 재설계 규약(#56)을 따릅니다 — ``sub_category`` 미지정 시
    전체 분류를 long-format으로, 지정 시 해당 분류 단일 시계열만 반환합니다.

    Parameters
    ----------
    sub_category : str, optional
        세부 분류(항목명 또는 item_code1). 지정 시 해당 분류 단일 시계열만
        반환합니다. 미지정 시 전체 분류를 long-format으로 반환합니다.
        예) '주택관련대출-예금취급기관', '기타대출-예금은행', 또는 item_code
        '11100A0'. 항목명은 길고 중복 가능하므로 유일 선택은 item_code를 권장합니다.
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 3년 전
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
        지정한 ``sub_category`` 가 존재하지 않는 경우 (사용 가능 항목을 함께 안내).

    Notes
    -----
    예금취급기관 = 은행 + 비은행 예금취급기관

    이 통계표(151Y005)는 총계('예금취급기관')와 용도×기관 분류, [참고] 항목이
    함께 있는 단일 분류축(item_code1)입니다. long-format에는 총계도 포함되므로
    특정 시계열이 필요하면 ``sub_category`` 로 선택하세요(단순 합산 금지).

    용도별 가계대출 현황은 부동산 시장과 가계 소비 패턴을
    분석하는 데 활용됩니다.

    Examples
    --------
    >>> import ecos
    >>> # 전체 분류 long-format
    >>> df = ecos.get_household_lending_detail()
    >>> df.head()
            date category_value   value unit

    >>> # 주택관련대출(예금취급기관) 단일 시계열
    >>> df = ecos.get_household_lending_detail(sub_category="11100A0")

    >>> df = ecos.get_household_lending_detail(start_date="202201", end_date="202412")
    """
    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(36)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # item_code1 미지정 → 전체 분류 수신 후 select_subcategory로 분류(#58 규약).
    # 151Y005는 단일 분류축(item_code1)이라 prefix="" 로 전량 분류한다.
    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_HOUSEHOLD_LENDING_PURPOSE,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
    )

    df = parse_response(response)
    return select_subcategory(
        df, prefix="", sub_category=sub_category, context="get_household_lending_detail"
    )


def get_borrower_loan(
    loan_type: Literal["신규", "잔액"] = "잔액",
    category: Literal[
        "전체", "성별", "연령별", "지역별", "업권별", "담보유형별", "다중대출별"
    ] = "전체",
    sub_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    차주별 가계대출을 조회합니다.

    가계대출 신규취급액(`181Y001`) 또는 잔액(`181Y002`)을 분류축별로 제공합니다.

    실제 ECOS 구조는 stat_code가 신규/잔액 2개뿐이고 모든 분류축(연령·지역·업권·
    담보유형·다중대출)은 `item_code1` prefix로 표현됩니다. 이 함수는 ``category``로
    분류축을 선택하면 해당 축의 모든 세부 항목을 조회한 뒤,

    - ``sub_category`` 미지정 시: long-format(축 전체)으로 반환하며
      ``category_value`` 컬럼에 세부 항목명을 담습니다.
    - ``sub_category`` 지정 시: 해당 세부 항목 단일 시계열만 반환합니다.

    Parameters
    ----------
    loan_type : str
        대출 유형
        - '신규': 신규취급액
        - '잔액': 잔액 (기본값)
    category : str
        분류축
        - '전체': 차주 전체 (기본값, item_code `0000`)
        - '성별': 성별 (남성/여성, prefix B)
        - '연령별': 연령대별 (prefix C)
        - '지역별': 지역별 (prefix D)
        - '업권별': 업권별 (은행/비은행, prefix E)
        - '담보유형별': 담보 유형별 (주담대/신용/전세 등, prefix F)
        - '다중대출별': 다중대출 건수별 (prefix G)
    sub_category : str, optional
        세부 항목. 지정 시 해당 항목 단일 시계열만 반환합니다.
        세부 항목명(`category_value`) 또는 item_code 둘 다 허용합니다.
        미지정 시 분류축 전체를 long-format으로 반환합니다.
    start_date : str, optional
        조회 시작일 (YYYYQN 형식, 예: 2024Q1), 기본값: 5년 전
    end_date : str, optional
        조회 종료일 (YYYYQN 형식), 기본값: 현재 분기

    Returns
    -------
    pd.DataFrame
        - ``sub_category`` 미지정: 컬럼 ``date, category_value, value, unit``
          (분류축의 각 세부 항목이 행으로 포함된 long-format)
        - ``sub_category`` 지정: 컬럼 ``date, value, unit`` (단일 시계열)

    Raises
    ------
    ValueError
        loan_type/category가 허용 값이 아니거나, 지정한 sub_category가
        해당 분류축에 존재하지 않는 경우 (사용 가능한 항목을 함께 안내).

    Notes
    -----
    차주별 가계대출 통계는 가계부채의 질적 구조를 파악하는 데 중요한 지표입니다.

    - 청년층/고령층 대출 비중 (연령별)
    - 수도권/지방 대출 비중 (지역별)
    - 은행/비은행 대출 비중 (업권별)

    Examples
    --------
    >>> import ecos
    >>> # 연령별 잔액 전체 (long-format)
    >>> df = ecos.get_borrower_loan(loan_type="잔액", category="연령별")
    >>> df.head()
            date category_value      value unit

    >>> # 연령별 중 30대 단일 시계열
    >>> df = ecos.get_borrower_loan(
    ...     loan_type="잔액", category="연령별", sub_category="30대"
    ... )
    """
    if loan_type not in BORROWER_LOAN_STAT_CODES:
        raise ValueError(f"loan_type은 {list(BORROWER_LOAN_STAT_CODES.keys())} 중 하나여야 합니다.")

    if category not in BORROWER_LOAN_CATEGORY_PREFIX:
        raise ValueError(
            f"category는 {list(BORROWER_LOAN_CATEGORY_PREFIX.keys())} 중 하나여야 합니다."
        )

    # 기본 날짜 설정 (분기)
    if start_date is None or end_date is None:
        default_start, default_end = default_quarterly(5)
        start_date = start_date or default_start
        end_date = end_date or default_end

    stat_code = BORROWER_LOAN_STAT_CODES[loan_type]
    prefix = BORROWER_LOAN_CATEGORY_PREFIX[category]

    # stat 전체 item을 받아 분류축 prefix로 client-side 필터링한다.
    # (ECOS item_code1은 정확 일치 필터라 prefix 조회가 불가능하므로 전량 수신 후 분류)
    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=PERIOD_QUARTERLY,
        start_date=start_date,
        end_date=end_date,
    )

    df = parse_response(response)
    # partial-coverage 재설계 공통 규약(#58) — _subcategory.select_subcategory 참고.
    # "전체"는 단일 코드 정확 일치, 나머지 분류축은 prefix 매칭.
    return select_subcategory(
        df,
        prefix=prefix,
        exact=(category == "전체"),
        sub_category=sub_category,
        context=f"loan_type='{loan_type}', category='{category}'",
    )
