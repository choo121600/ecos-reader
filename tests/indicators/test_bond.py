"""채권시장 지표 모듈 단위 테스트 (#13, #63 재설계).

`get_bond_yield`를 mock 응답으로 검증한다 (ECOS_API_KEY 불필요). #63에서 두 변형
모두 partial-coverage 경고를 제거하고 measure 고정 + 분류축 long-format/sub_category
선택을 제공하도록 재설계되었다. 두 통계표는 축 위치가 다르다:
  종류별(901Y015): item_code1=채권종류, item_code2=measure
  시장별(901Y120): item_code1=measure, item_code2=시장
"""

from __future__ import annotations

import re
import warnings

import pytest
import responses

from ecos.indicators._deprecations import EcosPartialCoverageWarning
from ecos.indicators.bond import get_bond_yield


def _type_mock() -> dict:
    """종류별(901Y015): item_code1=종류 × item_code2=measure."""
    types = [("1", "합계"), ("4", "국채"), ("7", "회사채")]
    measures = [("2040000", "거래대금", "100"), ("2030000", "거래량", "55")]
    rows = []
    for time in ["202401", "202402"]:
        for c1, n1 in types:
            for c2, n2, base in measures:
                rows.append(
                    {
                        "ITEM_CODE1": c1,
                        "ITEM_NAME1": n1,
                        "ITEM_CODE2": c2,
                        "ITEM_NAME2": n2,
                        "TIME": time,
                        "DATA_VALUE": f"{int(base) + int(c1) * 1000}",
                        "UNIT_NAME": "백만원",
                    }
                )
    return {"StatisticSearch": {"row": rows}}


def _market_mock() -> dict:
    """시장별(901Y120): item_code1=measure × item_code2=시장."""
    measures = [("AMT", "거래대금"), ("VOL", "거래량")]
    markets = [
        ("020101", "합계", "900"),
        ("0202", "국채전문 유통시장", "800"),
        ("0203", "일반채권 시장", "60"),
    ]
    rows = []
    for time in ["202401", "202402"]:
        for c1, n1 in measures:
            for c2, n2, base in markets:
                rows.append(
                    {
                        "ITEM_CODE1": c1,
                        "ITEM_NAME1": n1,
                        "ITEM_CODE2": c2,
                        "ITEM_NAME2": n2,
                        "TIME": time,
                        "DATA_VALUE": base,
                        "UNIT_NAME": "백만원",
                    }
                )
    return {"StatisticSearch": {"row": rows}}


@pytest.mark.usefixtures("set_api_key")
class TestGetBondYieldByType:
    """get_bond_yield 종류별 재설계 테스트 (#63)."""

    def _add_mock(self):
        responses.add(responses.GET, url=re.compile(r".*"), json=_type_mock(), status=200)

    @responses.activate
    def test_default_long_format_filters_measure(self):
        """기본(거래대금)은 거래대금 measure로 거른 채권종류 long-format을 반환한다."""
        self._add_mock()
        df = get_bond_yield(bond_type="종류별", start_date="202401", end_date="202402")
        assert list(df.columns) == ["date", "category_value", "value", "unit"]
        assert set(df["category_value"]) == {"합계", "국채", "회사채"}
        assert len(df) == 6  # 3종류 × 2개월 (거래량 measure는 제외됨)

    @responses.activate
    def test_sub_category_single_series(self):
        """sub_category로 단일 채권종류 시계열을 반환한다."""
        self._add_mock()
        df = get_bond_yield(sub_category="국채", start_date="202401", end_date="202402")
        assert list(df.columns) == ["date", "value", "unit"]
        assert (df["value"] == 4100).all()  # base 100 + 4*1000

    @responses.activate
    def test_measure_volume(self):
        """measure='거래량'은 거래량 measure로 필터한다."""
        self._add_mock()
        df = get_bond_yield(
            measure="거래량", sub_category="국채", start_date="202401", end_date="202401"
        )
        assert (df["value"] == 4055).all()  # base 55 + 4*1000

    @responses.activate
    def test_unknown_sub_category_raises(self):
        self._add_mock()
        with pytest.raises(ValueError, match="사용 가능한 항목"):
            get_bond_yield(sub_category="없는종류", start_date="202401", end_date="202401")

    @responses.activate
    def test_no_partial_coverage_warning(self):
        self._add_mock()
        with warnings.catch_warnings():
            warnings.simplefilter("error", EcosPartialCoverageWarning)
            get_bond_yield(start_date="202401", end_date="202401")


@pytest.mark.usefixtures("set_api_key")
class TestGetBondYieldByMarket:
    """get_bond_yield 시장별 재설계 테스트 (#63) — 축이 종류별과 반대."""

    def _add_mock(self):
        responses.add(responses.GET, url=re.compile(r".*"), json=_market_mock(), status=200)

    @responses.activate
    def test_default_long_format_promotes_market_axis(self):
        """시장별 기본은 measure로 item_code1을 거른 뒤 시장(item_code2)을 분류한다."""
        self._add_mock()
        df = get_bond_yield(bond_type="시장별", start_date="202401", end_date="202402")
        assert list(df.columns) == ["date", "category_value", "value", "unit"]
        assert set(df["category_value"]) == {"합계", "국채전문 유통시장", "일반채권 시장"}
        assert len(df) == 6

    @responses.activate
    def test_sub_category_by_market_code(self):
        """sub_category(시장 item_code2 코드)로 단일 시장 시계열을 반환한다."""
        self._add_mock()
        df = get_bond_yield(
            bond_type="시장별", sub_category="0202", start_date="202401", end_date="202402"
        )
        assert list(df.columns) == ["date", "value", "unit"]
        assert (df["value"] == 800).all()

    @responses.activate
    def test_measure_volume(self):
        """시장별 measure='거래량'도 동작한다."""
        self._add_mock()
        df = get_bond_yield(
            bond_type="시장별", measure="거래량", start_date="202401", end_date="202401"
        )
        assert set(df["category_value"]) == {"합계", "국채전문 유통시장", "일반채권 시장"}


@pytest.mark.usefixtures("set_api_key")
class TestGetBondYieldValidation:
    def test_invalid_bond_type_raises(self):
        with pytest.raises(ValueError, match="bond_type"):
            get_bond_yield(bond_type="invalid")  # type: ignore[arg-type]

    def test_invalid_type_measure_raises(self):
        with pytest.raises(ValueError, match="종류별 measure"):
            get_bond_yield(bond_type="종류별", measure="없음")  # type: ignore[arg-type]

    def test_invalid_market_measure_raises(self):
        """시장별은 상장잔액/상장종목수를 지원하지 않는다."""
        with pytest.raises(ValueError, match="시장별 measure"):
            get_bond_yield(bond_type="시장별", measure="상장잔액")  # type: ignore[arg-type]
