"""
카탈로그 탐색 API 단위 테스트 (#103).

동봉된 정적 스냅샷을 사용하므로 네트워크 호출이 없다(오프라인).
"""

from __future__ import annotations

import pandas as pd

import ecos
from ecos.catalog import _ROOT_PARENT, _load_catalog


class TestLoadCatalog:
    def test_loads_snapshot(self):
        df = ecos.load_catalog()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        # 필수 컬럼 존재
        for col in ("stat_code", "stat_name", "cycle", "srch_yn", "p_stat_code"):
            assert col in df.columns

    def test_codes_are_strings(self):
        # 숫자처럼 보이는 stat_code가 문자열로 유지(앞자리 0 보존)
        df = ecos.load_catalog()
        assert df["stat_code"].map(type).eq(str).all()

    def test_returns_copy_not_cached_original(self):
        a = ecos.load_catalog()
        a.loc[0, "stat_name"] = "MUTATED"
        b = ecos.load_catalog()
        assert b.loc[0, "stat_name"] != "MUTATED"

    def test_has_searchable_and_category_nodes(self):
        df = _load_catalog()
        counts = df["srch_yn"].value_counts()
        assert counts.get("Y", 0) > 0  # 조회 가능 통계표
        assert counts.get("N", 0) > 0  # 분류용 카테고리


class TestSearchTables:
    def test_keyword_match_case_insensitive(self):
        df = ecos.search_tables("기준금리")
        assert not df.empty
        assert df["stat_name"].str.contains("기준금리").all()

    def test_searchable_only_default(self):
        df = ecos.search_tables("")  # 전체(검색 가능 only)
        assert (df["srch_yn"] == "Y").all()

    def test_include_categories(self):
        all_nodes = ecos.search_tables("", searchable_only=False)
        searchable = ecos.search_tables("")
        assert len(all_nodes) > len(searchable)

    def test_no_match_returns_empty(self):
        df = ecos.search_tables("존재하지않는통계표명ZZZ")
        assert df.empty

    def test_substring_not_regex(self):
        # 정규식이 아닌 부분 문자열로 처리되어 특수문자가 그대로 매칭됨
        df = ecos.search_tables("1.", searchable_only=False)
        assert isinstance(df, pd.DataFrame)


class TestListTables:
    def test_root_when_parent_none(self):
        roots = ecos.list_tables()
        assert not roots.empty
        # 루트 노드의 부모는 모두 '*'
        assert (roots["p_stat_code"] == _ROOT_PARENT).all()

    def test_children_of_parent(self):
        roots = ecos.list_tables()
        first_root = roots.iloc[0]["stat_code"]
        children = ecos.list_tables(first_root)
        assert not children.empty
        assert (children["p_stat_code"] == first_root).all()

    def test_unknown_parent_empty(self):
        assert ecos.list_tables("NONEXISTENT").empty


class TestGetTableTree:
    def test_tree_structure(self):
        tree = ecos.get_table_tree()
        assert isinstance(tree, list)
        assert len(tree) > 0
        node = tree[0]
        assert {"stat_code", "stat_name", "cycle", "srch_yn", "children"} <= node.keys()
        assert isinstance(node["children"], list)

    def test_tree_node_count_matches_catalog(self):
        # 트리 전체 노드 수 == 카탈로그 행 수 (루트 부모 '*' 제외 모든 노드 포함)
        df = _load_catalog()

        def count(nodes):
            return sum(1 + count(n["children"]) for n in nodes)

        assert count(ecos.get_table_tree()) == len(df)

    def test_tree_has_nested_children(self):
        tree = ecos.get_table_tree()
        # 최소 한 노드는 자식을 가진다(중첩 구조 확인)
        assert any(node["children"] for node in tree)


def test_public_exports():
    for name in ("search_tables", "list_tables", "get_table_tree", "load_catalog"):
        assert hasattr(ecos, name)
        assert name in ecos.__all__


def test_offline_no_api_key_needed():
    # API 키 미설정 상태에서도 동작(오프라인)
    ecos.clear_api_key()
    assert not ecos.search_tables("금리").empty
    assert not ecos.list_tables().empty
    assert len(ecos.get_table_tree()) > 0
