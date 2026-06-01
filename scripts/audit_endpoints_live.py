"""전 엔드포인트 라이브 FM 전수 감사 (#151) — 재실행 가능한 하니스.

엔드포인트/변종마다 라이브 호출 → 기대치와 대조:
  존재 / 스키마 / 단위 / 값범위 / 계열정합성(항목명) / 파라미터효과(변종 구분).
결과를 results.json 에 증분 저장(rate-limit cooldown 대비, --group 으로 도메인 배치 실행).

사용:
  ECOS_API_KEY=... python phase4_rigorous.py --group prices
  ECOS_API_KEY=... python phase4_rigorous.py            # 전체
  python phase4_rigorous.py --report                    # results.json -> markdown 표
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import ecos

OUT = Path(__file__).parent / "audit_results.json"


def spec(label, group, call, unit=None, rng=None, dgroup=None):
    return {
        "label": label,
        "group": group,
        "call": call,
        "unit": unit,
        "rng": rng,
        "dgroup": dgroup,
    }


def build_specs():
    s = []
    # ---- 금리 ----
    s.append(spec("base_rate", "rates", lambda: ecos.get_base_rate(), "연%", (0, 10)))
    for m in ["1Y", "3Y", "5Y", "10Y", "20Y", "30Y"]:
        s.append(
            spec(
                f"treasury_yield[{m}]",
                "rates",
                lambda m=m: ecos.get_treasury_yield(maturity=m),
                "연%",
                (0, 10),
                "treasury",
            )
        )
    s.append(spec("yield_spread", "rates", lambda: ecos.get_yield_spread(), "%p", (-5, 5)))
    for b in ["신규취급액", "잔액"]:
        s.append(
            spec(
                f"bank_deposit_rate[{b}]",
                "rates",
                lambda b=b: ecos.get_bank_deposit_rate(basis=b),
                None,
                (0, 15),
                "deposit_rate",
            )
        )
        s.append(
            spec(
                f"bank_lending_rate[{b}]",
                "rates",
                lambda b=b: ecos.get_bank_lending_rate(basis=b),
                None,
                (0, 15),
                "lending_rate",
            )
        )
    # ---- 물가 ----
    for fn, name in [(ecos.get_cpi, "cpi"), (ecos.get_core_cpi, "core_cpi"), (ecos.get_ppi, "ppi")]:
        s.append(spec(f"{name}", "prices", lambda fn=fn: fn(), "2020=100", (80, 200)))
        s.append(spec(f"{name}[yoy]", "prices", lambda fn=fn: fn(measure="yoy"), "%", (-10, 20)))
        s.append(spec(f"{name}[mom]", "prices", lambda fn=fn: fn(measure="mom"), "%", (-10, 20)))
    for cat in [
        "전체",
        "상품",
        "서비스",
        "식품_에너지제외",
        "농산물_석유제외",
        "식료품_비주류음료",
        "주거_수도_전기",
        "교통",
    ]:
        s.append(
            spec(
                f"cpi_by_category[{cat}]",
                "prices",
                lambda cat=cat: ecos.get_cpi_by_category(category=cat),
                "2020=100",
                (80, 250),
                "cpi_cat",
            )
        )
    s.append(spec("cpi_monthly", "prices", lambda: ecos.get_cpi_monthly(), "2020=100", None))
    # ---- 성장 ----
    for fr in ["quarterly", "annual"]:
        for ba in ["real", "nominal"]:
            s.append(
                spec(
                    f"gdp[{fr},{ba}]",
                    "growth",
                    lambda fr=fr, ba=ba: ecos.get_gdp(frequency=fr, basis=ba),
                    "십억원",
                    (1e4, 1e7),
                )
            )
    s.append(
        spec(
            "gdp_growth_rate[q]",
            "growth",
            lambda: ecos.get_gdp_growth_rate(frequency="quarterly"),
            "%",
            (-15, 15),
        )
    )
    s.append(
        spec(
            "gdp_growth_rate[a]",
            "growth",
            lambda: ecos.get_gdp_growth_rate(frequency="annual"),
            "%",
            (-15, 15),
        )
    )
    s.append(spec("gdp_deflator", "growth", lambda: ecos.get_gdp_deflator(), "2020=100", (80, 160)))
    for ba in ["real", "nominal"]:
        s.append(
            spec(
                f"gdp_by_industry[{ba}]",
                "growth",
                lambda ba=ba: ecos.get_gdp_by_industry(basis=ba),
                "십억원",
                None,
            )
        )
        s.append(
            spec(
                f"gdp_by_expenditure[{ba}]",
                "growth",
                lambda ba=ba: ecos.get_gdp_by_expenditure(basis=ba),
                "십억원",
                None,
            )
        )
    s.append(
        spec(
            "gdp_deflator_by_industry",
            "growth",
            lambda: ecos.get_gdp_deflator_by_industry(),
            "2020=100",
            None,
        )
    )
    # ---- 통화 ----
    for ind in ["M1", "M2", "Lf"]:
        s.append(
            spec(
                f"money_supply[{ind}]",
                "money",
                lambda ind=ind: ecos.get_money_supply(indicator=ind),
                "십억원",
                (1e5, 1e7),
                "money_supply",
            )
        )
    for v in ["평잔_계절조정", "평잔_원계열", "말잔_계절조정"]:
        s.append(
            spec(
                f"m1_variants[{v}]",
                "money",
                lambda v=v: ecos.get_m1_variants(variant=v),
                "십억원",
                (1e5, 1e7),
                "m1",
            )
        )
        s.append(
            spec(
                f"m2_variants[{v}]",
                "money",
                lambda v=v: ecos.get_m2_variants(variant=v),
                "십억원",
                (1e5, 1e7),
                "m2",
            )
        )
    s.append(spec("m2_by_holder", "money", lambda: ecos.get_m2_by_holder(), "십억원", None))
    for sec in ["all", "household"]:
        s.append(
            spec(
                f"bank_lending[{sec}]",
                "money",
                lambda sec=sec: ecos.get_bank_lending(sector=sec),
                "십억원",
                (1e5, 1e7),
                "bank_lending",
            )
        )
    for cat in ["업권별", "용도별"]:
        s.append(
            spec(
                f"household_credit[{cat}]",
                "money",
                lambda cat=cat: ecos.get_household_credit(category=cat),
                "십억원",
                None,
            )
        )
    s.append(
        spec(
            "household_lending_detail",
            "money",
            lambda: ecos.get_household_lending_detail(),
            "십억원",
            None,
        )
    )
    s.append(spec("borrower_loan", "money", lambda: ecos.get_borrower_loan(), "십만원", None))
    # ---- 시장 ----
    for fr in ["daily", "monthly"]:
        s.append(
            spec(
                f"stock_index[{fr}]",
                "markets",
                lambda fr=fr: ecos.get_stock_index(frequency=fr),
                None,
                (500, 20000),
                "stock",
            )
        )
    for act in ["순매수", "매수", "매도"]:
        s.append(
            spec(
                f"investor_trading[{act}]",
                "markets",
                lambda act=act: ecos.get_investor_trading(action=act),
                "백만원",
                None,
                "investor",
            )
        )
    for bt, meas in [
        ("종류별", "거래대금"),
        ("종류별", "거래량"),
        ("종류별", "상장잔액"),
        ("종류별", "상장종목수"),
        ("시장별", "거래대금"),
        ("시장별", "거래량"),
    ]:
        s.append(
            spec(
                f"bond_market[{bt},{meas}]",
                "markets",
                lambda bt=bt, meas=meas: ecos.get_bond_market(bond_type=bt, measure=meas),
                None,
                None,
            )
        )
    # ---- 대외 ----
    for cur in ["USD", "JPY", "EUR", "CNY"]:
        s.append(
            spec(
                f"exchange_rate[{cur}]",
                "external",
                lambda cur=cur: ecos.get_exchange_rate(currency=cur),
                "원",
                (50, 3000),
                "fx",
            )
        )
    for acc in ["current", "capital", "financial"]:
        s.append(
            spec(
                f"bop[{acc}]",
                "external",
                lambda acc=acc: ecos.get_balance_of_payments(account=acc),
                "백만달러",
                None,
            )
        )
    for fl in ["export", "import"]:
        s.append(
            spec(
                f"trade[{fl}]",
                "external",
                lambda fl=fl: ecos.get_trade(flow=fl),
                "천불",
                (1e6, 1e9),
                "trade",
            )
        )
    # ---- 심리/실물 ----
    for sec in ["manufacturing", "non_manufacturing", "all"]:
        s.append(
            spec(
                f"business_sentiment[{sec}]",
                "sentiment",
                lambda sec=sec: ecos.get_business_sentiment(sector=sec),
                None,
                (20, 150),
                "bsi",
            )
        )
    s.append(
        spec(
            "consumer_sentiment",
            "sentiment",
            lambda: ecos.get_consumer_sentiment(),
            None,
            (50, 150),
        )
    )
    for idx in ["leading", "coincident", "lagging"]:
        s.append(
            spec(
                f"composite_index[{idx}]",
                "sentiment",
                lambda idx=idx: ecos.get_composite_index(index=idx),
                "2020=100",
                (80, 140),
                "composite",
            )
        )
    for ix in ["nominal", "real", "seasonal"]:
        s.append(
            spec(
                f"retail_sales[{ix}]",
                "sentiment",
                lambda ix=ix: ecos.get_retail_sales(index=ix),
                "2020=100",
                (80, 160),
                "retail",
            )
        )
    for sa in [False, True]:
        s.append(
            spec(
                f"industrial_production[sa={sa}]",
                "sentiment",
                lambda sa=sa: ecos.get_industrial_production(seasonal=sa),
                "2020=100",
                (80, 160),
                "ind_prod",
            )
        )
        s.append(
            spec(
                f"facility_investment[sa={sa}]",
                "sentiment",
                lambda sa=sa: ecos.get_facility_investment(seasonal=sa),
                "2020=100",
                (60, 180),
                "facility",
            )
        )
    return s


def run(group_filter=None):
    ecos.set_api_key(os.environ["ECOS_API_KEY"])
    ecos.disable_cache()
    specs = build_specs()
    results = json.loads(OUT.read_text()) if OUT.exists() else {}
    for sp in specs:
        if group_filter and sp["group"] != group_filter:
            continue
        if sp["label"] in results:
            print(f"  {sp['label']} cached")
            continue
        rec = {
            "group": sp["group"],
            "exp_unit": sp["unit"],
            "rng": sp["rng"],
            "dgroup": sp["dgroup"],
        }
        try:
            df = sp["call"]()
            valcol = (
                "value" if "value" in df.columns else ("spread" if "spread" in df.columns else None)
            )
            rec["n"] = len(df)
            rec["cols"] = list(df.columns)
            rec["unit"] = (
                sorted({str(x) for x in df["unit"].dropna().unique()})
                if "unit" in df.columns
                else []
            )
            if valcol and len(df):
                v = df[valcol].dropna()
                rec["sample"] = [round(float(x), 3) for x in v.tail(2).tolist()]
                rec["vmin"], rec["vmax"] = round(float(v.min()), 3), round(float(v.max()), 3)
            if "category_value" in df.columns:
                rec["categories"] = sorted({str(x) for x in df["category_value"].unique()})[:15]
            # 판정
            checks = []
            checks.append(("nonempty", rec["n"] > 0))
            if sp["unit"] is not None:
                checks.append(("unit", sp["unit"] in {u.strip() for u in rec.get("unit", [])}))
            if sp["rng"] and "vmin" in rec:
                lo, hi = sp["rng"]
                checks.append(("range", lo <= rec["vmin"] and rec["vmax"] <= hi))
            rec["checks"] = dict(checks)
            rec["verdict"] = "PASS" if all(v for _, v in checks) else "FLAG"
            print(
                f"  {sp['label']:32s} {rec['verdict']} unit={rec.get('unit')} sample={rec.get('sample')}"
            )
        except Exception as e:
            rec["error"] = str(e)
            rec["verdict"] = "ERROR"
            print(f"  {sp['label']:32s} ERROR {e}")
        results[sp["label"]] = rec
        OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1))
    return results


def distinctness(results):
    """같은 dgroup 변종들이 서로 다른 계열인지(파라미터 효과) 검사."""
    groups = {}
    for label, r in results.items():
        dg = r.get("dgroup")
        if dg and "sample" in r:
            groups.setdefault(dg, []).append((label, tuple(r["sample"])))
    out = {}
    for dg, items in groups.items():
        samples = [s for _, s in items]
        uniq = len(set(samples))
        out[dg] = {"variants": len(items), "distinct": uniq, "ok": uniq == len(items)}
    return out


def report():
    results = json.loads(OUT.read_text())
    rows = sorted(results.items(), key=lambda kv: (kv[1].get("group", ""), kv[0]))
    print("| endpoint | group | n | unit | sample | exp_unit | verdict |")
    print("|---|---|---|---|---|---|---|")
    for label, r in rows:
        print(
            f"| {label} | {r.get('group')} | {r.get('n', '-')} | {r.get('unit')} | "
            f"{r.get('sample')} | {r.get('exp_unit')} | {r.get('verdict')} |"
        )
    d = distinctness(results)
    print("\n### 파라미터 효과(변종 구분)")
    for dg, info in sorted(d.items()):
        mark = "OK" if info["ok"] else "FLAG"
        print(f"- {dg}: {info['distinct']}/{info['variants']} distinct [{mark}]")
    flags = [k for k, v in results.items() if v.get("verdict") in ("FLAG", "ERROR")]
    print(f"\n### 종합: {len(results)} endpoints, FLAG/ERROR {len(flags)}: {flags}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--group")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report:
        report()
    else:
        run(a.group)
        print("done.")
