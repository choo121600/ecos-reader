"""
심리 지표(BSI/CSI) 모듈 테스트 (#108)
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.sentiment import get_business_sentiment, get_consumer_sentiment


def _index_response(stat_code: str, item_code1: str, item_name1: str):
    return {
        "StatisticSearch": {
            "row": [
                {
                    "STAT_CODE": stat_code,
                    "ITEM_CODE1": item_code1,
                    "ITEM_NAME1": item_name1,
                    "TIME": "202401",
                    "DATA_VALUE": "92.3",
                    "UNIT_NAME": "",
                },
                {
                    "STAT_CODE": stat_code,
                    "ITEM_CODE1": item_code1,
                    "ITEM_NAME1": item_name1,
                    "TIME": "202402",
                    "DATA_VALUE": "95.1",
                    "UNIT_NAME": "",
                },
            ]
        }
    }


@pytest.mark.usefixtures("set_api_key")
class TestGetBusinessSentiment:
    @responses.activate
    def test_success_columns_and_value(self):
        responses.add(
            responses.GET,
            re.compile(r".*"),
            json=_index_response("512Y014", "99988", "전산업"),
            status=200,
        )
        df = get_business_sentiment("all", start_date="202401", end_date="202402")
        assert "date" in df.columns
        assert "value" in df.columns
        assert df["value"].iloc[0] == 92.3

    @responses.activate
    @pytest.mark.parametrize(
        ("sector", "item_code1"),
        [("manufacturing", "C0000"), ("non_manufacturing", "Y9900"), ("all", "99988")],
    )
    def test_sector_and_outlook_axis(self, sector, item_code1):
        responses.add(
            responses.GET,
            re.compile(r".*"),
            json=_index_response("512Y014", item_code1, "x"),
            status=200,
        )
        get_business_sentiment(sector, start_date="202401", end_date="202402")
        url = responses.calls[0].request.url
        # 업종(item_code1) + 업황전망BSI(item_code2=BA) 2-축이 URL에 반영됨
        assert item_code1 in url
        assert "BA" in url
        assert "/M/" in url

    @responses.activate
    def test_default_dates(self):
        responses.add(
            responses.GET,
            re.compile(r".*"),
            json=_index_response("512Y014", "99988", "전산업"),
            status=200,
        )
        assert not get_business_sentiment().empty

    def test_invalid_sector_raises(self):
        with pytest.raises(ValueError, match="sector"):
            get_business_sentiment("financial", start_date="202401", end_date="202402")


@pytest.mark.usefixtures("set_api_key")
class TestGetConsumerSentiment:
    @responses.activate
    def test_success(self):
        responses.add(
            responses.GET,
            re.compile(r".*"),
            json=_index_response("511Y002", "FME", "소비자심리지수"),
            status=200,
        )
        df = get_consumer_sentiment(start_date="202401", end_date="202402")
        assert "value" in df.columns
        assert df["value"].iloc[0] == 92.3

    @responses.activate
    def test_uses_csi_codes(self):
        responses.add(
            responses.GET,
            re.compile(r".*"),
            json=_index_response("511Y002", "FME", "소비자심리지수"),
            status=200,
        )
        get_consumer_sentiment(start_date="202401", end_date="202402")
        url = responses.calls[0].request.url
        assert "511Y002" in url
        assert "FME" in url
        assert "/M/" in url


def test_public_exports():
    import ecos

    for name in ("get_business_sentiment", "get_consumer_sentiment"):
        assert hasattr(ecos, name)
        assert name in ecos.__all__
