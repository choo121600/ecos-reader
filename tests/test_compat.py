"""0.9 → 1.0 전환 하위호환 계층(_compat) 테스트."""

from __future__ import annotations

import inspect

import pytest

import ecos
from ecos._compat import LEGACY_VALUES, api_transition
from ecos.exceptions import EcosDeprecationWarning


@api_transition(renamed={"seasonal": "seasonal_adj"}, legacy_values=("action", "category"))
def _fn(name=None, *, action="net_buy", category="all", seasonal_adj=False):
    return {"name": name, "action": action, "category": category, "seasonal_adj": seasonal_adj}


def test_keyword_call_does_not_warn(recwarn):
    assert _fn("x", action="buy") == {
        "name": "x",
        "action": "buy",
        "category": "all",
        "seasonal_adj": False,
    }
    assert not [w for w in recwarn if issubclass(w.category, EcosDeprecationWarning)]


def test_positional_call_warns_and_binds_in_order():
    with pytest.warns(EcosDeprecationWarning, match=r"_fn\(action=\.\.\., category=\.\.\.\)"):
        result = _fn("x", "sell", "goods")
    assert result["action"] == "sell"
    assert result["category"] == "goods"


def test_warning_points_at_caller():
    with pytest.warns(EcosDeprecationWarning) as record:
        _fn("x", "sell")
    assert record[0].filename == __file__


def test_too_many_positional_args_raise():
    with pytest.raises(TypeError, match="너무 많습니다"):
        _fn("x", "sell", "goods", True, "extra")


def test_positional_and_keyword_duplicate_raises():
    with pytest.raises(TypeError, match="중복"), pytest.warns(EcosDeprecationWarning):
        _fn("x", "sell", action="buy")


def test_renamed_argument_warns_and_maps():
    with pytest.warns(EcosDeprecationWarning, match="'seasonal' 인자는 deprecated"):
        result = _fn(seasonal=True)
    assert result["seasonal_adj"] is True


def test_renamed_and_new_argument_together_raise():
    with pytest.raises(TypeError, match="함께 전달할 수 없습니다"):
        _fn(seasonal=True, seasonal_adj=True)


def test_korean_value_warns_and_maps_to_english():
    with pytest.warns(EcosDeprecationWarning, match=r"action='net_buy'를 사용하세요"):
        result = _fn(action="순매수")
    assert result["action"] == "net_buy"


def test_positional_korean_value_is_mapped_too():
    with pytest.warns(EcosDeprecationWarning) as record:
        result = _fn("x", "매도", "교통")
    assert result["action"] == "sell"
    assert result["category"] == "transport"
    assert len(record) == 3  # 위치 인자 1회 + 한글 값 2회


def test_unknown_legacy_param_rejected_at_decoration():
    with pytest.raises(ValueError, match="LEGACY_VALUES에 없는 인자"):
        api_transition(legacy_values=("nope",))


def test_wrapped_signature_is_keyword_only():
    params = inspect.signature(ecos.get_trade).parameters
    assert all(p.kind is p.KEYWORD_ONLY for p in params.values())


def test_get_indicator_keeps_name_positional():
    params = list(inspect.signature(ecos.get_indicator).parameters.values())
    assert params[0].name == "name"
    assert params[0].kind is params[0].POSITIONAL_OR_KEYWORD
    assert all(p.kind is p.KEYWORD_ONLY for p in params[1:])


def test_legacy_values_map_to_distinct_english_values():
    for param, mapping in LEGACY_VALUES.items():
        english = list(mapping.values())
        # 같은 영문 값으로 합쳐지는 한글 값은 없어야 한다 (의미 손실 방지)
        assert len(set(english)) == len(english), param
        assert all(v.isascii() for v in english), param


def test_public_indicators_accept_english_values_in_literal():
    """Literal 타입 힌트가 레거시 한글이 아닌 영문 값을 선언해야 한다."""
    sig = inspect.signature(ecos.get_investor_trading)
    assert "net_buy" in str(sig.parameters["action"].annotation)
    assert "순매수" not in str(sig.parameters["action"].annotation)
