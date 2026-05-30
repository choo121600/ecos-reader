"""partial-coverage 재설계 공통 헬퍼 테스트 (#58).

:func:`ecos.indicators._subcategory.select_subcategory` 의 규약을 API 호출 없이
DataFrame 입력으로 직접 검증한다. 카테고리별 하위 이슈(#59~#63)가 이 규약을
따르므로, 헬퍼 자체의 동작을 단일 진실원천으로 고정해 둔다.
"""

from __future__ import annotations

import pandas as pd
import pytest

from ecos.indicators._subcategory import LONG_FORMAT_COLUMNS, select_subcategory


def _axis_df() -> pd.DataFrame:
    """parse_response 출력 형태를 흉내낸 분류축 DataFrame.

    0000 전체 / B0xx 성별 / C0xx 연령 — 2개 분기.
    """
    rows = []
    for time in ["2024Q1", "2024Q2"]:
        rows += [
            {
                "item_code1": "0000",
                "item_name1": "전체",
                "time": time,
                "value": 100.0,
                "unit": "조원",
            },
            {
                "item_code1": "B001",
                "item_name1": "남성",
                "time": time,
                "value": 55.0,
                "unit": "조원",
            },
            {
                "item_code1": "B002",
                "item_name1": "여성",
                "time": time,
                "value": 45.0,
                "unit": "조원",
            },
            {
                "item_code1": "C001",
                "item_name1": "20대",
                "time": time,
                "value": 10.0,
                "unit": "조원",
            },
            {
                "item_code1": "C002",
                "item_name1": "30대",
                "time": time,
                "value": 20.0,
                "unit": "조원",
            },
        ]
    return pd.DataFrame(rows)


def test_long_format_filters_by_prefix():
    """sub_category 미지정 시 prefix 분류축 전체를 long-format으로 반환한다."""
    df = select_subcategory(_axis_df(), prefix="C", context="연령")
    assert list(df.columns) == LONG_FORMAT_COLUMNS
    assert set(df["category_value"]) == {"20대", "30대"}
    assert len(df) == 4  # 2항목 × 2분기. 다른 축(0000/B)은 제외.


def test_exact_match_single_code():
    """exact=True 는 정확히 일치하는 단일 코드만 매칭한다."""
    df = select_subcategory(_axis_df(), prefix="0000", exact=True, context="전체")
    assert set(df["category_value"]) == {"전체"}
    assert (df["value"] == 100.0).all()


def test_sub_category_by_name_returns_single_series():
    """sub_category(항목명) 지정 시 단일 시계열만 반환한다."""
    df = select_subcategory(_axis_df(), prefix="C", sub_category="30대", context="연령")
    assert list(df.columns) == ["date", "value", "unit"]
    assert len(df) == 2
    assert (df["value"] == 20.0).all()


def test_sub_category_accepts_item_code():
    """sub_category 로 item_code1 도 허용한다."""
    df = select_subcategory(_axis_df(), prefix="C", sub_category="C001", context="연령")
    assert (df["value"] == 10.0).all()


def test_unknown_sub_category_raises_with_available():
    """존재하지 않는 sub_category 는 사용 가능한 항목과 함께 ValueError."""
    with pytest.raises(ValueError, match="사용 가능한 항목"):
        select_subcategory(_axis_df(), prefix="C", sub_category="없는항목", context="연령")


def test_context_included_in_error_message():
    """context 가 ValueError 메시지에 포함된다."""
    with pytest.raises(ValueError, match="loan_type='잔액'"):
        select_subcategory(
            _axis_df(), prefix="C", sub_category="없는항목", context="loan_type='잔액'"
        )


def test_empty_input_returns_unchanged():
    """빈 DataFrame 은 그대로 반환한다."""
    empty = pd.DataFrame()
    assert select_subcategory(empty, prefix="C").empty


def test_missing_item_code_column_returns_unchanged():
    """item_code1 컬럼이 없으면 입력을 그대로 반환한다."""
    df = pd.DataFrame({"value": [1.0]})
    result = select_subcategory(df, prefix="C")
    assert list(result.columns) == ["value"]


def test_unmatched_prefix_returns_empty():
    """분류축에 해당하는 항목이 없으면 빈 DataFrame."""
    result = select_subcategory(_axis_df(), prefix="Z")
    assert result.empty
