"""Descriptive and scenario numbers for the thesis. Reads only the CSV files in this folder.

Everything here is DESCRIPTIVE or a labelled SENSITIVITY, not a forecast.
Items marked POST-HOC were not in PREREGISTRATION.md and are exploratory.
Run: python scenarios.py
"""
import json
import os

import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
nd = pd.read_csv(f"{D}/near_daily.csv", parse_dates=["date"]).set_index("date")
sup = pd.read_csv(f"{D}/near_total_supply_weekly.csv", parse_dates=["week_ending"]).set_index("week_ending").total_supply
bb = pd.read_csv(f"{D}/near_buybacks_daily.csv", parse_dates=["date"]).set_index("date").buybacks_usd

INTENTS = pd.Timestamp("2025-09-23")
nd["rev_c"] = nd.rev.where(~((nd.index >= INTENTS) & ((nd.rev - nd.fees).abs() < 1)))
nd["intents"] = (nd.rev_c - nd.fees).clip(lower=0)
nd.loc[nd.index < INTENTS, "intents"] = 0.0
nd.loc[nd.rev_c.isna() & (nd.index >= INTENTS), "intents"] = np.nan
out = {}

# ---- 1. monthly revenue composition (complete months) ----
m = pd.DataFrame({"gas": nd.fees.resample("MS").sum(), "intents": nd.intents.resample("MS").sum(min_count=20)}).loc[:"2026-10-01"]
m["share_intents"] = m.intents / (m.gas + m.intents)
print("== Monthly revenue composition (USD) ==")
print((m.loc["2025-08-01":] / 1).round(2).assign(gas=lambda x: x.gas.round(0), intents=lambda x: x.intents.round(0)).to_string())
out["monthly"] = {k.strftime("%Y-%m"): {"gas": round(float(r.gas)), "intents": None if pd.isna(r.intents) else round(float(r.intents))} for k, r in m.iterrows()}

# ---- 2. POST-HOC: volatility link and concentration in the Intents period ----
ip = nd.loc[INTENTS:"2026-11-03"].dropna(subset=["price", "intents"])
ret = np.log(ip.price).diff().abs()
c = pd.concat([ret, ip.intents], axis=1, keys=["absret", "intents"]).dropna()
top = c.intents.nlargest(int(len(c) * 0.1)).sum() / c.intents.sum()
print("\n== POST-HOC: Intents revenue behaviour, 2025-09-23 to 2026-11-03 ==")
print(f"corr(|daily return|, Intents revenue) = {c.absret.corr(c.intents):.2f} (n={len(c)}) | corr(Spearman) = {c.absret.corr(c.intents, method='spearman'):.2f}")
print(f"top 10% of days = {top*100:.0f}% of Intents revenue | median day ${c.intents.median():,.0f} vs mean ${c.intents.mean():,.0f}")
out["posthoc"] = {"corr_absret_intents": round(float(c.absret.corr(c.intents)), 2), "top10_share": round(float(top), 2)}

# ---- 3. run-rates as of 2026-11-01 ----
last = pd.Timestamp("2026-11-01")
px = float(nd.price.loc[last])
mc = float(nd.mcap.loc[last])
rr = {}
for days in (30, 91, 180):
    w = nd.loc[last - pd.Timedelta(days=days - 1):last]
    rr[days] = {"total": w.rev_c.mean() * 365, "intents": w.intents.mean() * 365, "gas": w.fees.mean() * 365}
print(f"\n== Run-rates annualised to {last.date()} (price ${px:.2f}, circulating market cap ${mc/1e9:.2f}B) ==")
for d_, v in rr.items():
    print(f"trailing {d_:>3}d: total ${v['total']/1e6:5.1f}M | Intents ${v['intents']/1e6:5.1f}M | gas ${v['gas']/1e6:4.2f}M | P/S on total {mc/v['total']:.0f}x")
out["runrate_91d"] = {k: round(float(v) / 1e6, 2) for k, v in rr[91].items()}

# ---- 4. dilution ----
d0, d1 = pd.Timestamp("2026-01-04"), pd.Timestamp("2026-11-01")
iss_near = (sup.loc[d1] - sup.loc[d0]) / (d1 - d0).days * 365
print(f"\n== Net new supply (total supply growth, {d0.date()} to {d1.date()}) ==")
print(f"{iss_near/1e6:.1f}M NEAR/yr = {iss_near/sup.loc[d1]*100:.2f}% of supply; worth ${iss_near*px/1e6:.0f}M/yr at ${px:.2f}")
bshare = float(np.median(bb / nd.intents.loc[bb.index].replace(0, np.nan)))
print(f"buybacks / Intents revenue (median day): {bshare:.2f}; last-30d buyback run-rate ${bb.iloc[-30:].sum()/30*365/1e6:.1f}M/yr")
out["issuance"] = {"near_per_year_M": round(iss_near / 1e6, 1), "pct": round(iss_near / sup.loc[d1] * 100, 2), "usd_M_at_spot": round(iss_near * px / 1e6)}
out["buyback_share"] = round(bshare, 2)

# ---- 5. coverage grid (SENSITIVITY, not a forecast) ----
base = rr[91]["total"]
print("\n== Sensitivity: revenue multiple vs price. Holds net new supply fixed at the 2026 rate ==")
print("coverage = revenue / dollar value of net new supply; buyback coverage assumes the median buyback share")
prices = [2.0, px, 6.0, 8.0]
rows = []
for mult in (1, 2, 4, 8, 12):
    rev = base * mult
    row = {"mult": mult, "rev_M": rev / 1e6, "ps_at_current_mcap": mc / rev}
    for p in prices:
        row[f"cover@{p:.2f}"] = rev / (iss_near * p)
        row[f"bb_cover@{p:.2f}"] = bshare * rev / (iss_near * p)
    rows.append(row)
G = pd.DataFrame(rows).set_index("mult")
show = G[["rev_M", "ps_at_current_mcap"] + [f"cover@{p:.2f}" for p in prices]].copy()
for p in prices:
    show[f"cover@{p:.2f}"] = (show[f"cover@{p:.2f}"] * 100).round(0).astype(int).astype(str) + "%"
show["rev_M"] = show.rev_M.round(0)
show["ps_at_current_mcap"] = show.ps_at_current_mcap.round(0)
print(show.to_string())
be = iss_near * px / (bshare * base)
be_rev = iss_near * px / bshare
print(f"\nBreak-even: buybacks fully offset net new supply at ${px:.2f} when revenue is {be:.1f}x the trailing-91-day run-rate (${be_rev/1e6:.0f}M/yr).")
print(f"At current market cap that revenue would be a P/S of {mc/be_rev:.0f}x.")
print(f"Net dilution after buybacks today: {(iss_near*px - bshare*base)/mc*100:.2f}% of market cap per year (gross {iss_near*px/mc*100:.2f}%).")
out["breakeven_multiple"] = round(be, 1)
out["breakeven_rev_M"] = round(be_rev / 1e6)
out["grid"] = {int(k): {kk: round(float(vv), 3) for kk, vv in r.items()} for k, r in G.iterrows()}

# ---- 6. data for the dashboard ----
wk = nd.intents.resample("W-SUN").sum(min_count=6)
out["intents_28d_last"] = round(float(nd.intents.loc[:"2026-11-04"].iloc[-28:].mean()))
print(f"\nlatest 28-day average Intents revenue: ${out['intents_28d_last']:,.0f}/day")
pre = nd.intents.loc["2026-08-07":"2026-09-02"].mean()
ral = nd.intents.loc["2026-09-17":"2026-10-15"].mean()
pul = nd.intents.loc["2026-10-16":"2026-11-04"].mean()
print(f"Intents revenue/day: Aug7-Sep2 ${pre:,.0f} | Sep17-Oct15 ${ral:,.0f} | Oct16-Nov4 ${pul:,.0f}")
out["phase_intents"] = {"pre": round(float(pre)), "rally": round(float(ral)), "pullback": round(float(pul))}
# ---- 7. POST-HOC: does Intents revenue line up with on-chain usage? ----
print("\n== POST-HOC: Intents revenue vs on-chain usage ==")
ph = {"pre (Aug 7-Sep 2)": ("2026-08-07", "2026-09-02"), "rally (Sep 17-Oct 15)": ("2026-09-17", "2026-10-15"), "pullback (Oct 16-Nov 3)": ("2026-10-16", "2026-11-03")}
rowsu = {}
for lab, (a, b) in ph.items():
    w = nd.loc[a:b]
    rowsu[lab] = {"intents_usd": w.intents.mean(), "gas_usd": w.fees.mean(), "gas_near": (w.fees / w.price).mean(), "transactions": w.tx.mean(), "active_addresses": w.active.mean(), "price": w.price.mean()}
U = pd.DataFrame(rowsu)
print(U.round(0).to_string())
idx = (U.div(U.iloc[:, 0], axis=0) * 100).round(0)
print("\nIndexed to pre = 100:\n" + idx.to_string())
out["phase_index"] = {k: [float(x) for x in v] for k, v in idx.iterrows()}
out["phase_index_labels"] = list(idx.columns)
wk2 = pd.DataFrame({"intents": nd.intents, "gas": nd.fees, "tx": nd.tx, "active": nd.active}).loc["2026-04-03":"2026-11-01"].resample("W-SUN").agg({"intents": "sum", "gas": "sum", "tx": "sum", "active": "mean"})
sp = wk2.corr(method="spearman")
print(f"\nWeekly Spearman correlations after the 2026-04-02 break (n={len(wk2)} weeks):")
print(sp.round(2).to_string())
out["spearman_intents_active"] = round(float(sp.loc["intents", "active"]), 2)
out["spearman_intents_gas"] = round(float(sp.loc["intents", "gas"]), 2)
out["spearman_intents_tx"] = round(float(sp.loc["intents", "tx"]), 2)

json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenario_numbers.json"), "w"), indent=1)
