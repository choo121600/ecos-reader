"""
frequency 어휘 통일 + deprecation 경로 (#20).

과거에는 카테고리마다 ``frequency`` 값 표기가 달랐다:

- ``growth.py``  : ``"Q"`` / ``"A"`` (단일 문자)
- ``interest_rate.py`` : ``"D"`` / ``"M"`` (단일 문자)
- ``stock.py``   : ``"daily"`` / ``"monthly"`` (풀네임)

#20에서 정식(canonical) 어휘를 풀네임으로 통일한다::

    daily | monthly | quarterly | annual

기존 단일 문자 표기(``D/M/Q/A``)는 한동안 함께 허용하되
:class:`EcosDeprecationWarning` 을 발생시키고, v0.4.0에서 제거한다.

경고 클래스 설계 (#19)
----------------------
파이썬의 기본 경고 필터는 ``DeprecationWarning`` 을 ``__main__`` 밖
호출자에게는 **숨긴다**. 노트북/스크립트 사용자가 마이그레이션 안내를
보지 못하면 deprecation의 의미가 사라지므로, 가시성이 보장되는
``UserWarning`` 하위 클래스를 사용한다.

경고를 끄려면::

    import warnings
    from ecos import EcosDeprecationWarning
    warnings.simplefilter("ignore", EcosDeprecationWarning)
"""

from __future__ import annotations

import warnings

# 레거시 단일 문자 → 정식 풀네임 매핑.
_LEGACY_FREQUENCY_ALIASES = {
    "D": "daily",
    "M": "monthly",
    "Q": "quarterly",
    "A": "annual",
}


class EcosDeprecationWarning(UserWarning):
    """Deprecated 입력값(레거시 frequency 표기 등) 사용 시 발생.

    기본 경고 필터에서 숨겨지는 ``DeprecationWarning`` 대신
    ``UserWarning`` 을 상속해 노트북/스크립트 사용자에게도 보이도록 한다.
    """


def normalize_frequency(
    value: str,
    *,
    allowed: tuple[str, ...],
    func_name: str,
) -> str:
    """레거시 frequency 표기를 정식 어휘로 정규화한다.

    Parameters
    ----------
    value : str
        호출자가 전달한 frequency 값. 정식(``daily``/``monthly``/
        ``quarterly``/``annual``) 또는 레거시(``D``/``M``/``Q``/``A``).
    allowed : tuple of str
        해당 지표가 지원하는 정식 frequency 값의 튜플
        (예: ``("quarterly", "annual")``).
    func_name : str
        경고/에러 메시지에 쓰이는 공개 함수명(예: ``"get_gdp"``).

    Returns
    -------
    str
        정식 어휘로 정규화된 frequency 값.

    Raises
    ------
    ValueError
        정규화 결과가 ``allowed`` 에 없을 때.

    Notes
    -----
    레거시 별칭이 ``allowed`` 범위 내로 정규화되는 경우에만
    :class:`EcosDeprecationWarning` 을 발생시킨다. 잘못된 값
    (예: ``"W"``)은 경고 없이 곧바로 ``ValueError`` 로 처리한다.

    ``stacklevel=3`` 은 사용자의 호출 지점을 가리킨다
    (user → indicator 함수 → normalize_frequency → ``warnings.warn``).
    """
    canonical = _LEGACY_FREQUENCY_ALIASES.get(value, value)

    if value in _LEGACY_FREQUENCY_ALIASES and canonical in allowed:
        warnings.warn(
            f"{func_name}(): frequency={value!r}는 deprecated입니다. "
            f"frequency={canonical!r}를 사용하세요. "
            "단일 문자 표기(D/M/Q/A)는 v0.4.0에서 제거됩니다.",
            EcosDeprecationWarning,
            stacklevel=3,
        )

    if canonical not in allowed:
        allowed_str = " 또는 ".join(repr(a) for a in allowed)
        raise ValueError(f"frequency는 {allowed_str} 중 하나여야 합니다.")

    return canonical
