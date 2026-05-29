"""
금리 지표 모듈

한국은행 기준금리, 국고채 수익률 등 금리 관련 지표를 조회합니다.
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

from ..client import get_client
from ..constants import (
    ITEM_BASE_RATE,
    PERIOD_DAILY,
    PERIOD_MONTHLY,
    STAT_BASE_RATE,
    STAT_DEPOSIT_RATE_BALANCE,
    STAT_DEPOSIT_RATE_NEW,
    STAT_LENDING_RATE_BALANCE,
    STAT_LENDING_RATE_NEW,
    STAT_MARKET_RATE,
    TREASURY_YIELD_ITEMS,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_daily, default_monthly
from ._registry import get_indicator


def get_base_rate(
    start_date: str | None = None,
    end_date: str | None = None,
    frequency: Literal["D", "M"] = "M",
) -> pd.DataFrame:
    """
    한국은행 기준금리를 조회합니다.

    Parameters
    ----------
    start_date : str, optional
        조회 시작일, 기본값: 1년 전.
        주기에 맞춘 형식 — 'M'이면 YYYYMM, 'D'이면 YYYYMMDD.
    end_date : str, optional
        조회 종료일, 기본값: 현재. (형식은 ``start_date`` 와 동일)
    frequency : str
        조회 주기 (ECOS 통계표 ``722Y001`` 은 일별 원천)
        - 'M': 월별 (기본값, 날짜 YYYYMM)
        - 'D': 일별 (날짜 YYYYMMDD). 기준금리는 변경일에만 갱신되어
          결과가 sparse 합니다 (변경이 없는 날은 행이 없음).

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 기준금리 (%)
        - unit: 단위

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_base_rate()
    >>> df.head()
            date  value unit
    0 2024-01-01   3.50    %

    >>> df = ecos.get_base_rate(start_date="202001", end_date="202312")

    >>> # 일별 (변경일 단위) 조회
    >>> df = ecos.get_base_rate(
    ...     start_date="20200101", end_date="20231231", frequency="D"
    ... )
    """
    if frequency not in ("D", "M"):
        raise ValueError("frequency는 'D' 또는 'M' 중 하나여야 합니다.")

    # 월별(기본)은 선언적 레지스트리(#16)에 위임 — base_rate의 단일 진실원천.
    if frequency == "M":
        return get_indicator("base_rate", start_date=start_date, end_date=end_date)

    # 일별(변경일 단위, sparse)은 별도 포맷이라 직접 조회.
    if start_date is None or end_date is None:
        default_start, default_end = default_daily(365)
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_BASE_RATE,
        period=PERIOD_DAILY,
        start_date=start_date,
        end_date=end_date,
        item_code1=ITEM_BASE_RATE,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_treasury_yield(
    maturity: Literal["1Y", "3Y", "5Y", "10Y", "20Y", "30Y"] = "3Y",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    국고채 수익률을 조회합니다.

    Parameters
    ----------
    maturity : str
        국고채 만기
        - '1Y': 1년물
        - '3Y': 3년물 (기본값)
        - '5Y': 5년물
        - '10Y': 10년물
        - '20Y': 20년물
        - '30Y': 30년물
    start_date : str, optional
        조회 시작일 (YYYYMMDD 형식), 기본값: 1년 전
    end_date : str, optional
        조회 종료일 (YYYYMMDD 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 국고채 수익률 (%)
        - unit: 단위

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_treasury_yield()  # 3년물 기본
    >>> df.head()

    >>> df = ecos.get_treasury_yield(maturity="10Y")  # 10년물
    """
    if maturity not in TREASURY_YIELD_ITEMS:
        raise ValueError(f"maturity는 {list(TREASURY_YIELD_ITEMS.keys())} 중 하나여야 합니다.")

    # 기본 날짜 설정 (일간 데이터)
    if start_date is None or end_date is None:
        default_start, default_end = default_daily(365)
        start_date = start_date or default_start
        end_date = end_date or default_end

    item_code = TREASURY_YIELD_ITEMS[maturity]

    client = get_client()
    response = client.get_statistic_search(
        stat_code=STAT_MARKET_RATE,
        period=PERIOD_DAILY,
        start_date=start_date,
        end_date=end_date,
        item_code1=item_code,
    )

    df = parse_response(response)
    return normalize_stat_result(df)


def get_yield_spread(
    long_maturity: Literal["10Y", "20Y", "30Y"] = "10Y",
    short_maturity: Literal["1Y", "3Y", "5Y"] = "3Y",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    국고채 장단기 금리차를 계산합니다.

    장단기 금리차는 경기 침체의 선행 지표로 활용됩니다.
    음수 전환(역전) 시 경기 침체 가능성을 시사합니다.

    Parameters
    ----------
    long_maturity : str
        장기 국고채 만기 ('10Y', '20Y', '30Y'), 기본값: '10Y'
    short_maturity : str
        단기 국고채 만기 ('1Y', '3Y', '5Y'), 기본값: '3Y'
    start_date : str, optional
        조회 시작일 (YYYYMMDD 형식)
    end_date : str, optional
        조회 종료일 (YYYYMMDD 형식)

    Returns
    -------
    pd.DataFrame
        컬럼: date, long_yield, short_yield, spread, unit
        - spread: 장기금리 - 단기금리

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_yield_spread()  # 10년-3년 스프레드
    >>> df.head()

    >>> df = ecos.get_yield_spread(long_maturity="30Y", short_maturity="1Y")
    """
    # 장기/단기 수익률 조회
    long_df = get_treasury_yield(
        maturity=long_maturity,  # type: ignore
        start_date=start_date,
        end_date=end_date,
    )
    short_df = get_treasury_yield(
        maturity=short_maturity,  # type: ignore
        start_date=start_date,
        end_date=end_date,
    )

    if long_df.empty or short_df.empty:
        return pd.DataFrame(columns=["date", "long_yield", "short_yield", "spread", "unit"])

    # 날짜 기준 병합
    long_df = long_df.rename(columns={"value": "long_yield"})
    short_df = short_df.rename(columns={"value": "short_yield"})

    merged = pd.merge(
        long_df[["date", "long_yield"]],
        short_df[["date", "short_yield"]],
        on="date",
        how="inner",
    )

    # 스프레드 계산
    merged["spread"] = merged["long_yield"] - merged["short_yield"]
    merged["unit"] = "%p"

    return merged.sort_values("date").reset_index(drop=True)


def get_bank_deposit_rate(
    basis: Literal["신규취급액", "잔액"] = "신규취급액",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    예금은행 수신금리를 조회합니다.

    신규취급액 기준 또는 잔액 기준 수신금리를 제공합니다.

    Parameters
    ----------
    basis : str
        금리 산정 기준
        - '신규취급액': 신규취급액 기준 (기본값)
        - '잔액': 잔액 기준
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 1년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 수신금리 (%)
        - unit: 단위

    Notes
    -----
    - 수신금리: 은행이 예금을 받을 때 지급하는 이자율
    - 신규취급액 기준: 당월 신규로 취급된 예금의 금리
    - 잔액 기준: 전체 예금 잔액 기준 가중평균 금리

    수신금리는 기준금리의 변화를 반영하며, 예금자의 저축 수익률을
    결정하는 중요한 지표입니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_bank_deposit_rate()
    >>> df.head()
            date  value unit
    0 2024-01-01   3.20    %

    >>> df = ecos.get_bank_deposit_rate(basis="잔액")
    """
    if basis not in ["신규취급액", "잔액"]:
        raise ValueError("basis는 '신규취급액' 또는 '잔액' 중 하나여야 합니다.")

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(12)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # basis에 따른 stat_code 및 item_code 선택
    if basis == "신규취급액":
        stat_code = STAT_DEPOSIT_RATE_NEW
        item_code = "BEABAA2"  # 저축성수신
    else:  # 잔액
        stat_code = STAT_DEPOSIT_RATE_BALANCE
        item_code = "BEABAB2"  # 총수신

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


def get_bank_lending_rate(
    basis: Literal["신규취급액", "잔액"] = "신규취급액",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    예금은행 대출금리를 조회합니다.

    신규취급액 기준 또는 잔액 기준 대출금리를 제공합니다.

    Parameters
    ----------
    basis : str
        금리 산정 기준
        - '신규취급액': 신규취급액 기준 (기본값)
        - '잔액': 잔액 기준
    start_date : str, optional
        조회 시작일 (YYYYMM 형식), 기본값: 1년 전
    end_date : str, optional
        조회 종료일 (YYYYMM 형식), 기본값: 현재

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit
        - date: 날짜 (datetime)
        - value: 대출금리 (%)
        - unit: 단위

    Notes
    -----
    - 대출금리: 은행이 대출을 실행할 때 적용하는 이자율
    - 신규취급액 기준: 당월 신규로 실행된 대출의 금리
    - 잔액 기준: 전체 대출 잔액 기준 가중평균 금리

    대출금리는 기준금리와 시장 상황을 반영하며, 기업과 가계의
    자금 조달 비용을 결정하는 핵심 지표입니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_bank_lending_rate()
    >>> df.head()
            date  value unit
    0 2024-01-01   4.50    %

    >>> df = ecos.get_bank_lending_rate(basis="잔액")
    """
    if basis not in ["신규취급액", "잔액"]:
        raise ValueError("basis는 '신규취급액' 또는 '잔액' 중 하나여야 합니다.")

    # 기본 날짜 설정
    if start_date is None or end_date is None:
        default_start, default_end = default_monthly(12)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # basis에 따른 stat_code 및 item_code 선택
    if basis == "신규취급액":
        stat_code = STAT_LENDING_RATE_NEW
        item_code = "BECBLA01"  # 대출평균
    else:  # 잔액
        stat_code = STAT_LENDING_RATE_BALANCE
        item_code = "BECBLB01"  # 총대출

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
