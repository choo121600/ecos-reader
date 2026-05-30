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
#
# v0.3.0(#59~#63)에서 모든 partial-coverage 함수가 전체 시리즈 long-format +
# sub_category 선택으로 재설계되어 더 이상 EcosPartialCoverageWarning을 내지
# 않는다. 따라서 이 목록은 비어 있다. 각 함수의 "경고 없음"은 해당 모듈 테스트
# (test_growth/stock/prices/money/bond의 test_no_partial_coverage_warning)에서
# 검증한다. 경고 인프라(_deprecations) 자체는 #64 cleanup에서 제거 예정.
#   - get_gdp_* (#59), get_stock_index(monthly)/get_investor_trading (#60),
#     get_cpi_monthly (#61), get_household_lending_detail (#62),
#     get_bond_yield(종류별/시장별) (#63), get_borrower_loan (#29 v0.2.0)
_PARTIAL_COVERAGE_CASES: list[tuple[str, object]] = []


@pytest.mark.skipif(
    not _PARTIAL_COVERAGE_CASES,
    reason="모든 partial-coverage 함수가 재설계됨 (#59~#63); #64에서 경고 인프라 제거 예정.",
)
@pytest.mark.parametrize(
    ("func_name", "call"),
    _PARTIAL_COVERAGE_CASES or [("none", lambda: None)],
    ids=lambda c: c if isinstance(c, str) else "",
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
