"""
성장 지표 모듈 테스트
"""

from __future__ import annotations

import re
import warnings
from typing import ClassVar

import pytest
import responses

from ecos.indicators.growth import (
    get_gdp,
    get_gdp_by_expenditure,
    get_gdp_by_industry,
    get_gdp_deflator,
    get_gdp_deflator_by_industry,
    get_gdp_growth_rate,
)


@pytest.mark.usefixtures("set_api_key")
class TestGetGdp:
    """get_gdp 함수 테스트"""

    @responses.activate
    def test_get_gdp_quarterly(self, mock_gdp_response):
        """분기별 GDP 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_gdp_response,
            status=200,
        )

        df = get_gdp(frequency="quarterly", start_date="2024Q1", end_date="2024Q2")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns

    @responses.activate
    def test_get_gdp_annual(self):
        """연간 GDP 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "200Y001",
                        "TIME": "2023",
                        "DATA_VALUE": "2100000",
                        "UNIT_NAME": "십억원",
                    }
                ]
            }
        }

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        df = get_gdp(frequency="annual", start_date="2023", end_date="2023")
        assert not df.empty

    @responses.activate
    def test_get_gdp_nominal(self):
        """명목 GDP 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "200Y002",
                        "TIME": "2024Q1",
                        "DATA_VALUE": "600000",
                        "UNIT_NAME": "십억원",
                    }
                ]
            }
        }

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        df = get_gdp(frequency="quarterly", basis="nominal", start_date="2024Q1", end_date="2024Q1")
        assert not df.empty


@pytest.mark.usefixtures("set_api_key")
class TestGetGdpDeflator:
    """get_gdp_deflator 함수 테스트"""

    @responses.activate
    def test_get_gdp_deflator(self):
        """GDP 디플레이터 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "200Y004",
                        "TIME": "2024Q1",
                        "DATA_VALUE": "110.5",
                        "UNIT_NAME": "2015=100",
                    }
                ]
            }
        }

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        df = get_gdp_deflator(start_date="2024Q1", end_date="2024Q1")
        assert not df.empty
        assert df["value"].iloc[0] == 110.5


@pytest.mark.usefixtures("set_api_key")
class TestGetGdpGrowthRate:
    """get_gdp_growth_rate 함수 테스트"""

    @responses.activate
    def test_get_gdp_growth_rate_quarterly(self):
        """분기별 GDP 성장률 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "902Y015",
                        "TIME": "2024Q1",
                        "DATA_VALUE": "1.3",
                        "UNIT_NAME": "%",
                    }
                ]
            }
        }

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        df = get_gdp_growth_rate(frequency="quarterly", start_date="2024Q1", end_date="2024Q1")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert df["value"].iloc[0] == 1.3

    @responses.activate
    def test_get_gdp_growth_rate_annual(self):
        """연간 GDP 성장률 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "902Y015",
                        "TIME": "2023",
                        "DATA_VALUE": "1.4",
                        "UNIT_NAME": "%",
                    }
                ]
            }
        }

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        df = get_gdp_growth_rate(frequency="annual", start_date="2023", end_date="2023")

        assert not df.empty
        assert df["value"].iloc[0] == 1.4


def _multi_item_mock(items: list[tuple[str, str, str]], unit: str) -> dict:
    """다항목 통계표 응답 모킹 — partial-coverage 재설계(#59) 검증용.

    items: (item_code1, item_name1, data_value) 튜플 목록. 2개 시점(2024Q1/Q2)으로 전개.
    """
    rows = []
    for time in ["2024Q1", "2024Q2"]:
        for code, name, value in items:
            rows.append(
                {
                    "ITEM_CODE1": code,
                    "ITEM_NAME1": name,
                    "TIME": time,
                    "DATA_VALUE": value,
                    "UNIT_NAME": unit,
                }
            )
    return {"StatisticSearch": {"row": rows}}


_INDUSTRY_ITEMS = [
    ("1101", "농림어업", "30"),
    ("1201", "제조업", "500"),
    ("1301", "서비스업", "900"),
]
_EXPENDITURE_ITEMS = [
    ("10601", "민간소비지출", "350"),
    ("10701", "정부소비지출", "120"),
    ("10801", "총고정자본형성", "400"),
]


@pytest.mark.usefixtures("set_api_key")
class TestGetGdpByIndustry:
    """get_gdp_by_industry 재설계 테스트 (#59)."""

    def _add_mock(self):
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_multi_item_mock(_INDUSTRY_ITEMS, "십억원"),
            status=200,
        )

    @responses.activate
    def test_default_returns_full_series_long_format(self):
        """sub_category 미지정 시 전체 산업을 long-format으로 반환한다."""
        self._add_mock()
        df = get_gdp_by_industry(
            basis="real",
            seasonal_adj=True,
            frequency="quarterly",
            start_date="2024Q1",
            end_date="2024Q2",
        )
        assert list(df.columns) == ["date", "category_value", "value", "unit"]
        assert set(df["category_value"]) == {"농림어업", "제조업", "서비스업"}
        assert len(df) == 6  # 3항목 × 2분기

    @responses.activate
    def test_sub_category_returns_single_series(self):
        """sub_category 지정 시 해당 산업 단일 시계열만 반환한다."""
        self._add_mock()
        df = get_gdp_by_industry(sub_category="제조업", start_date="2024Q1", end_date="2024Q2")
        assert list(df.columns) == ["date", "value", "unit"]
        assert len(df) == 2
        assert (df["value"] == 500.0).all()

    @responses.activate
    def test_sub_category_accepts_item_code(self):
        """sub_category로 item_code1도 허용한다."""
        self._add_mock()
        df = get_gdp_by_industry(sub_category="1101", start_date="2024Q1", end_date="2024Q2")
        assert (df["value"] == 30.0).all()

    @responses.activate
    def test_unknown_sub_category_raises_with_available(self):
        """존재하지 않는 sub_category는 사용 가능한 항목과 함께 ValueError."""
        self._add_mock()
        with pytest.raises(ValueError, match="사용 가능한 항목"):
            get_gdp_by_industry(sub_category="없는산업", start_date="2024Q1", end_date="2024Q2")

    @responses.activate
    def test_emits_no_warning(self):
        """재설계 후 어떤 경고도 발생시키지 않는다 (partial-coverage 경고 제거, #64)."""
        self._add_mock()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            get_gdp_by_industry(start_date="2024Q1", end_date="2024Q2")

    def test_invalid_seasonal_adj_annual(self):
        """계절조정=True + 연간 조합은 ValueError"""
        with pytest.raises(ValueError, match="seasonal_adj=True"):
            get_gdp_by_industry(basis="real", seasonal_adj=True, frequency="annual")


@pytest.mark.usefixtures("set_api_key")
class TestGetGdpByExpenditure:
    """get_gdp_by_expenditure 재설계 테스트 (#59)."""

    def _add_mock(self):
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_multi_item_mock(_EXPENDITURE_ITEMS, "십억원"),
            status=200,
        )

    @responses.activate
    def test_default_returns_full_series_long_format(self):
        """sub_category 미지정 시 전체 지출항목을 long-format으로 반환한다."""
        self._add_mock()
        df = get_gdp_by_expenditure(
            basis="real", frequency="quarterly", start_date="2024Q1", end_date="2024Q2"
        )
        assert list(df.columns) == ["date", "category_value", "value", "unit"]
        assert set(df["category_value"]) == {"민간소비지출", "정부소비지출", "총고정자본형성"}
        assert len(df) == 6

    @responses.activate
    def test_sub_category_returns_single_series(self):
        """sub_category 지정 시 해당 항목 단일 시계열만 반환한다."""
        self._add_mock()
        df = get_gdp_by_expenditure(
            sub_category="민간소비지출", start_date="2024Q1", end_date="2024Q2"
        )
        assert list(df.columns) == ["date", "value", "unit"]
        assert (df["value"] == 350.0).all()

    @responses.activate
    def test_unknown_sub_category_raises_with_available(self):
        """존재하지 않는 sub_category는 사용 가능한 항목과 함께 ValueError."""
        self._add_mock()
        with pytest.raises(ValueError, match="사용 가능한 항목"):
            get_gdp_by_expenditure(sub_category="없는항목", start_date="2024Q1", end_date="2024Q2")


@pytest.mark.usefixtures("set_api_key")
class TestGetGdpDeflatorByIndustry:
    """get_gdp_deflator_by_industry 재설계 테스트 (#59)."""

    _DEFLATOR_ITEMS: ClassVar = [
        ("1101", "농림어업", "108.0"),
        ("1201", "제조업", "115.2"),
        ("1301", "서비스업", "121.5"),
    ]

    def _add_mock(self):
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_multi_item_mock(self._DEFLATOR_ITEMS, "2015=100"),
            status=200,
        )

    @responses.activate
    def test_default_returns_full_series_long_format(self):
        """sub_category 미지정 시 전체 산업을 long-format으로 반환한다."""
        self._add_mock()
        df = get_gdp_deflator_by_industry(
            frequency="quarterly", start_date="2024Q1", end_date="2024Q2"
        )
        assert list(df.columns) == ["date", "category_value", "value", "unit"]
        assert set(df["category_value"]) == {"농림어업", "제조업", "서비스업"}
        assert len(df) == 6

    @responses.activate
    def test_sub_category_returns_single_series(self):
        """sub_category 지정 시 해당 산업 단일 시계열만 반환한다."""
        self._add_mock()
        df = get_gdp_deflator_by_industry(
            sub_category="제조업", start_date="2024Q1", end_date="2024Q2"
        )
        assert list(df.columns) == ["date", "value", "unit"]
        assert (df["value"] == 115.2).all()

    @responses.activate
    def test_unknown_sub_category_raises_with_available(self):
        """존재하지 않는 sub_category는 사용 가능한 항목과 함께 ValueError."""
        self._add_mock()
        with pytest.raises(ValueError, match="사용 가능한 항목"):
            get_gdp_deflator_by_industry(
                sub_category="없는산업", start_date="2024Q1", end_date="2024Q2"
            )
