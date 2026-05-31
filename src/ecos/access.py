"""
범용 조회 API (#100, ADR 0001).

임의의 ``(stat_code, period, item_code)`` 를 받아 정규화된 long-format tidy
DataFrame을 반환하는 공개 함수 :func:`get_series` 를 제공한다. ECOS의 모든
통계표(700여 개)에 도달하는 단일 진입점이며, 기존 엔진
(``EcosClient.get_statistic_search`` → :func:`~ecos.parser.parse_response` →
:func:`~ecos.parser.normalize_stat_result`)을 재사용한다.

시그니처·출력 스키마·period 어휘·에러 의미는
``docs/adr/0001-generic-access-api.md`` 에서 확정되었다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .client import get_client
from .parser import normalize_stat_result, parse_response

if TYPE_CHECKING:
    import pandas as pd

    from .client import EcosClient

# period 어휘 → ECOS 원시 코드 매핑 (ADR §2.3).
# 정식 풀네임과 원시 코드 passthrough를 모두 수용하며, 키는 소문자로 두어
# 대소문자를 구분하지 않는 정규화를 구현한다.
_PERIOD_MAP: dict[str, str] = {
    # 정식 어휘(canonical)
    "daily": "D",
    "monthly": "M",
    "quarterly": "Q",
    "annual": "A",
    "semiannual": "S",
    "semimonthly": "SM",
    # 원시 코드 passthrough
    "d": "D",
    "m": "M",
    "q": "Q",
    "a": "A",
    "s": "S",
    "sm": "SM",
}

# 에러 메시지에 노출할 정식 어휘 목록(원시 코드 제외).
_PERIOD_CANONICAL = ("daily", "monthly", "quarterly", "annual", "semiannual", "semimonthly")

# ECOS StatisticSearch가 지원하는 항목축 개수.
_MAX_ITEM_AXES = 4

# list_items 정규화 출력의 선호 컬럼 순서(StatisticItemList 기준).
# stat_code/stat_name은 입력과 중복이라 제외하며, 전부 비어있는 컬럼은 동적으로 제거한다.
_ITEM_COLUMNS = [
    "item_code",
    "item_name",
    "cycle",
    "start_time",
    "end_time",
    "unit",
    "data_cnt",
    "p_item_code",
    "p_item_name",
    "grp_code",
    "grp_name",
    "weight",
]


def normalize_period(period: str) -> str:
    """period 어휘를 ECOS 원시 코드로 정규화한다 (ADR §2.3).

    Parameters
    ----------
    period : str
        조회 주기. 정식 어휘(``daily``/``monthly``/``quarterly``/``annual``/
        ``semiannual``/``semimonthly``), 원시 코드(``D``/``M``/``Q``/``A``/
        ``S``/``SM``)를 모두 수용하며 대소문자를 구분하지 않는다.

    Returns
    -------
    str
        ECOS 원시 코드(``D``/``M``/``Q``/``A``/``S``/``SM``).

    Raises
    ------
    ValueError
        매핑표에 없는 값일 때(네트워크 호출 전 fail-fast).
    """
    key = period.strip().lower()
    if key not in _PERIOD_MAP:
        allowed = ", ".join(_PERIOD_CANONICAL)
        raise ValueError(
            f"get_series(): period는 {allowed} "
            f"(또는 원시 코드 D/M/Q/A/S/SM) 중 하나여야 합니다. (받은 값: {period!r})"
        )
    return _PERIOD_MAP[key]


def _resolve_item_codes(item_code: str | list[str] | None) -> list[str]:
    """``item_code`` 선택자를 ``item_code1..4`` 4축으로 매핑한다 (ADR §2.1).

    ``None`` 은 전체(모든 축 빈 문자열), 단일 문자열은 1축, 리스트는 다축으로
    매핑한다. 리스트 길이가 4를 초과하면 네트워크 호출 전 ``ValueError``.
    """
    if item_code is None:
        codes: list[str] = []
    elif isinstance(item_code, str):
        codes = [item_code]
    else:
        codes = list(item_code)

    if len(codes) > _MAX_ITEM_AXES:
        raise ValueError(
            f"get_series(): item_code 리스트는 최대 {_MAX_ITEM_AXES}개 축까지 "
            f"가능합니다. (받은 개수: {len(codes)})"
        )

    # 4축까지 빈 문자열로 패딩해 get_statistic_search 의 item_code1..4 에 매핑.
    return (codes + [""] * _MAX_ITEM_AXES)[:_MAX_ITEM_AXES]


def _is_empty_axis(series: pd.Series) -> bool:
    """항목축 컬럼이 전부 빈 문자열/결측이면 True (ADR §2.2 빈 축 제거)."""
    stripped = series.fillna("").astype(str).str.strip()
    return bool((stripped == "").all())


def _to_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """``parse_response`` 결과를 long-format tidy 스키마로 정규화한다 (ADR §2.2).

    ``date``/``value``/``unit`` 와 비어있지 않은 항목축(``item_code{n}`` +
    대응 ``item_name{n}``)만 선택한다. 새 파싱 로직 없이
    :func:`~ecos.parser.normalize_stat_result` 를 재사용한다.
    """
    columns: list[str] = ["date"]  # normalize_stat_result가 time→date 생성 후 선택
    for base in ("value", "unit"):
        if base in df.columns:
            columns.append(base)

    for n in range(1, _MAX_ITEM_AXES + 1):
        code_col = f"item_code{n}"
        name_col = f"item_name{n}"
        # 모두 빈 축은 제외해 잡음을 없앤다.
        if code_col in df.columns and not _is_empty_axis(df[code_col]):
            columns.append(code_col)
            if name_col in df.columns:
                columns.append(name_col)

    return normalize_stat_result(df, columns=columns, date_col="time")


def get_series(
    stat_code: str,
    period: str,
    *,
    start_date: str,
    end_date: str,
    item_code: str | list[str] | None = None,
    tidy: bool = True,
    client: EcosClient | None = None,
) -> pd.DataFrame:
    """임의의 ECOS 통계표를 조회해 정규화 DataFrame으로 반환한다 (ADR 0001).

    ECOS의 모든 통계표에 도달하는 범용 접근의 단일 진입점이다. 도메인 지표
    함수(:func:`~ecos.get_base_rate` 등)와 달리 ``(stat_code, period,
    item_code)`` 를 직접 받아, 큐레이션 없이 어떤 표든 조회할 수 있다.

    Parameters
    ----------
    stat_code : str
        ECOS 통계표코드 (예: ``"722Y001"``).
    period : str
        조회 주기. 정식 어휘(``daily``/``monthly``/``quarterly``/``annual``/
        ``semiannual``/``semimonthly``) 또는 원시 코드(``D``/``M``/``Q``/``A``/
        ``S``/``SM``). 대소문자를 구분하지 않는다(ADR §2.3).
    start_date : str
        조회 시작 시점. ``period`` 에 맞는 ECOS 표기
        (``YYYY``/``YYYYMM``/``YYYYMMDD`` 등). 키워드 전용.
    end_date : str
        조회 종료 시점. 키워드 전용.
    item_code : str or list of str, optional
        항목코드 선택자. ``None``(전체), 단일 문자열, 또는 길이 ≤ 4 리스트(다축).
        리스트가 4축을 초과하면 ``ValueError``. 키워드 전용.
    tidy : bool, default True
        ``True`` 면 long-format tidy 스키마로 정규화(ADR §2.2). ``False`` 면
        :func:`~ecos.parser.parse_response` 의 원본 컬럼(snake_case)을 그대로
        반환(이스케이프 해치). 키워드 전용.
    client : EcosClient, optional
        사용할 클라이언트. 생략 시 전역 클라이언트(:func:`~ecos.get_client`).

    Returns
    -------
    pd.DataFrame
        ``tidy=True`` 일 때 컬럼: ``date``, ``value``, (있으면) ``unit``,
        그리고 비어있지 않은 ``item_code{n}``/``item_name{n}`` 축. 한 행 =
        한 (시점 × 항목조합) 관측치. 빈 결과는 빈 DataFrame.

    Raises
    ------
    ValueError
        잘못된 ``period`` 또는 ``item_code`` 리스트 길이 > 4 (네트워크 호출 전).
    EcosAPIError
        존재하지 않는 ``stat_code`` 등 ECOS 비즈니스 에러.

    Examples
    --------
    >>> import ecos
    >>> # 기준금리(722Y001) 월별 조회
    >>> df = ecos.get_series(
    ...     "722Y001", "monthly",
    ...     start_date="202401", end_date="202412",
    ...     item_code="0101000",
    ... )
    >>> df.columns.tolist()
    ['date', 'value', 'unit', 'item_code1', 'item_name1']

    >>> # 다축 조회 (item_code 리스트)
    >>> df = ecos.get_series(
    ...     "200Y001", "Q",
    ...     start_date="2024Q1", end_date="2024Q4",
    ...     item_code=["10101", "10102"],
    ... )

    >>> # 원본 컬럼이 필요하면 tidy=False
    >>> raw = ecos.get_series(
    ...     "722Y001", "M",
    ...     start_date="202401", end_date="202412", tidy=False,
    ... )
    """
    # 입력 검증은 네트워크 비용 이전에 fail-fast (ADR §2.4).
    raw_period = normalize_period(period)
    item_codes = _resolve_item_codes(item_code)

    client = client or get_client()
    response = client.get_statistic_search(
        stat_code=stat_code,
        period=raw_period,
        start_date=start_date,
        end_date=end_date,
        item_code1=item_codes[0],
        item_code2=item_codes[1],
        item_code3=item_codes[2],
        item_code4=item_codes[3],
    )

    df = parse_response(response)

    if not tidy or df.empty:
        return df

    return _to_tidy(df)


def list_items(stat_code: str, *, client: EcosClient | None = None) -> pd.DataFrame:
    """통계표의 세부 항목 목록을 조회해 정규화 DataFrame으로 반환한다 (#104).

    :func:`get_series` 로 조회할 때 필요한 ``item_code`` 를 찾기 위한 탐색
    함수다. ECOS ``StatisticItemList`` 를 래핑하며, 한 항목은 지원 주기
    (``cycle``)마다 별도 행으로 나온다(예: 같은 항목의 일/월/연 주기).

    Parameters
    ----------
    stat_code : str
        ECOS 통계표코드 (예: ``"722Y001"``).
    client : EcosClient, optional
        사용할 클라이언트. 생략 시 전역 클라이언트(:func:`~ecos.get_client`).
        클라이언트의 캐시 설정이 그대로 적용된다.

    Returns
    -------
    pd.DataFrame
        컬럼: ``item_code``, ``item_name``, ``cycle``, ``start_time``,
        ``end_time``, ``unit``, ``data_cnt`` 와 (비어있지 않으면)
        ``p_item_code``/``p_item_name``/``grp_code``/``grp_name``/``weight``.
        전부 비어있는 컬럼은 제외한다. 항목이 없으면 빈 DataFrame.

    Examples
    --------
    >>> import ecos
    >>> items = ecos.list_items("722Y001")
    >>> items[["item_code", "item_name", "cycle"]].head(1)
    >>> # 찾은 item_code로 바로 조회
    >>> df = ecos.get_series(
    ...     "722Y001", "monthly",
    ...     start_date="202401", end_date="202412",
    ...     item_code=items.iloc[0]["item_code"],
    ... )
    """
    client = client or get_client()
    response = client.get_statistic_item_list(stat_code=stat_code, start=1, end=100000)

    df = parse_response(response)
    if df.empty:
        return df

    # 존재하면서 전부 비어있지 않은 컬럼만 선택(_is_empty_axis는 빈문자/NaN 모두 처리).
    columns = [c for c in _ITEM_COLUMNS if c in df.columns and not _is_empty_axis(df[c])]
    return df[columns].reset_index(drop=True)
