"""
통화 지표 모듈 테스트
"""

from __future__ import annotations

import re
import warnings

import pytest
import responses

from ecos.indicators._deprecations import EcosPartialCoverageWarning
from ecos.indicators.money import (
    get_bank_lending,
    get_borrower_loan,
    get_household_credit,
    get_household_lending_detail,
    get_m1_variants,
    get_m2_by_holder,
    get_m2_variants,
    get_money_supply,
)


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
        with pytest.raises(ValueError, match="indicator"):
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
        with pytest.raises(ValueError, match="sector"):
            get_bank_lending(sector="government")  # type: ignore


# ---------------------------------------------------------------------------
# 새로 추가된 6개 함수 테스트
# ---------------------------------------------------------------------------


def _simple_monthly_mock(data_value: str = "500000", time: str = "202401") -> dict:
    return {
        "StatisticSearch": {
            "row": [
                {
                    "STAT_CODE": "dummy",
                    "ITEM_CODE1": "BBLA00",
                    "ITEM_NAME1": "M1",
                    "TIME": time,
                    "DATA_VALUE": data_value,
                    "UNIT_NAME": "십억원",
                }
            ]
        }
    }


def _simple_quarterly_mock(data_value: str = "200000", time: str = "2024Q1") -> dict:
    return {
        "StatisticSearch": {
            "row": [
                {
                    "STAT_CODE": "dummy",
                    "ITEM_CODE1": "1110000",
                    "ITEM_NAME1": "예금취급기관",
                    "TIME": time,
                    "DATA_VALUE": data_value,
                    "UNIT_NAME": "조원",
                }
            ]
        }
    }


@pytest.mark.usefixtures("set_api_key")
class TestGetM1Variants:
    """get_m1_variants 함수 테스트"""

    @responses.activate
    def test_default_variant_returns_dataframe(self):
        """기본 variant(말잔_계절조정)로 데이터 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_simple_monthly_mock("450000", "202401"),
            status=200,
        )
        df = get_m1_variants(variant="말잔_계절조정", start_date="202401", end_date="202401")
        assert not df.empty
        assert list(df.columns) == ["date", "value", "unit"]
        assert df["value"].iloc[0] == 450000.0

    @responses.activate
    def test_variant_평잔_원계열(self):
        """평잔_원계열 variant 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_simple_monthly_mock("430000", "202401"),
            status=200,
        )
        df = get_m1_variants(variant="평잔_원계열", start_date="202401", end_date="202401")
        assert not df.empty
        assert list(df.columns) == ["date", "value", "unit"]

    @responses.activate
    def test_variant_평잔_계절조정(self):
        """평잔_계절조정 variant 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_simple_monthly_mock("440000", "202401"),
            status=200,
        )
        df = get_m1_variants(variant="평잔_계절조정", start_date="202401", end_date="202401")
        assert not df.empty

    def test_invalid_variant_raises(self):
        """잘못된 variant 지정 시 ValueError"""
        with pytest.raises(ValueError, match="variant"):
            get_m1_variants(variant="없는변형")  # type: ignore[arg-type]


@pytest.mark.usefixtures("set_api_key")
class TestGetM2Variants:
    """get_m2_variants 함수 테스트"""

    @responses.activate
    def test_default_variant_returns_dataframe(self):
        """기본 variant(말잔_계절조정)로 데이터 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_simple_monthly_mock("3800000", "202401"),
            status=200,
        )
        df = get_m2_variants(variant="말잔_계절조정", start_date="202401", end_date="202401")
        assert not df.empty
        assert list(df.columns) == ["date", "value", "unit"]
        assert df["value"].iloc[0] == 3800000.0

    @responses.activate
    def test_variant_평잔_원계열(self):
        """평잔_원계열 variant 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_simple_monthly_mock("3700000", "202401"),
            status=200,
        )
        df = get_m2_variants(variant="평잔_원계열", start_date="202401", end_date="202401")
        assert not df.empty
        assert list(df.columns) == ["date", "value", "unit"]

    def test_invalid_variant_raises(self):
        """잘못된 variant 지정 시 ValueError"""
        with pytest.raises(ValueError, match="variant"):
            get_m2_variants(variant="없는변형")  # type: ignore[arg-type]


@pytest.mark.usefixtures("set_api_key")
class TestGetM2ByHolder:
    """get_m2_by_holder 함수 테스트"""

    @responses.activate
    def test_default_variant_returns_dataframe(self):
        """기본 variant(말잔_원계열)로 데이터 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_simple_monthly_mock("3900000", "202401"),
            status=200,
        )
        df = get_m2_by_holder(variant="말잔_원계열", start_date="202401", end_date="202401")
        assert not df.empty
        assert list(df.columns) == ["date", "value", "unit"]
        assert df["value"].iloc[0] == 3900000.0

    @responses.activate
    def test_variant_말잔_계절조정(self):
        """말잔_계절조정 variant 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_simple_monthly_mock("3850000", "202401"),
            status=200,
        )
        df = get_m2_by_holder(variant="말잔_계절조정", start_date="202401", end_date="202401")
        assert not df.empty
        assert list(df.columns) == ["date", "value", "unit"]

    @responses.activate
    def test_variant_평잔_계절조정(self):
        """평잔_계절조정 variant 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_simple_monthly_mock("3820000", "202401"),
            status=200,
        )
        df = get_m2_by_holder(variant="평잔_계절조정", start_date="202401", end_date="202401")
        assert not df.empty

    @responses.activate
    def test_variant_평잔_원계열(self):
        """평잔_원계열 variant 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_simple_monthly_mock("3810000", "202401"),
            status=200,
        )
        df = get_m2_by_holder(variant="평잔_원계열", start_date="202401", end_date="202401")
        assert not df.empty

    def test_invalid_variant_raises(self):
        """잘못된 variant 지정 시 ValueError"""
        with pytest.raises(ValueError, match="variant"):
            get_m2_by_holder(variant="없는변형")  # type: ignore[arg-type]


@pytest.mark.usefixtures("set_api_key")
class TestGetHouseholdCredit:
    """get_household_credit 함수 테스트"""

    @responses.activate
    def test_sector_category_returns_dataframe(self):
        """업권별 카테고리 조회 (기본값)"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_simple_quarterly_mock("1900000", "2024Q1"),
            status=200,
        )
        df = get_household_credit(category="업권별", start_date="2024Q1", end_date="2024Q1")
        assert not df.empty
        assert list(df.columns) == ["date", "value", "unit"]
        assert df["value"].iloc[0] == 1900000.0

    @responses.activate
    def test_purpose_category_returns_dataframe(self):
        """용도별 카테고리 조회"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_simple_quarterly_mock("1850000", "2024Q1"),
            status=200,
        )
        df = get_household_credit(category="용도별", start_date="2024Q1", end_date="2024Q1")
        assert not df.empty
        assert list(df.columns) == ["date", "value", "unit"]

    def test_invalid_category_raises(self):
        """잘못된 category 지정 시 ValueError"""
        with pytest.raises(ValueError, match="category"):
            get_household_credit(category="소득별")  # type: ignore[arg-type]


def _household_lending_mock() -> dict:
    """예금취급기관 가계대출(용도별, 151Y005) 다항목 응답 모킹."""
    items = [
        ("1110000", "예금취급기관", "1100000"),
        ("11100A0", "주택관련대출-예금취급기관", "784794.3"),
        ("11100B0", "기타대출-예금취급기관", "315205.7"),
        ("11110A0", "주택관련대출-예금은행", "560000.0"),
        ("11110B0", "기타대출-예금은행", "242374.7"),
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
                    "UNIT_NAME": "십억원",
                }
            )
    return {"StatisticSearch": {"row": rows}}


@pytest.mark.usefixtures("set_api_key")
class TestGetHouseholdLendingDetail:
    """get_household_lending_detail 재설계 테스트 (#62)."""

    def _add_mock(self):
        responses.add(
            responses.GET, url=re.compile(r".*"), json=_household_lending_mock(), status=200
        )

    @responses.activate
    def test_default_returns_full_series_long_format(self):
        """sub_category 미지정 시 전체 분류를 long-format으로 반환한다."""
        self._add_mock()
        df = get_household_lending_detail(start_date="202401", end_date="202402")
        assert list(df.columns) == ["date", "category_value", "value", "unit"]
        assert "주택관련대출-예금취급기관" in set(df["category_value"])
        assert df["category_value"].nunique() == 5
        assert len(df) == 10  # 5분류 × 2개월

    @responses.activate
    def test_sub_category_by_item_code(self):
        """sub_category로 item_code1을 지정하면 단일 시계열을 반환한다."""
        self._add_mock()
        df = get_household_lending_detail(
            sub_category="11100A0", start_date="202401", end_date="202402"
        )
        assert list(df.columns) == ["date", "value", "unit"]
        assert (df["value"] == 784794.3).all()

    @responses.activate
    def test_sub_category_by_name(self):
        """sub_category로 항목명도 허용한다."""
        self._add_mock()
        df = get_household_lending_detail(
            sub_category="기타대출-예금은행", start_date="202401", end_date="202401"
        )
        assert (df["value"] == 242374.7).all()

    @responses.activate
    def test_unknown_sub_category_raises(self):
        """없는 sub_category는 사용 가능한 항목과 함께 ValueError."""
        self._add_mock()
        with pytest.raises(ValueError, match="사용 가능한 항목"):
            get_household_lending_detail(
                sub_category="없는분류", start_date="202401", end_date="202401"
            )

    @responses.activate
    def test_no_partial_coverage_warning(self):
        """재설계 후에는 EcosPartialCoverageWarning을 발생시키지 않는다."""
        self._add_mock()
        with warnings.catch_warnings():
            warnings.simplefilter("error", EcosPartialCoverageWarning)
            get_household_lending_detail(start_date="202401", end_date="202401")

    @responses.activate
    def test_date_column_is_datetime(self):
        """date 컬럼이 datetime 타입인지 확인"""
        self._add_mock()
        df = get_household_lending_detail(
            sub_category="11100A0", start_date="202401", end_date="202402"
        )
        import pandas as pd

        assert pd.api.types.is_datetime64_any_dtype(df["date"])


@pytest.mark.usefixtures("set_api_key")
class TestGetBorrowerLoanExtra:
    """get_borrower_loan 추가 테스트 (담보유형별, 다중대출별 분류축)."""

    def _mock_with_prefixes(self) -> dict:
        """F(담보유형별), G(다중대출별) prefix를 포함한 mock."""
        rows = []
        for time in ["2024Q1"]:
            rows += [
                {
                    "ITEM_CODE1": "0000",
                    "ITEM_NAME1": "전체",
                    "TIME": time,
                    "DATA_VALUE": "100",
                    "UNIT_NAME": "조원",
                },
                {
                    "ITEM_CODE1": "F001",
                    "ITEM_NAME1": "주택담보",
                    "TIME": time,
                    "DATA_VALUE": "60",
                    "UNIT_NAME": "조원",
                },
                {
                    "ITEM_CODE1": "F002",
                    "ITEM_NAME1": "신용대출",
                    "TIME": time,
                    "DATA_VALUE": "30",
                    "UNIT_NAME": "조원",
                },
                {
                    "ITEM_CODE1": "G001",
                    "ITEM_NAME1": "1건",
                    "TIME": time,
                    "DATA_VALUE": "70",
                    "UNIT_NAME": "조원",
                },
                {
                    "ITEM_CODE1": "G002",
                    "ITEM_NAME1": "2건이상",
                    "TIME": time,
                    "DATA_VALUE": "30",
                    "UNIT_NAME": "조원",
                },
            ]
        return {"StatisticSearch": {"row": rows}}

    @responses.activate
    def test_담보유형별_long_format(self):
        """담보유형별(prefix F) 분류축이 long-format으로 반환된다."""
        responses.add(
            responses.GET, url=re.compile(r".*"), json=self._mock_with_prefixes(), status=200
        )
        df = get_borrower_loan(
            loan_type="잔액", category="담보유형별", start_date="2024Q1", end_date="2024Q1"
        )
        assert list(df.columns) == ["date", "category_value", "value", "unit"]
        assert set(df["category_value"]) == {"주택담보", "신용대출"}

    @responses.activate
    def test_다중대출별_long_format(self):
        """다중대출별(prefix G) 분류축이 long-format으로 반환된다."""
        responses.add(
            responses.GET, url=re.compile(r".*"), json=self._mock_with_prefixes(), status=200
        )
        df = get_borrower_loan(
            loan_type="신규", category="다중대출별", start_date="2024Q1", end_date="2024Q1"
        )
        assert list(df.columns) == ["date", "category_value", "value", "unit"]
        assert set(df["category_value"]) == {"1건", "2건이상"}

    @responses.activate
    def test_sub_category_by_item_name(self):
        """sub_category로 ITEM_NAME1을 지정해 단일 시계열 반환."""
        responses.add(
            responses.GET, url=re.compile(r".*"), json=self._mock_with_prefixes(), status=200
        )
        df = get_borrower_loan(
            loan_type="잔액",
            category="담보유형별",
            sub_category="주택담보",
            start_date="2024Q1",
            end_date="2024Q1",
        )
        assert list(df.columns) == ["date", "value", "unit"]
        assert df["value"].iloc[0] == 60.0
