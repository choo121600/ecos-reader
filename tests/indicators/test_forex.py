"""
환율 지표 모듈 테스트 (#106)
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.forex import get_exchange_rate


def _forex_response(item_code: str = "0000001", item_name: str = "원/미국달러(매매기준율)"):
    return {
        "StatisticSearch": {
            "row": [
                {
                    "STAT_CODE": "731Y001",
                    "ITEM_CODE1": item_code,
                    "ITEM_NAME1": item_name,
                    "TIME": "20240102",
                    "DATA_VALUE": "1289.4",
                    "UNIT_NAME": "원",
                },
                {
                    "STAT_CODE": "731Y001",
                    "ITEM_CODE1": item_code,
                    "ITEM_NAME1": item_name,
                    "TIME": "20240103",
                    "DATA_VALUE": "1299.3",
                    "UNIT_NAME": "원",
                },
            ]
        }
    }


@pytest.mark.usefixtures("set_api_key")
class TestGetExchangeRate:
    @responses.activate
    def test_success_normalized_columns(self):
        responses.add(responses.GET, re.compile(r".*"), json=_forex_response(), status=200)
        df = get_exchange_rate("USD", start_date="20240101", end_date="20240110")
        assert not df.empty
        assert df.columns.tolist() == ["date", "value", "unit"]
        assert df["value"].iloc[0] == 1289.4
        assert df["unit"].iloc[0] == "원"

    @responses.activate
    def test_default_currency_is_usd(self):
        responses.add(responses.GET, re.compile(r".*"), json=_forex_response(), status=200)
        get_exchange_rate(start_date="20240101", end_date="20240110")
        # USD item_code(0000001)와 일별(D) 표가 URL에 반영됨
        url = responses.calls[0].request.url
        assert "/D/" in url
        assert "0000001" in url
        assert "731Y001" in url

    @responses.activate
    @pytest.mark.parametrize(
        ("currency", "item_code"),
        [("USD", "0000001"), ("JPY", "0000002"), ("EUR", "0000003"), ("CNY", "0000053")],
    )
    def test_currency_maps_to_item_code(self, currency, item_code):
        responses.add(responses.GET, re.compile(r".*"), json=_forex_response(item_code), status=200)
        get_exchange_rate(currency, start_date="20240101", end_date="20240110")
        assert item_code in responses.calls[0].request.url

    @responses.activate
    def test_default_dates_applied(self):
        responses.add(responses.GET, re.compile(r".*"), json=_forex_response(), status=200)
        df = get_exchange_rate("USD")  # 날짜 미지정 → 기본 1년
        assert not df.empty

    def test_invalid_currency_raises(self):
        with pytest.raises(ValueError, match="currency"):
            get_exchange_rate("GBP", start_date="20240101", end_date="20240110")

    def test_public_export(self):
        import ecos

        assert hasattr(ecos, "get_exchange_rate")
        assert "get_exchange_rate" in ecos.__all__
