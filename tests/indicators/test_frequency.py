"""frequency 어휘 통일 + deprecation 테스트 (#20)."""

from __future__ import annotations

import re

import pytest
import responses

import ecos
from ecos import EcosDeprecationWarning
from ecos.indicators._frequency import normalize_frequency
from ecos.indicators.growth import get_gdp
from ecos.indicators.interest_rate import get_base_rate
from ecos.indicators.stock import get_stock_index


class TestNormalizeFrequency:
    @pytest.mark.parametrize(
        ("legacy", "canonical"),
        [("D", "daily"), ("M", "monthly"), ("Q", "quarterly"), ("A", "annual")],
    )
    def test_legacy_alias_maps_and_warns(self, legacy, canonical):
        with pytest.warns(EcosDeprecationWarning) as rec:
            result = normalize_frequency(
                legacy, allowed=("daily", "monthly", "quarterly", "annual"), func_name="fn"
            )
        assert result == canonical
        msg = str(rec[0].message)
        assert canonical in msg
        assert "v0.4.0" in msg

    @pytest.mark.parametrize("canonical", ["daily", "monthly", "quarterly", "annual"])
    def test_canonical_passes_without_warning(self, canonical, recwarn):
        result = normalize_frequency(
            canonical, allowed=("daily", "monthly", "quarterly", "annual"), func_name="fn"
        )
        assert result == canonical
        assert len(recwarn) == 0

    def test_value_outside_allowed_raises_without_warning(self, recwarn):
        with pytest.raises(ValueError, match="frequency"):
            normalize_frequency("W", allowed=("daily", "monthly"), func_name="fn")
        assert len(recwarn) == 0

    def test_legacy_alias_outside_allowed_raises(self):
        # "Q" maps to "quarterly", which is not in a daily/monthly-only indicator
        with pytest.raises(ValueError, match="frequency"):
            normalize_frequency("Q", allowed=("daily", "monthly"), func_name="fn")

    def test_warning_is_visible_userwarning_subclass(self):
        assert issubclass(EcosDeprecationWarning, UserWarning)

    def test_exported_from_package(self):
        assert ecos.EcosDeprecationWarning is EcosDeprecationWarning


@pytest.mark.usefixtures("set_api_key")
class TestFrequencyWiringPerFunction:
    """per-function wiring: legacy alias → EcosDeprecationWarning, canonical → no warning."""

    @responses.activate
    def test_get_gdp_legacy_q_warns(self):
        """get_gdp(frequency='Q') raises EcosDeprecationWarning, result is non-empty."""
        mock_json = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "200Y001",
                        "TIME": "2024Q1",
                        "DATA_VALUE": "100",
                        "UNIT_NAME": "조원",
                    }
                ]
            }
        }
        responses.add(responses.GET, url=re.compile(r".*"), json=mock_json, status=200)

        with pytest.warns(EcosDeprecationWarning):
            df = get_gdp(frequency="Q", start_date="2024Q1", end_date="2024Q1")

        assert not df.empty

    @responses.activate
    def test_get_gdp_canonical_quarterly_no_warn(self, recwarn):
        """get_gdp(frequency='quarterly') does NOT emit EcosDeprecationWarning."""
        mock_json = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "200Y001",
                        "TIME": "2024Q1",
                        "DATA_VALUE": "100",
                        "UNIT_NAME": "조원",
                    }
                ]
            }
        }
        responses.add(responses.GET, url=re.compile(r".*"), json=mock_json, status=200)

        df = get_gdp(frequency="quarterly", start_date="2024Q1", end_date="2024Q1")

        assert not df.empty
        deprecation_warnings = [
            w for w in recwarn if issubclass(w.category, EcosDeprecationWarning)
        ]
        assert len(deprecation_warnings) == 0

    @responses.activate
    def test_get_base_rate_legacy_d_warns(self):
        """get_base_rate(frequency='D') raises EcosDeprecationWarning."""
        mock_json = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "722Y001",
                        "TIME": "20240101",
                        "DATA_VALUE": "3.5",
                        "UNIT_NAME": "%",
                    }
                ]
            }
        }
        responses.add(responses.GET, url=re.compile(r".*"), json=mock_json, status=200)

        with pytest.warns(EcosDeprecationWarning):
            get_base_rate(frequency="D", start_date="20240101", end_date="20241231")

    @responses.activate
    def test_get_stock_index_canonical_daily_no_warn(self, recwarn):
        """get_stock_index(frequency='daily') does NOT emit EcosDeprecationWarning."""
        mock_json = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "802Y001",
                        "TIME": "20240102",
                        "DATA_VALUE": "2600",
                        "UNIT_NAME": "포인트",
                    }
                ]
            }
        }
        responses.add(responses.GET, url=re.compile(r".*"), json=mock_json, status=200)

        df = get_stock_index(frequency="daily", start_date="20240102", end_date="20240102")

        assert not df.empty
        deprecation_warnings = [
            w for w in recwarn if issubclass(w.category, EcosDeprecationWarning)
        ]
        assert len(deprecation_warnings) == 0
