"""
무역 지표(수출입) 모듈 테스트 (#127)
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.trade import get_trade


def _trade_response(item_code: str = "T002", item_name: str = "수출금액"):
    return {
        "StatisticSearch": {
            "row": [
                {
                    "STAT_CODE": "901Y118",
                    "ITEM_CODE1": item_code,
                    "ITEM_NAME1": item_name,
                    "TIME": "202401",
                    "DATA_VALUE": "54000000",
                    "UNIT_NAME": "천불",
                },
                {
                    "STAT_CODE": "901Y118",
                    "ITEM_CODE1": item_code,
                    "ITEM_NAME1": item_name,
                    "TIME": "202402",
                    "DATA_VALUE": "52000000",
                    "UNIT_NAME": "천불",
                },
            ]
        }
    }


@pytest.mark.usefixtures("set_api_key")
class TestGetTrade:
    @responses.activate
    def test_success_columns(self):
        responses.add(responses.GET, re.compile(r".*"), json=_trade_response(), status=200)
        df = get_trade("export", start_date="202401", end_date="202402")
        assert df.columns.tolist() == ["date", "value", "unit"]
        assert df["unit"].iloc[0] == "천불"

    @responses.activate
    @pytest.mark.parametrize(("flow", "item_code"), [("export", "T002"), ("import", "T004")])
    def test_flow_maps_to_item(self, flow, item_code):
        responses.add(responses.GET, re.compile(r".*"), json=_trade_response(item_code), status=200)
        get_trade(flow, start_date="202401", end_date="202402")
        assert item_code in responses.calls[0].request.url

    @responses.activate
    @pytest.mark.parametrize(("frequency", "marker"), [("monthly", "/M/"), ("annual", "/A/")])
    def test_frequency_maps_to_period(self, frequency, marker):
        responses.add(responses.GET, re.compile(r".*"), json=_trade_response(), status=200)
        get_trade("export", start_date="2020", end_date="2024", frequency=frequency)
        assert marker in responses.calls[0].request.url

    @responses.activate
    def test_default_dates(self):
        responses.add(responses.GET, re.compile(r".*"), json=_trade_response(), status=200)
        assert not get_trade().empty

    def test_invalid_flow_raises(self):
        with pytest.raises(ValueError, match="flow"):
            get_trade("balance", start_date="202401", end_date="202402")

    def test_invalid_frequency_raises(self):
        with pytest.raises(ValueError, match="frequency"):
            get_trade("export", frequency="daily")


def test_public_export():
    import ecos

    assert hasattr(ecos, "get_trade")
    assert "get_trade" in ecos.__all__
