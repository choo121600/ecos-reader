"""stat_code/item_code 라이브 대조 회귀 테스트 (#67).

``scripts/audit_codes.py`` 의 감사를 실제 ECOS API 로 실행해, 선언된 코드 매핑이
드리프트하지 않는지 검증한다. ``ECOS_API_KEY`` 가 없으면 skip (``e2e`` 마커).

알려진 결함(``KNOWN_DEFECTS``)을 베이스라인으로 둔다:
- **신규 결함**(베이스라인에 없는 FAIL/WARN)이 생기면 FAIL → 새 오매핑 차단.
- 베이스라인 결함이 **정정되면** 그것도 FAIL → 베이스라인에서 제거하라는 알림.

따라서 이 테스트는 "현재 알려진 기술부채는 통과시키되, 그 집합의 모든 변화를
가시화" 한다. 결함이 PR 로 정정될 때마다 ``KNOWN_DEFECTS`` 를 함께 줄여나간다.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

# scripts/ 를 import 경로에 추가 (audit_codes 는 패키지가 아닌 스크립트).
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import audit_codes as audit  # noqa: E402

# (group, label, status) — 2026-05-30 라이브 대조 기준 알려진 코드 매핑 결함.
# 정정 PR 마다 해당 항목을 제거할 것 (#67 후속).
KNOWN_DEFECTS: set[tuple[str, str, str]] = {
    # forex(731Y003→731Y001) 정정 완료 — #70 에서 해소.
    # 실효환율: STAT_EFFECTIVE_RATE(731Y004)/0000001~2 = "원/미국달러(매매기준율)" 등 — 실효환율 아님.
    ("effective_rate", "NEER", audit.WARN),
    ("effective_rate", "REER", audit.WARN),
    # bop(301Y017→301Y013, CA/KA→000000/BOPC...) 정정 완료 — #74 에서 해소.
    # real_economy facility_invest(901Y049→901Y066) 정정 완료 — #72 에서 해소.
    # sentiment BSI(512Y014 item A001/B001/C001 → C0000/Y9900/99988) 정정 완료 — #73 에서 해소.
}


@pytest.fixture
def client():
    api_key = os.getenv("ECOS_API_KEY")
    if not api_key:
        pytest.skip("ECOS_API_KEY 환경 변수가 설정되지 않았습니다.")
    from ecos.client import EcosClient

    return EcosClient(api_key=api_key, use_cache=False)


def _defects(results: list) -> set[tuple[str, str, str]]:
    return {
        (r.case.group, r.case.label, r.status)
        for r in results
        if r.status in (audit.FAIL, audit.WARN)
    }


def test_no_unexpected_code_drift(client):
    results = audit.collect_results(client)
    current = _defects(results)

    new = current - KNOWN_DEFECTS
    resolved = KNOWN_DEFECTS - current

    msg = []
    if new:
        msg.append(f"신규 코드 매핑 결함 {len(new)}건 (정정 필요): {sorted(new)}")
    if resolved:
        msg.append(
            f"베이스라인 결함 {len(resolved)}건이 해소됨 — KNOWN_DEFECTS 에서 제거할 것: "
            f"{sorted(resolved)}"
        )
    assert not msg, "\n".join(msg)


def test_sanity_pass_count(client):
    """대다수 케이스는 PASS 여야 한다 (전수 실패 = 감사 자체 오류 신호)."""
    results = audit.collect_results(client)
    passes = sum(1 for r in results if r.status == audit.PASS)
    assert passes >= 40, f"PASS {passes}건 — 감사 인프라/네트워크 이상 의심"
