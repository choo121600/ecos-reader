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
    M1_ITEMS,
    M1_VARIANTS,
    M2_HOLDER_ITEMS,
    M2_HOLDER_VARIANTS,
    M2_ITEMS,
    M2_VARIANTS,
    MONEY_SUPPLY_ITEMS,
    MONEY_SUPPLY_STAT_CODES,
    PERIOD_MONTHLY,
    PERIOD_QUARTERLY,
    STAT_BANK_LENDING,
    STAT_BORROWER_LOAN_BALANCE,
    STAT_BORROWER_LOAN_NEW,
    STAT_HOUSEHOLD_CREDIT_PURPOSE,
    STAT_HOUSEHOLD_CREDIT_SECTOR,
    STAT_HOUSEHOLD_LENDING,
    STAT_HOUSEHOLD_LENDING_PURPOSE,
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


def get_m1_variants(
    variant: Literal["평잔_계절조정", "평잔_원계열", "말잔_계절조정"] = "말잔_계절조정",
    start_date: str | None = None,
    end_date: str | None = None,
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
        조회 시작일 (YYYYMM 형식), 기본값: 3년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: M1 (조원)
        - unit: 단위

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
    """
    if variant not in M1_VARIANTS:
        raise ValueError(f"variant는 {list(M1_VARIANTS.keys())} 중 하나여야 합니다.")

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates(36)
        start_date = start_date or default_start
        end_date = end_date or default_end

    stat_code = M1_VARIANTS[variant]
    item_code = M1_ITEMS[variant]

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


def get_m2_variants(
    variant: Literal["평잔_계절조정", "평잔_원계열", "말잔_계절조정"] = "말잔_계절조정",
    start_date: str | None = None,
    end_date: str | None = None,
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
        조회 시작일 (YYYYMM 형식), 기본값: 3년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: M2 (조원)
        - unit: 단위

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
    """
    if variant not in M2_VARIANTS:
        raise ValueError(f"variant는 {list(M2_VARIANTS.keys())} 중 하나여야 합니다.")

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates(36)
        start_date = start_date or default_start
        end_date = end_date or default_end

    stat_code = M2_VARIANTS[variant]
    item_code = M2_ITEMS[variant]

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


def get_m2_by_holder(
    variant: Literal[
        "평잔_계절조정", "평잔_원계열", "말잔_계절조정", "말잔_원계열"
    ] = "말잔_원계열",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    M2 경제주체별 보유 현황을 조회합니다.

    기업, 가계, 기타 경제주체별 M2 보유액을 제공합니다.

    Parameters
    ----------
    variant : str
        M2 변형 종류
        - '평잔_계절조정': 평잔 계절조정 계열
        - '평잔_원계열': 평잔 원계열
        - '말잔_계절조정': 말잔 계절조정 계열
        - '말잔_원계열': 말잔 원계열 (기본값)
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 3년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: M2 보유액 (조원)
        - unit: 단위

    Notes
    -----
    경제주체별 M2 보유 현황은 자금 흐름과 유동성 분포를 파악하는 데
    중요한 지표입니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_m2_by_holder()
    >>> df.head()

    >>> df = ecos.get_m2_by_holder(variant="평잔_계절조정")
    """
    if variant not in M2_HOLDER_VARIANTS:
        raise ValueError(f"variant는 {list(M2_HOLDER_VARIANTS.keys())} 중 하나여야 합니다.")

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates(36)
        start_date = start_date or default_start
        end_date = end_date or default_end

    stat_code = M2_HOLDER_VARIANTS[variant]
    item_code = M2_HOLDER_ITEMS[variant]

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
        - value: 가계신용 (조원)
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
        end_date_obj = datetime.now()
        start_year = end_date_obj.year - 5
        current_quarter = (end_date_obj.month - 1) // 3 + 1

        start_str = f"{start_year}Q1"
        end_str = f"{end_date_obj.year}Q{current_quarter}"

        start_date = start_date or start_str
        end_date = end_date or end_str

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
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    예금취급기관 가계대출(용도별)을 조회합니다.

    주택담보대출, 기타대출 등 용도별 가계대출 잔액을 제공합니다.

    Parameters
    ----------
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 3년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 가계대출 (조원)
        - unit: 단위

    Notes
    -----
    예금취급기관 = 은행 + 비은행 예금취급기관

    용도별 가계대출 현황은 부동산 시장과 가계 소비 패턴을
    분석하는 데 활용됩니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_household_lending_detail()
    >>> df.head()

    >>> df = ecos.get_household_lending_detail(start_date="202201", end_date="202412")
    """
    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = _get_default_dates(36)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_HOUSEHOLD_LENDING_PURPOSE,
        period=PERIOD_MONTHLY,
        start_date=start_date,
        end_date=end_date,
        item_code1="1110000",  # 예금취급기관 (StatisticItemList로 확인 필요)
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_borrower_loan(
    loan_type: Literal["신규", "잔액"] = "잔액",
    category: Literal["차주별", "소득별", "연령별", "지역별", "담보유형별", "업권별"] = "차주별",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    차주별 가계대출을 조회합니다.

    차주 특성별(소득, 연령 등) 가계대출 신규취급액 또는 잔액을 제공합니다.

    Parameters
    ----------
    loan_type : str
        대출 유형
        - '신규': 신규취급액
        - '잔액': 잔액 (기본값)
    category : str
        차주 분류
        - '차주별': 차주 전체 (기본값)
        - '소득별': 소득 구간별
        - '연령별': 연령대별
        - '지역별': 지역별
        - '담보유형별': 담보 유형별
        - '업권별': 업권별
    start_date : str, optional
        조회 시작일 (YYYYQN 형식, 예: 2024Q1), 기본값: 5년 전
    end_date : str, optional
        조회 종료일 (YYYYQN 형식), 기본값: 현재 분기

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 대출액 (조원)
        - unit: 단위

    Notes
    -----
    차주별 가계대출 통계는 가계부채의 질적 구조를 파악하는 데
    중요한 지표입니다.

    - 저소득층/고소득층 대출 비중
    - 청년층/고령층 대출 비중
    - 수도권/지방 대출 비중

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_borrower_loan()
    >>> df.head()

    >>> df = ecos.get_borrower_loan(loan_type="신규", category="소득별")
    """
    if loan_type not in ["신규", "잔액"]:
        raise ValueError("loan_type은 '신규' 또는 '잔액' 중 하나여야 합니다.")

    # 기본 날짜 설정 (분기)
    if start_date is None or end_date is None:
        end_date_obj = datetime.now()
        start_year = end_date_obj.year - 5
        current_quarter = (end_date_obj.month - 1) // 3 + 1

        start_str = f"{start_year}Q1"
        end_str = f"{end_date_obj.year}Q{current_quarter}"

        start_date = start_date or start_str
        end_date = end_date or end_str

    # loan_type과 category에 따른 stat_code 선택
    stat_codes = STAT_BORROWER_LOAN_NEW if loan_type == "신규" else STAT_BORROWER_LOAN_BALANCE

    if category not in stat_codes:
        raise ValueError(f"category는 {list(stat_codes.keys())} 중 하나여야 합니다.")

    stat_code = stat_codes[category]

    client = get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=PERIOD_QUARTERLY,
        start_date=start_date,
        end_date=end_date,
        item_code1="F001",  # 주택담보대출
    )

    df = parse_response(response)
    return normalize_stat_result(df)
