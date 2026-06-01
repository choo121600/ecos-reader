"""완전 전수 값-정확성 대조 (#151) — 전 파라미터 조합 × 전 기간.

각 큐레이션 함수의 **모든 파라미터 데카르트 곱**을, 가용 **전 기간**(1960~)에 대해
같은 코드 원시 get_series 조회와 값 단위로 대조한다. get_series 는 큐레이션 함수의
단일요청 한도(end=100000)와 동일하게 max_rows=100000 으로 맞춰 공정 비교한다.

값 비교는 공유 날짜 키 기준(절단이 발생해도 동일 구간이면 값은 일치). 키 차이는
truncation 정보로 별도 표기. rate limit(300/3분) — 배치(--group)로 실행.
사용: ECOS_API_KEY=... python scripts/audit_values_full.py [--group G|--report]
"""

from __future__ import annotations

import argparse
import collections
import itertools
import json
import os
from pathlib import Path

import ecos
import ecos.constants as c

OUT = Path(__file__).parent / "audit_values_full.json"
R = 3
RANGES = {
    "D": ("19600101", "20261231"),
    "M": ("196001", "202612"),
    "Q": ("1960Q1", "2026Q4"),
    "A": ("1960", "2026"),
}
PMAP = {"monthly": "M", "quarterly": "Q", "annual": "A", "daily": "D"}


def _raw(stat, period, item, *, fix1=None, fix2=None, prefix="", exclude1=None):
    s, e = RANGES[period]
    df = ecos.get_series(
        stat, period, item_code=item, start_date=s, end_date=e, max_rows=100000, page_size=100000
    )
    if fix2 is not None and "item_code2" in df.columns:
        df = df[df["item_code2"] == fix2]
    if fix1 is not None and "item_code1" in df.columns:
        df = df[df["item_code1"] == fix1]
    if exclude1 is not None and "item_code1" in df.columns:
        df = df[df["item_code1"] != exclude1]
    if prefix and "item_code1" in df.columns:
        df = df[df["item_code1"].astype(str).str.startswith(prefix)]
    return df


def _isnan(v):
    return v != v


def _single(df, valcol="value"):
    if df.empty or "date" not in df.columns:
        return {}
    d = df.sort_values("date")
    return {
        str(t.date()): round(float(v), R)
        for t, v in zip(d["date"], d[valcol], strict=False)
        if not _isnan(v)
    }


def _multiset(df):
    # NaN(결측)은 양측 동일하게 제외 — 값 multiset만 대조 (nan!=nan 거짓불일치 방지).
    if df.empty or "date" not in df.columns:
        return {}
    by = collections.defaultdict(list)
    for t, v in zip(df["date"], df["value"], strict=False):
        if not _isnan(v):
            by[str(t.date())].append(round(float(v), R))
    out = {}
    for d, vs in by.items():
        for i, v in enumerate(sorted(vs)):
            out[(d, i)] = v
    return out


def _rng(period):
    return RANGES[period]


# 각 엔트리: (label, group, kind, cur_call, raw_call)
# kind 'single' -> _single 비교 / 'long' -> _multiset 비교
def build():
    e = []

    def add_single(label, grp, cur, raw):
        e.append((label, grp, "single", cur, raw))

    def add_long(label, grp, cur, raw):
        e.append((label, grp, "long", cur, raw))

    # ---------- 물가 ----------
    for fn, name, stat, item in (
        (ecos.get_cpi, "cpi", c.STAT_CPI, c.ITEM_CPI_TOTAL),
        (ecos.get_core_cpi, "core_cpi", c.STAT_CORE_CPI, c.ITEM_CORE_CPI),
        (ecos.get_ppi, "ppi", c.STAT_PPI, c.ITEM_PPI_TOTAL),
    ):
        rs, re = _rng("M")
        add_single(
            f"{name}[index]",
            "prices",
            lambda fn=fn, rs=rs, re=re: _single(fn(rs, re)),
            lambda stat=stat, item=item: _single(_raw(stat, "M", item)),
        )
        for meas, per in (("yoy", 12), ("mom", 1)):
            add_single(
                f"{name}[{meas}]",
                "prices",
                lambda fn=fn, meas=meas, rs=rs, re=re: _single(fn(rs, re, measure=meas)),
                lambda stat=stat, item=item, per=per: _yoy(stat, item, per),
            )
    for cat, (st, it) in c.CPI_CATEGORY_CODES.items():
        add_single(
            f"cpi_by_category[{cat}]",
            "prices",
            lambda cat=cat: _single(ecos.get_cpi_by_category(cat, *_rng("M"))),
            lambda st=st, it=it: _single(_raw(st, "M", it)),
        )
    add_long(
        "cpi_monthly",
        "prices",
        lambda: _multiset(ecos.get_cpi_monthly(start_date=_rng("M")[0], end_date=_rng("M")[1])),
        lambda: _multiset(_raw(c.STAT_CPI_MONTHLY, "M", None)),
    )

    # ---------- 금리 ----------
    for fr in ("daily", "monthly"):
        p = PMAP[fr]
        add_single(
            f"base_rate[{fr}]",
            "rates",
            lambda fr=fr, p=p: _single(ecos.get_base_rate(*_rng(p), frequency=fr)),
            lambda p=p: _single(_raw(c.STAT_BASE_RATE, p, c.ITEM_BASE_RATE)),
        )
    for m, it in c.TREASURY_YIELD_ITEMS.items():
        add_single(
            f"treasury[{m}]",
            "rates",
            lambda m=m: _single(ecos.get_treasury_yield(m, *_rng("D"))),
            lambda it=it: _single(_raw(c.STAT_MARKET_RATE, "D", it)),
        )
    for lo, sh in itertools.product(("10Y", "20Y", "30Y"), ("1Y", "3Y", "5Y")):
        add_single(
            f"yield_spread[{lo}-{sh}]",
            "rates",
            lambda lo=lo, sh=sh: _spread_cur(lo, sh),
            lambda lo=lo, sh=sh: _spread_raw(lo, sh),
        )
    for b, st, it in (
        ("신규취급액", c.STAT_DEPOSIT_RATE_NEW, "BEABAA2"),
        ("잔액", c.STAT_DEPOSIT_RATE_BALANCE, "BEABAB2"),
    ):
        add_single(
            f"deposit_rate[{b}]",
            "rates",
            lambda b=b: _single(ecos.get_bank_deposit_rate(b, *_rng("M"))),
            lambda st=st, it=it: _single(_raw(st, "M", it)),
        )
    for b, st, it in (
        ("신규취급액", c.STAT_LENDING_RATE_NEW, "BECBLA01"),
        ("잔액", c.STAT_LENDING_RATE_BALANCE, "BECBLB01"),
    ):
        add_single(
            f"lending_rate[{b}]",
            "rates",
            lambda b=b: _single(ecos.get_bank_lending_rate(b, *_rng("M"))),
            lambda st=st, it=it: _single(_raw(st, "M", it)),
        )

    # ---------- 성장 ----------
    for fr, ba in itertools.product(("quarterly", "annual"), ("real", "nominal")):
        p = PMAP[fr]
        stat = c.STAT_GDP_REAL if ba == "real" else c.STAT_GDP_NOMINAL
        add_single(
            f"gdp[{fr},{ba}]",
            "growth",
            lambda fr=fr, ba=ba, p=p: _single(ecos.get_gdp(fr, ba, *_rng(p))),
            lambda stat=stat, p=p: _single(_raw(stat, p, c.ITEM_GDP)),
        )
    for fr in ("quarterly", "annual"):
        p = PMAP[fr]
        add_single(
            f"gdp_growth_rate[{fr}]",
            "growth",
            lambda fr=fr, p=p: _single(ecos.get_gdp_growth_rate(fr, *_rng(p))),
            lambda p=p: _single(_raw(c.STAT_GDP_GROWTH_RATE, p, c.ITEM_GDP_GROWTH_RATE)),
        )
        add_single(
            f"gdp_deflator[{fr}]",
            "growth",
            lambda fr=fr, p=p: _single(ecos.get_gdp_deflator(fr, *_rng(p))),
            lambda p=p: _single(_raw(c.STAT_GDP_DEFLATOR, p, c.ITEM_GDP_DEFLATOR)),
        )
        add_single(
            f"gdp_deflator_by_industry[{fr}]",
            "growth",
            lambda fr=fr, p=p: _multiset(
                ecos.get_gdp_deflator_by_industry(fr, start_date=_rng(p)[0], end_date=_rng(p)[1])
            ),
            lambda p=p: _multiset(_raw(c.STAT_GDP_DEFLATOR_BY_INDUSTRY, p, None)),
        )
    for ba, sa, fr in itertools.product(
        ("real", "nominal"), (True, False), ("quarterly", "annual")
    ):
        p = PMAP[fr]
        key = f"{'계절조정' if sa else '원계열'}_{'실질' if ba == 'real' else '명목'}"
        stat = c.GDP_BY_INDUSTRY_VARIANTS[key]
        # 계절조정 표는 분기만 — 연간 요청 시 함수가 예외/빈값일 수 있어 분기만 검증
        if sa and fr == "annual":
            continue
        add_long(
            f"gdp_by_industry[{ba},sa={sa},{fr}]",
            "growth",
            lambda ba=ba, sa=sa, fr=fr, p=p: _multiset(
                ecos.get_gdp_by_industry(ba, sa, fr, start_date=_rng(p)[0], end_date=_rng(p)[1])
            ),
            lambda stat=stat, p=p: _multiset(_raw(stat, p, None)),
        )
    for ba, fr in itertools.product(("real", "nominal"), ("quarterly", "annual")):
        p = PMAP[fr]
        # 함수와 동일: 분기=계절조정, 연간=원계열 fallback.
        season = "계절조정" if fr == "quarterly" else "원계열"
        key = f"{season}_{'실질' if ba == 'real' else '명목'}"
        stat = c.GDP_BY_EXPENDITURE_VARIANTS[key]
        add_long(
            f"gdp_by_expenditure[{ba},{fr}]",
            "growth",
            lambda ba=ba, fr=fr, p=p: _multiset(
                ecos.get_gdp_by_expenditure(ba, fr, start_date=_rng(p)[0], end_date=_rng(p)[1])
            ),
            lambda stat=stat, p=p: _multiset(_raw(stat, p, None)),
        )

    # ---------- 통화 ----------
    for ind, fr in itertools.product(("M1", "M2", "Lf"), ("monthly", "quarterly", "annual")):
        p = PMAP[fr]
        add_single(
            f"money_supply[{ind},{fr}]",
            "money",
            lambda ind=ind, fr=fr, p=p: _single(ecos.get_money_supply(ind, *_rng(p), frequency=fr)),
            lambda ind=ind, p=p: _single(
                _raw(c.MONEY_SUPPLY_STAT_CODES[ind], p, c.MONEY_SUPPLY_ITEMS[ind])
            ),
        )
    for v, fr in itertools.product(c.M1_ITEMS, ("monthly", "quarterly", "annual")):
        p = PMAP[fr]
        add_single(
            f"m1_variants[{v},{fr}]",
            "money",
            lambda v=v, fr=fr, p=p: _single(
                ecos.get_m1_variants(v, start_date=_rng(p)[0], end_date=_rng(p)[1], frequency=fr)
            ),
            lambda v=v, p=p: _single(_raw(c.M1_VARIANTS[v], p, c.M1_ITEMS[v])),
        )
    for v, fr in itertools.product(c.M2_ITEMS, ("monthly", "quarterly", "annual")):
        p = PMAP[fr]
        add_single(
            f"m2_variants[{v},{fr}]",
            "money",
            lambda v=v, fr=fr, p=p: _single(
                ecos.get_m2_variants(v, start_date=_rng(p)[0], end_date=_rng(p)[1], frequency=fr)
            ),
            lambda v=v, p=p: _single(_raw(c.M2_VARIANTS[v], p, c.M2_ITEMS[v])),
        )
    for v, fr in itertools.product(c.M2_HOLDER_VARIANTS, ("monthly", "quarterly", "annual")):
        p = PMAP[fr]
        add_long(
            f"m2_by_holder[{v},{fr}]",
            "money",
            lambda v=v, fr=fr, p=p: _multiset(
                ecos.get_m2_by_holder(v, start_date=_rng(p)[0], end_date=_rng(p)[1], frequency=fr)
            ),
            lambda v=v, p=p: _multiset(_raw(c.M2_HOLDER_VARIANTS[v], p, None)),
        )
    for sec, fr in itertools.product(("all", "household"), ("monthly", "quarterly", "annual")):
        p = PMAP[fr]
        stat = c.STAT_BANK_LENDING if sec == "all" else c.STAT_HOUSEHOLD_LENDING
        it = c.BANK_LENDING_ITEMS["all"] if sec == "all" else "1110000"
        add_single(
            f"bank_lending[{sec},{fr}]",
            "money",
            lambda sec=sec, fr=fr, p=p: _single(ecos.get_bank_lending(sec, *_rng(p), frequency=fr)),
            lambda stat=stat, it=it, p=p: _single(_raw(stat, p, it)),
        )
    for cat, st, it in (
        ("업권별", c.STAT_HOUSEHOLD_CREDIT_SECTOR, "1110000"),
        ("용도별", c.STAT_HOUSEHOLD_CREDIT_PURPOSE, "1000000"),
    ):
        add_single(
            f"household_credit[{cat}]",
            "money",
            lambda cat=cat: _single(ecos.get_household_credit(cat, *_rng("Q"))),
            lambda st=st, it=it: _single(_raw(st, "Q", it)),
        )
    add_long(
        "household_lending_detail",
        "money",
        lambda: _multiset(
            ecos.get_household_lending_detail(start_date=_rng("M")[0], end_date=_rng("M")[1])
        ),
        lambda: _multiset(_raw(c.STAT_HOUSEHOLD_LENDING_PURPOSE, "M", None)),
    )
    for lt, cat in itertools.product(("잔액", "신규"), c.BORROWER_LOAN_CATEGORY_PREFIX):
        pre = c.BORROWER_LOAN_CATEGORY_PREFIX[cat]
        stat = c.BORROWER_LOAN_STAT_CODES[lt]
        exact = cat == "전체"
        add_long(
            f"borrower_loan[{lt},{cat}]",
            "money",
            lambda lt=lt, cat=cat: _multiset(
                ecos.get_borrower_loan(lt, cat, start_date=_rng("Q")[0], end_date=_rng("Q")[1])
            ),
            lambda stat=stat, pre=pre, exact=exact: _multiset(
                _raw(stat, "Q", None, fix1=pre) if exact else _raw(stat, "Q", None, prefix=pre)
            ),
        )

    # ---------- 대외 ----------
    for cur_, it in c.EXCHANGE_RATE_ITEMS.items():
        add_single(
            f"exchange[{cur_}]",
            "external",
            lambda cur_=cur_: _single(ecos.get_exchange_rate(cur_, *_rng("D"))),
            lambda it=it: _single(_raw(c.STAT_EXCHANGE_RATE, "D", it)),
        )
    for acc, fr in itertools.product(c.BOP_ACCOUNT_ITEMS, ("monthly", "quarterly", "annual")):
        p = PMAP[fr]
        add_single(
            f"bop[{acc},{fr}]",
            "external",
            lambda acc=acc, fr=fr, p=p: _single(
                ecos.get_balance_of_payments(acc, *_rng(p), frequency=fr)
            ),
            lambda acc=acc, p=p: _single(_raw(c.STAT_BOP, p, c.BOP_ACCOUNT_ITEMS[acc])),
        )
    for fl, fr in itertools.product(("export", "import"), ("monthly", "annual")):
        p = PMAP[fr]
        add_single(
            f"trade[{fl},{fr}]",
            "external",
            lambda fl=fl, fr=fr, p=p: _single(ecos.get_trade(fl, *_rng(p), frequency=fr)),
            lambda fl=fl, p=p: _single(_raw(c.STAT_TRADE, p, c.TRADE_FLOW_ITEMS[fl])),
        )

    # ---------- 시장 ----------
    for fr, stat, it in (
        ("daily", c.STAT_STOCK_DAILY, c.ITEM_STOCK_INDEX_DAILY),
        ("monthly", c.STAT_STOCK_MONTHLY, c.ITEM_STOCK_INDEX_MONTHLY),
    ):
        p = PMAP[fr]
        add_single(
            f"stock[{fr}]",
            "markets",
            lambda fr=fr, p=p: _single(
                ecos.get_stock_index(fr, start_date=_rng(p)[0], end_date=_rng(p)[1])
            ),
            lambda stat=stat, it=it, p=p: _single(_raw(stat, p, it)),
        )
    for act, metric, fr in itertools.product(
        ("순매수", "매수", "매도"), ("거래대금", "거래량"), ("monthly", "annual")
    ):
        p = PMAP[fr]
        pre = c.INVESTOR_TRADING_ACTION_PREFIX[act]
        mc = c.INVESTOR_TRADING_METRIC_CODE[metric]
        add_long(
            f"investor_trading[{act},{metric},{fr}]",
            "markets",
            lambda act=act, metric=metric, fr=fr, p=p: _multiset(
                ecos.get_investor_trading(
                    act, metric, start_date=_rng(p)[0], end_date=_rng(p)[1], frequency=fr
                )
            ),
            lambda pre=pre, mc=mc, p=p: _multiset(
                _raw(c.STAT_INVESTOR_TRADING, p, None, fix2=mc, prefix=pre, exclude1=pre)
            ),
        )
    for bt, meas, fr in itertools.product(
        ("종류별", "시장별"),
        ("거래대금", "거래량", "상장잔액", "상장종목수"),
        ("monthly", "annual"),
    ):
        p = PMAP[fr]
        if bt == "종류별":
            mc = c.BOND_YIELD_TYPE_MEASURE_CODE[meas]
            add_long(
                f"bond_market[{bt},{meas},{fr}]",
                "markets",
                lambda bt=bt, meas=meas, fr=fr, p=p: _multiset(
                    ecos.get_bond_market(
                        bt, meas, start_date=_rng(p)[0], end_date=_rng(p)[1], frequency=fr
                    )
                ),
                lambda mc=mc, p=p: _multiset(_raw(c.STAT_BOND_YIELD_TYPE, p, None, fix2=mc)),
            )
        elif meas in c.BOND_MARKET_MEASURE_CODE:
            mc = c.BOND_MARKET_MEASURE_CODE[meas]
            add_long(
                f"bond_market[{bt},{meas},{fr}]",
                "markets",
                lambda bt=bt, meas=meas, fr=fr, p=p: _multiset(
                    ecos.get_bond_market(
                        bt, meas, start_date=_rng(p)[0], end_date=_rng(p)[1], frequency=fr
                    )
                ),
                lambda mc=mc, p=p: _multiset(_raw(c.STAT_BOND_MARKET, p, None, fix1=mc)),
            )

    # ---------- 심리/실물 ----------
    for sec, it in c.BSI_SECTOR_ITEMS.items():
        add_single(
            f"bsi[{sec}]",
            "sentiment",
            lambda sec=sec: _single(ecos.get_business_sentiment(sec, *_rng("M"))),
            lambda it=it: _single(_raw(c.STAT_BSI, "M", [it, c.ITEM_BSI_OUTLOOK])),
        )
    add_single(
        "consumer_sentiment",
        "sentiment",
        lambda: _single(ecos.get_consumer_sentiment(*_rng("M"))),
        lambda: _single(_raw(c.STAT_CSI, "M", c.ITEM_CSI)),
    )
    for idx, it in c.COMPOSITE_INDEX_ITEMS.items():
        add_single(
            f"composite[{idx}]",
            "sentiment",
            lambda idx=idx: _single(ecos.get_composite_index(idx, *_rng("M"))),
            lambda it=it: _single(_raw(c.STAT_COMPOSITE_INDEX, "M", it)),
        )
    for ix, fr in itertools.product(
        ("nominal", "real", "seasonal"), ("monthly", "quarterly", "annual")
    ):
        if ix == "seasonal" and fr == "annual":
            continue  # ECOS 미제공(계절조정 연간) — 함수가 ValueError
        p = PMAP[fr]
        t2 = c.RETAIL_SALES_INDEX_ITEMS[ix]
        add_long(
            f"retail[{ix},{fr}]",
            "sentiment",
            lambda ix=ix, fr=fr, p=p: _multiset(
                ecos.get_retail_sales(ix, start_date=_rng(p)[0], end_date=_rng(p)[1], frequency=fr)
            ),
            lambda t2=t2, p=p: _multiset(_raw(c.STAT_RETAIL_SALES, p, None, fix2=t2)),
        )
    for sa, fr in itertools.product((False, True), ("monthly", "quarterly", "annual")):
        if sa and fr == "annual":
            continue  # ECOS 미제공(계절조정 연간) — 함수가 ValueError
        p = PMAP[fr]
        ic2 = c.ITEM_INDUSTRIAL_SEASONAL if sa else c.ITEM_INDUSTRIAL_ORIGINAL
        add_single(
            f"industrial[sa={sa},{fr}]",
            "sentiment",
            lambda sa=sa, fr=fr, p=p: _single(
                ecos.get_industrial_production(*_rng(p), seasonal=sa, frequency=fr)
            ),
            lambda ic2=ic2, p=p: _single(
                _raw(c.STAT_INDUSTRIAL_PRODUCTION, p, [c.ITEM_INDUSTRIAL_PRODUCTION, ic2])
            ),
        )
        it = c.ITEM_FACILITY_INVESTMENT_SA if sa else c.ITEM_FACILITY_INVESTMENT
        add_single(
            f"facility[sa={sa},{fr}]",
            "sentiment",
            lambda sa=sa, fr=fr, p=p: _single(
                ecos.get_facility_investment(*_rng(p), seasonal=sa, frequency=fr)
            ),
            lambda it=it, p=p: _single(_raw(c.STAT_FACILITY_INVESTMENT, p, it)),
        )
    return e


def _yoy(stat, item, periods):
    df = _raw(stat, "M", item).sort_values("date")
    df["v"] = (df["value"].pct_change(periods) * 100).round(2)
    df = df.dropna(subset=["v"])
    return {str(t.date()): float(v) for t, v in zip(df["date"], df["v"], strict=False)}


def _spread_cur(lo, sh):
    df = ecos.get_yield_spread(lo, sh, *RANGES["D"]).sort_values("date")
    return {
        str(t.date()): round(float(v), R) for t, v in zip(df["date"], df["spread"], strict=False)
    }


def _spread_raw(lo, sh):
    a = _raw(c.STAT_MARKET_RATE, "D", c.TREASURY_YIELD_ITEMS[lo]).set_index("date")["value"]
    b = _raw(c.STAT_MARKET_RATE, "D", c.TREASURY_YIELD_ITEMS[sh]).set_index("date")["value"]
    sp = (a - b).round(R).dropna()
    return {str(t.date()): float(v) for t, v in sp.items()}


ALL = build()


def run(group=None):
    ecos.set_api_key(os.environ["ECOS_API_KEY"])
    ecos.disable_cache()
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    for label, grp, _kind, cur, raw in ALL:
        if group and grp != group:
            continue
        if label in res:
            continue
        try:
            cv, rv = cur(), raw()
            keys = sorted(set(cv) & set(rv))
            mism = [(k, cv[k], rv[k]) for k in keys if cv[k] != rv[k]]
            only_cur, only_raw = sorted(set(cv) - set(rv)), sorted(set(rv) - set(cv))
            both_empty = not cv and not rv  # 양측 빈값 = 데이터 없는 조합(일관) = OK
            # 값 일치(공유 키 전부) + 키 누락 없음이면 OK. 키 차이는 별도 표기.
            ok = both_empty or (not mism and not only_cur and not only_raw and len(keys) > 0)
            res[label] = {
                "group": grp,
                "n": len(keys),
                "match_on_shared": not mism,
                "ok": ok,
                "n_cur": len(cv),
                "n_raw": len(rv),
                "mismatch": mism[:3],
                "only_cur": len(only_cur),
                "only_raw": len(only_raw),
            }
            tag = "OK" if ok else ("VALOK/keydiff" if not mism else "FAIL")
            print(
                f"  {label:40s} {tag} n={len(keys)} cur={len(cv)} raw={len(rv)}"
                f"{'' if not mism else ' MISM=' + str(mism[:2])}"
            )
        except Exception as ex:
            res[label] = {"group": grp, "error": str(ex), "ok": False}
            print(f"  {label:40s} ERROR {ex}")
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    return res


def report():
    res = json.loads(OUT.read_text())
    val_fail = [k for k, v in res.items() if v.get("mismatch")]
    err = [k for k, v in res.items() if v.get("error")]
    keydiff = [
        k
        for k, v in res.items()
        if not v.get("ok") and not v.get("mismatch") and not v.get("error")
    ]
    print(f"완전 전수: {len(res)} 조합")
    print(f"  값 불일치(MISM): {len(val_fail)} {val_fail}")
    print(f"  에러: {len(err)} {err}")
    print(f"  값일치+키차이(절단/범위차, 값오류 아님): {len(keydiff)} {keydiff[:10]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--group")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run(a.group)
