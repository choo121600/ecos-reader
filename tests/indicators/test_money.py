"""
통화 지표 모듈 테스트
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.money import get_bank_lending, get_money_supply


@pytest.mark.usefixtures("set_api_key")
class TestGetMoneySupply:
    """get_money_supply 함수 테스트"""

    @responses.activate
    def test_get_money_supply_m2(self):
        """M2 통화량 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "101Y018",
                        "TIME": "202401",
                        "DATA_VALUE": "3800000",
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

        df = get_money_supply(indicator="M2", start_date="202401", end_date="202401")
        assert not df.empty
        assert df["value"].iloc[0] == 3800000

    @responses.activate
    def test_get_money_supply_m1(self):
        """M1 통화량 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "101Y018",
                        "TIME": "202401",
                        "DATA_VALUE": "1200000",
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

        df = get_money_supply(indicator="M1", start_date="202401", end_date="202401")
        assert not df.empty

    def test_invalid_indicator_raises(self):
        """잘못된 지표 지정 시 에러"""
        with pytest.raises(ValueError):
            get_money_supply(indicator="M3")  # type: ignore


@pytest.mark.usefixtures("set_api_key")
class TestGetBankLending:
    """get_bank_lending 함수 테스트"""

    @responses.activate
    def test_get_bank_lending_all(self):
        """전체 대출 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "104Y016",
                        "TIME": "202401",
                        "DATA_VALUE": "2500000",
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

        df = get_bank_lending(sector="all", start_date="202401", end_date="202401")
        assert not df.empty

    @responses.activate
    def test_get_bank_lending_household(self):
        """가계대출 조회"""
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "104Y016",
                        "TIME": "202401",
                        "DATA_VALUE": "1100000",
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

        df = get_bank_lending(sector="household", start_date="202401", end_date="202401")
        assert not df.empty

    def test_invalid_sector_raises(self):
        """잘못된 부문 지정 시 에러"""
        with pytest.raises(ValueError):
            get_bank_lending(sector="government")  # type: ignore
