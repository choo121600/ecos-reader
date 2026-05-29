"""주식시장 지표 모듈 단위 테스트 (#13).

`get_stock_index`(daily/monthly)와 `get_investor_trading`을 mock 응답으로
검증한다 (ECOS_API_KEY 불필요). monthly/investor_trading은
EcosPartialCoverageWarning을 발생시키므로 함께 검증한다.
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators._deprecations import EcosPartialCoverageWarning
from ecos.indicators.stock import get_investor_trading, get_stock_index


def _mock(value: str, unit: str = "포인트", stat_code: str = "802Y001") -> dict:
    return {
        "StatisticSearch": {
            "row": [
                {"STAT_CODE": stat_code, "TIME": "20240102", "DATA_VALUE": value, "UNIT_NAME": unit}
            ]
        }
    }


@pytest.mark.usefixtures("set_api_key")
class TestGetStockIndex:
    """get_stock_index 함수 테스트"""

    @responses.activate
    def test_daily_success(self):
        """일별 주가지수 조회 성공 (경고 없음)"""
        responses.add(responses.GET, url=re.compile(r".*"), json=_mock("2655.28"), status=200)

        df = get_stock_index(frequency="daily", start_date="20240102", end_date="20240102")

        assert not df.empty
        assert {"date", "value", "unit"} <= set(df.columns)
        assert df["value"].iloc[0] == 2655.28

    @responses.activate
    def test_monthly_success_warns_partial_coverage(self):
        """월별 조회는 부분커버리지 경고를 발생시킨다"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_mock("783", unit="개", stat_code="802Y002"),
            status=200,
        )

        with pytest.warns(EcosPartialCoverageWarning):
            df = get_stock_index(frequency="monthly", start_date="202401", end_date="202401")

        assert not df.empty
        assert df["value"].iloc[0] == 783

    def test_invalid_frequency_raises(self):
        """허용되지 않은 frequency는 ValueError"""
        with pytest.raises(ValueError, match="frequency"):
            get_stock_index(frequency="weekly")


@pytest.mark.usefixtures("set_api_key")
class TestGetInvestorTrading:
    """get_investor_trading 함수 테스트"""

    @responses.activate
    def test_success_warns_partial_coverage(self):
        """투자자별 거래 조회는 부분커버리지 경고를 발생시킨다"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_mock("1250.50", unit="십억원", stat_code="901Y055"),
            status=200,
        )

        with pytest.warns(EcosPartialCoverageWarning):
            df = get_investor_trading(start_date="202401", end_date="202401")

        assert not df.empty
        assert {"date", "value", "unit"} <= set(df.columns)
        assert df["value"].iloc[0] == 1250.50
