"""
실물경기 지표(산업생산/설비투자) 모듈 테스트 (#109)
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.real_economy import (
    get_facility_investment,
    get_industrial_production,
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


def test_public_exports():
    import ecos

    for name in ("get_industrial_production", "get_facility_investment"):
        assert hasattr(ecos, name)
        assert name in ecos.__all__
