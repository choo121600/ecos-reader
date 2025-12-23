"""
금리 지표 모듈 테스트
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.interest_rate import (
    get_base_rate,
    get_treasury_yield,
    get_yield_spread,
)


@pytest.mark.usefixtures("set_api_key")
class TestGetBaseRate:
    """get_base_rate 함수 테스트"""

    @responses.activate
    def test_get_base_rate_success(self, mock_base_rate_response):
        """기준금리 조회 성공"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_base_rate_response,
            status=200,
        )

        df = get_base_rate(start_date="202401", end_date="202402")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert df["value"].iloc[0] == 3.50

    @responses.activate
    def test_get_base_rate_default_dates(self, mock_base_rate_response):
        """기본 날짜 범위로 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_base_rate_response,
            status=200,
        )

        # 날짜 미지정 시 기본값 사용
        df = get_base_rate()
        assert not df.empty


@pytest.mark.usefixtures("set_api_key")
class TestGetTreasuryYield:
    """get_treasury_yield 함수 테스트"""

    @responses.activate
    def test_get_treasury_yield_3y(self):
        """국고채 3년물 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "817Y002",
                        "TIME": "20240101",
                        "DATA_VALUE": "3.20",
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

        df = get_treasury_yield(maturity="3Y", start_date="20240101", end_date="20240131")
        assert not df.empty
        assert df["value"].iloc[0] == 3.20

    def test_invalid_maturity_raises(self):
        """잘못된 만기 지정 시 에러"""
        with pytest.raises(ValueError):
            get_treasury_yield(maturity="2Y")  # type: ignore


@pytest.mark.usefixtures("set_api_key")
class TestGetYieldSpread:
    """get_yield_spread 함수 테스트"""

    @responses.activate
    def test_get_yield_spread(self):
        """장단기 금리차 계산"""
        # 10년물 응답
        mock_10y = {
            "StatisticSearch": {
                "row": [
                    {"TIME": "20240101", "DATA_VALUE": "3.50", "UNIT_NAME": "%"},
                    {"TIME": "20240102", "DATA_VALUE": "3.52", "UNIT_NAME": "%"},
                ]
            }
        }

        # 3년물 응답
        mock_3y = {
            "StatisticSearch": {
                "row": [
                    {"TIME": "20240101", "DATA_VALUE": "3.20", "UNIT_NAME": "%"},
                    {"TIME": "20240102", "DATA_VALUE": "3.22", "UNIT_NAME": "%"},
                ]
            }
        }

        responses.add(responses.GET, url=re.compile(r".*"), json=mock_10y, status=200)
        responses.add(responses.GET, url=re.compile(r".*"), json=mock_3y, status=200)

        df = get_yield_spread(start_date="20240101", end_date="20240102")

        assert not df.empty
        assert "spread" in df.columns
        assert "long_yield" in df.columns
        assert "short_yield" in df.columns

        # 스프레드 계산 확인 (3.50 - 3.20 = 0.30)
        assert abs(df["spread"].iloc[0] - 0.30) < 0.01
