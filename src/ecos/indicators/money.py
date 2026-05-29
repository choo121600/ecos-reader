"""
통화 지표 모듈

통화량(M1, M2, Lf), 은행 대출 등 통화 관련 지표를 조회합니다.
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

from ..client import get_client
from ..constants import (
    BANK_LENDING_ITEMS,
    BORROWER_LOAN_CATEGORY_PREFIX,
    BORROWER_LOAN_STAT_CODES,
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
    STAT_HOUSEHOLD_CREDIT_PURPOSE,
    STAT_HOUSEHOLD_CREDIT_SECTOR,
    STAT_HOUSEHOLD_LENDING,
    STAT_HOUSEHOLD_LENDING_PURPOSE,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_monthly, default_quarterly
from ._deprecations import warn_partial_coverage as _warn_partial_coverage


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
        default_start, default_end = default_monthly(36)
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
        default_start, default_end = default_monthly(36)
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
        default_start, default_end = default_monthly(36)
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
        default_start, default_end = default_monthly(36)
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
        default_start, default_end = default_monthly(36)
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

    Warnings
    --------
    DeprecationWarning
        현재 단일 항목(`item_code1="1110000"`, 예금취급기관(미확인))만 반환하며 함수명이
        시사하는 전체 용도별 대출 시리즈를 다루지 않습니다. v0.3.0에서 시그니처가 변경될
        예정이며, 현재 동작에 의존한다면 `EcosClient.get_statistic_search`로 직접
        item_code1을 전달하는 방식으로 마이그레이션하세요. (이슈 #8)

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
        default_start, default_end = default_monthly(36)
        start_date = start_date or default_start
        end_date = end_date or default_end

    _warn_partial_coverage("get_household_lending_detail", "1110000", "예금취급기관(미확인)")

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
    if df.empty or "item_code1" not in df.columns:
        return df

    # 분류축 필터: "전체"는 단일 코드, 나머지는 prefix 매칭
    if category == "전체":
        axis = df[df["item_code1"] == prefix].copy()
    else:
        axis = df[df["item_code1"].str.startswith(prefix, na=False)].copy()

    if axis.empty:
        return parse_response({})  # 빈 DataFrame

    if sub_category is not None:
        # 세부 항목명(item_name1) 또는 item_code로 단일 시계열 선택
        match = axis[
            (axis.get("item_name1") == sub_category) | (axis["item_code1"] == sub_category)
        ]
        if match.empty:
            available = sorted(axis.get("item_name1", axis["item_code1"]).dropna().unique())
            raise ValueError(
                f"sub_category='{sub_category}'는 loan_type='{loan_type}', "
                f"category='{category}' 분류축에 존재하지 않습니다. "
                f"사용 가능한 항목: {available}"
            )
        return normalize_stat_result(match)

    # long-format: 세부 항목명을 category_value로 노출
    axis = axis.rename(columns={"item_name1": "category_value"})
    return normalize_stat_result(axis, columns=["date", "category_value", "value", "unit"])
