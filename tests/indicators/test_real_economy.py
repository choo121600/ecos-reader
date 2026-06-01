"""
실물경기 지표(산업생산/설비투자) 모듈 테스트 (#109)
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.real_economy import (
    get_composite_index,
    get_facility_investment,
    get_industrial_production,
    get_retail_sales,
)


def _index_response(stat_code: str):
    return {
        "StatisticSearch": {
            "row": [
                {
                    "STAT_CODE": stat_code,
                    "TIME": "202401",
                    "DATA_VALUE": "110.5",
                    "UNIT_NAME": "2020=100",
                },
                {
                    "STAT_CODE": stat_code,
                    "TIME": "202402",
                    "DATA_VALUE": "113.7",
                    "UNIT_NAME": "2020=100",
                },
            ]
        }
    }


@pytest.mark.usefixtures("set_api_key")
class TestGetIndustrialProduction:
    @responses.activate
    def test_success_columns(self):
        responses.add(responses.GET, re.compile(r".*"), json=_index_response("901Y033"), status=200)
        df = get_industrial_production(start_date="202401", end_date="202402")
        assert df.columns.tolist() == ["date", "value", "unit"]
        assert df["value"].iloc[0] == 110.5

    @responses.activate
    def test_original_series_axis(self):
        responses.add(responses.GET, re.compile(r".*"), json=_index_response("901Y033"), status=200)
        get_industrial_production(start_date="202401", end_date="202402")
        url = responses.calls[0].request.url
        # 901Y033 + A00(item_code1) + 원계열(item_code2='1') + 월
        assert "901Y033" in url
        assert "A00" in url
        assert url.rstrip("/").endswith("/1")  # item_code2=1 (원계열)
        assert "/M/" in url

    @responses.activate
    def test_seasonal_series_axis(self):
        responses.add(responses.GET, re.compile(r".*"), json=_index_response("901Y033"), status=200)
        get_industrial_production(start_date="202401", end_date="202402", seasonal=True)
        # 계절조정(item_code2='2')
        assert responses.calls[0].request.url.rstrip("/").endswith("/2")

    @responses.activate
    def test_default_dates(self):
        responses.add(responses.GET, re.compile(r".*"), json=_index_response("901Y033"), status=200)
        assert not get_industrial_production().empty


@pytest.mark.usefixtures("set_api_key")
class TestGetFacilityInvestment:
    @responses.activate
    def test_success_columns(self):
        responses.add(responses.GET, re.compile(r".*"), json=_index_response("901Y066"), status=200)
        df = get_facility_investment(start_date="202401", end_date="202402")
        assert df.columns.tolist() == ["date", "value", "unit"]

    @responses.activate
    def test_original_vs_seasonal_item(self):
        responses.add(responses.GET, re.compile(r".*"), json=_index_response("901Y066"), status=200)
        get_facility_investment(start_date="202401", end_date="202402")
        assert "I15A" in responses.calls[0].request.url  # 원지수

    @responses.activate
    def test_seasonal_item(self):
        responses.add(responses.GET, re.compile(r".*"), json=_index_response("901Y066"), status=200)
        get_facility_investment(start_date="202401", end_date="202402", seasonal=True)
        assert "I15B" in responses.calls[0].request.url  # 계절조정지수


@pytest.mark.usefixtures("set_api_key")
class TestGetCompositeIndex:
    @responses.activate
    def test_success_columns(self):
        responses.add(responses.GET, re.compile(r".*"), json=_index_response("901Y067"), status=200)
        df = get_composite_index("coincident", start_date="202401", end_date="202402")
        assert df.columns.tolist() == ["date", "value", "unit"]

    @responses.activate
    @pytest.mark.parametrize(
        ("index", "item_code"),
        [("leading", "I16A"), ("coincident", "I16B"), ("lagging", "I16C")],
    )
    def test_index_maps_to_item(self, index, item_code):
        responses.add(responses.GET, re.compile(r".*"), json=_index_response("901Y067"), status=200)
        get_composite_index(index, start_date="202401", end_date="202402")
        url = responses.calls[0].request.url
        assert "901Y067" in url
        assert item_code in url
        assert "/M/" in url

    @responses.activate
    def test_default_dates(self):
        responses.add(responses.GET, re.compile(r".*"), json=_index_response("901Y067"), status=200)
        assert not get_composite_index().empty

    def test_invalid_index_raises(self):
        with pytest.raises(ValueError, match="index"):
            get_composite_index("trailing", start_date="202401", end_date="202402")


def _retail_mock() -> dict:
    """901Y100: 상품군(item_code1) × 계열(item_code2 T1/T2/T3) 2축 응답 모킹 (#150)."""
    cats = [("G0", "총지수"), ("G1", "내구재"), ("G31", "음식료품")]
    series = [("T1", "경상지수", 100), ("T2", "불변지수", 200), ("T3", "계절조정지수", 300)]
    rows = []
    for time in ["202401", "202402"]:
        for c1, n1 in cats:
            for c2, n2, base in series:
                rows.append(
                    {
                        "ITEM_CODE1": c1,
                        "ITEM_NAME1": n1,
                        "ITEM_CODE2": c2,
                        "ITEM_NAME2": n2,
                        "TIME": time,
                        "DATA_VALUE": str(base + int(c1[1:] or 0)),
                        "UNIT_NAME": "2020=100",
                    }
                )
    return {"StatisticSearch": {"row": rows}}


@pytest.mark.usefixtures("set_api_key")
class TestGetRetailSales:
    def _add_mock(self):
        responses.add(responses.GET, re.compile(r".*"), json=_retail_mock(), status=200)

    @responses.activate
    def test_default_long_format_all_categories(self):
        """sub_category 미지정 시 전체 상품군 long-format (#150)."""
        self._add_mock()
        df = get_retail_sales(start_date="202401", end_date="202402")
        assert df.columns.tolist() == ["date", "category_value", "value", "unit"]
        assert {"총지수", "내구재", "음식료품"} <= set(df["category_value"])

    @responses.activate
    def test_sub_category_single_series(self):
        """sub_category 지정 시 해당 상품군 단일 시계열."""
        self._add_mock()
        df = get_retail_sales(sub_category="음식료품", start_date="202401", end_date="202402")
        assert df.columns.tolist() == ["date", "value", "unit"]
        # 음식료품(G31) × 불변지수(T2, base 200) → 200+31
        assert (df["value"] == 231).all()

    @responses.activate
    def test_index_filters_series_axis_client_side(self):
        """index(계열)는 item_code2로 client-side 필터; 경상(T1, base100)."""
        self._add_mock()
        df = get_retail_sales(
            "nominal", sub_category="총지수", start_date="202401", end_date="202402"
        )
        assert (df["value"] == 100).all()  # G0(0) + T1(100)

    @responses.activate
    def test_sub_category_by_item_code(self):
        self._add_mock()
        df = get_retail_sales(sub_category="G1", start_date="202401", end_date="202402")
        assert (df["value"] == 201).all()  # G1(1) + T2(200)

    @responses.activate
    @pytest.mark.parametrize(("frequency", "marker"), [("monthly", "/M/"), ("annual", "/A/")])
    def test_frequency_maps_to_period(self, frequency, marker):
        self._add_mock()
        get_retail_sales(start_date="2020", end_date="2024", frequency=frequency)
        assert marker in responses.calls[0].request.url

    @responses.activate
    def test_unknown_sub_category_raises(self):
        self._add_mock()
        with pytest.raises(ValueError, match="사용 가능한 항목"):
            get_retail_sales(sub_category="없는상품군", start_date="202401", end_date="202402")

    def test_invalid_index_raises(self):
        with pytest.raises(ValueError, match="index"):
            get_retail_sales("constant", start_date="202401", end_date="202402")


def test_public_exports():
    import ecos

    for name in (
        "get_industrial_production",
        "get_facility_investment",
        "get_composite_index",
        "get_retail_sales",
    ):
        assert hasattr(ecos, name)
        assert name in ecos.__all__
