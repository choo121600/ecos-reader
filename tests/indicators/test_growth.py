"""
성장 지표 모듈 테스트
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.growth import get_gdp, get_gdp_deflator


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

        df = get_gdp(frequency="Q", start_date="2024Q1", end_date="2024Q2")

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

        df = get_gdp(frequency="A", start_date="2023", end_date="2023")
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

        df = get_gdp(frequency="Q", basis="nominal", start_date="2024Q1", end_date="2024Q1")
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
