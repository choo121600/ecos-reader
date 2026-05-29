"""
성장 지표 모듈 테스트
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators._deprecations import EcosPartialCoverageWarning
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
                        "STAT_CODE": "200Y104",
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

        df = get_gdp_growth_rate(frequency="Q", start_date="2024Q1", end_date="2024Q1")

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
                        "STAT_CODE": "200Y106",
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

        df = get_gdp_growth_rate(frequency="A", start_date="2023", end_date="2023")

        assert not df.empty
        assert df["value"].iloc[0] == 1.4


@pytest.mark.usefixtures("set_api_key")
class TestGetGdpByIndustry:
    """get_gdp_by_industry 함수 테스트"""

    @responses.activate
    def test_get_gdp_by_industry_quarterly(self):
        """분기별 산업별 GDP 조회 (실질, 계절조정)"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "200Y007",
                        "TIME": "2024Q1",
                        "DATA_VALUE": "5000",
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

        with pytest.warns(EcosPartialCoverageWarning):
            df = get_gdp_by_industry(
                basis="real",
                seasonal_adj=True,
                frequency="Q",
                start_date="2024Q1",
                end_date="2024Q1",
            )

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert df["value"].iloc[0] == 5000.0

    @responses.activate
    def test_get_gdp_by_industry_annual_no_seasonal_adj(self):
        """연간 산업별 GDP 조회 (원계열)"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "200Y009",
                        "TIME": "2023",
                        "DATA_VALUE": "20000",
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

        with pytest.warns(EcosPartialCoverageWarning):
            df = get_gdp_by_industry(
                basis="real",
                seasonal_adj=False,
                frequency="A",
                start_date="2023",
                end_date="2023",
            )

        assert not df.empty
        assert df["value"].iloc[0] == 20000.0

    def test_get_gdp_by_industry_invalid_seasonal_adj_annual(self):
        """계절조정=True + 연간 조합은 ValueError"""
        with pytest.raises(ValueError, match="seasonal_adj=True"):
            get_gdp_by_industry(basis="real", seasonal_adj=True, frequency="A")


@pytest.mark.usefixtures("set_api_key")
class TestGetGdpByExpenditure:
    """get_gdp_by_expenditure 함수 테스트"""

    @responses.activate
    def test_get_gdp_by_expenditure_quarterly(self):
        """분기별 지출항목별 GDP 조회 (실질)"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "200Y107",
                        "TIME": "2024Q1",
                        "DATA_VALUE": "350000",
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

        with pytest.warns(EcosPartialCoverageWarning):
            df = get_gdp_by_expenditure(
                basis="real",
                frequency="Q",
                start_date="2024Q1",
                end_date="2024Q1",
            )

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert df["value"].iloc[0] == 350000.0

    @responses.activate
    def test_get_gdp_by_expenditure_annual_nominal(self):
        """연간 지출항목별 GDP 조회 (명목)"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "200Y110",
                        "TIME": "2023",
                        "DATA_VALUE": "1400000",
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

        with pytest.warns(EcosPartialCoverageWarning):
            df = get_gdp_by_expenditure(
                basis="nominal",
                frequency="A",
                start_date="2023",
                end_date="2023",
            )

        assert not df.empty
        assert df["value"].iloc[0] == 1400000.0


@pytest.mark.usefixtures("set_api_key")
class TestGetGdpDeflatorByIndustry:
    """get_gdp_deflator_by_industry 함수 테스트"""

    @responses.activate
    def test_get_gdp_deflator_by_industry_quarterly(self):
        """분기별 산업별 GDP 디플레이터 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "200Y013",
                        "TIME": "2024Q1",
                        "DATA_VALUE": "115.2",
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

        with pytest.warns(EcosPartialCoverageWarning):
            df = get_gdp_deflator_by_industry(
                frequency="Q",
                start_date="2024Q1",
                end_date="2024Q1",
            )

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert df["value"].iloc[0] == 115.2

    @responses.activate
    def test_get_gdp_deflator_by_industry_annual(self):
        """연간 산업별 GDP 디플레이터 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "200Y013",
                        "TIME": "2023",
                        "DATA_VALUE": "112.0",
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

        with pytest.warns(EcosPartialCoverageWarning):
            df = get_gdp_deflator_by_industry(
                frequency="A",
                start_date="2023",
                end_date="2023",
            )

        assert not df.empty
        assert df["value"].iloc[0] == 112.0
