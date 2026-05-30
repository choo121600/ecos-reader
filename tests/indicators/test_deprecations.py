"""Verify partial-coverage indicators emit EcosPartialCoverageWarning (#8)."""

from __future__ import annotations

import re

import pytest
import responses

import ecos


@pytest.fixture(autouse=True)
def _set_key():
    ecos.set_api_key("test-key-deprecation")
    yield
    ecos.clear_api_key()


@pytest.fixture
def _empty_mock():
    """Catch any ECOS request with an empty StatisticSearch payload."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            rsps.GET,
            url=re.compile(r".*"),
            json={"StatisticSearch": {"row": []}},
            status=200,
        )
        yield rsps


# (func_name, callable that invokes the indicator with valid default args)
_PARTIAL_COVERAGE_CASES = [
    ("get_gdp_by_industry", lambda: ecos.get_gdp_by_industry()),
    ("get_gdp_by_expenditure", lambda: ecos.get_gdp_by_expenditure()),
    ("get_gdp_deflator_by_industry", lambda: ecos.get_gdp_deflator_by_industry()),
    (
        "get_stock_index",
        lambda: ecos.get_stock_index(frequency="monthly"),
    ),
    ("get_investor_trading", lambda: ecos.get_investor_trading()),
    ("get_bond_yield(종류별)", lambda: ecos.get_bond_yield(bond_type="종류별")),
    ("get_bond_yield(시장별)", lambda: ecos.get_bond_yield(bond_type="시장별")),
    (
        "get_household_lending_detail",
        lambda: ecos.get_household_lending_detail(),
    ),
    # get_borrower_loan은 v0.2.0(#29)에서 분류축 전체를 long-format으로 반환하도록
    # 재설계되어 더 이상 단일 항목 partial-coverage 경고를 내지 않으므로 제외.
    ("get_cpi_monthly", lambda: ecos.get_cpi_monthly()),
    # get_cpi_by_category는 v0.1.6에서 (stat_code, item_code) 매핑이 수정되어
    # 정상 데이터를 반환하므로 partial-coverage 목록에서 제외 (PR #27).
]


@pytest.mark.parametrize(
    ("func_name", "call"),
    _PARTIAL_COVERAGE_CASES,
    ids=[name for name, _ in _PARTIAL_COVERAGE_CASES],
)
@pytest.mark.usefixtures("_empty_mock")
def test_partial_coverage_emits_visible_warning(func_name, call):
    """Every documented partial-coverage helper must warn (#8 review).

    - Warning must be visible by default (UserWarning subclass), not
      filtered like a plain DeprecationWarning.
    - Warning message must mention the public function name so users
      can pinpoint which helper they hit.
    - Exactly one warning of this class fires per call — guards
      against accidental duplicate/double-warn regressions.
    """
    with pytest.warns(ecos.EcosPartialCoverageWarning, match=re.escape(func_name)) as rec:
        call()
    assert len(rec) == 1, (
        f"{func_name}: expected exactly 1 EcosPartialCoverageWarning, got {len(rec)}"
    )


def test_warning_class_is_user_warning_subclass():
    """User-visible warning class (not DeprecationWarning) per #8 review."""
    assert issubclass(ecos.EcosPartialCoverageWarning, UserWarning)
    # Sanity: not a DeprecationWarning, so default filter does NOT suppress it.
    assert not issubclass(ecos.EcosPartialCoverageWarning, DeprecationWarning)
