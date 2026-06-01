"""매핑 정합성 가드 (오프라인, API 불필요) — #133/#134/#136/#142 부류 재발 방지.

이 부류 버그의 공통 원인은 "통계표는 맞지만 표 안의 item_code/단위를 실데이터로
검증하지 않음"이다. 여기서는 라이브러리가 참조하는 (stat_code, item_code) 를
커밋된 ECOS 항목 스냅샷(tests/fixtures/ecos_item_catalog.json)과 대조해:

  1. 선언한 item_code 가 해당 통계표에 실제로 존재하는지 (오매핑/오타 차단)
  2. registry 가 선언한 단위가 ECOS 실제 단위와 일치하는지 (조원 vs 십억원, % vs 지수 차단)

스냅샷은 scripts/snapshot_item_units.py 로 라이브에서 재생성하며, 야간 CI가 drift 를
검사한다. 따라서 본 가드는 API 호출 없이 매 PR 에서 빠르게 실행된다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import ecos.constants as c
from ecos.indicators._registry import INDICATORS

FIXTURE = Path(__file__).parent / "fixtures" / "ecos_item_catalog.json"
CATALOG: dict[str, dict[str, list[str]]] = json.loads(FIXTURE.read_text())

STRUCT_FIXTURE = Path(__file__).parent / "fixtures" / "ecos_table_structure.json"
STRUCTURE: dict[str, dict] = json.loads(STRUCT_FIXTURE.read_text())


def _units(stat: str, item: str) -> list[str] | None:
    """스냅샷에서 (stat, item) 의 단위 목록. item 미존재 시 None."""
    return CATALOG.get(stat, {}).get(item)


# ---------------------------------------------------------------------------
# 단일 시계열 매핑 — (label, stat_code, item_code, expected_unit | None).
# expected_unit=None: 존재만 확인(단위가 다른 축에서 오거나 ECOS가 단위 미제공).
# 다축(item_code1=분류, 측정은 item_code2)·prefix 기반 매핑(bond_yield/investor_trading/
# borrower_loan 등)은 단일 item_code 로 환원되지 않아 본 표에서 의도적으로 제외한다.
# ---------------------------------------------------------------------------
def _single_series_mappings() -> list[tuple[str, str, str, str | None]]:
    m: list[tuple[str, str, str, str | None]] = []
    # 직접 스칼라 매핑
    m += [
        ("cpi", c.STAT_CPI, c.ITEM_CPI_TOTAL, "2020=100"),
        ("core_cpi", c.STAT_CORE_CPI, c.ITEM_CORE_CPI, "2020=100"),
        ("ppi", c.STAT_PPI, c.ITEM_PPI_TOTAL, "2020=100"),
        ("base_rate", c.STAT_BASE_RATE, c.ITEM_BASE_RATE, "연%"),
        ("fiscal_balance", c.STAT_FISCAL_BALANCE, c.ITEM_FISCAL_BALANCE, "십억원"),
        ("gdp_real", c.STAT_GDP_REAL, c.ITEM_GDP, "십억원"),
        ("gdp_nominal", c.STAT_GDP_NOMINAL, c.ITEM_GDP, "십억원"),
        ("gdp_deflator", c.STAT_GDP_DEFLATOR, c.ITEM_GDP_DEFLATOR, "2020=100"),
        ("gdp_growth_rate", c.STAT_GDP_GROWTH_RATE, c.ITEM_GDP_GROWTH_RATE, "%"),
        (
            "industrial_production",
            c.STAT_INDUSTRIAL_PRODUCTION,
            c.ITEM_INDUSTRIAL_PRODUCTION,
            "2020=100",
        ),
        ("facility_investment", c.STAT_FACILITY_INVESTMENT, c.ITEM_FACILITY_INVESTMENT, "2020=100"),
        (
            "facility_investment_sa",
            c.STAT_FACILITY_INVESTMENT,
            c.ITEM_FACILITY_INVESTMENT_SA,
            "2020=100",
        ),
        ("retail_sales", c.STAT_RETAIL_SALES, c.ITEM_RETAIL_SALES, None),  # 단위는 index축(item2)
        ("stock_daily", c.STAT_STOCK_DAILY, c.ITEM_STOCK_INDEX_DAILY, "1980.01.04=100"),
        ("stock_monthly", c.STAT_STOCK_MONTHLY, c.ITEM_STOCK_INDEX_MONTHLY, "1980.01.04=100"),
        ("csi", c.STAT_CSI, c.ITEM_CSI, None),  # ECOS 단위 미제공
        ("bank_lending_all", c.STAT_BANK_LENDING, c.BANK_LENDING_ITEMS["all"], "십억원"),
    ]
    # money_supply / variants / holder
    for ind, item in c.MONEY_SUPPLY_ITEMS.items():
        m.append((f"money_supply[{ind}]", c.MONEY_SUPPLY_STAT_CODES[ind], item, "십억원"))
    for v, item in c.M1_ITEMS.items():
        m.append((f"m1_variants[{v}]", c.M1_VARIANTS[v], item, "십억원"))
    for v, item in c.M2_ITEMS.items():
        m.append((f"m2_variants[{v}]", c.M2_VARIANTS[v], item, "십억원"))
    for v, item in c.M2_HOLDER_ITEMS.items():
        m.append((f"m2_by_holder[{v}]", c.M2_HOLDER_VARIANTS[v], item, "십억원"))
    # treasury / exchange / bop / composite / trade / bsi
    for mat, item in c.TREASURY_YIELD_ITEMS.items():
        m.append((f"treasury[{mat}]", c.STAT_MARKET_RATE, item, "연%"))
    for cur, item in c.EXCHANGE_RATE_ITEMS.items():
        m.append((f"exchange[{cur}]", c.STAT_EXCHANGE_RATE, item, "원"))
    for acc, item in c.BOP_ACCOUNT_ITEMS.items():
        m.append((f"bop[{acc}]", c.STAT_BOP, item, "백만달러"))
    for idx, item in c.COMPOSITE_INDEX_ITEMS.items():
        m.append((f"composite[{idx}]", c.STAT_COMPOSITE_INDEX, item, "2020=100"))
    for fl, item in c.TRADE_FLOW_ITEMS.items():
        m.append((f"trade[{fl}]", c.STAT_TRADE, item, "천불"))
    for sec, item in c.BSI_SECTOR_ITEMS.items():
        m.append((f"bsi[{sec}]", c.STAT_BSI, item, None))  # ECOS 단위 미제공
    return m


SINGLE_SERIES = _single_series_mappings()
EXISTENCE = [(label, stat, item) for label, stat, item, _u in SINGLE_SERIES]
UNIT_CHECKS = [(label, stat, item, u) for label, stat, item, u in SINGLE_SERIES if u is not None]


@pytest.mark.parametrize(("label", "stat", "item"), EXISTENCE, ids=[x[0] for x in EXISTENCE])
def test_item_code_exists_in_table(label, stat, item):
    """라이브러리가 가리키는 item_code 가 해당 통계표에 실제 존재해야 한다 (#134 부류)."""
    units = _units(stat, item)
    assert units is not None, (
        f"{label}: item '{item}' 가 통계표 {stat} 에 없음 "
        f"(스냅샷 기준). 매핑 오류이거나 스냅샷 갱신 필요."
    )


@pytest.mark.parametrize(
    ("label", "stat", "item", "expected_unit"),
    UNIT_CHECKS,
    ids=[x[0] for x in UNIT_CHECKS],
)
def test_declared_unit_matches_catalog(label, stat, item, expected_unit):
    """선언 단위가 ECOS 실제 단위와 일치해야 한다 (#136/#142 부류: 조원 vs 십억원, % vs 지수)."""
    units = _units(stat, item)
    assert units is not None, f"{label}: item '{item}' 미존재"
    actual = {u.strip() for u in units}
    assert expected_unit.strip() in actual, (
        f"{label}: 선언 단위 {expected_unit!r} 가 ECOS 실제 단위 {sorted(actual)} 에 없음. "
        f"docstring/상수 단위 오라벨 가능성."
    )


def test_registry_unit_matches_catalog():
    """registry IndicatorSpec.unit 이 ECOS 실제 단위와 일치해야 한다 (권장 경로 보호)."""
    mismatches = []
    for name, spec in INDICATORS.items():
        if spec.unit is None:
            continue
        units = _units(spec.stat_code, spec.item_code1)
        if units is None:
            mismatches.append(f"{name}: item {spec.item_code1} not in {spec.stat_code}")
            continue
        actual = {u.strip() for u in units}
        if spec.unit.strip() not in actual:
            mismatches.append(f"{name}: registry unit {spec.unit!r} not in {sorted(actual)}")
    assert not mismatches, "registry 단위 불일치:\n" + "\n".join(mismatches)


# ---------------------------------------------------------------------------
# 주기(period) 유효성 — 함수가 ECOS 호출에 쓰는 period 가 해당 통계표에 실제 존재하는가.
# 잘못된 주기는 빈 응답을 부른다(과거 v0.1.5 사례). (label, stat_code, period)
# period 분기형 함수는 사용 가능한 모든 period 를 나열한다.
# ---------------------------------------------------------------------------
def _period_checks() -> list[tuple[str, str, str]]:
    p: list[tuple[str, str, str]] = []
    p += [
        ("cpi", c.STAT_CPI, "M"),
        ("core_cpi", c.STAT_CORE_CPI, "M"),
        ("ppi", c.STAT_PPI, "M"),
        ("cpi_monthly", c.STAT_CPI_MONTHLY, "M"),
        ("base_rate/monthly", c.STAT_BASE_RATE, "M"),
        ("base_rate/daily", c.STAT_BASE_RATE, "D"),
        ("fiscal_balance", c.STAT_FISCAL_BALANCE, "M"),
        ("gdp_growth_rate/q", c.STAT_GDP_GROWTH_RATE, "Q"),
        ("gdp_growth_rate/a", c.STAT_GDP_GROWTH_RATE, "A"),
        ("gdp_deflator", c.STAT_GDP_DEFLATOR, "Q"),
        ("gdp_real/q", c.STAT_GDP_REAL, "Q"),
        ("gdp_real/a", c.STAT_GDP_REAL, "A"),
        ("gdp_nominal/a", c.STAT_GDP_NOMINAL, "A"),
        ("treasury", c.STAT_MARKET_RATE, "D"),
        ("exchange", c.STAT_EXCHANGE_RATE, "D"),
        ("stock_daily", c.STAT_STOCK_DAILY, "D"),
        ("stock_monthly", c.STAT_STOCK_MONTHLY, "M"),
        ("investor_trading", c.STAT_INVESTOR_TRADING, "M"),
        ("bsi", c.STAT_BSI, "M"),
        ("csi", c.STAT_CSI, "M"),
        ("composite_index", c.STAT_COMPOSITE_INDEX, "M"),
        ("industrial_production", c.STAT_INDUSTRIAL_PRODUCTION, "M"),
        ("facility_investment", c.STAT_FACILITY_INVESTMENT, "M"),
        ("bond_type", c.STAT_BOND_YIELD_TYPE, "M"),
        ("bond_market", c.STAT_BOND_MARKET, "M"),
        ("bank_lending", c.STAT_BANK_LENDING, "M"),
        ("household_lending_detail", c.STAT_HOUSEHOLD_LENDING, "M"),
        # 비-월간 주기를 쓰는 함수 (테이블에 M 이 없어 Q 를 써야 함 — 회귀 시 빈 응답)
        ("household_credit/sector", c.STAT_HOUSEHOLD_CREDIT_SECTOR, "Q"),
        ("household_credit/purpose", c.STAT_HOUSEHOLD_CREDIT_PURPOSE, "Q"),
        ("borrower_loan/new", c.BORROWER_LOAN_STAT_CODES["신규"], "Q"),
        ("borrower_loan/balance", c.BORROWER_LOAN_STAT_CODES["잔액"], "Q"),
    ]
    # bop / retail / trade — period 분기형
    for per in ("M", "Q", "A"):
        p.append((f"bop/{per}", c.STAT_BOP, per))
        p.append((f"retail/{per}", c.STAT_RETAIL_SALES, per))
    for per in ("M", "A"):
        p.append((f"trade/{per}", c.STAT_TRADE, per))
    # money_supply / m1 / m2 / m2_holder — 월간
    for stat in c.MONEY_SUPPLY_STAT_CODES.values():
        p.append((f"money_supply[{stat}]", stat, "M"))
    for stat in {**c.M1_VARIANTS, **c.M2_VARIANTS, **c.M2_HOLDER_VARIANTS}.values():
        p.append((f"m_variant[{stat}]", stat, "M"))
    return p


PERIOD_CHECKS = _period_checks()


@pytest.mark.parametrize(
    ("label", "stat", "period"), PERIOD_CHECKS, ids=[x[0] for x in PERIOD_CHECKS]
)
def test_used_period_is_available_in_table(label, stat, period):
    """함수가 호출에 쓰는 period 가 해당 통계표가 제공하는 주기에 있어야 한다.

    없는 주기를 쓰면 ECOS 가 빈 응답을 돌려준다(silent 실패). 잘못된 주기 매핑을
    스냅샷 대비로 차단한다.
    """
    info = STRUCTURE.get(stat)
    assert info is not None, f"{label}: {stat} 구조 스냅샷 없음 (스냅샷 갱신 필요)"
    assert period in info["cycles"], (
        f"{label}: period '{period}' 가 통계표 {stat} 의 제공 주기 {info['cycles']} 에 없음. "
        f"잘못된 주기 매핑(빈 응답)이거나 스냅샷 갱신 필요."
    )


def test_table_structure_snapshot_covers_all_used_stats():
    """라이브러리가 쓰는 모든 stat_code 가 구조 스냅샷에 존재해야 한다(신규 표 누락 방지)."""
    used = {stat for _label, stat, _item, _u in SINGLE_SERIES}
    used |= {stat for _label, stat, _p in PERIOD_CHECKS}
    missing = sorted(used - set(STRUCTURE))
    assert not missing, (
        f"구조 스냅샷에 없는 stat_code: {missing} (scripts/snapshot_item_units.py 재생성)"
    )
