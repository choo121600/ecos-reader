"""Partial-coverage 재설계 공통 규약 (#58, epic #56).

``item_code1`` 단일 항목만 반환하던 partial-coverage 지표 함수들을 함수명이
시사하는 **전체 시리즈** 또는 **sub-category 선택** 제공으로 재설계하기 위한
공통 헬퍼입니다. v0.2.0 의 :func:`ecos.indicators.money.get_borrower_loan`
재설계(#29) 패턴을 일반화한 단일 진실원천으로, 카테고리별 하위 이슈
(#59~#63)는 모두 이 규약을 따릅니다.

규약
----
ECOS 의 한 통계표(``stat_code``)는 여러 세부 항목을 ``item_code1`` 으로 묶어
제공합니다. ECOS API 의 ``item_code1`` 필터는 *정확 일치* 만 지원하므로 prefix
조회가 불가능합니다. 따라서 재설계 함수는 다음 흐름을 따릅니다.

1. 입력값을 검증한다 (허용되지 않는 값은 사용 가능 목록과 함께 ``ValueError``).
2. ``item_code1`` 필터 없이 통계표 전량을 조회한다.
3. :func:`select_subcategory` 로 분류축(prefix/정확코드)을 client-side 필터링하고
   ``sub_category`` 지정 여부에 따라 형식을 결정한다.

   - ``sub_category`` **미지정**: 분류축 전체를 long-format
     (:data:`LONG_FORMAT_COLUMNS`, ``date, category_value, value, unit``)으로
     반환하며 ``category_value`` 컬럼에 세부 항목명을 담는다.
   - ``sub_category`` **지정**: 해당 세부 항목 단일 시계열
     (``date, value, unit``)만 반환한다. 세부 항목명(``item_name1``)과
     ``item_code1`` 둘 다 허용한다.

4. 존재하지 않는 ``sub_category`` 는 **사용 가능한 항목 목록과 함께**
   ``ValueError`` 를 던진다.

이 규약을 사용하는 함수의 골격은 다음과 같습니다::

    def get_something(sub_category=None, start_date=None, end_date=None):
        # 1) 입력 검증 + 기본 날짜
        client = get_client()
        response = client.get_statistic_search(
            stat_code=STAT_SOMETHING,
            period=PERIOD_MONTHLY,
            start_date=start_date,
            end_date=end_date,
        )  # item_code1 미지정 → 전량 수신
        df = parse_response(response)
        return select_subcategory(
            df,
            prefix=PREFIX,            # 분류축 prefix 또는 정확코드
            exact=False,             # 정확 일치가 필요하면 True
            sub_category=sub_category,
            context="<함수 맥락 설명>",
        )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..parser import normalize_stat_result

if TYPE_CHECKING:
    import pandas as pd

#: ``sub_category`` 미지정 시 반환하는 long-format 컬럼 순서.
LONG_FORMAT_COLUMNS = ["date", "category_value", "value", "unit"]


def select_subcategory(
    df: pd.DataFrame,
    *,
    prefix: str,
    exact: bool = False,
    sub_category: str | None = None,
    context: str = "",
) -> pd.DataFrame:
    """분류축으로 필터링한 뒤 long-format 또는 단일 시계열을 반환합니다.

    partial-coverage 재설계 규약(:mod:`ecos.indicators._subcategory` 모듈
    docstring 참고)의 공통 선택 로직입니다.

    Parameters
    ----------
    df : pd.DataFrame
        :func:`ecos.parser.parse_response` 결과. ``item_code1`` /
        ``item_name1`` / ``time`` / ``value`` / ``unit`` 컬럼을 기대합니다.
    prefix : str
        분류축 ``item_code1`` prefix. ``exact=True`` 이면 정확히 일치할 코드.
    exact : bool, optional
        ``True`` 이면 ``item_code1 == prefix`` 정확 일치, ``False`` (기본값)
        이면 ``startswith(prefix)`` 매칭. "전체"처럼 단일 코드로 표현되는
        축은 ``True`` 를 사용합니다.
    sub_category : str, optional
        세부 항목명(``item_name1``) 또는 ``item_code1``. 지정 시 해당 단일
        시계열만, 미지정 시 분류축 전체 long-format 을 반환합니다.
    context : str, optional
        ``ValueError`` 메시지에 포함할 호출 맥락 설명
        (예: ``"loan_type='잔액', category='연령별'"``).

    Returns
    -------
    pd.DataFrame
        - ``sub_category`` 미지정: 컬럼 :data:`LONG_FORMAT_COLUMNS`
          (``date, category_value, value, unit``).
        - ``sub_category`` 지정: 컬럼 ``date, value, unit``.
        - 입력이 비었거나 분류축에 해당하는 항목이 없으면 빈 DataFrame.

    Raises
    ------
    ValueError
        지정한 ``sub_category`` 가 분류축에 존재하지 않을 때. 사용 가능한
        항목 목록을 함께 안내합니다.
    """
    if df.empty or "item_code1" not in df.columns:
        return df

    if exact:
        axis = df[df["item_code1"] == prefix].copy()
    else:
        axis = df[df["item_code1"].str.startswith(prefix, na=False)].copy()

    if axis.empty:
        return axis

    if sub_category is not None:
        match = axis[
            (axis.get("item_name1") == sub_category) | (axis["item_code1"] == sub_category)
        ]
        if match.empty:
            available = sorted(axis.get("item_name1", axis["item_code1"]).dropna().unique())
            suffix = f"{context} " if context else ""
            raise ValueError(
                f"sub_category='{sub_category}'는 {suffix}분류축에 존재하지 않습니다. "
                f"사용 가능한 항목: {available}"
            )
        return normalize_stat_result(match)

    # long-format: 세부 항목명을 category_value 로 노출.
    axis = axis.rename(columns={"item_name1": "category_value"})
    return normalize_stat_result(axis, columns=LONG_FORMAT_COLUMNS)
