"""
재정 지표 모듈

통합재정수지 등 재정 관련 지표를 조회합니다.
"""

from __future__ import annotations

import pandas as pd

from ._registry import get_indicator


def get_fiscal_balance(
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    통합재정수지를 조회합니다.

    통합재정수지는 중앙정부와 지방정부를 합한 일반정부의 재정수지로,
    정부의 재정건전성을 나타내는 핵심 지표입니다.

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
        - value: 통합재정수지 (조원)
        - unit: 단위

    Notes
    -----
    - 통합재정수지 = 총수입 - 총지출
    - 흑자(+): 재정 여력 있음
    - 적자(-): 재정 건전성 악화

    통합재정수지는 국가채무 증감과 직접적인 관련이 있으며,
    지속적인 적자는 국가 신용등급에 영향을 미칠 수 있습니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_fiscal_balance()
    >>> df.head()
            date  value unit
    0 2023-01-01   -5.2  조원
    1 2023-02-01   -3.8  조원

    >>> df = ecos.get_fiscal_balance(start_date="202301", end_date="202312")
    """
    # 선언적 레지스트리(#16)에 위임하는 얇은 alias. 동작·기본값은 spec이 보존합니다.
    return get_indicator("fiscal_balance", start_date=start_date, end_date=end_date)
