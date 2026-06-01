"""값-정확성 전수 대조 (#151 심화) — 큐레이션 함수 출력 == 원시 get_series/재계산.

각 엔드포인트의 반환 '값'을, 같은 통계표·항목코드로 직접 조회한 get_series 결과
(또는 파생 함수의 경우 원시 지수에서 독립 재계산)와 **소수점까지 정확 비교**한다.
범위 검증(phase4)이 못 잡는 래퍼 계층의 매핑·변환 오류를 값 단위로 확정한다.

사용: ECOS_API_KEY=... python scripts/audit_values_vs_raw.py [--group G] [--report]
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import ecos
import ecos.constants as c

OUT = Path(__file__).parent / "audit_values.json"
R = 3  # 비교 반올림 자리


def _ser(df, valcol="value"):
    """DataFrame -> {YYYY-MM-DD: round(value)} (단일 계열 비교용)."""
    d = df.sort_values("date")
    return {str(t.date()): round(float(v), R) for t, v in zip(d["date"], d[valcol], strict=False)}


def _raw(stat, period, item, s, e):
    return ecos.get_series(stat, period, item_code=item, start_date=s, end_date=e)


# (label, group, cur_callable, raw_callable) — 둘 다 단일계열 {date:value} 반환.
def single_checks():
    chk = []

    def add(label, group, cur, raw):
        chk.append((label, group, cur, raw))

    # 직접 단일계열: 큐레이션 vs get_series(동일 stat,item,period)
    add(
        "cpi",
        "prices",
        lambda: _ser(ecos.get_cpi("202301", "202312")),
        lambda: _ser(_raw(c.STAT_CPI, "M", c.ITEM_CPI_TOTAL, "202301", "202312")),
    )
    add(
        "core_cpi",
        "prices",
        lambda: _ser(ecos.get_core_cpi("202301", "202312")),
        lambda: _ser(_raw(c.STAT_CORE_CPI, "M", c.ITEM_CORE_CPI, "202301", "202312")),
    )
    add(
        "ppi",
        "prices",
        lambda: _ser(ecos.get_ppi("202301", "202312")),
        lambda: _ser(_raw(c.STAT_PPI, "M", c.ITEM_PPI_TOTAL, "202301", "202312")),
    )
    for cat, (st, it) in c.CPI_CATEGORY_CODES.items():
        add(
            f"cpi_by_category[{cat}]",
            "prices",
            lambda cat=cat: _ser(ecos.get_cpi_by_category(cat, "202301", "202312")),
            lambda st=st, it=it: _ser(_raw(st, "M", it, "202301", "202312")),
        )
    add(
        "base_rate",
        "rates",
        lambda: _ser(ecos.get_base_rate("202301", "202312")),
        lambda: _ser(_raw(c.STAT_BASE_RATE, "M", c.ITEM_BASE_RATE, "202301", "202312")),
    )
    for m, it in c.TREASURY_YIELD_ITEMS.items():
        add(
            f"treasury[{m}]",
            "rates",
            lambda m=m: _ser(ecos.get_treasury_yield(m, "20230101", "20231231")),
            lambda it=it: _ser(_raw(c.STAT_MARKET_RATE, "D", it, "20230101", "20231231")),
        )
    add(
        "fiscal_balance",
        "money",
        lambda: _ser(ecos.get_fiscal_balance("202301", "202312")),
        lambda: _ser(_raw(c.STAT_FISCAL_BALANCE, "M", c.ITEM_FISCAL_BALANCE, "202301", "202312")),
    )
    for ind in ("M1", "M2", "Lf"):
        add(
            f"money_supply[{ind}]",
            "money",
            lambda ind=ind: _ser(ecos.get_money_supply(ind, "202301", "202312")),
            lambda ind=ind: _ser(
                _raw(
                    c.MONEY_SUPPLY_STAT_CODES[ind],
                    "M",
                    c.MONEY_SUPPLY_ITEMS[ind],
                    "202301",
                    "202312",
                )
            ),
        )
    for v in c.M1_ITEMS:
        add(
            f"m1_variants[{v}]",
            "money",
            lambda v=v: _ser(ecos.get_m1_variants(v, start_date="202301", end_date="202312")),
            lambda v=v: _ser(_raw(c.M1_VARIANTS[v], "M", c.M1_ITEMS[v], "202301", "202312")),
        )
    for v in c.M2_ITEMS:
        add(
            f"m2_variants[{v}]",
            "money",
            lambda v=v: _ser(ecos.get_m2_variants(v, start_date="202301", end_date="202312")),
            lambda v=v: _ser(_raw(c.M2_VARIANTS[v], "M", c.M2_ITEMS[v], "202301", "202312")),
        )
    add(
        "bank_lending[all]",
        "money",
        lambda: _ser(ecos.get_bank_lending("all", "202301", "202312")),
        lambda: _ser(
            _raw(c.STAT_BANK_LENDING, "M", c.BANK_LENDING_ITEMS["all"], "202301", "202312")
        ),
    )
    add(
        "bank_lending[household]",
        "money",
        lambda: _ser(ecos.get_bank_lending("household", "202301", "202312")),
        lambda: _ser(_raw(c.STAT_HOUSEHOLD_LENDING, "M", "1110000", "202301", "202312")),
    )
    for cur_, it in c.EXCHANGE_RATE_ITEMS.items():
        add(
            f"exchange[{cur_}]",
            "external",
            lambda cur_=cur_: _ser(ecos.get_exchange_rate(cur_, "20230101", "20231231")),
            lambda it=it: _ser(_raw(c.STAT_EXCHANGE_RATE, "D", it, "20230101", "20231231")),
        )
    for acc, it in c.BOP_ACCOUNT_ITEMS.items():
        add(
            f"bop[{acc}]",
            "external",
            lambda acc=acc: _ser(ecos.get_balance_of_payments(acc, "202301", "202312")),
            lambda it=it: _ser(_raw(c.STAT_BOP, "M", it, "202301", "202312")),
        )
    for fl, it in c.TRADE_FLOW_ITEMS.items():
        add(
            f"trade[{fl}]",
            "external",
            lambda fl=fl: _ser(ecos.get_trade(fl, "202301", "202312")),
            lambda it=it: _ser(_raw(c.STAT_TRADE, "M", it, "202301", "202312")),
        )
    for idx, it in c.COMPOSITE_INDEX_ITEMS.items():
        add(
            f"composite[{idx}]",
            "real",
            lambda idx=idx: _ser(ecos.get_composite_index(idx, "202301", "202312")),
            lambda it=it: _ser(_raw(c.STAT_COMPOSITE_INDEX, "M", it, "202301", "202312")),
        )
    # 2축 고정 (item_code 리스트)
    for sa, ic2 in ((False, c.ITEM_INDUSTRIAL_ORIGINAL), (True, c.ITEM_INDUSTRIAL_SEASONAL)):
        add(
            f"industrial[sa={sa}]",
            "real",
            lambda sa=sa: _ser(ecos.get_industrial_production("202301", "202312", seasonal=sa)),
            lambda ic2=ic2: _ser(
                _raw(
                    c.STAT_INDUSTRIAL_PRODUCTION,
                    "M",
                    [c.ITEM_INDUSTRIAL_PRODUCTION, ic2],
                    "202301",
                    "202312",
                )
            ),
        )
    for sa, it in ((False, c.ITEM_FACILITY_INVESTMENT), (True, c.ITEM_FACILITY_INVESTMENT_SA)):
        add(
            f"facility[sa={sa}]",
            "real",
            lambda sa=sa: _ser(ecos.get_facility_investment("202301", "202312", seasonal=sa)),
            lambda it=it: _ser(_raw(c.STAT_FACILITY_INVESTMENT, "M", it, "202301", "202312")),
        )
    for sec, it in c.BSI_SECTOR_ITEMS.items():
        add(
            f"bsi[{sec}]",
            "sentiment",
            lambda sec=sec: _ser(ecos.get_business_sentiment(sec, "202301", "202312")),
            lambda it=it: _ser(_raw(c.STAT_BSI, "M", [it, c.ITEM_BSI_OUTLOOK], "202301", "202312")),
        )
    add(
        "consumer_sentiment",
        "sentiment",
        lambda: _ser(ecos.get_consumer_sentiment("202301", "202312")),
        lambda: _ser(_raw(c.STAT_CSI, "M", c.ITEM_CSI, "202301", "202312")),
    )
    # GDP (분기/연)
    add(
        "gdp[q,real]",
        "growth",
        lambda: _ser(ecos.get_gdp("quarterly", "real", "2022Q1", "2023Q4")),
        lambda: _ser(_raw(c.STAT_GDP_REAL, "Q", c.ITEM_GDP, "2022Q1", "2023Q4")),
    )
    add(
        "gdp[a,nominal]",
        "growth",
        lambda: _ser(ecos.get_gdp("annual", "nominal", "2020", "2023")),
        lambda: _ser(_raw(c.STAT_GDP_NOMINAL, "A", c.ITEM_GDP, "2020", "2023")),
    )
    add(
        "gdp_deflator",
        "growth",
        lambda: _ser(ecos.get_gdp_deflator("quarterly", "2022Q1", "2023Q4")),
        lambda: _ser(_raw(c.STAT_GDP_DEFLATOR, "Q", c.ITEM_GDP_DEFLATOR, "2022Q1", "2023Q4")),
    )
    add(
        "gdp_growth_rate[q]",
        "growth",
        lambda: _ser(ecos.get_gdp_growth_rate("quarterly", "2022Q1", "2023Q4")),
        lambda: _ser(_raw(c.STAT_GDP_GROWTH_RATE, "Q", c.ITEM_GDP_GROWTH_RATE, "2022Q1", "2023Q4")),
    )
    # 주식
    add(
        "stock[daily]",
        "markets",
        lambda: _ser(ecos.get_stock_index("daily", start_date="20230101", end_date="20230331")),
        lambda: _ser(
            _raw(c.STAT_STOCK_DAILY, "D", c.ITEM_STOCK_INDEX_DAILY, "20230101", "20230331")
        ),
    )
    add(
        "stock[monthly]",
        "markets",
        lambda: _ser(ecos.get_stock_index("monthly", start_date="202301", end_date="202312")),
        lambda: _ser(
            _raw(c.STAT_STOCK_MONTHLY, "M", c.ITEM_STOCK_INDEX_MONTHLY, "202301", "202312")
        ),
    )
    # --- 누락 단일계열 변종 (100% 커버리지, #151) ---
    add(
        "gdp[q,nominal]",
        "growth",
        lambda: _ser(ecos.get_gdp("quarterly", "nominal", "2022Q1", "2023Q4")),
        lambda: _ser(_raw(c.STAT_GDP_NOMINAL, "Q", c.ITEM_GDP, "2022Q1", "2023Q4")),
    )
    add(
        "gdp[a,real]",
        "growth",
        lambda: _ser(ecos.get_gdp("annual", "real", "2020", "2023")),
        lambda: _ser(_raw(c.STAT_GDP_REAL, "A", c.ITEM_GDP, "2020", "2023")),
    )
    add(
        "gdp_growth_rate[a]",
        "growth",
        lambda: _ser(ecos.get_gdp_growth_rate("annual", "2020", "2023")),
        lambda: _ser(_raw(c.STAT_GDP_GROWTH_RATE, "A", c.ITEM_GDP_GROWTH_RATE, "2020", "2023")),
    )
    # 금리 함수는 특정 item 단일계열 (interest_rate.py 기준)
    for b, st, it in (
        ("신규취급액", c.STAT_DEPOSIT_RATE_NEW, "BEABAA2"),
        ("잔액", c.STAT_DEPOSIT_RATE_BALANCE, "BEABAB2"),
    ):
        add(
            f"bank_deposit_rate[{b}]",
            "rates",
            lambda b=b: _ser(ecos.get_bank_deposit_rate(b, "202301", "202312")),
            lambda st=st, it=it: _ser(_raw(st, "M", it, "202301", "202312")),
        )
    for b, st, it in (
        ("신규취급액", c.STAT_LENDING_RATE_NEW, "BECBLA01"),
        ("잔액", c.STAT_LENDING_RATE_BALANCE, "BECBLB01"),
    ):
        add(
            f"bank_lending_rate[{b}]",
            "rates",
            lambda b=b: _ser(ecos.get_bank_lending_rate(b, "202301", "202312")),
            lambda st=st, it=it: _ser(_raw(st, "M", it, "202301", "202312")),
        )
    add(
        "household_credit[업권별]",
        "money",
        lambda: _ser(ecos.get_household_credit("업권별", "2022Q1", "2023Q4")),
        lambda: _ser(_raw(c.STAT_HOUSEHOLD_CREDIT_SECTOR, "Q", "1110000", "2022Q1", "2023Q4")),
    )
    add(
        "household_credit[용도별]",
        "money",
        lambda: _ser(ecos.get_household_credit("용도별", "2022Q1", "2023Q4")),
        lambda: _ser(_raw(c.STAT_HOUSEHOLD_CREDIT_PURPOSE, "Q", "1000000", "2022Q1", "2023Q4")),
    )
    return chk


# 파생: 원시 지수에서 독립 재계산.
def derived_checks():
    import pandas as pd

    chk = []

    def yoy_raw(stat, item, s_idx, e):
        df = _raw(stat, "M", item, s_idx, e).sort_values("date")
        # 함수(_price_measure)는 round(2) 하므로 재계산도 2자리로 맞춘다.
        df["v"] = (df["value"].pct_change(12) * 100).round(2)
        return df

    def add_change(label, fn, stat, item):
        # cur: 함수의 yoy, raw: get_series 지수에서 pct_change(12)*100 후 요청구간 trim
        def cur():
            return _ser(fn(start_date="202401", end_date="202412", measure="yoy"))

        def raw():
            df = yoy_raw(stat, item, "202301", "202412")
            df = df[df["date"] >= pd.Timestamp("2024-01-01")]
            return {
                str(t.date()): float(v)
                for t, v in zip(df["date"], df["v"], strict=False)
                if pd.notna(v)
            }

        chk.append((label, "derived", cur, raw))

    add_change("cpi[yoy]", ecos.get_cpi, c.STAT_CPI, c.ITEM_CPI_TOTAL)
    add_change("core_cpi[yoy]", ecos.get_core_cpi, c.STAT_CORE_CPI, c.ITEM_CORE_CPI)
    add_change("ppi[yoy]", ecos.get_ppi, c.STAT_PPI, c.ITEM_PPI_TOTAL)

    # yield_spread = long - short
    def ys_cur():
        df = ecos.get_yield_spread("10Y", "3Y", "20230101", "20230630").sort_values("date")
        return {
            str(t.date()): round(float(v), R)
            for t, v in zip(df["date"], df["spread"], strict=False)
        }

    def ys_raw():
        lo = _raw(c.STAT_MARKET_RATE, "D", c.TREASURY_YIELD_ITEMS["10Y"], "20230101", "20230630")
        sh = _raw(c.STAT_MARKET_RATE, "D", c.TREASURY_YIELD_ITEMS["3Y"], "20230101", "20230630")
        lo, sh = lo.set_index("date")["value"], sh.set_index("date")["value"]
        spread = (lo - sh).round(R)
        return {str(t.date()): float(v) for t, v in spread.items()}

    chk.append(("yield_spread", "derived", ys_cur, ys_raw))
    return chk


def _vmultiset(dates, values):
    """{(date, rank): value} — 날짜별 값 multiset(정렬). 동명 item_code1 충돌을 피하고
    값 집합의 정확 일치를 검증한다."""
    import collections

    by_date = collections.defaultdict(list)
    for t, v in zip(dates, values, strict=False):
        by_date[str(t.date())].append(round(float(v), R))
    out = {}
    for d, vs in by_date.items():
        for i, v in enumerate(sorted(vs)):
            out[(d, i)] = v
    return out


def _long(df):
    """long-format 함수 출력 -> 날짜별 값 multiset."""
    return _vmultiset(df["date"], df["value"])


def _raw_long(stat, period, s, e, *, fix1=None, fix2=None, prefix="", exclude1=None):
    """get_series 전량 조회 → 함수 내부와 동일한 고정축/prefix 필터 후 날짜별 값 multiset."""
    df = ecos.get_series(stat, period, start_date=s, end_date=e)
    if fix2 is not None and "item_code2" in df.columns:
        df = df[df["item_code2"] == fix2]
    if fix1 is not None and "item_code1" in df.columns:
        df = df[df["item_code1"] == fix1]
    if exclude1 is not None and "item_code1" in df.columns:
        df = df[df["item_code1"] != exclude1]
    if prefix and "item_code1" in df.columns:
        df = df[df["item_code1"].astype(str).str.startswith(prefix)]
    return _vmultiset(df["date"], df["value"])


# long-format / 다축 함수 — 함수 출력 vs 원시(고정축 적용) 행단위 정확 대조.
def long_checks():
    chk = []

    def add(label, group, cur, raw):
        chk.append((label, group, cur, raw))

    # retail: item_code2=index 고정, 분류=item_name1
    for ix, t2 in c.RETAIL_SALES_INDEX_ITEMS.items():
        add(
            f"retail[{ix}]",
            "real",
            lambda ix=ix: _long(ecos.get_retail_sales(ix, start_date="202301", end_date="202312")),
            lambda t2=t2: _raw_long(c.STAT_RETAIL_SALES, "M", "202301", "202312", fix2=t2),
        )
    # bond 종류별: item_code2=measure 고정, 분류=item_name1
    for meas, mc in c.BOND_YIELD_TYPE_MEASURE_CODE.items():
        add(
            f"bond_market[종류별,{meas}]",
            "markets",
            lambda meas=meas: _long(
                ecos.get_bond_market("종류별", meas, start_date="202301", end_date="202312")
            ),
            lambda mc=mc: _raw_long(c.STAT_BOND_YIELD_TYPE, "M", "202301", "202312", fix2=mc),
        )
    # bond 시장별: item_code1=measure 고정, 분류=item_name2
    for meas, mc in c.BOND_MARKET_MEASURE_CODE.items():
        add(
            f"bond_market[시장별,{meas}]",
            "markets",
            lambda meas=meas: _long(
                ecos.get_bond_market("시장별", meas, start_date="202301", end_date="202312")
            ),
            lambda mc=mc: _raw_long(c.STAT_BOND_MARKET, "M", "202301", "202312", fix1=mc),
        )
    # m2_by_holder: 고정축 없음, 분류=item_name1
    add(
        "m2_by_holder",
        "money",
        lambda: _long(ecos.get_m2_by_holder(start_date="202301", end_date="202312")),
        lambda: _raw_long(c.M2_HOLDER_VARIANTS["말잔_원계열"], "M", "202301", "202312"),
    )
    # gdp_by_industry / expenditure / deflator_by_industry / cpi_monthly / lending_detail
    add(
        "gdp_by_industry[real]",
        "growth",
        lambda: _long(ecos.get_gdp_by_industry("real", start_date="2023Q1", end_date="2023Q4")),
        lambda: _raw_long(c.GDP_BY_INDUSTRY_VARIANTS["계절조정_실질"], "Q", "2023Q1", "2023Q4"),
    )
    add(
        "gdp_by_expenditure[real]",
        "growth",
        lambda: _long(ecos.get_gdp_by_expenditure("real", start_date="2023Q1", end_date="2023Q4")),
        lambda: _raw_long(c.GDP_BY_EXPENDITURE_VARIANTS["계절조정_실질"], "Q", "2023Q1", "2023Q4"),
    )
    add(
        "gdp_deflator_by_industry",
        "growth",
        lambda: _long(ecos.get_gdp_deflator_by_industry(start_date="2023Q1", end_date="2023Q4")),
        lambda: _raw_long(c.STAT_GDP_DEFLATOR_BY_INDUSTRY, "Q", "2023Q1", "2023Q4"),
    )
    add(
        "cpi_monthly",
        "prices",
        lambda: _long(ecos.get_cpi_monthly(start_date="202401", end_date="202403")),
        lambda: _raw_long(c.STAT_CPI_MONTHLY, "M", "202401", "202403"),
    )
    add(
        "household_lending_detail",
        "money",
        lambda: _long(ecos.get_household_lending_detail(start_date="202401", end_date="202403")),
        lambda: _raw_long(c.STAT_HOUSEHOLD_LENDING_PURPOSE, "M", "202401", "202403"),
    )
    # investor_trading: item_code2=metric 고정, prefix=action, 합계행(prefix 정확) 제외
    for act, pre in c.INVESTOR_TRADING_ACTION_PREFIX.items():
        add(
            f"investor_trading[{act}]",
            "markets",
            lambda act=act: _long(
                ecos.get_investor_trading(act, "거래대금", start_date="202401", end_date="202403")
            ),
            lambda pre=pre: _raw_long(
                c.STAT_INVESTOR_TRADING,
                "M",
                "202401",
                "202403",
                fix2=c.INVESTOR_TRADING_METRIC_CODE["거래대금"],
                prefix=pre,
                exclude1=pre,
            ),
        )
    # borrower_loan: prefix=category, 잔액
    for cat, pre in (
        ("연령별", c.BORROWER_LOAN_CATEGORY_PREFIX["연령별"]),
        ("업권별", c.BORROWER_LOAN_CATEGORY_PREFIX["업권별"]),
    ):
        add(
            f"borrower_loan[{cat}]",
            "money",
            lambda cat=cat: _long(
                ecos.get_borrower_loan("잔액", cat, start_date="2023Q1", end_date="2023Q4")
            ),
            lambda pre=pre: _raw_long(
                c.BORROWER_LOAN_STAT_CODES["잔액"], "Q", "2023Q1", "2023Q4", prefix=pre
            ),
        )
    # consumer_sentiment 구성지표 (인구통계 전체 고정)
    add(
        "consumer_sentiment[소비지출전망CSI]",
        "sentiment",
        lambda: _ser(
            ecos.get_consumer_sentiment("202301", "202312", sub_category="소비지출전망CSI")
        ),
        lambda: _ser(_raw(c.STAT_CSI, "M", ["FMCB", "99988"], "202301", "202312")),
    )
    return chk


ALL = single_checks() + derived_checks() + long_checks()


def run(group=None):
    ecos.set_api_key(os.environ["ECOS_API_KEY"])
    ecos.disable_cache()
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    for label, grp, cur, raw in ALL:
        if group and grp != group:
            continue
        if label in res:
            print(f"  {label} cached")
            continue
        try:
            cv, rv = cur(), raw()
            keys = sorted(set(cv) & set(rv))
            mism = [(k, cv.get(k), rv.get(k)) for k in keys if cv.get(k) != rv.get(k)]
            only = sorted(set(cv) ^ set(rv))
            ok = not mism and not only and len(keys) > 0
            res[label] = {
                "group": grp,
                "n": len(keys),
                "match": ok,
                "mismatch": mism[:5],
                "key_diff": only[:5],
            }
            print(
                f"  {label:30s} {'OK' if ok else 'FAIL'} n={len(keys)}"
                f"{'' if ok else ' mism=' + str(mism[:3]) + ' keydiff=' + str(only[:3])}"
            )
        except Exception as e:
            res[label] = {"group": grp, "error": str(e), "match": False}
            print(f"  {label:30s} ERROR {e}")
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    return res


def report():
    res = json.loads(OUT.read_text())
    ok = [k for k, v in res.items() if v.get("match")]
    bad = [k for k, v in res.items() if not v.get("match")]
    print(f"값-정확성 대조: {len(ok)}/{len(res)} 일치")
    for k in bad:
        print(f"  FAIL {k}: {res[k]}")
    print("FAIL/ERROR:", bad or "없음")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--group")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run(a.group)
