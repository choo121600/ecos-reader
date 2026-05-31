"""frequency 정규화 동작 검증 (#20, #57).

정식 어휘(daily/monthly/quarterly/annual)만 허용한다. 레거시 단일 문자
(D/M/Q/A)는 v0.4.0(#57)에서 제거되어 즉시 ValueError로 처리된다.
"""

from __future__ import annotations

import warnings

import pytest

from ecos.indicators._frequency import normalize_frequency


class TestNormalizeFrequencyCanonical:
    """정식 어휘는 그대로 통과한다."""

    def test_canonical_passthrough(self):
        for value in ("daily", "monthly", "quarterly", "annual"):
            assert (
                normalize_frequency(
                    value,
                    allowed=("daily", "monthly", "quarterly", "annual"),
                    func_name="test",
                )
                == value
            )

    def test_canonical_no_warning(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = normalize_frequency("monthly", allowed=("monthly",), func_name="test")
        assert result == "monthly"


class TestNormalizeFrequencyLegacyRemoved:
    """레거시 단일 문자는 제거되어 즉시 ValueError로 처리된다."""

    def test_legacy_aliases_raise(self):
        for legacy in ("D", "M", "Q", "A"):
            with pytest.raises(ValueError, match="frequency"):
                normalize_frequency(
                    legacy,
                    allowed=("daily", "monthly", "quarterly", "annual"),
                    func_name="test",
                )

    def test_legacy_raises_without_warning(self):
        """레거시 표기는 경고 없이 곧바로 ValueError."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with pytest.raises(ValueError, match="frequency"):
                normalize_frequency("Q", allowed=("quarterly", "annual"), func_name="get_gdp")

    def test_invalid_raises_valueerror(self):
        with pytest.raises(ValueError, match="frequency"):
            normalize_frequency("W", allowed=("daily", "monthly"), func_name="test")

    def test_canonical_outside_allowed_raises(self):
        """정식 어휘라도 allowed에 없으면 ValueError."""
        with pytest.raises(ValueError, match="frequency"):
            normalize_frequency("daily", allowed=("quarterly", "annual"), func_name="test")

    def test_error_message_includes_func_name(self):
        with pytest.raises(ValueError, match="get_gdp"):
            normalize_frequency("Q", allowed=("quarterly", "annual"), func_name="get_gdp")


class TestFrequencyWiringPerFunction:
    """per-function wiring: 레거시 표기는 ValueError로 거부된다."""

    def test_get_gdp_legacy_quarterly_raises(self):
        """get_gdp(frequency='Q')는 ValueError."""
        from ecos import get_gdp

        with pytest.raises(ValueError, match="frequency"):
            get_gdp(frequency="Q", start_date="2024Q1", end_date="2024Q1")

    def test_get_base_rate_legacy_daily_raises(self):
        """get_base_rate(frequency='D')는 ValueError."""
        from ecos import get_base_rate

        with pytest.raises(ValueError, match="frequency"):
            get_base_rate(frequency="D", start_date="20240101", end_date="20241231")

    def test_get_stock_index_legacy_daily_raises(self):
        """get_stock_index(frequency='D')는 ValueError."""
        from ecos import get_stock_index

        with pytest.raises(ValueError, match="frequency"):
            get_stock_index(frequency="D")
