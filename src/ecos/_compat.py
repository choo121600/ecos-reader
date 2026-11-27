"""
1.0 전환용 하위호환 계층 (deprecation-policy.md).

0.9.0에서 공개 지표 함수의 API를 정리하면서 바뀐 호출 방식을 한시적으로
계속 받아들이고 :class:`~ecos.exceptions.EcosDeprecationWarning` 을 낸다.

- 위치 인자 호출 → 키워드 전용 인자
- 이름이 바뀐 인자 (예: ``seasonal`` → ``seasonal_adj``)
- 한글 선택값 → 영문 선택값 (예: ``action='순매수'`` → ``action='net_buy'``)

이 모듈과 레거시 경로는 1.0.0에서 제거한다.
"""

from __future__ import annotations

import functools
import inspect
import warnings
from collections.abc import Callable, Iterable, Mapping
from typing import Any, TypeVar

from .exceptions import EcosDeprecationWarning

F = TypeVar("F", bound=Callable[..., Any])

REMOVAL_VERSION = "1.0.0"

# 인자 이름 → {레거시 한글 값: 영문 값}. 같은 인자 이름은 모든 함수에서 같은 매핑을 쓴다.
LEGACY_VALUES: dict[str, dict[str, str]] = {
    "action": {"순매수": "net_buy", "매수": "buy", "매도": "sell"},
    "metric": {"거래대금": "value", "거래량": "volume"},
    "bond_type": {"종류별": "by_type", "시장별": "by_market"},
    "measure": {
        "거래대금": "value",
        "거래량": "volume",
        "상장잔액": "listed_balance",
        "상장종목수": "listed_count",
    },
    "basis": {"신규취급액": "new", "잔액": "outstanding"},
    "loan_type": {"신규": "new", "잔액": "outstanding"},
    "variant": {
        "평잔_계절조정": "average_sa",
        "평잔_원계열": "average_nsa",
        "말잔_계절조정": "end_sa",
        "말잔_원계열": "end_nsa",
    },
    "category": {
        # get_cpi_by_category
        "전체": "all",
        "상품": "goods",
        "서비스": "services",
        "식품_에너지제외": "ex_food_energy",
        "농산물_석유제외": "ex_agri_oil",
        "식료품_비주류음료": "food_beverages",
        "주거_수도_전기": "housing_utilities",
        "교통": "transport",
        # get_household_credit / get_borrower_loan
        "업권별": "by_lender",
        "용도별": "by_purpose",
        "성별": "by_gender",
        "연령별": "by_age",
        "지역별": "by_region",
        "담보유형별": "by_collateral",
        "다중대출별": "by_loan_count",
    },
}


def _warn(message: str) -> None:
    # _warn ← wrapper ← 사용자 코드
    warnings.warn(message, EcosDeprecationWarning, stacklevel=3)


def api_transition(
    *,
    renamed: Mapping[str, str] | None = None,
    legacy_values: Iterable[str] = (),
) -> Callable[[F], F]:
    """키워드 전용으로 바뀐 공개 함수가 0.x 호출 방식을 경고와 함께 받아들이게 한다.

    Parameters
    ----------
    renamed
        ``{옛 인자 이름: 새 인자 이름}``.
    legacy_values
        :data:`LEGACY_VALUES` 의 한글 → 영문 변환을 적용할 인자 이름들.
    """
    renamed = dict(renamed or {})
    value_params = tuple(legacy_values)
    unknown = [p for p in value_params if p not in LEGACY_VALUES]
    if unknown:
        raise ValueError(f"LEGACY_VALUES에 없는 인자: {unknown}")

    def decorator(func: F) -> F:
        params = list(inspect.signature(func).parameters.values())
        n_positional = sum(p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) for p in params)
        keyword_only = [p.name for p in params if p.kind is p.KEYWORD_ONLY]
        name = func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if len(args) > n_positional:
                extra = args[n_positional:]
                if len(extra) > len(keyword_only):
                    raise TypeError(f"{name}()에 인자가 너무 많습니다 (위치 인자 {len(args)}개).")
                mapped = keyword_only[: len(extra)]
                hint = ", ".join(f"{p}=..." for p in mapped)
                _warn(
                    f"{name}()에 인자를 위치로 전달하는 방식은 deprecated이며 "
                    f"{REMOVAL_VERSION}에서 TypeError가 됩니다. "
                    f"키워드로 전달하세요: {name}({hint})"
                )
                for param, value in zip(mapped, extra, strict=True):
                    if param in kwargs:
                        raise TypeError(f"{name}()에 '{param}' 인자가 중복 전달되었습니다.")
                    kwargs[param] = value
                args = args[:n_positional]

            for old, new in renamed.items():
                if old in kwargs:
                    if new in kwargs:
                        raise TypeError(f"{name}()에 '{old}'와 '{new}'를 함께 전달할 수 없습니다.")
                    _warn(
                        f"{name}()의 '{old}' 인자는 deprecated이며 "
                        f"{REMOVAL_VERSION}에서 제거됩니다. '{new}'를 사용하세요."
                    )
                    kwargs[new] = kwargs.pop(old)

            for param in value_params:
                value = kwargs.get(param)
                if isinstance(value, str) and value in LEGACY_VALUES[param]:
                    new_value = LEGACY_VALUES[param][value]
                    _warn(
                        f"{name}({param}={value!r})의 한글 값은 deprecated이며 "
                        f"{REMOVAL_VERSION}에서 제거됩니다. "
                        f"{param}={new_value!r}를 사용하세요."
                    )
                    kwargs[param] = new_value

            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
