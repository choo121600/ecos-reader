"""
범용 조회 API(get_series) 단위 테스트 (#100, ADR 0001).

실제 ECOS API를 호출하지 않고 mock 응답으로 검증한다.
"""

from __future__ import annotations

import pandas as pd
import pytest

import ecos
from ecos.access import _resolve_item_codes, normalize_period

from .conftest import make_empty_response, make_statistic_search_response


class _StubClient:
    """get_statistic_search 호출 인자를 기록하고 고정 응답을 반환하는 스텁."""

    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: list[dict] = []

    def get_statistic_search(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


# ---------------------------------------------------------------------------
# period 어휘 정규화 (ADR §2.3)
# ---------------------------------------------------------------------------


class TestNormalizePeriod:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("daily", "D"),
            ("monthly", "M"),
            ("quarterly", "Q"),
            ("annual", "A"),
            ("semiannual", "S"),
            ("semimonthly", "SM"),
        ],
    )
    def test_canonical(self, value, expected):
        assert normalize_period(value) == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("D", "D"), ("M", "M"), ("Q", "Q"), ("A", "A"), ("S", "S"), ("SM", "SM")],
    )
    def test_raw_code_passthrough(self, value, expected):
        assert normalize_period(value) == expected

    @pytest.mark.parametrize("value", ["Daily", "MONTHLY", "sm", "Sm", " annual "])
    def test_case_insensitive_and_strip(self, value):
        # 대소문자/공백 무관하게 정규화된다.
        assert normalize_period(value) in {"D", "M", "Q", "A", "S", "SM"}

    @pytest.mark.parametrize("value", ["weekly", "yearly", "", "MM", "x"])
    def test_invalid_raises(self, value):
        with pytest.raises(ValueError, match="period"):
            normalize_period(value)


# ---------------------------------------------------------------------------
# item_code 선택자 매핑 (ADR §2.1)
# ---------------------------------------------------------------------------


class TestResolveItemCodes:
    def test_none_is_all_empty(self):
        assert _resolve_item_codes(None) == ["", "", "", ""]

    def test_single_string(self):
        assert _resolve_item_codes("0101000") == ["0101000", "", "", ""]

    def test_list_multi_axis(self):
        assert _resolve_item_codes(["A", "B"]) == ["A", "B", "", ""]

    def test_full_four_axes(self):
        assert _resolve_item_codes(["A", "B", "C", "D"]) == ["A", "B", "C", "D"]

    def test_too_many_raises(self):
        with pytest.raises(ValueError, match="최대 4"):
            _resolve_item_codes(["A", "B", "C", "D", "E"])


# ---------------------------------------------------------------------------
# get_series — tidy 출력 스키마 (ADR §2.2)
# ---------------------------------------------------------------------------


class TestGetSeriesSingleAxis:
    def test_single_axis_tidy(self):
        client = _StubClient(make_statistic_search_response())
        df = ecos.get_series(
            "722Y001",
            "monthly",
            start_date="202401",
            end_date="202403",
            item_code="0101000",
            client=client,
        )

        # date, value, unit, 비어있지 않은 item_code1/item_name1만 포함
        assert df.columns.tolist() == ["date", "value", "unit", "item_code1", "item_name1"]
        assert pd.api.types.is_datetime64_any_dtype(df["date"])
        assert len(df) == 3
        # 날짜 오름차순 정렬
        assert df["date"].is_monotonic_increasing

    def test_empty_axes_dropped(self):
        # item_code2~4가 빈 문자열인 응답 → 해당 축 컬럼 제외
        data = [
            {
                "STAT_CODE": "722Y001",
                "ITEM_CODE1": "0101000",
                "ITEM_NAME1": "기준금리",
                "ITEM_CODE2": "",
                "ITEM_NAME2": "",
                "TIME": "202401",
                "DATA_VALUE": "3.50",
                "UNIT_NAME": "%",
            }
        ]
        client = _StubClient(make_statistic_search_response(data=data))
        df = ecos.get_series("722Y001", "M", start_date="202401", end_date="202401", client=client)
        assert "item_code2" not in df.columns
        assert "item_code1" in df.columns

    def test_period_mapped_to_raw_code(self):
        client = _StubClient(make_statistic_search_response())
        ecos.get_series("722Y001", "monthly", start_date="202401", end_date="202403", client=client)
        assert client.calls[0]["period"] == "M"

    def test_item_code_mapped_to_axes(self):
        client = _StubClient(make_statistic_search_response())
        ecos.get_series(
            "200Y001",
            "Q",
            start_date="2024Q1",
            end_date="2024Q4",
            item_code=["10101", "10102"],
            client=client,
        )
        call = client.calls[0]
        assert call["item_code1"] == "10101"
        assert call["item_code2"] == "10102"
        assert call["item_code3"] == ""
        assert call["item_code4"] == ""


class TestGetSeriesMultiAxis:
    def test_multi_axis_long_format(self):
        # 2축 항목이 별도 행으로 보존되는 long-format
        data = [
            {
                "STAT_CODE": "200Y001",
                "ITEM_CODE1": "10101",
                "ITEM_NAME1": "항목A",
                "ITEM_CODE2": "20201",
                "ITEM_NAME2": "세부1",
                "TIME": "2024Q1",
                "DATA_VALUE": "100",
                "UNIT_NAME": "십억원",
            },
            {
                "STAT_CODE": "200Y001",
                "ITEM_CODE1": "10101",
                "ITEM_NAME1": "항목A",
                "ITEM_CODE2": "20202",
                "ITEM_NAME2": "세부2",
                "TIME": "2024Q1",
                "DATA_VALUE": "200",
                "UNIT_NAME": "십억원",
            },
        ]
        client = _StubClient(make_statistic_search_response(data=data))
        df = ecos.get_series(
            "200Y001",
            "quarterly",
            start_date="2024Q1",
            end_date="2024Q1",
            item_code=["10101"],
            client=client,
        )
        assert df.columns.tolist() == [
            "date",
            "value",
            "unit",
            "item_code1",
            "item_name1",
            "item_code2",
            "item_name2",
        ]
        # 두 항목조합이 별도 행으로 유지됨
        assert len(df) == 2
        assert set(df["item_code2"]) == {"20201", "20202"}


# ---------------------------------------------------------------------------
# get_series — tidy=False 이스케이프 해치 & 에러 의미 (ADR §2.2/§2.4)
# ---------------------------------------------------------------------------


class TestGetSeriesRawAndErrors:
    def test_tidy_false_returns_raw_columns(self):
        client = _StubClient(make_statistic_search_response())
        df = ecos.get_series(
            "722Y001",
            "M",
            start_date="202401",
            end_date="202403",
            tidy=False,
            client=client,
        )
        # parse_response의 원본 컬럼(snake_case) 그대로 — stat_name/time 포함
        assert "time" in df.columns
        assert "stat_name" in df.columns

    def test_empty_result_returns_empty_df(self):
        client = _StubClient(make_empty_response())
        df = ecos.get_series("722Y001", "M", start_date="202401", end_date="202403", client=client)
        assert df.empty

    def test_invalid_period_fails_before_network(self):
        client = _StubClient(make_statistic_search_response())
        with pytest.raises(ValueError, match="period"):
            ecos.get_series(
                "722Y001", "weekly", start_date="202401", end_date="202403", client=client
            )
        # 네트워크 호출이 일어나지 않아야 한다.
        assert client.calls == []

    def test_too_many_item_codes_fails_before_network(self):
        client = _StubClient(make_statistic_search_response())
        with pytest.raises(ValueError, match="최대 4"):
            ecos.get_series(
                "722Y001",
                "M",
                start_date="202401",
                end_date="202403",
                item_code=["a", "b", "c", "d", "e"],
                client=client,
            )
        assert client.calls == []


def test_public_exports():
    # 공개 export 확인 (#100)
    assert hasattr(ecos, "get_series")
    assert hasattr(ecos, "parse_response")
    assert hasattr(ecos, "normalize_stat_result")
    for name in ("get_series", "parse_response", "normalize_stat_result"):
        assert name in ecos.__all__
