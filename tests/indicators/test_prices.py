"""
물가 지표 모듈 테스트
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.prices import get_core_cpi, get_cpi, get_ppi


@pytest.mark.usefixtures("set_api_key")
class TestGetCpi:
    """get_cpi 함수 테스트"""

    @responses.activate
    def test_get_cpi_success(self, mock_cpi_response):
        """CPI 조회 성공"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_cpi_response,
            status=200,
        )

        df = get_cpi(start_date="202401", end_date="202402")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert df["value"].iloc[0] == 3.20


@pytest.mark.usefixtures("set_api_key")
class TestGetCoreCpi:
    """get_core_cpi 함수 테스트"""

    @responses.activate
    def test_get_core_cpi_success(self):
        """근원 CPI 조회 성공"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "901Y010",
                        "TIME": "202401",
                        "DATA_VALUE": "2.80",
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

        df = get_core_cpi(start_date="202401", end_date="202401")
        assert not df.empty
        assert df["value"].iloc[0] == 2.80


@pytest.mark.usefixtures("set_api_key")
class TestGetPpi:
    """get_ppi 함수 테스트"""

    @responses.activate
    def test_get_ppi_success(self):
        """PPI 조회 성공"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "404Y014",
                        "TIME": "202401",
                        "DATA_VALUE": "1.50",
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

        df = get_ppi(start_date="202401", end_date="202401")
        assert not df.empty
        assert df["value"].iloc[0] == 1.50
