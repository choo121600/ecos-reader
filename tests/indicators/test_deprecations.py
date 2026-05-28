"""Verify that documented partial-coverage indicators emit DeprecationWarning (#8)."""

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


@responses.activate
def test_get_gdp_by_industry_warns():
    responses.add(
        responses.GET,
        url=re.compile(r".*"),
        json={"StatisticSearch": {"row": []}},
        status=200,
    )
    with pytest.warns(DeprecationWarning, match=r"get_gdp_by_industry"):
        ecos.get_gdp_by_industry()


@responses.activate
def test_get_investor_trading_warns():
    responses.add(
        responses.GET,
        url=re.compile(r".*"),
        json={"StatisticSearch": {"row": []}},
        status=200,
    )
    with pytest.warns(DeprecationWarning, match=r"get_investor_trading"):
        ecos.get_investor_trading()


@responses.activate
def test_get_bond_yield_warns():
    responses.add(
        responses.GET,
        url=re.compile(r".*"),
        json={"StatisticSearch": {"row": []}},
        status=200,
    )
    with pytest.warns(DeprecationWarning, match=r"get_bond_yield"):
        ecos.get_bond_yield()
