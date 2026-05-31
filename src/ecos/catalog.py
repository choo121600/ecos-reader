"""
통계표 카탈로그 탐색 API (#103).

ECOS 전체 통계표 목록을 패키지에 정적 스냅샷(``data/catalog.csv.gz``)으로
동봉하고, 네트워크/rate limit 없이 **오프라인으로** 탐색하는 공개 함수를
제공한다.

- :func:`search_tables` — 키워드로 통계표 검색
- :func:`list_tables` — 특정 부모(카테고리) 아래 직계 노드 나열
- :func:`get_table_tree` — 전체 카탈로그를 트리(중첩 dict)로 반환

스냅샷은 ``p_stat_code``(부모 코드)/``stat_code``/``stat_name``/``cycle``/
``srch_yn``(조회 가능 여부)/``org_name`` 컬럼을 가지며, 최상위 노드의
``p_stat_code`` 는 ``"*"`` 다. ``srch_yn == "Y"`` 인 노드만 :func:`get_series`
로 실제 조회할 수 있는 통계표다(나머지는 분류용 카테고리 노드).
"""

from __future__ import annotations

import gzip
import io
from functools import lru_cache
from importlib.resources import files
from typing import Any

import pandas as pd

# 최상위 노드의 부모 코드 표식 (ECOS StatisticTableList 규약).
_ROOT_PARENT = "*"

# 스냅샷 컬럼 순서.
_COLUMNS = ["stat_code", "stat_name", "cycle", "srch_yn", "p_stat_code", "org_name"]


@lru_cache(maxsize=1)
def _load_catalog() -> pd.DataFrame:
    """동봉된 카탈로그 스냅샷을 DataFrame으로 로드한다(프로세스 1회 캐시).

    모든 컬럼을 문자열로 읽고 결측 추론을 끈다(``stat_code`` 가 숫자처럼
    보여도 문자열로 유지). 반환값은 캐시된 원본이므로 :func:`load_catalog`
    를 통해 복사본으로 제공한다.
    """
    raw = files("ecos.data").joinpath("catalog.csv.gz").read_bytes()
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
        df = pd.read_csv(f, dtype=str, keep_default_na=False)
    # 컬럼 순서 정규화(존재하는 컬럼만).
    ordered = [c for c in _COLUMNS if c in df.columns]
    return df[ordered]


def load_catalog() -> pd.DataFrame:
    """전체 카탈로그 스냅샷을 DataFrame 복사본으로 반환한다.

    Returns
    -------
    pd.DataFrame
        컬럼: ``stat_code``, ``stat_name``, ``cycle``, ``srch_yn``,
        ``p_stat_code``, ``org_name``. 카테고리 노드와 조회 가능 통계표를
        모두 포함한다.
    """
    return _load_catalog().copy()


def search_tables(keyword: str, *, searchable_only: bool = True) -> pd.DataFrame:
    """키워드로 통계표를 검색한다(오프라인, 대소문자 무시).

    Parameters
    ----------
    keyword : str
        통계표명(``stat_name``)에 대한 부분 일치 검색어. 대소문자를 구분하지
        않는다. 빈 문자열이면 (필터 적용된) 전체를 반환한다.
    searchable_only : bool, default True
        ``True`` 면 실제 조회 가능한 통계표(``srch_yn == "Y"``)만 반환한다.
        ``False`` 면 분류용 카테고리 노드까지 포함한다.

    Returns
    -------
    pd.DataFrame
        매칭된 통계표. :func:`load_catalog` 와 동일한 컬럼 구성.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.search_tables("기준금리")
    >>> df[["stat_code", "stat_name"]].head(1)
    """
    df = _load_catalog()
    if searchable_only:
        df = df[df["srch_yn"] == "Y"]
    if keyword:
        mask = df["stat_name"].str.contains(keyword, case=False, na=False, regex=False)
        df = df[mask]
    return df.reset_index(drop=True).copy()


def list_tables(parent: str | None = None) -> pd.DataFrame:
    """특정 부모 노드의 직계 자식을 나열한다(오프라인).

    Parameters
    ----------
    parent : str, optional
        부모 ``stat_code``. ``None`` 이면 최상위(루트) 노드를 반환한다.

    Returns
    -------
    pd.DataFrame
        ``parent`` 의 직계 자식. :func:`load_catalog` 와 동일한 컬럼 구성.
        존재하지 않는 부모면 빈 DataFrame.

    Examples
    --------
    >>> import ecos
    >>> roots = ecos.list_tables()            # 최상위 카테고리
    >>> children = ecos.list_tables("0000000001")
    """
    df = _load_catalog()
    key = _ROOT_PARENT if parent is None else parent
    return df[df["p_stat_code"] == key].reset_index(drop=True).copy()


def get_table_tree() -> list[dict[str, Any]]:
    """전체 카탈로그를 중첩 트리로 반환한다(오프라인).

    Returns
    -------
    list of dict
        최상위 노드의 리스트. 각 노드는
        ``{"stat_code", "stat_name", "cycle", "srch_yn", "children": [...]}``
        형태이며 ``children`` 은 직계 자식 노드의 리스트다(잎이면 빈 리스트).
    """
    df = _load_catalog()

    # 부모 코드 -> 자식 행 목록.
    children_by_parent: dict[str, list[dict[str, Any]]] = {}
    for row in df.itertuples(index=False):
        children_by_parent.setdefault(row.p_stat_code, []).append(
            {
                "stat_code": row.stat_code,
                "stat_name": row.stat_name,
                "cycle": row.cycle,
                "srch_yn": row.srch_yn,
            }
        )

    def build(node: dict[str, Any]) -> dict[str, Any]:
        node["children"] = [build(c) for c in children_by_parent.get(node["stat_code"], [])]
        return node

    return [build(root) for root in children_by_parent.get(_ROOT_PARENT, [])]
