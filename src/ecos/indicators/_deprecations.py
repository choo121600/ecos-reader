"""
Indicator deprecation warnings (#8).

A handful of high-level indicator helpers currently fetch a single
ECOS `item_code1` and return it, even though their name/docstring
imply a broader series (e.g. "산업별 GDP", "투자자별 거래"). The
v0.1.6 patch keeps behavior identical but emits a DeprecationWarning
so callers see the limitation, and the v0.3.0 redesign (issue #3
epic) can change the signature without surprise.
"""

from __future__ import annotations

import warnings


def warn_partial_coverage(
    func_name: str,
    item_code: str,
    item_label: str,
) -> None:
    """Emit a DeprecationWarning that the helper returns a single ECOS item only.

    Parameters
    ----------
    func_name : str
        Public name of the indicator function (e.g. ``"get_gdp_by_industry"``).
    item_code : str
        The hard-coded ``item_code1`` value being requested under the hood.
    item_label : str
        Human-readable label for ``item_code`` (e.g. ``"농림어업"``).
    """
    warnings.warn(
        (
            f"{func_name}() currently returns only ECOS item_code1={item_code!r} "
            f"({item_label}) and does not cover the full series implied by its name. "
            "The signature will change in v0.3.0 to accept the sub-category or "
            "return the full series; pin to v0.1.x and pass item_code1 yourself "
            "via EcosClient.get_statistic_search if you rely on this behavior."
        ),
        DeprecationWarning,
        stacklevel=3,
    )
