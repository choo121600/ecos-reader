"""
frequency 어휘 통일 (#20, #57).

과거에는 카테고리마다 ``frequency`` 값 표기가 달랐고, 레거시 단일 문자
표기(``D``/``M``/``Q``/``A``)를 :class:`EcosDeprecationWarning` 과 함께
한시적으로 허용했다.

v0.4.0(#57)부터 레거시 표기는 **제거**되었으며, 정식(canonical) 풀네임
어휘만 허용한다::

    daily | monthly | quarterly | annual

정식이 아닌 값은 경고 없이 즉시 :class:`ValueError` 로 처리한다.
"""

from __future__ import annotations


def normalize_frequency(
    value: str,
    *,
    allowed: tuple[str, ...],
    func_name: str,
) -> str:
    """frequency 값을 검증한다.

    Parameters
    ----------
    value : str
        호출자가 전달한 frequency 값
        (정식 어휘 ``daily``/``monthly``/``quarterly``/``annual``).
    allowed : tuple of str
        해당 지표가 지원하는 정식 frequency 값의 튜플
        (예: ``("quarterly", "annual")``).
    func_name : str
        에러 메시지에 쓰이는 공개 함수명(예: ``"get_gdp"``).

    Returns
    -------
    str
        검증된 frequency 값.

    Raises
    ------
    ValueError
        ``value`` 가 ``allowed`` 에 없을 때. 레거시 단일 문자 표기
        (``D``/``M``/``Q``/``A``)는 v0.4.0에서 제거되었으므로 동일하게
        ``ValueError`` 로 처리된다.
    """
    if value not in allowed:
        allowed_str = " 또는 ".join(repr(a) for a in allowed)
        raise ValueError(f"{func_name}(): frequency는 {allowed_str} 중 하나여야 합니다.")

    return value
