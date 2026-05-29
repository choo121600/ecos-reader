"""
물가 지표 모듈 테스트
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators._deprecations import EcosPartialCoverageWarning
from ecos.indicators.prices import (
    get_core_cpi,
    get_cpi,
    get_cpi_by_category,
    get_cpi_monthly,
    get_ppi,
)


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


@pytest.mark.usefixtures("set_api_key")
class TestGetCpiMonthly:
    """get_cpi_monthly 함수 테스트"""

    @responses.activate
    def test_get_cpi_monthly_success(self):
        """CPI 월별 원지수 조회 성공 및 EcosPartialCoverageWarning 발생 확인"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "901Y009",
                        "STAT_NAME": "소비자물가지수",
                        "ITEM_CODE1": "0",
                        "ITEM_NAME1": "총지수",
                        "TIME": "202401",
                        "DATA_VALUE": "113.52",
                        "UNIT_NAME": "지수",
                    },
                    {
                        "STAT_CODE": "901Y009",
                        "STAT_NAME": "소비자물가지수",
                        "ITEM_CODE1": "0",
                        "ITEM_NAME1": "총지수",
                        "TIME": "202402",
                        "DATA_VALUE": "114.10",
                        "UNIT_NAME": "지수",
                    },
                ]
            }
        }

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        with pytest.warns(EcosPartialCoverageWarning):
            df = get_cpi_monthly(start_date="202401", end_date="202402")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert df["value"].iloc[0] == 113.52


@pytest.mark.usefixtures("set_api_key")
class TestGetCpiByCategory:
    """get_cpi_by_category 함수 테스트"""

    @responses.activate
    def test_get_cpi_by_category_success(self):
        """CPI 카테고리별 조회 성공"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "901Y010",
                        "STAT_NAME": "소비자물가지수 특수분류",
                        "ITEM_CODE1": "DB",
                        "ITEM_NAME1": "식료품및에너지제외지수",
                        "TIME": "202401",
                        "DATA_VALUE": "109.75",
                        "UNIT_NAME": "지수",
                    },
                    {
                        "STAT_CODE": "901Y010",
                        "STAT_NAME": "소비자물가지수 특수분류",
                        "ITEM_CODE1": "DB",
                        "ITEM_NAME1": "식료품및에너지제외지수",
                        "TIME": "202402",
                        "DATA_VALUE": "110.20",
                        "UNIT_NAME": "지수",
                    },
                ]
            }
        }

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        df = get_cpi_by_category(category="식품_에너지제외", start_date="202401", end_date="202402")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert df["value"].iloc[0] == 109.75

    @responses.activate
    def test_get_cpi_by_category_coicop(self):
        """COICOP 계열 카테고리(901Y009) 조회 성공"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "901Y009",
                        "STAT_NAME": "소비자물가지수",
                        "ITEM_CODE1": "G",
                        "ITEM_NAME1": "교통",
                        "TIME": "202401",
                        "DATA_VALUE": "107.30",
                        "UNIT_NAME": "지수",
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

        df = get_cpi_by_category(category="교통", start_date="202401", end_date="202401")

        assert not df.empty
        assert df["value"].iloc[0] == 107.30

    def test_get_cpi_by_category_invalid_category(self):
        """잘못된 category 값에 대해 ValueError 발생"""
        with pytest.raises(ValueError):
            get_cpi_by_category(category="invalid_category")  # type: ignore[arg-type]
