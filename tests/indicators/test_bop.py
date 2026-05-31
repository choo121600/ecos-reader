"""
국제수지(BoP) 지표 모듈 테스트 (#107)
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.bop import get_balance_of_payments


def _bop_response(item_code: str = "000000", item_name: str = "경상수지"):
    return {
        "StatisticSearch": {
            "row": [
                {
                    "STAT_CODE": "301Y013",
                    "ITEM_CODE1": item_code,
                    "ITEM_NAME1": item_name,
                    "TIME": "202401",
                    "DATA_VALUE": "3045.6",
                    "UNIT_NAME": "백만달러",
                },
                {
                    "STAT_CODE": "301Y013",
                    "ITEM_CODE1": item_code,
                    "ITEM_NAME1": item_name,
                    "TIME": "202402",
                    "DATA_VALUE": "-1200.1",
                    "UNIT_NAME": "백만달러",
                },
            ]
        }
    }


@pytest.mark.usefixtures("set_api_key")
class TestGetBalanceOfPayments:
    @responses.activate
    def test_success_normalized_columns(self):
        responses.add(responses.GET, re.compile(r".*"), json=_bop_response(), status=200)
        df = get_balance_of_payments("current", start_date="202401", end_date="202402")
        assert df.columns.tolist() == ["date", "value", "unit"]
        assert df["unit"].iloc[0] == "백만달러"
        # 적자(음수)도 그대로 보존
        assert (df["value"] < 0).any()

    @responses.activate
    @pytest.mark.parametrize(
        ("account", "item_code"),
        [("current", "000000"), ("capital", "BOPC00000000"), ("financial", "BOPF00000000")],
    )
    def test_account_maps_to_item_code(self, account, item_code):
        responses.add(responses.GET, re.compile(r".*"), json=_bop_response(item_code), status=200)
        get_balance_of_payments(account, start_date="202401", end_date="202402")
        assert item_code in responses.calls[0].request.url

    @responses.activate
    @pytest.mark.parametrize(
        ("frequency", "marker"),
        [("monthly", "/M/"), ("quarterly", "/Q/"), ("annual", "/A/")],
    )
    def test_frequency_maps_to_period(self, frequency, marker):
        responses.add(responses.GET, re.compile(r".*"), json=_bop_response(), status=200)
        get_balance_of_payments("current", start_date="2020", end_date="2024", frequency=frequency)
        assert marker in responses.calls[0].request.url

    @responses.activate
    def test_default_dates_applied(self):
        responses.add(responses.GET, re.compile(r".*"), json=_bop_response(), status=200)
        assert not get_balance_of_payments("current").empty

    def test_invalid_account_raises(self):
        with pytest.raises(ValueError, match="account"):
            get_balance_of_payments("trade", start_date="202401", end_date="202402")

    def test_invalid_frequency_raises(self):
        with pytest.raises(ValueError, match="frequency"):
            get_balance_of_payments("current", frequency="daily")

    def test_public_export(self):
        import ecos

        assert hasattr(ecos, "get_balance_of_payments")
        assert "get_balance_of_payments" in ecos.__all__
