#!/usr/bin/env python3
"""ECOS stat_code/item_code 라이브 대조 감사 + 전체 코드 카탈로그 (#67).

라이브러리가 선언한 통계코드/항목코드가 **실제 ECOS 응답과 일치하는지** 라이브로
대조한다. 환율 스캐폴딩(``STAT_EXCHANGE_RATE`` ↔ ``EXCHANGE_RATE_ITEMS``)에서
stat/item 불일치가 발견되어(#67), 전 코드의 회귀 방지 감사를 제공한다.

핵심 검사(주기 비의존): 각 (stat_code, item_code) 에 대해
``get_statistic_item_list(stat_code)`` 의 항목 목록에 item_code 가 존재하는지 확인.
존재하면 응답에서 ITEM_NAME / CYCLE / coverage 를 가져와 의도된 의미와 대조한다.
``--search`` 시 항목의 CYCLE 로 최근 윈도우를 조회해 데이터 비어있지 않음까지 확인.

두 가지 모드
-----------
audit
    선언된 (stat, item) 쌍을 라이브 ECOS 와 대조 → PASS/FAIL/MISMATCH/WARN 리포트.
    하나라도 FAIL 이면 종료코드 1 (CI 게이트용).
catalog
    ECOS 전체 통계표 목록(StatisticTableList)을 덤프해 reference 문서 생성.
    ``--items`` 시 표별 항목 목록까지 크롤(대량 호출, 느림).

사용법
------
    export ECOS_API_KEY=...
    python scripts/audit_codes.py audit
    python scripts/audit_codes.py audit --search          # 데이터 유무까지 확인
    python scripts/audit_codes.py audit --only forex       # 그룹 필터
    python scripts/audit_codes.py catalog -o docs/reference/ecos_code_catalog.md
    python scripts/audit_codes.py catalog --items          # 항목까지 (대량)

참고: 본 스크립트는 ``ecos.constants`` / 레지스트리를 단일 진실원천으로 삼아
감사 케이스를 조립하므로, 상수에 새 코드를 추가하면 케이스 매니페스트(CASES)에만
한 줄 반영하면 된다.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

# src 레이아웃을 import 경로에 추가 (설치 없이 실행 가능하도록).
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists():
    sys.path.insert(0, str(_SRC))

from ecos import constants as const  # noqa: E402
from ecos.client import EcosClient  # noqa: E402
from ecos.indicators._registry import INDICATORS as REGISTRY  # noqa: E402

# ============================================================================
# 감사 케이스 매니페스트
# ============================================================================
# 각 케이스는 라이브러리가 "이 의미의 데이터" 라고 선언한 (stat_code, item_code) 쌍이다.
# wired=True 는 이미 함수로 노출돼 사용 중인 코드(회귀 가드 목적),
# wired=False 는 함수 미연결 스캐폴딩 상수(라이브 미검증 위험 — 본 이슈의 주 대상).


@dataclass(frozen=True)
class Case:
    group: str
    label: str
    stat_code: str
    item_code: str
    intended: str  # 상수 주석 기준 의도된 의미
    wired: bool = True
    expect: tuple[str, ...] = ()  # ITEM_NAME 에 포함돼야 할 키워드(의미 검증). 비면 생략.


def _registry_cases() -> list[Case]:
    """선언적 레지스트리(#16)에 등록된 단순 지표 — 자동 수집."""
    cases: list[Case] = []
    for name, spec in REGISTRY.items():
        cases.append(
            Case(
                group="registry",
                label=name,
                stat_code=spec.stat_code,
                item_code=spec.item_code1,
                intended=spec.description or name,
                wired=True,
            )
        )
    return cases


def _paired(group: str, stat_map: dict, item_map: dict, *, wired: bool) -> list[Case]:
    """키를 공유하는 (stat 딕셔너리, item 딕셔너리)를 쌍으로 묶어 케이스 생성."""
    cases: list[Case] = []
    for key in stat_map:
        if key in item_map:
            cases.append(Case(group, key, stat_map[key], item_map[key], intended=key, wired=wired))
    return cases


def _under_stat(group: str, stat: str, item_map: dict, *, wired: bool) -> list[Case]:
    """단일 stat 아래 item 딕셔너리(통화→item 등)를 케이스로 펼친다."""
    return [
        Case(group, key, stat, item, intended=key, wired=wired) for key, item in item_map.items()
    ]


def build_cases() -> list[Case]:
    cases: list[Case] = []

    # --- 구현(wired) 코드: 회귀 가드 ---------------------------------------
    cases += _registry_cases()
    # 국고채 만기별 (817Y002 아래)
    cases += _under_stat(
        "treasury_yield", const.STAT_MARKET_RATE, const.TREASURY_YIELD_ITEMS, wired=True
    )
    # 통화량 M1/M2/Lf (stat·item 병렬 딕셔너리)
    cases += _paired(
        "money_supply", const.MONEY_SUPPLY_STAT_CODES, const.MONEY_SUPPLY_ITEMS, wired=True
    )
    # M1/M2/M2보유주체 세부 변형 (variant stat ↔ item 병렬)
    cases += _paired("m1_variants", const.M1_VARIANTS, const.M1_ITEMS, wired=True)
    cases += _paired("m2_variants", const.M2_VARIANTS, const.M2_ITEMS, wired=True)
    cases += _paired("m2_holder", const.M2_HOLDER_VARIANTS, const.M2_HOLDER_ITEMS, wired=True)
    # CPI 세부 항목별 — 이미 (stat, item) 튜플
    for key, (stat, item) in const.CPI_CATEGORY_CODES.items():
        cases.append(Case("cpi_category", key, stat, item, intended=key, wired=True))
    # 단일 코드 지표 (상수 직접)
    cases.append(Case("gdp", "real", const.STAT_GDP_REAL, const.ITEM_GDP, "실질 GDP 지출", True))
    cases.append(
        Case("gdp", "nominal", const.STAT_GDP_NOMINAL, const.ITEM_GDP, "명목 GDP 지출", True)
    )
    cases.append(
        Case(
            "gdp",
            "deflator",
            const.STAT_GDP_DEFLATOR,
            const.ITEM_GDP_DEFLATOR,
            "GDP 디플레이터",
            True,
        )
    )
    cases.append(
        Case(
            "bank_lending",
            "all",
            const.STAT_BANK_LENDING,
            const.BANK_LENDING_ITEMS["all"],
            "총대출금",
            True,
        )
    )

    # --- 스캐폴딩(unwired) 코드: 본 이슈 주 대상 ----------------------------
    # 환율 (731Y003 ↔ 731Y001 item 불일치 의심 — #67). 통화별 기대 키워드로 silent-wrong 탐지.
    _forex_expect = {"USD": ("달러",), "JPY": ("엔",), "EUR": ("유로",), "CNY": ("위안",)}
    for cur, item in const.EXCHANGE_RATE_ITEMS.items():
        cases.append(
            Case(
                "forex",
                cur,
                const.STAT_EXCHANGE_RATE,
                item,
                f"원/{cur}",
                False,
                _forex_expect.get(cur, ()),
            )
        )
    # 실효환율 NEER/REER (731Y004) — ITEM_NAME 에 "실효" 가 있어야 함
    cases.append(
        Case(
            "effective_rate",
            "NEER",
            const.STAT_EFFECTIVE_RATE,
            const.ITEM_NEER,
            "명목실효환율",
            False,
            ("실효",),
        )
    )
    cases.append(
        Case(
            "effective_rate",
            "REER",
            const.STAT_EFFECTIVE_RATE,
            const.ITEM_REER,
            "실질실효환율",
            False,
            ("실효",),
        )
    )
    # 국제수지
    cases.append(
        Case(
            "bop",
            "current_account",
            const.STAT_BOP,
            const.ITEM_CURRENT_ACCOUNT,
            "경상수지",
            False,
            ("경상",),
        )
    )
    cases.append(
        Case(
            "bop",
            "capital_account",
            const.STAT_BOP,
            const.ITEM_CAPITAL_ACCOUNT,
            "자본수지",
            False,
            ("자본", "금융"),
        )
    )
    # 실물
    cases.append(
        Case(
            "real_economy",
            "industrial",
            const.STAT_INDUSTRIAL_PRODUCTION,
            const.ITEM_INDUSTRIAL_PRODUCTION,
            "산업생산지수",
            False,
        )
    )
    cases.append(
        Case(
            "real_economy",
            "facility_invest",
            const.STAT_FACILITY_INVESTMENT,
            const.ITEM_FACILITY_INVESTMENT,
            "설비투자지수",
            False,
        )
    )
    cases.append(
        Case(
            "real_economy",
            "retail_sales",
            const.STAT_RETAIL_SALES,
            const.ITEM_RETAIL_SALES,
            "소매판매지수",
            False,
        )
    )
    # 심리
    cases.append(
        Case(
            "sentiment",
            "bsi_manufacturing",
            const.STAT_BSI,
            const.ITEM_BSI_MANUFACTURING,
            "BSI 제조업",
            False,
            ("제조",),
        )
    )
    cases.append(
        Case(
            "sentiment",
            "bsi_non_manufacturing",
            const.STAT_BSI,
            const.ITEM_BSI_NON_MANUFACTURING,
            "BSI 비제조업",
            False,
            ("비제조",),
        )
    )
    cases.append(
        Case(
            "sentiment",
            "bsi_all",
            const.STAT_BSI,
            const.ITEM_BSI_ALL,
            "BSI 전산업",
            False,
            ("전 산업", "전산업", "전 산 업"),
        )
    )
    cases.append(
        Case("sentiment", "csi", const.STAT_CSI, const.ITEM_CSI, "소비자심리지수", False, ("심리",))
    )

    return cases


# stat_code 만 있고 단일 표준 item 이 없는 상수(예금/대출 금리, 채권/주식 표) —
# 표 존재 여부만 table_list 로 확인한다.
STAT_ONLY: list[tuple[str, str, str]] = [
    ("deposit_rate", const.STAT_DEPOSIT_RATE_NEW, "예금은행 수신금리(신규)"),
    ("deposit_rate", const.STAT_DEPOSIT_RATE_BALANCE, "예금은행 수신금리(잔액)"),
    ("lending_rate", const.STAT_LENDING_RATE_NEW, "예금은행 대출금리(신규)"),
    ("lending_rate", const.STAT_LENDING_RATE_BALANCE, "예금은행 대출금리(잔액)"),
    ("bond", const.STAT_BOND_YIELD_TYPE, "채권종류별 거래"),
    ("bond", const.STAT_BOND_MARKET, "채권시장별 거래"),
    ("stock", const.STAT_STOCK_DAILY, "주식시장(일별)"),
    ("stock", const.STAT_STOCK_MONTHLY, "주식시장(월/연)"),
    ("household_credit", const.STAT_HOUSEHOLD_CREDIT_SECTOR, "가계신용(업권별)"),
    ("household_credit", const.STAT_HOUSEHOLD_CREDIT_PURPOSE, "가계신용(용도별)"),
    ("forex_related", const.STAT_EXCHANGE_RATE_RELATED, "환율 관련 통계"),
]


# ============================================================================
# 라이브 대조
# ============================================================================

# 검사 결과 상태
PASS = "PASS"  # noqa: S105 — 검사 상태 라벨(비밀번호 아님)
FAIL = "FAIL"  # item_code 가 stat 의 항목 목록에 없음 (오매핑)
EMPTY = "EMPTY"  # 항목은 존재하나 최근 윈도우 데이터 없음 (--search)
WARN = "WARN"  # 항목 존재하나 의도된 의미와 ITEM_NAME 불일치 의심
SKIP = "SKIP"  # 와일드카드/total selector — 멤버십 검사 비대상 (양성)


@dataclass
class Result:
    case: Case
    status: str
    item_name: str = ""
    cycle: str = ""
    coverage: str = ""
    note: str = ""
    extra: list[str] = field(default_factory=list)  # 같은 stat 의 실제 item 후보


def _item_index(client: EcosClient, stat_code: str) -> dict[str, dict]:
    """stat 의 항목 목록을 {item_code: row} 로 반환 (없으면 빈 dict)."""
    payload = client.get_statistic_item_list(stat_code)
    block = payload.get("StatisticItemList") if isinstance(payload, dict) else None
    rows = (block or {}).get("row") or []
    idx: dict[str, dict] = {}
    for r in rows:
        code = str(r.get("ITEM_CODE", "")).strip()
        if code:
            idx.setdefault(code, r)
    return idx


def _recent_window(cycle: str) -> tuple[str, str, str]:
    """CYCLE → (period, start, end) 최근 윈도우 (데이터 유무 확인용)."""
    today = date.today()
    if cycle == "D":
        return "D", (today - timedelta(days=30)).strftime("%Y%m%d"), today.strftime("%Y%m%d")
    if cycle == "M":
        return "M", (today - timedelta(days=400)).strftime("%Y%m"), today.strftime("%Y%m")
    if cycle == "Q":
        y = today.year
        return "Q", f"{y - 2}Q1", f"{y}Q4"
    if cycle in ("A", "Y"):
        return "A", str(today.year - 5), str(today.year)
    return "M", (today - timedelta(days=400)).strftime("%Y%m"), today.strftime("%Y%m")


def audit_case(client: EcosClient, case: Case, *, do_search: bool) -> Result:
    item = str(case.item_code).strip()
    # 와일드카드/총지수 selector 는 항목목록 멤버십 검사 대상이 아님.
    if item in ("", "*"):
        return Result(case, SKIP, note=f"selector {item!r} (멤버십 검사 생략)")

    try:
        idx = _item_index(client, case.stat_code)
    except Exception as e:
        return Result(case, FAIL, note=f"item_list 조회 실패: {type(e).__name__}: {e}")

    if not idx:
        return Result(case, FAIL, note="stat 의 항목 목록이 비어있음 (stat_code 오류 의심)")

    row = idx.get(item)
    if row is None:
        # 오매핑 — 같은 stat 의 실제 item 후보 몇 개를 보여 디버깅을 돕는다.
        sample = [f"{c}={idx[c].get('ITEM_NAME')}" for c in list(idx)[:4]]
        return Result(case, FAIL, note="item_code 가 stat 항목 목록에 없음", extra=sample)

    name = str(row.get("ITEM_NAME", "")).strip()
    cycle = str(row.get("CYCLE", "")).strip()
    cov = f"{row.get('START_TIME', '?')}~{row.get('END_TIME', '?')}"
    status = PASS
    note = ""

    # 의미 검증: item_code 는 존재하나 ITEM_NAME 이 의도와 다른 "silent wrong" 탐지.
    # ECOS ITEM_NAME 은 "제 조 업" 처럼 자간 공백이 섞이므로 공백 제거 후 비교.
    _name_ns = name.replace(" ", "")
    if case.expect and not any(tok.replace(" ", "") in _name_ns for tok in case.expect):
        return Result(
            case,
            WARN,
            item_name=name,
            cycle=cycle,
            coverage=cov,
            note=f"의미 불일치 의심 — 기대 키워드 {list(case.expect)} 없음 (실제 '{name}')",
        )

    if do_search and cycle:
        try:
            period, s, e = _recent_window(cycle)
            res = client.get_statistic_search(
                stat_code=case.stat_code,
                period=period,
                start_date=s,
                end_date=e,
                item_code1=item,
            )
            if isinstance(res, dict) and "RESULT" in res:
                status, note = EMPTY, str(res["RESULT"].get("MESSAGE", "데이터 없음"))
            else:
                block = res.get("StatisticSearch", {}) if isinstance(res, dict) else {}
                if not (block.get("row") or []):
                    status, note = EMPTY, "최근 윈도우 데이터 없음"
        except Exception as e:
            status, note = EMPTY, f"search 실패: {type(e).__name__}: {e}"

    return Result(case, status, item_name=name, cycle=cycle, coverage=cov, note=note)


def audit_stat_only(client: EcosClient, group: str, stat: str, desc: str) -> Result:
    case = Case(group, stat, stat, "(table)", intended=desc, wired=True)
    try:
        idx = _item_index(client, stat)
    except Exception as e:
        return Result(case, FAIL, note=f"item_list 조회 실패: {type(e).__name__}: {e}")
    if not idx:
        return Result(case, FAIL, note="stat 항목 목록 비어있음 (stat_code 오류 의심)")
    return Result(case, PASS, item_name=desc, note=f"{len(idx)}개 항목")


# ============================================================================
# 리포트 출력
# ============================================================================

_SYMBOL = {PASS: "✅", FAIL: "❌", EMPTY: "⚠️ ", WARN: "🔸", SKIP: "⏭️"}


def print_report(results: list[Result]) -> int:
    by_status: dict[str, int] = {}
    print(f"\n{'STATUS':<7} {'GROUP':<16} {'LABEL':<22} {'STAT':<9} {'ITEM':<12} 비고")
    print("-" * 100)
    for r in results:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        sym = _SYMBOL.get(r.status, r.status)
        detail = r.item_name or r.note
        if r.cycle:
            detail = f"[{r.cycle}] {detail} ({r.coverage})"
        line = (
            f"{sym:<6} {r.case.group:<16} {r.case.label:<22} "
            f"{r.case.stat_code:<9} {r.case.item_code!s:<12} {detail}"
        )
        print(line)
        if r.status == FAIL and r.note:
            print(f"          ↳ {r.note}")
            for s in r.extra:
                print(f"            · 실제 item 후보: {s}")
        elif r.status in (EMPTY, WARN) and r.note:
            print(f"          ↳ {r.note}")

    print("-" * 100)
    summary = "  ".join(f"{_SYMBOL.get(k, k)}{k}={v}" for k, v in sorted(by_status.items()))
    print(f"합계 {len(results)}건 — {summary}")
    fails = by_status.get(FAIL, 0)
    if fails:
        print(f"\n❌ FAIL {fails}건 — stat/item 매핑 결함. 정정 필요 (#67).")
    return 1 if fails else 0


def collect_results(
    client: EcosClient, *, do_search: bool = False, only: str | None = None
) -> list[Result]:
    """모든 감사 케이스를 라이브 대조해 Result 리스트 반환 (테스트/CI 재사용)."""
    cases = build_cases()
    if only:
        cases = [c for c in cases if c.group == only]
    results = [audit_case(client, c, do_search=do_search) for c in cases]
    for group, stat, desc in STAT_ONLY:
        if not only or group == only:
            results.append(audit_stat_only(client, group, stat, desc))
    return results


def run_audit(client: EcosClient, *, do_search: bool, only: str | None) -> int:
    results = collect_results(client, do_search=do_search, only=only)
    return print_report(results)


# ============================================================================
# 카탈로그 (ECOS 전체 통계표)
# ============================================================================


def run_catalog(client: EcosClient, *, out: Path | None, with_items: bool) -> int:
    payload = client.get_statistic_table_list("")
    block = payload.get("StatisticTableList", {}) if isinstance(payload, dict) else {}
    rows = block.get("row") or []
    total = block.get("list_total_count", len(rows))

    lines: list[str] = []
    lines.append("# ECOS 전체 통계표 카탈로그")
    lines.append("")
    lines.append("> `scripts/audit_codes.py catalog` 자동 생성 — 수기 편집 금지.")
    lines.append(f"> StatisticTableList 전체 {total}개 통계표.")
    lines.append("")
    searchable_total = sum(1 for r in rows if r.get("SRCH_YN") == "Y")
    lines.append(f"> 검색가능(SRCH_YN=Y, 실제 데이터 조회 대상) {searchable_total}개.")
    lines.append("")
    lines.append("| 통계표코드 | 통계명 | 주기 | 검색가능 | 상위코드 |")
    lines.append("|---|---|---|---|---|")
    for r in rows:
        code = r.get("STAT_CODE", "")
        name = str(r.get("STAT_NAME", "")).replace("|", "/")
        cycle = r.get("CYCLE", "") or "-"
        srch = r.get("SRCH_YN", "")
        parent = r.get("P_STAT_CODE", "") or "-"
        lines.append(f"| {code} | {name} | {cycle} | {srch} | {parent} |")

    if with_items:
        lines.append("")
        lines.append("## 통계표별 항목 목록 (--items)")
        searchable = [r for r in rows if (r.get("SRCH_YN") == "Y") and r.get("STAT_CODE")]
        lines.append("")
        lines.append(f"> 검색가능 통계표 {len(searchable)}개의 항목을 크롤.")
        for i, r in enumerate(searchable, 1):
            code = r["STAT_CODE"]
            try:
                idx = _item_index(client, code)
            except Exception as e:
                lines.append(f"\n### {code} — 항목 조회 실패: {type(e).__name__}")
                continue
            lines.append(f"\n### {code} — {r.get('STAT_NAME', '')} ({len(idx)}개 항목)")
            lines.append("")
            lines.append("| 항목코드 | 항목명 | 주기 | 기간 |")
            lines.append("|---|---|---|---|")
            for ic, irow in list(idx.items())[:200]:
                nm = str(irow.get("ITEM_NAME", "")).replace("|", "/")
                cy = irow.get("CYCLE", "")
                span = f"{irow.get('START_TIME', '?')}~{irow.get('END_TIME', '?')}"
                lines.append(f"| {ic} | {nm} | {cy} | {span} |")
            if i % 50 == 0:
                print(f"  ... {i}/{len(searchable)} 통계표 크롤")

    text = "\n".join(lines) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"카탈로그 {total}개 통계표 → {out}")
    else:
        print(text)
    return 0


# ============================================================================
# CLI
# ============================================================================


def _client() -> EcosClient:
    key = os.getenv("ECOS_API_KEY")
    if not key:
        print("환경변수 ECOS_API_KEY 필요", file=sys.stderr)
        raise SystemExit(2)
    return EcosClient(api_key=key, use_cache=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ECOS 코드 라이브 감사 + 카탈로그 (#67)")
    sub = ap.add_subparsers(dest="mode", required=True)

    pa = sub.add_parser("audit", help="선언된 (stat,item) 쌍을 라이브 대조")
    pa.add_argument("--search", action="store_true", help="최근 윈도우 데이터 유무까지 확인")
    pa.add_argument("--only", default=None, help="그룹명으로 필터 (예: forex)")

    pc = sub.add_parser("catalog", help="ECOS 전체 통계표 덤프")
    pc.add_argument("-o", "--out", type=Path, default=None, help="출력 markdown 경로")
    pc.add_argument("--items", action="store_true", help="통계표별 항목까지 크롤 (대량)")

    args = ap.parse_args(argv)
    client = _client()

    if args.mode == "audit":
        return run_audit(client, do_search=args.search, only=args.only)
    if args.mode == "catalog":
        return run_catalog(client, out=args.out, with_items=args.items)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
