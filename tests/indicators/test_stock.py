"""주식시장 지표 모듈 단위 테스트 (#13, #60 재설계).

`get_stock_index`(daily/monthly)와 `get_investor_trading`을 mock 응답으로
검증한다 (ECOS_API_KEY 불필요). #60에서 두 함수 모두 partial-coverage 경고를
제거하고 전체 시리즈/sub_category 선택을 제공하도록 재설계되었다.
"""

from __future__ import annotations

import re
import warnings

import pytest
import responses

from ecos.indicators.stock import get_investor_trading, get_stock_index


def _single_mock(item_code: str, name: str, value: str, unit: str, time: str = "202401") -> dict:
    """단일 항목 응답 (서버측 item_code1 필터를 흉내)."""
    return {
        "StatisticSearch": {
            "row": [
                {
                    "ITEM_CODE1": item_code,
                    "ITEM_NAME1": name,
                    "TIME": time,
                    "DATA_VALUE": value,
                    "UNIT_NAME": unit,
                }
            ]
        }
    }


def _monthly_full_mock() -> dict:
    """월별 주식시장 통계표(901Y014) 다항목 응답."""
    items = [
        ("1010000", "KOSPI_회사수", "783"),
        ("1070000", "KOSPI_종가", "2746.63"),
        ("1040000", "KOSPI_시가총액", "2030032668711"),
    ]
    rows = [
        {"ITEM_CODE1": c, "ITEM_NAME1": n, "TIME": "202401", "DATA_VALUE": v, "UNIT_NAME": "포인트"}
        for c, n, v in items
    ]
    return {"StatisticSearch": {"row": rows}}


def _investor_mock() -> dict:
    """투자자별 거래(901Y055) 2차원 응답 — item_code1=행위×투자자, item_code2=지표."""
    # (item_code1, item_name1, item_code2, item_name2, value)
    data = [
        ("S22C", "순매수 2)", "VA", "거래대금", "0"),  # 합계 — long-format에서 제외돼야
        ("S22CA", "기관투자자(순매수)", "VA", "거래대금", "-6249574"),
        ("S22CB", "개인(순매수)", "VA", "거래대금", "2861123"),
        ("S22CC", "외국인(순매수) 3)", "VA", "거래대금", "3482838"),
        ("S22CA", "기관투자자(순매수)", "VO", "거래량", "-66286"),  # 다른 metric — VA 필터로 제외
        ("S22BA", "기관투자자(매수)", "VO", "거래량", "715731"),
        ("S22BB", "개인(매수)", "VO", "거래량", "9564854"),
    ]
    rows = []
    for time in ["202401", "202402"]:
        for c1, n1, c2, n2, v in data:
            rows.append(
                {
                    "ITEM_CODE1": c1,
                    "ITEM_NAME1": n1,
                    "ITEM_CODE2": c2,
                    "ITEM_NAME2": n2,
                    "TIME": time,
                    "DATA_VALUE": v,
                    "UNIT_NAME": "백만원",
                }
            )
    return {"StatisticSearch": {"row": rows}}


@pytest.mark.usefixtures("set_api_key")
class TestGetStockIndex:
    """get_stock_index 재설계 테스트 (#60)."""

    @responses.activate
    def test_daily_returns_kospi_index(self):
        """일별 기본값은 KOSPI 지수를 반환한다 (경고 없음)."""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_single_mock("0001000", "KOSPI지수", "2655.28", "포인트", time="20240102"),
            status=200,
        )
        df = get_stock_index(frequency="daily", start_date="20240102", end_date="20240102")
        assert {"date", "value", "unit"} <= set(df.columns)
        assert df["value"].iloc[0] == 2655.28

    @responses.activate
    def test_monthly_returns_kospi_index_not_company_count(self):
        """월별 기본값은 KOSPI 종가(지수)를 반환한다 (1010000 회사수가 아님, #60 정정)."""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_single_mock("1070000", "KOSPI_종가", "2746.63", "1980.01.04=100"),
            status=200,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # 재설계 후 경고 없음 (#60/#64)
            df = get_stock_index(frequency="monthly", start_date="202401", end_date="202401")
        assert df["value"].iloc[0] == 2746.63

    @responses.activate
    def test_monthly_sub_category_selects_item(self):
        """sub_category로 월별 통계표의 다른 항목을 선택한다."""
        responses.add(responses.GET, url=re.compile(r".*"), json=_monthly_full_mock(), status=200)
        df = get_stock_index(
            frequency="monthly",
            sub_category="KOSPI_시가총액",
            start_date="202401",
            end_date="202401",
        )
        assert list(df.columns) == ["date", "value", "unit"]
        assert df["value"].iloc[0] == 2030032668711

    @responses.activate
    def test_monthly_unknown_sub_category_raises(self):
        """없는 sub_category는 사용 가능한 항목과 함께 ValueError."""
        responses.add(responses.GET, url=re.compile(r".*"), json=_monthly_full_mock(), status=200)
        with pytest.raises(ValueError, match="사용 가능한 항목"):
            get_stock_index(
                frequency="monthly", sub_category="없는항목", start_date="202401", end_date="202401"
            )

    def test_invalid_frequency_raises(self):
        """허용되지 않은 frequency는 ValueError"""
        with pytest.raises(ValueError, match="frequency"):
            get_stock_index(frequency="weekly")


@pytest.mark.usefixtures("set_api_key")
class TestGetInvestorTrading:
    """get_investor_trading 재설계 테스트 (#60)."""

    def _add_mock(self):
        responses.add(responses.GET, url=re.compile(r".*"), json=_investor_mock(), status=200)

    @responses.activate
    def test_default_net_buy_value_long_format(self):
        """기본값(순매수·거래대금)은 투자자별 long-format을 반환하며 합계행은 제외한다."""
        self._add_mock()
        df = get_investor_trading(start_date="202401", end_date="202402")
        assert list(df.columns) == ["date", "category_value", "value", "unit"]
        assert set(df["category_value"]) == {
            "기관투자자(순매수)",
            "개인(순매수)",
            "외국인(순매수) 3)",
        }
        assert "순매수 2)" not in set(df["category_value"])  # 합계행 제외
        assert len(df) == 6  # 3투자자 × 2개월

    @responses.activate
    def test_sub_category_by_item_code(self):
        """sub_category(item_code)로 단일 투자자 시계열을 반환한다."""
        self._add_mock()
        df = get_investor_trading(sub_category="S22CC", start_date="202401", end_date="202402")
        assert list(df.columns) == ["date", "value", "unit"]
        assert (df["value"] == 3482838).all()

    @responses.activate
    def test_action_and_metric_filter(self):
        """action=매수, metric=거래량은 매수 거래량 투자자별 시리즈를 반환한다."""
        self._add_mock()
        df = get_investor_trading(
            action="매수", metric="거래량", start_date="202401", end_date="202401"
        )
        assert set(df["category_value"]) == {"기관투자자(매수)", "개인(매수)"}

    @responses.activate
    def test_unknown_sub_category_raises(self):
        """없는 sub_category는 사용 가능한 항목과 함께 ValueError."""
        self._add_mock()
        with pytest.raises(ValueError, match="사용 가능한 항목"):
            get_investor_trading(sub_category="S99XX", start_date="202401", end_date="202401")

    def test_invalid_action_raises(self):
        with pytest.raises(ValueError, match="action"):
            get_investor_trading(action="없음")  # type: ignore[arg-type]

    def test_invalid_metric_raises(self):
        with pytest.raises(ValueError, match="metric"):
            get_investor_trading(metric="없음")  # type: ignore[arg-type]

    @responses.activate
    @pytest.mark.parametrize(("frequency", "marker"), [("monthly", "/M/"), ("annual", "/A/")])
    def test_frequency_maps_to_period(self, frequency, marker):
        self._add_mock()
        get_investor_trading(start_date="2020", end_date="2024", frequency=frequency)
        assert marker in responses.calls[0].request.url

    def test_quarterly_frequency_raises(self):
        """이 통계표는 분기 자료를 제공하지 않으므로 quarterly는 ValueError."""
        with pytest.raises(ValueError, match="frequency"):
            get_investor_trading(frequency="quarterly")  # type: ignore[arg-type]

    @responses.activate
    def test_emits_no_warning(self):
        """재설계 후 어떤 경고도 발생시키지 않는다 (partial-coverage 경고 제거, #64)."""
        self._add_mock()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            get_investor_trading(start_date="202401", end_date="202401")
