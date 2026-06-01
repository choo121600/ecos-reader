"""라이브러리가 사용하는 모든 stat_code의 item→단위 스냅샷을 ECOS 라이브에서 재생성.

산출물: tests/fixtures/ecos_item_catalog.json  ({stat_code: {item_code: [units...]}})
오프라인 매핑 정합성 가드(tests/test_mapping_consistency.py)의 기준 데이터다.

사용:
    ECOS_API_KEY=... python scripts/snapshot_item_units.py            # 재생성
    ECOS_API_KEY=... python scripts/snapshot_item_units.py --check    # 라이브와 drift 검사(쓰기 없음)

--check 는 커밋된 스냅샷이 라이브 ECOS와 어긋나면 비0 종료(야간 CI 용). ECOS rate limit:
3분 300회 / 초과 시 30분 차단 — 본 스크립트는 라이브러리가 쓰는 stat_code 수(현재 ~56)만 호출.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import ecos
import ecos.constants as c

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ecos_item_catalog.json"


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


def fetch_live() -> dict:
    ecos.set_api_key(os.environ["ECOS_API_KEY"])
    snap: dict = {}
    for sc in sorted(library_stat_codes()):
        df = ecos.list_items(sc)
        m: dict[str, set] = {}
        for r in df.to_dict("records"):
            m.setdefault(r["item_code"], set()).add(str(r.get("unit")))
        snap[sc] = {k: sorted(v) for k, v in sorted(m.items())}
    return snap


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="라이브와 drift 검사 (쓰기 없음)")
    args = ap.parse_args()

    live = fetch_live()

    if args.check:
        committed = json.loads(FIXTURE.read_text())
        if committed == live:
            print("OK: 스냅샷이 라이브 ECOS와 일치.")
            return 0
        # 차이 요약
        only_live = set(live) - set(committed)
        only_committed = set(committed) - set(live)
        changed = [sc for sc in set(live) & set(committed) if live[sc] != committed[sc]]
        print("DRIFT 감지 — 스냅샷 재생성 필요 (scripts/snapshot_item_units.py):")
        if only_live:
            print(f"  라이브에만 있는 stat_code: {sorted(only_live)}")
        if only_committed:
            print(f"  스냅샷에만 있는 stat_code: {sorted(only_committed)}")
        if changed:
            print(f"  항목/단위가 바뀐 stat_code: {sorted(changed)}")
        return 1

    FIXTURE.write_text(json.dumps(live, ensure_ascii=False, indent=1, sort_keys=True))
    print(f"Saved {FIXTURE} ({len(live)} stat_codes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
