"""
E2E 도달성 커버리지 — 카탈로그 카테고리 샘플링 (#111, E12).

ECOS의 어떤 표든 ``get_series`` 로 도달 가능하다는 것을, 동봉 카탈로그의
각 최상위 카테고리에서 **검색가능 표 1개씩 샘플링**해 실제 조회로 검증한다.
전량이 아니라 샘플이며(rate-limit 인지), 샘플 범위와 누락(skip)을 로그로
명시한다.
"""

from __future__ import annotations

import os

import pandas as pd
import pytest

import ecos

pytestmark = pytest.mark.e2e

# 카탈로그 cycle → (get_series period, 최근 윈도우 start, end).
# S(반기)/SM(반월)은 표가 극소수(각 1개)라 샘플에서 제외하고 로그로 남긴다.
_CYCLE_WINDOW = {
    "D": ("D", "20240101", "20240131"),
    "M": ("M", "202401", "202406"),
    "Q": ("Q", "2023Q1", "2023Q4"),
    "A": ("A", "2019", "2023"),
}


@pytest.fixture(scope="module", autouse=True)
def setup_api_key():
    api_key = os.getenv("ECOS_API_KEY")
    if not api_key:
        pytest.skip("ECOS_API_KEY 환경 변수가 설정되지 않았습니다.")
    ecos.set_api_key(api_key)
    yield
    ecos.clear_api_key()


def _first_searchable_leaf(node: dict) -> dict | None:
    """노드 서브트리에서 조회 가능(srch_yn=Y, 지원 cycle) 첫 표를 찾는다."""
    if node.get("srch_yn") == "Y" and node.get("cycle") in _CYCLE_WINDOW:
        return node
    for child in node.get("children", []):
        found = _first_searchable_leaf(child)
        if found is not None:
            return found
    return None


def _build_category_sample() -> tuple[list[dict], list[str]]:
    """최상위 카테고리별 검색가능 표 1개를 샘플로 모은다. (sample, skips)"""
    sample: list[dict] = []
    skips: list[str] = []
    for root in ecos.get_table_tree():
        leaf = _first_searchable_leaf(root)
        if leaf is None:
            skips.append(f"{root['stat_name']}: 지원 cycle 검색가능 표 없음")
        else:
            sample.append(leaf)
    return sample, skips


class TestE2ECatalogReachability:
    def test_sampled_tables_are_reachable(self):
        sample, skips = _build_category_sample()

        # 샘플 범위/누락을 로그로 명시 (#111 요구사항).
        print(f"\n[커버리지 샘플] 최상위 카테고리 {len(sample)}개 표 샘플링:")
        for s in sample:
            print(f"  - {s['stat_code']} [{s['cycle']}] {s['stat_name']}")
        if skips:
            print("[누락/skip]")
            for s in skips:
                print(f"  - {s}")

        assert sample, "샘플이 비어있음 — 카탈로그/트리 확인 필요"

        reached = 0
        for s in sample:
            period, start, end = _CYCLE_WINDOW[s["cycle"]]
            # 도달성 검증: 구조적 에러 없이 DataFrame을 돌려받으면 도달 성공.
            # (데이터가 빈 표도 있을 수 있으나 그 자체로 '도달'은 성립.)
            df = ecos.get_series(s["stat_code"], period, start_date=start, end_date=end)
            assert isinstance(df, pd.DataFrame), f"{s['stat_code']} 비-DataFrame 반환"
            reached += 1
            print(f"  reached {s['stat_code']}: {len(df)} rows")

        print(f"[결과] {reached}/{len(sample)} 카테고리 표 도달 성공")
        assert reached == len(sample)
