"""라이브러리가 사용하는 모든 stat_code의 ECOS 스냅샷을 라이브에서 재생성.

산출물 (오프라인 매핑 정합성 가드 tests/test_mapping_consistency.py 의 기준 데이터):
- tests/fixtures/ecos_item_catalog.json   {stat_code: {item_code: [units...]}}
- tests/fixtures/ecos_table_structure.json {stat_code: {cycles: [...], axes: {item_codeN: n}}}

사용:
    ECOS_API_KEY=... python scripts/snapshot_item_units.py            # 재생성
    ECOS_API_KEY=... python scripts/snapshot_item_units.py --check    # 라이브와 drift 검사(쓰기 없음)

--check 는 커밋된 스냅샷이 라이브 ECOS와 어긋나면 비0 종료(야간 CI 용). ECOS rate limit:
3분 300회 / 초과 시 30분 차단 — 본 스크립트는 stat_code 당 list_items + statistic_search
각 1회(현재 ~56표 × 2 = ~112회)만 호출한다.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import ecos
import ecos.constants as c
from ecos.parser import parse_response

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ecos_item_catalog.json"
STRUCT_FIXTURE = (
    Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ecos_table_structure.json"
)

# 축 구조 probe 용 대표 조회 범위 (주기별).
_WINDOWS = {
    "D": ("20240101", "20240105"),
    "M": ("202401", "202402"),
    "Q": ("2024Q1", "2024Q2"),
    "A": ("2023", "2024"),
}
_PERIOD_PREF = ["M", "Q", "A", "D"]


def library_stat_codes() -> set[str]:
    """라이브러리가 실제로 참조하는 모든 stat_code."""
    codes: set[str] = set()
    for k, v in vars(c).items():
        if k.startswith("STAT_") and isinstance(v, str):
            codes.add(v)
    for dname in (
        "MONEY_SUPPLY_STAT_CODES",
        "M1_VARIANTS",
        "M2_VARIANTS",
        "M2_HOLDER_VARIANTS",
        "BORROWER_LOAN_STAT_CODES",
        "GDP_BY_INDUSTRY_VARIANTS",
        "GDP_BY_EXPENDITURE_VARIANTS",
    ):
        codes.update(getattr(c, dname).values())
    for stat, _item in c.CPI_CATEGORY_CODES.values():
        codes.add(stat)
    return codes


def fetch_live() -> tuple[dict, dict]:
    """(item_catalog, table_structure) 를 라이브 ECOS 에서 수집한다."""
    ecos.set_api_key(os.environ["ECOS_API_KEY"])
    client = ecos.get_client()
    catalog: dict = {}
    structure: dict = {}
    for sc in sorted(library_stat_codes()):
        df = ecos.list_items(sc)
        m: dict[str, set] = {}
        cycles: set[str] = set()
        for r in df.to_dict("records"):
            m.setdefault(r["item_code"], set()).add(str(r.get("unit")))
            if r.get("cycle"):
                cycles.add(str(r["cycle"]))
        catalog[sc] = {k: sorted(v) for k, v in sorted(m.items())}

        # 축 구조 probe — 선호 주기로 1회 조회해 item_codeN distinct 수를 센다.
        period = next(
            (p for p in _PERIOD_PREF if p in cycles), sorted(cycles)[0] if cycles else "M"
        )
        s, e = _WINDOWS[period]
        adf = parse_response(
            client.get_statistic_search(stat_code=sc, period=period, start_date=s, end_date=e)
        )
        axes = {}
        for ax in ("item_code1", "item_code2", "item_code3", "item_code4"):
            if ax in adf.columns:
                vals = [x for x in adf[ax].dropna().unique() if str(x) != ""]
                if vals:
                    axes[ax] = len(vals)
        structure[sc] = {"cycles": sorted(cycles), "axes": axes}
    return catalog, structure


def _diff(committed: dict, live: dict, label: str) -> bool:
    """일치하면 True. 불일치면 차이를 출력하고 False."""
    if committed == live:
        print(f"OK: {label} 스냅샷이 라이브 ECOS와 일치.")
        return True
    only_live = sorted(set(live) - set(committed))
    only_committed = sorted(set(committed) - set(live))
    changed = sorted(sc for sc in set(live) & set(committed) if live[sc] != committed[sc])
    print(f"DRIFT 감지 ({label}) — 스냅샷 재생성 필요 (scripts/snapshot_item_units.py):")
    if only_live:
        print(f"  라이브에만 있는 stat_code: {only_live}")
    if only_committed:
        print(f"  스냅샷에만 있는 stat_code: {only_committed}")
    if changed:
        print(f"  내용이 바뀐 stat_code: {changed}")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="라이브와 drift 검사 (쓰기 없음)")
    args = ap.parse_args()

    catalog, structure = fetch_live()

    if args.check:
        ok = _diff(json.loads(FIXTURE.read_text()), catalog, "item_catalog")
        ok = _diff(json.loads(STRUCT_FIXTURE.read_text()), structure, "table_structure") and ok
        return 0 if ok else 1

    FIXTURE.write_text(json.dumps(catalog, ensure_ascii=False, indent=1, sort_keys=True))
    STRUCT_FIXTURE.write_text(json.dumps(structure, ensure_ascii=False, indent=1, sort_keys=True))
    print(f"Saved {FIXTURE} ({len(catalog)} stat_codes)")
    print(f"Saved {STRUCT_FIXTURE} ({len(structure)} stat_codes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
