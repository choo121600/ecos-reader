"""선언적 IndicatorSpec 레지스트리 단위 테스트 (#16).

`get_indicator` 단일 엔트리, `IndicatorSpec` 기본 날짜 계산, alias 위임의
동작 동등성을 mock 응답으로 검증한다 (ECOS_API_KEY 불필요).
"""

from __future__ import annotations

import re

import pytest
import responses

import ecos
from ecos.indicators import (
    INDICATORS,
    IndicatorSpec,
    get_indicator,
    list_indicators,
)

from ..conftest import make_statistic_search_response


@pytest.mark.usefixtures("set_api_key")
class TestGetIndicator:
    """get_indicator 단일 엔트리 함수."""

    @responses.activate
    def test_registered_indicator_returns_normalized_df(self):
        """레지스트리에 등록된 지표를 이름으로 조회하면 정규화 DataFrame을 반환한다."""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=make_statistic_search_response(stat_code="901Y009", item_code1="0"),
            status=200,
        )

        df = get_indicator("cpi", start_date="202401", end_date="202403")

        assert not df.empty
        assert {"date", "value", "unit"} <= set(df.columns)
        assert len(df) == 3

    def test_unknown_indicator_raises_with_available_names(self):
        """미등록 이름은 사용 가능 목록과 함께 ValueError."""
        with pytest.raises(ValueError, match="알 수 없는 지표"):
            get_indicator("does_not_exist")

    @responses.activate
    def test_default_dates_applied_when_omitted(self):
        """날짜 생략 시 spec 기본 기간이 요청 쿼리에 반영된다."""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=make_statistic_search_response(stat_code="901Y009", item_code1="0"),
            status=200,
        )

        get_indicator("cpi")  # 날짜 생략

        # 요청 URL에 기본 시작/종료(YYYYMM)가 포함되었는지 확인.
        called_url = responses.calls[0].request.url
        assert called_url is not None
        # 월별 포맷 YYYYMM 두 개가 path에 들어간다 (stat search는 path 파라미터 방식).
        assert re.search(r"/\d{6}/\d{6}", called_url) or re.search(r"\d{6}.*\d{6}", called_url)


class TestIndicatorSpec:
    """IndicatorSpec 자료형 자체의 동작."""

    def test_period_derived_from_date_format(self):
        spec = IndicatorSpec(name="x", stat_code="000Y000", date_format="Q")
        assert spec.period == "Q"

    def test_default_lookback_uses_format_default(self):
        """default_lookback 미지정 시 date_format별 기본값(M=12개월)을 사용한다."""
        spec_m = IndicatorSpec(name="m", stat_code="x", date_format="M")
        start, end = spec_m.default_dates()
        assert re.fullmatch(r"\d{6}", start)
        assert re.fullmatch(r"\d{6}", end)
        # 현재 날짜에 의존하지 않고 시작↔종료 간격이 정확히 12개월인지 검증.
        start_months = int(start[:4]) * 12 + int(start[4:6])
        end_months = int(end[:4]) * 12 + int(end[4:6])
        assert end_months - start_months == 12

    def test_explicit_lookback_overrides(self):
        spec = IndicatorSpec(name="x", stat_code="y", date_format="A", default_lookback=3)
        start, end = spec.default_dates()
        assert re.fullmatch(r"\d{4}", start)
        assert int(end) - int(start) == 3


class TestRegistryIntegrity:
    """레지스트리 메타데이터 일관성."""

    def test_keys_match_spec_names(self):
        for key, spec in INDICATORS.items():
            assert key == spec.name

    def test_list_indicators_sorted_and_complete(self):
        names = [s.name for s in list_indicators()]
        assert names == sorted(INDICATORS)
        assert set(names) == set(INDICATORS)

    def test_expected_indicators_registered(self):
        for name in ("base_rate", "fiscal_balance", "cpi", "core_cpi", "ppi", "cpi_monthly"):
            assert name in INDICATORS


@pytest.mark.usefixtures("set_api_key")
class TestAliasDelegation:
    """기존 get_* 함수가 레지스트리 위임 후에도 동일하게 동작한다 (BC)."""

    @responses.activate
    def test_get_cpi_alias_matches_get_indicator(self):
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=make_statistic_search_response(stat_code="901Y009", item_code1="0"),
            status=200,
        )

        via_alias = ecos.get_cpi(start_date="202401", end_date="202403")
        via_entry = get_indicator("cpi", start_date="202401", end_date="202403")

        assert list(via_alias.columns) == list(via_entry.columns)
        assert via_alias["value"].tolist() == via_entry["value"].tolist()

    @responses.activate
    def test_get_fiscal_balance_alias_works(self):
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=make_statistic_search_response(stat_code="901Y013", item_code1="A"),
            status=200,
        )
        df = ecos.get_fiscal_balance(start_date="202401", end_date="202403")
        assert not df.empty
        assert {"date", "value", "unit"} <= set(df.columns)


class TestPublicExports:
    """레지스트리 심볼이 공개 API로 노출된다."""

    def test_registry_symbols_exported_at_top_level(self):
        assert ecos.get_indicator is get_indicator
        assert ecos.INDICATORS is INDICATORS
        assert hasattr(ecos, "IndicatorSpec")
        assert hasattr(ecos, "list_indicators")

    def test_indicators_all_is_auto_generated(self):
        import ecos.indicators as ind

        # 모든 등록 alias가 __all__에 포함된다.
        assert "get_cpi" in ind.__all__
        assert "get_indicator" in ind.__all__
        assert "IndicatorSpec" in ind.__all__

    def test_all_submodule_get_functions_exported(self):
        """카테고리 서브모듈의 모든 공개 get_* 함수가 __all__에 노출된다.

        새 지표 함수를 추가하고 ``indicators/__init__.py`` 에 import 하는 것을
        빠뜨리면 자동 생성 ``__all__`` 에서 조용히 누락되므로, 이를 CI에서 잡는다.
        """
        import importlib
        import inspect

        import ecos.indicators as ind

        submodules = (
            "bond",
            "fiscal",
            "growth",
            "interest_rate",
            "money",
            "prices",
            "stock",
        )
        expected: set[str] = set()
        for mod_name in submodules:
            mod = importlib.import_module(f"ecos.indicators.{mod_name}")
            for name, obj in vars(mod).items():
                # 해당 모듈에서 정의된 공개 get_* 함수만 (import된 헬퍼 제외).
                if (
                    name.startswith("get_")
                    and inspect.isfunction(obj)
                    and obj.__module__ == mod.__name__
                ):
                    expected.add(name)

        missing = expected - set(ind.__all__)
        assert not missing, f"__all__에서 누락된 지표 함수: {sorted(missing)}"
