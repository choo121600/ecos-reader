"""
커버리지 검증 — 카탈로그 정합 + 큐레이션 일관성 (#111, E12, 오프라인).

동봉 카탈로그가 내부적으로 정합하고, 큐레이션된 도메인 함수가 참조하는
통계표가 카탈로그에 실제로 존재하는지(드리프트 방지) 검증한다. 네트워크
호출이 없으므로 rate-limit과 무관하다. 라이브 도달성 샘플링은
``tests/test_e2e_coverage.py`` 참고.
"""

from __future__ import annotations

import ecos
from ecos import constants as const
from ecos.catalog import _ROOT_PARENT
from ecos.indicators._registry import INDICATORS

# 큐레이션 도메인 함수가 단일 진실원천으로 쓰는 통계표코드.
# (레지스트리 외 직접 함수들 — 카탈로그와의 드리프트를 막는 가드.)
_CURATED_STAT_CODES = {
    "base_rate/treasury": const.STAT_BASE_RATE,
    "market_rate": const.STAT_MARKET_RATE,
    "exchange_rate": const.STAT_EXCHANGE_RATE,
    "bop": const.STAT_BOP,
    "bsi": const.STAT_BSI,
    "csi": const.STAT_CSI,
    "industrial": const.STAT_INDUSTRIAL_PRODUCTION,
    "facility": const.STAT_FACILITY_INVESTMENT,
    "gdp_real": const.STAT_GDP_REAL,
    "gdp_nominal": const.STAT_GDP_NOMINAL,
    "bank_lending": const.STAT_BANK_LENDING,
}


class TestCatalogIntegrity:
    def test_nonempty_and_columns(self):
        df = ecos.load_catalog()
        assert not df.empty
        for col in ("stat_code", "stat_name", "cycle", "srch_yn", "p_stat_code"):
            assert col in df.columns

    def test_searchable_have_cycle(self):
        # 검색가능(srch_yn=Y) 표는 모두 주기(cycle)를 가진다.
        df = ecos.load_catalog()
        searchable = df[df["srch_yn"] == "Y"]
        assert (searchable["cycle"].str.strip() != "").all()

    def test_parent_refs_resolve(self):
        # 모든 노드의 부모는 루트('*') 이거나 카탈로그 내 다른 노드여야 한다.
        df = ecos.load_catalog()
        codes = set(df["stat_code"])
        parents = set(df["p_stat_code"]) - {_ROOT_PARENT}
        dangling = parents - codes
        assert not dangling, f"부모 코드가 카탈로그에 없음: {sorted(dangling)[:10]}"

    def test_has_top_level_categories(self):
        assert len(ecos.list_tables()) > 0

    def test_tree_covers_all_nodes(self):
        df = ecos.load_catalog()

        def count(nodes):
            return sum(1 + count(n["children"]) for n in nodes)

        assert count(ecos.get_table_tree()) == len(df)


class TestCurationConsistency:
    def test_registry_stat_codes_in_catalog(self):
        codes = set(ecos.load_catalog()["stat_code"])
        missing = [s.stat_code for s in INDICATORS.values() if s.stat_code not in codes]
        assert not missing, f"레지스트리 stat_code가 카탈로그에 없음: {missing}"

    def test_curated_stat_codes_in_catalog(self):
        codes = set(ecos.load_catalog()["stat_code"])
        missing = {k: v for k, v in _CURATED_STAT_CODES.items() if v not in codes}
        assert not missing, f"큐레이션 stat_code가 카탈로그에 없음: {missing}"

    def test_search_finds_curated_table(self):
        # 큐레이션된 표는 키워드 탐색으로도 찾을 수 있어야 한다(샘플).
        hits = ecos.search_tables("소비자물가")
        assert (hits["stat_code"] == "901Y009").any()
