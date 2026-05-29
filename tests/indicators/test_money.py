"""
통화 지표 모듈 테스트
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.money import get_bank_lending, get_borrower_loan, get_money_supply


def _borrower_loan_mock() -> dict:
    """차주별 가계대출(181Y00x) 응답 모킹.

    분류축이 모두 item_code1 prefix로 표현되는 실제 ECOS 구조를 흉내낸다:
    0000 전체 / B0xx 성별 / C0xx 연령 / D0xx 지역 / E0xx 업권.
    """
    rows = []
    for time in ["2024Q1", "2024Q2"]:
        rows += [
            {
                "ITEM_CODE1": "0000",
                "ITEM_NAME1": "전체",
                "TIME": time,
                "DATA_VALUE": "100",
                "UNIT_NAME": "조원",
            },
            {
                "ITEM_CODE1": "B001",
                "ITEM_NAME1": "남성",
                "TIME": time,
                "DATA_VALUE": "55",
                "UNIT_NAME": "조원",
            },
            {
                "ITEM_CODE1": "B002",
                "ITEM_NAME1": "여성",
                "TIME": time,
                "DATA_VALUE": "45",
                "UNIT_NAME": "조원",
            },
            {
                "ITEM_CODE1": "C001",
                "ITEM_NAME1": "20대",
                "TIME": time,
                "DATA_VALUE": "10",
                "UNIT_NAME": "조원",
            },
            {
                "ITEM_CODE1": "C002",
                "ITEM_NAME1": "30대",
                "TIME": time,
                "DATA_VALUE": "20",
                "UNIT_NAME": "조원",
            },
            {
                "ITEM_CODE1": "D001",
                "ITEM_NAME1": "수도권",
                "TIME": time,
                "DATA_VALUE": "60",
                "UNIT_NAME": "조원",
            },
            {
                "ITEM_CODE1": "E001",
                "ITEM_NAME1": "예금은행",
                "TIME": time,
                "DATA_VALUE": "70",
                "UNIT_NAME": "조원",
            },
        ]
    return {"StatisticSearch": {"row": rows}}


@pytest.mark.usefixtures("set_api_key")
class TestGetBorrowerLoan:
    """get_borrower_loan 재설계 테스트 (#29)."""

    def _add_mock(self):
        responses.add(responses.GET, url=re.compile(r".*"), json=_borrower_loan_mock(), status=200)

    @responses.activate
    def test_long_format_returns_axis_items(self):
        """sub_category 미지정 시 분류축 전체를 long-format으로 반환한다."""
        self._add_mock()
        df = get_borrower_loan(
            loan_type="잔액", category="연령별", start_date="2024Q1", end_date="2024Q2"
        )
        assert list(df.columns) == ["date", "category_value", "value", "unit"]
        # C001(20대), C002(30대) × 2분기 = 4행. 다른 축(D/E/0000)은 제외돼야 함.
        assert set(df["category_value"]) == {"20대", "30대"}
        assert len(df) == 4

    @responses.activate
    def test_sub_category_returns_single_series(self):
        """sub_category 지정 시 해당 항목 단일 시계열만 반환한다."""
        self._add_mock()
        df = get_borrower_loan(
            loan_type="잔액",
            category="연령별",
            sub_category="30대",
            start_date="2024Q1",
            end_date="2024Q2",
        )
        assert list(df.columns) == ["date", "value", "unit"]
        assert len(df) == 2
        assert (df["value"] == 20).all()

    @responses.activate
    def test_sub_category_accepts_item_code(self):
        """sub_category로 item_code도 허용한다."""
        self._add_mock()
        df = get_borrower_loan(
            loan_type="잔액",
            category="연령별",
            sub_category="C001",
            start_date="2024Q1",
            end_date="2024Q2",
        )
        assert (df["value"] == 10).all()

    @responses.activate
    def test_category_all_uses_single_code(self):
        """category='전체'는 item_code 0000만 매칭한다."""
        self._add_mock()
        df = get_borrower_loan(
            loan_type="잔액", category="전체", start_date="2024Q1", end_date="2024Q2"
        )
        assert set(df["category_value"]) == {"전체"}
        assert (df["value"] == 100).all()

    @responses.activate
    def test_category_sex_axis(self):
        """category='성별'(prefix B)은 남성/여성만 묶는다."""
        self._add_mock()
        df = get_borrower_loan(
            loan_type="잔액", category="성별", start_date="2024Q1", end_date="2024Q2"
        )
        assert set(df["category_value"]) == {"남성", "여성"}
        assert len(df) == 4

    @responses.activate
    def test_unknown_sub_category_raises_with_available(self):
        """존재하지 않는 sub_category는 사용 가능한 항목과 함께 ValueError."""
        self._add_mock()
        with pytest.raises(ValueError, match="사용 가능한 항목"):
            get_borrower_loan(
                loan_type="잔액",
                category="연령별",
                sub_category="없는항목",
                start_date="2024Q1",
                end_date="2024Q2",
            )

    def test_invalid_loan_type_raises(self):
        with pytest.raises(ValueError, match="loan_type"):
            get_borrower_loan(loan_type="월별")  # type: ignore[arg-type]

    def test_invalid_category_raises(self):
        with pytest.raises(ValueError, match="category"):
            get_borrower_loan(category="소득별")  # type: ignore[arg-type]


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
