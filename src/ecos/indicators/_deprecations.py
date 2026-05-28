"""
Indicator deprecation warnings (#8).

A handful of high-level indicator helpers currently fetch a single
ECOS ``item_code1`` and return it, even though their name/docstring
imply a broader series (e.g. "산업별 GDP", "투자자별 거래"). The
v0.1.6 patch keeps behavior identical but emits a warning so callers
see the limitation, and the v0.3.0 redesign (issue #3 epic) can
change the signature without surprise.

The warning is raised as :class:`EcosPartialCoverageWarning`, a
``UserWarning`` subclass. ``UserWarning`` is shown by default by
Python's warning filter, whereas plain ``DeprecationWarning`` is
suppressed for callers outside ``__main__`` — which would have
silently defeated the whole point of this warning for the typical
notebook/script consumer.

Users who want to silence the warning can do::

    import warnings
    from ecos.indicators._deprecations import EcosPartialCoverageWarning
    warnings.simplefilter("ignore", EcosPartialCoverageWarning)

Call-site convention (#25 review)
---------------------------------
Each affected indicator must call :func:`warn_partial_coverage`
**after input validation** (so a ``ValueError`` for bad arguments
does not also emit a warning) and **before any network request**
(so even a network failure still informs the caller about the
partial coverage). This ordering is enforced by convention only —
new indicators added in this family must follow the same pattern.
"""

from __future__ import annotations

import warnings


class EcosPartialCoverageWarning(UserWarning):
    """Raised when an indicator helper returns only a single ECOS item.

    Subclasses ``UserWarning`` so the message is visible under Python's
    default warning filter, unlike ``DeprecationWarning``.
    """


def warn_partial_coverage(
    func_name: str,
    item_code: str,
    item_label: str,
) -> None:
    """Emit :class:`EcosPartialCoverageWarning` describing the actual coverage.

    Parameters
    ----------
    func_name : str
        Public name of the indicator function (e.g. ``"get_gdp_by_industry"``).
    item_code : str
        The hard-coded ``item_code1`` value being requested under the hood.
    item_label : str
        Human-readable label for ``item_code`` (e.g. ``"농림어업"``).

    Notes
    -----
    ``stacklevel=3`` attributes the warning to the *user's* caller
    (user code → indicator function → this helper → ``warnings.warn``).
    If an indicator function later gets wrapped by a decorator, this
    level must be updated.
    """
    # 메시지 가독성: func_name이 이미 "(variant)" 형태로 끝나면 추가 ()를 붙이지 않는다.
    # 예) "get_bond_yield(종류별)" -> "get_bond_yield(종류별) currently returns..."
    #     "get_gdp_by_industry"    -> "get_gdp_by_industry() currently returns..."
    label = func_name if func_name.endswith(")") else f"{func_name}()"
    warnings.warn(
        (
            f"{label} currently returns only ECOS item_code1={item_code!r} "
            f"({item_label}) and does not cover the full series implied by its name. "
            "The signature will change in v0.3.0 to accept the sub-category or "
            "return the full series; pin to v0.1.x and pass item_code1 yourself "
            "via EcosClient.get_statistic_search if you rely on this behavior."
        ),
        EcosPartialCoverageWarning,
        stacklevel=3,
    )
