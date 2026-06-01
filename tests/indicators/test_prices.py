"""
물가 지표 모듈 테스트
"""

from __future__ import annotations

import re
import warnings

import pytest
import responses

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
        assert df["value"].iloc[0] == 113.52  # 지수(2020=100), 전년동월비 아님 (#136)
        assert df["unit"].iloc[0] == "2020=100"

    @responses.activate
    def test_measure_yoy_computes_change_and_trims(self):
        """measure='yoy'는 전년동월비(%)를 계산하고 확장분을 잘라낸다 (#139)."""
        # 202301~202402 14개월 지수 (100,101,...,113)
        rows = []
        for i in range(14):
            ym = f"2023{i + 1:02d}" if i < 12 else f"2024{i - 11:02d}"
            rows.append(
                {"ITEM_CODE1": "0", "TIME": ym, "DATA_VALUE": str(100 + i), "UNIT_NAME": "2020=100"}
            )
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json={"StatisticSearch": {"row": rows}},
            status=200,
        )
        df = get_cpi(start_date="202401", end_date="202402", measure="yoy")
        # 요청 구간(202401~202402)만, 확장분(2023..)은 제거
        assert df["date"].min().strftime("%Y%m") == "202401"
        assert df["unit"].iloc[0] == "%"
        # 202401(value 112) vs 202301(value 100) = +12.0%
        assert df["value"].iloc[0] == 12.0

    @responses.activate
    def test_measure_mom_unit_is_percent(self):
        """measure='mom'는 전월비(%)를 반환한다."""
        rows = [
            {
                "ITEM_CODE1": "0",
                "TIME": f"2024{m:02d}",
                "DATA_VALUE": str(100 + m),
                "UNIT_NAME": "2020=100",
            }
            for m in range(1, 5)
        ]
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json={"StatisticSearch": {"row": rows}},
            status=200,
        )
        df = get_cpi(start_date="202402", end_date="202404", measure="mom")
        assert df["unit"].iloc[0] == "%"
        assert not df.empty

    def test_invalid_measure_raises(self):
        """잘못된 measure는 ValueError."""
        with pytest.raises(ValueError, match="measure"):
            get_cpi(measure="quarterly")  # type: ignore[arg-type]


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
                        "DATA_VALUE": "114.87",
                        "UNIT_NAME": "2020=100",
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
        assert df["value"].iloc[0] == 114.87  # 지수(2020=100), 전년동월비 아님 (#136)
        assert df["unit"].iloc[0] == "2020=100"


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
                        "DATA_VALUE": "123.28",
                        "UNIT_NAME": "2020=100",
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
        assert df["value"].iloc[0] == 123.28  # 지수(2020=100), 전년동월비 아님 (#136)
        assert df["unit"].iloc[0] == "2020=100"


def _cpi_monthly_mock() -> dict:
    """CPI 월별 통계표(901Y009) 다항목(계층) 응답 모킹."""
    items = [
        ("0", "총지수", "113.52"),
        ("A", "식료품 및 비주류음료", "120.30"),
        ("A01101", "쌀", "104.96"),
    ]
    rows = []
    for time in ["202401", "202402"]:
        for code, name, value in items:
            rows.append(
                {
                    "ITEM_CODE1": code,
                    "ITEM_NAME1": name,
                    "TIME": time,
                    "DATA_VALUE": value,
                    "UNIT_NAME": "2020=100",
                }
            )
    return {"StatisticSearch": {"row": rows}}


@pytest.mark.usefixtures("set_api_key")
class TestGetCpiMonthly:
    """get_cpi_monthly 재설계 테스트 (#61)."""

    def _add_mock(self):
        responses.add(responses.GET, url=re.compile(r".*"), json=_cpi_monthly_mock(), status=200)

    @responses.activate
    def test_default_returns_full_series_long_format(self):
        """sub_category 미지정 시 전체 품목을 long-format으로 반환한다."""
        self._add_mock()
        df = get_cpi_monthly(start_date="202401", end_date="202402")
        assert list(df.columns) == ["date", "category_value", "value", "unit"]
        assert set(df["category_value"]) == {"총지수", "식료품 및 비주류음료", "쌀"}
        assert len(df) == 6  # 3품목 × 2개월

    @responses.activate
    def test_sub_category_total_index(self):
        """sub_category='총지수'는 총지수 단일 시계열을 반환한다."""
        self._add_mock()
        df = get_cpi_monthly(sub_category="총지수", start_date="202401", end_date="202402")
        assert list(df.columns) == ["date", "value", "unit"]
        assert df["value"].iloc[0] == 113.52

    @responses.activate
    def test_sub_category_by_item_code(self):
        """sub_category로 item_code1(쌀=A01101)도 허용한다."""
        self._add_mock()
        df = get_cpi_monthly(sub_category="A01101", start_date="202401", end_date="202402")
        assert (df["value"] == 104.96).all()

    @responses.activate
    def test_unknown_sub_category_raises(self):
        """없는 sub_category는 사용 가능한 항목과 함께 ValueError."""
        self._add_mock()
        with pytest.raises(ValueError, match="사용 가능한 항목"):
            get_cpi_monthly(sub_category="없는품목", start_date="202401", end_date="202402")

    @responses.activate
    def test_emits_no_warning(self):
        """재설계 후 어떤 경고도 발생시키지 않는다 (partial-coverage 경고 제거, #64)."""
        self._add_mock()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            get_cpi_monthly(start_date="202401", end_date="202402")


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
        with pytest.raises(ValueError, match="category"):
            get_cpi_by_category(category="invalid_category")  # type: ignore[arg-type]
