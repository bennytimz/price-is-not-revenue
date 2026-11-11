"""Pre-registered confirmatory tests for the NEAR investment thesis.

Run:  pip install pandas numpy statsmodels scipy ; python analysis_confirmatory.py
Reads only the CSV files in this folder (Blockworks pulls, row counts and sums verified against the source totals).
Specification: PREREGISTRATION.md (Amendments 1-6). Confirmatory sample 2024-01-01 to 2026-08-06;
fit period 2024-01-01 to 2025-06-30; holdout 2025-07-01 to 2026-08-06.
Where a rolling window would inflate significance, non-overlapping 28-day blocks are used.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

D = os.path.dirname(os.path.abspath(__file__))
nd = pd.read_csv(f"{D}/near_daily.csv", parse_dates=["date"]).set_index("date")
pw = pd.read_csv(f"{D}/peers_weekly.csv", parse_dates=["week"])
sup = pd.read_csv(f"{D}/near_total_supply_weekly.csv", parse_dates=["week_ending"]).set_index("week_ending").total_supply
bb = pd.read_csv(f"{D}/near_buybacks_daily.csv", parse_dates=["date"]).set_index("date").buybacks_usd

CS, CE = pd.Timestamp("2024-01-01"), pd.Timestamp("2026-08-06")
BREAK = pd.Timestamp("2026-04-02")
INTENTS = pd.Timestamp("2025-09-23")
BONF = 0.0125


def hac(y, X, lags):
    return sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})


# ---------- cleaning rules (Amendments 1-2) ----------
nd["rev_c"] = nd.rev.where(~((nd.index >= INTENTS) & ((nd.rev - nd.fees).abs() < 1)))  # rule: rev==fees after 2025-09-23 is missing data
s = nd.mcap / nd.price
med7 = s.rolling(7, center=True, min_periods=4).median()
dev = (s / med7 - 1).abs()
spike = (dev > 0.03) & (dev.shift(1) <= 0.03) & (dev.shift(-1) <= 0.03)
nd["mcap_c"] = nd.mcap.where(~spike)
flag = pd.Series(False, index=nd.index)
for seg in (nd.active.loc[: BREAK - pd.Timedelta(days=1)], nd.active.loc[BREAK:]):
    m = seg.rolling(14, center=True, min_periods=7).median()
    flag.loc[seg.index] = seg < 0.5 * m
nd["flag"] = flag
conf = nd.loc[CS:CE].copy()
print(f"Confirmatory days {len(conf)} | incomplete-day flags {int(conf.flag.sum())} | mcap spikes removed {int(spike.loc[CS:CE].sum())} | rev==fees days set missing {int(nd.rev_c.loc[CS:CE].isna().sum())}")


def elasticity(y, p, lags=5, extra=None):
    X = pd.DataFrame({"lp": np.log(p)})
    if extra is not None:
        X["brk"] = extra
    m = hac(np.log(y), X, lags)
    lo, hi = m.conf_int().loc["lp"]
    return m.params["lp"], lo, hi, int(m.nobs)


print("\n==== H1  price pass-through ====")
brk = (conf.index >= BREAK).astype(float)
for lab, mask in (("all days", np.ones(len(conf), bool)), ("excl flagged", ~conf.flag.values)):
    c = conf[mask]
    b, lo, hi, n = elasticity(c.fees, c.price)
    b2, lo2, hi2, _ = elasticity(c.fees, c.price, extra=brk[mask])
    print(f"A gas fees  [{lab}] elasticity {b:.2f} CI[{lo:.2f},{hi:.2f}] n={n} | with break term {b2:.2f} CI[{lo2:.2f},{hi2:.2f}]")
c = conf[~conf.flag]
fn = (conf.fees / conf.price).where(~conf.flag)
nb = len(conf) // 28
blk = pd.DataFrame({"b": np.arange(nb).repeat(28), "fn": fn.values[: nb * 28], "mid": conf.index[: nb * 28]})
g = blk.groupby("b").agg(fn=("fn", "mean"), mid=("mid", "median"))
tr = hac(np.log(g.fn), pd.Series(np.arange(nb), index=g.index, name="t"), 2)
tr2 = hac(np.log(g.fn), pd.DataFrame({"t": np.arange(nb), "brk": (g.mid >= BREAK).astype(float).values}, index=g.index), 2)
print(f"A token-denominated gas fees, {nb} blocks of 28d: trend/block {tr.params['t']*100:+.1f}% p={tr.pvalues['t']:.3f} | with break term {tr2.params['t']*100:+.1f}% p={tr2.pvalues['t']:.3f}")
v1 = (conf.rev_c.dropna())
b, lo, hi, n = elasticity(conf.rev_c.dropna(), conf.price[conf.rev_c.notna()])
print(f"B total protocol revenue elasticity {b:.2f} CI[{lo:.2f},{hi:.2f}] n={n}")
nf = (conf.rev_c - conf.fees)
cc = conf[(conf.index >= INTENTS) & (nf > 0)]
b, lo, hi, n = elasticity(nf[cc.index], cc.price)
print(f"C non-fee (Intents) revenue since {INTENTS.date()} elasticity {b:.2f} CI[{lo:.2f},{hi:.2f}] n={n}")
ex = nd.loc["2026-08-07":"2026-11-04"].dropna(subset=["price"])
b, lo, hi, n = elasticity(ex.rev, ex.price)
print(f"   exploratory window (not confirmatory) total revenue elasticity {b:.2f} CI[{lo:.2f},{hi:.2f}] n={n}")

print("\n==== H2  activity leads price (4-week horizon) ====")
FIT_END, HO_S, HO_E = pd.Timestamp("2025-06-01"), pd.Timestamp("2025-07-06"), pd.Timestamp("2026-07-05")


def xy_from(tokens_w, price_w):
    s4 = tokens_w.rolling(4).sum()
    x = np.log(s4) - np.log(s4.shift(4))
    y = np.log(price_w.shift(-4) / price_w)
    return pd.DataFrame({"x": x, "y": y}).dropna()


def run_h2(df, label):
    fit, ho = df.loc[:FIT_END], df.loc[HO_S:HO_E]
    m = hac(fit.y, fit.x, 4)
    pred = m.params["const"] + m.params["x"] * ho.x
    oos = 1 - ((ho.y - pred) ** 2).sum() / (ho.y ** 2).sum()
    mh = hac(ho.y, ho.x, 4)
    ok = (m.pvalues["x"] < 0.05) and (oos > 0) and (np.sign(mh.params["x"]) == np.sign(m.params["x"]))
    print(f"{label:6s} fit beta {m.params['x']:+.3f} p={m.pvalues['x']:.3f} (n={len(fit)}) | holdout OOS R2 {oos*100:+.1f}% | holdout beta {mh.params['x']:+.3f} p={mh.pvalues['x']:.3f} (n={len(ho)}) | meets all conditions: {ok}")
    return ok


fnw = (nd.fees / nd.price).resample("W-SUN").sum(min_count=7)
pnw = nd.price.resample("W-SUN").last()
last = pd.Timestamp("2026-11-01")
dfs = {"NEAR": xy_from(fnw.loc[:last], pnw.loc[:last])}
panel = [dfs["NEAR"].assign(asset="NEAR")]
nw_close = nd.price.reindex(pd.date_range("2024-01-07", last, freq="W-SUN"))
nfees_w = nd.fees.resample("W-SUN").sum(min_count=7).loc[:last]
approx = xy_from(nfees_w / nw_close, nw_close)
for a, g2 in pw.groupby("asset"):
    g2 = g2.set_index("week")
    dfs[a] = xy_from(g2.fees / g2.price, g2.price)
    panel.append(dfs[a].assign(asset=a))
panel.append(approx.assign(asset="NEARa"))
res = {k: run_h2(v, k) for k, v in dfs.items()}
pan = pd.concat([p for p in panel if p.asset.iloc[0] != "NEARa"]).sort_index(kind="stable")
pf = pan[pan.index <= FIT_END].copy()
for c_ in ("x", "y"):
    pf[c_] = pf[c_] - pf.groupby("asset")[c_].transform("mean")
codes = pd.factorize(pf.index)[0]
mp = sm.OLS(pf.y, sm.add_constant(pf.x)).fit(cov_type="cluster", cov_kwds={"groups": codes})
ph = pan[(pan.index >= HO_S) & (pan.index <= HO_E)].copy()
fm = pan[pan.index <= FIT_END].groupby("asset")[["x", "y"]].mean()
pred = ph.apply(lambda r: fm.loc[r.asset, "y"] + mp.params["x"] * (r.x - fm.loc[r.asset, "x"]), axis=1)
oosp = 1 - ((ph.y - pred) ** 2).sum() / (ph.y ** 2).sum()
print(f"POOLED fixed-effects (6 assets) fit beta {mp.params['x']:+.3f} p={mp.pvalues['x']:.3f} | holdout OOS R2 {oosp*100:+.1f}%")
nfw = (nd.rev_c - nd.fees).resample("W-SUN").sum(min_count=7).loc[:last]
s4n = nfw.rolling(4).sum()
x2 = np.log(s4n.where(s4n > 0)) - np.log(s4n.shift(4).where(s4n.shift(4) > 0))
d2 = pd.DataFrame({"x": x2, "y": dfs["NEAR"].y}).dropna().loc[HO_S:HO_E]
m2 = hac(d2.y, d2.x, 4)
print(f"secondary: 4-wk growth in retained Intents revenue (USD) vs next-4wk return, holdout only: beta {m2.params['x']:+.3f} p={m2.pvalues['x']:.3f} n={len(d2)} (underpowered; not used for the verdict)")

print("\n==== H3  relative valuation (P/S = circulating mkt cap / trailing 91-day revenue, annualised), as of 2026-11-01 ====")
k = 365 / 91
nm = nd.mcap_c.ffill().loc[last]
t91 = nd.loc["2026-08-03":"2026-11-01"]
near = {"fees": nm / (t91.fees.sum() * k), "total": nm / (t91.rev_c.sum() * k)}
rows = []
for a, g2 in pw.groupby("asset"):
    g2 = g2.set_index("week").sort_index()
    t13 = g2.loc[:last].iloc[-13:]
    mc = g2.mcap.loc[last]
    rows.append((a, mc / (t13.rev.sum() * k), mc / (t13.fees.sum() * k)))
pdf = pd.DataFrame(rows, columns=["asset", "ps_rev", "ps_fees"]).set_index("asset")
print(pdf.round(0).to_string())
print(f"peer median: protocol revenue {pdf.ps_rev.median():.0f}x | fees only {pdf.ps_fees.median():.0f}x")
print(f"NEAR: on gas fees {near['fees']:.0f}x | on total protocol revenue {near['total']:.0f}x")
wk = pd.date_range("2024-01-07", last, freq="W-SUN")
fees_w = nd.fees.resample("W-SUN").sum(min_count=7).reindex(wk)
rev_w = nd.rev_c.resample("W-SUN").sum(min_count=6).reindex(wk)
mc_w = nd.mcap_c.ffill().reindex(wk)
px_w = nd.price.reindex(wk)
sup_end = nd.mcap_c.ffill().loc[last] / nd.price.loc[last]
hist = {}
for lab, ser in (("fees", fees_w), ("total", rev_w)):
    ps = mc_w / (ser.rolling(13).sum() * k)
    psf = (px_w * sup_end) / (ser.rolling(13).sum() * k)
    h = ps.dropna().iloc[:-1]
    hf = psf.dropna().iloc[:-1]
    hist[lab] = (ps.dropna().iloc[-1], (h < ps.dropna().iloc[-1]).mean(), h.quantile(0.75), (hf < psf.dropna().iloc[-1]).mean())
    print(f"NEAR own history ({lab}): now {hist[lab][0]:.0f}x | percentile {hist[lab][1]*100:.0f}% (fixed-supply {hist[lab][3]*100:.0f}%) | 75th pct {hist[lab][2]:.0f}x")
for lab, num, peer in (("(a) NEAR fees vs peers' revenue", near["fees"], pdf.ps_rev), ("(b) fees vs fees", near["fees"], pdf.ps_fees), ("(c) NEAR total vs peers' revenue [not like-for-like]", near["total"], pdf.ps_rev)):
    hh = hist["fees"] if "total" not in lab and "(c)" not in lab else hist["total"]
    verdict = "SUPPORTED" if (num > peer.median() and hh[0] > hh[2]) else ("REJECTED" if num < peer.median() else "not supported")
    print(f"  {lab}: NEAR {num:.0f}x vs peer median {peer.median():.0f}x; above own 75th pct: {hh[0] > hh[2]} -> {verdict}")

print("\n==== H4  usage not monetised (28-day blocks) ====")
cf = conf.copy()
nb = len(cf) // 28
rows = []
for b in range(nb):
    w = cf.iloc[b * 28:(b + 1) * 28]
    for lab, ex_flag in (("all", False), ("excl", True)):
        ww = w[~w.flag] if ex_flag else w
        ok = ww.active.notna() & ww.rev_c.notna()
        rows.append(dict(b=b, mode=lab, start=w.index[0], end=w.index[-1], act=ww.active.mean(), rpa=(ww.rev_c[ok] / ww.active[ok]).mean(), fpa=(ww.fees / ww.active).mean()))
B = pd.DataFrame(rows)
for mode in ("excl", "all"):
    Bm = B[B["mode"] == mode].copy()
    pre = Bm[Bm.end < BREAK]
    post = Bm[Bm.start > BREAK]
    full = Bm[(Bm.end < BREAK) | (Bm.start > BREAK)].copy()
    full["brk"] = (full.start > BREAK).astype(float)
    for lab, sub in (("pre-break", pre), ("post-break", post)):
        if len(sub) >= 3:
            a_ = hac(np.log(sub.act), sub.b.rename("t"), 2)
            r_ = hac(np.log(sub.rpa), sub.b.rename("t"), 2)
            print(f"[{mode}] {lab:10s} n={len(sub)} blocks | active addresses {a_.params['t']*100:+.1f}%/block p={a_.pvalues['t']:.3f} | revenue per active address {r_.params['t']*100:+.1f}%/block p={r_.pvalues['t']:.3f}")
    X = pd.DataFrame({"t": full.b, "brk": full.brk})
    a_ = hac(np.log(full.act), X, 2)
    r_ = hac(np.log(full.rpa), X, 2)
    print(f"[{mode}] full + break term n={len(full)} | active {a_.params['t']*100:+.1f}%/block p={a_.pvalues['t']:.3f} (break {a_.params['brk']:+.2f} log) | rev/active {r_.params['t']*100:+.1f}%/block p={r_.pvalues['t']:.3f}")

print("\n==== H5 (descriptive) revenue vs new supply and buybacks ====")
ns = sup.loc["2024-10-13":]
iss_near = (ns.shift(0) - ns.shift(13)) / ns.shift(13) * 4  # 13-week growth annualised (fraction of supply)
for m_end in pd.to_datetime(["2025-06-29", "2025-12-28", "2026-03-29", "2026-06-28", "2026-10-25"]):
    p = nd.price.loc[m_end]
    iss = iss_near.loc[m_end] * ns.loc[m_end] * p
    r90 = nd.rev_c.loc[m_end - pd.Timedelta(days=90):m_end].mean() * 365
    print(f"{m_end.date()}: trailing-90d annualised revenue ${r90/1e6:.1f}M vs annualised net issuance ${iss/1e6:.0f}M -> {r90/iss*100:.0f}%")
nfee = (nd.rev - nd.fees).loc[bb.index]
print(f"buybacks / retained revenue: median {np.median(bb / nfee):.2f}; last 30d buyback run-rate ${bb.iloc[-30:].sum()/30*365/1e6:.1f}M/yr")


import json
json.dump({"near_ps_gas": float(near["fees"]), "near_ps_total": float(near["total"]),
           "peers_ps_rev": {k: float(v) for k, v in pdf.ps_rev.items()},
           "peers_ps_fees": {k: float(v) for k, v in pdf.ps_fees.items()}},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "confirmatory_numbers.json"), "w"), indent=1)
