"""Extension tests E1-E5, pre-registered in PREREGISTRATION.md Amendment 8 (pushed 2026-11-11T19:30:13+01:00)
and Amendment 8a (pushed 2026-11-11T20:28:58+01:00). Thresholds are copied from Amendment 8 unchanged.

Inputs (read only): raw_defillama_intents*.json (S1, pulled locally by pull_defillama_intents.py and not committed,
per DefiLlama's terms; Amendment 8b), raw_bigquery_daily_usage.csv (S2, hash in RAW_PULLS.sha256), near_daily.csv (Blockworks),
raw_bigquery_intents_contract.csv (S4, hash in RAW_PULLS.sha256; tests F1 and F2, pre-registered in Amendment 9).
Outputs: stdout (saved by run_all.py as extension_results.txt) and extension_numbers.json.
Results labelled "Exploratory" are post-hoc, are not in Amendment 8, and do not affect any E1-E5 verdict.
"""
import datetime as dt
import hashlib
import json
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

D = os.path.dirname(os.path.abspath(__file__))
SEED, NBOOT = 20261111, 10_000
INTENTS = pd.Timestamp("2025-09-23")     # retained Intents revenue exists from here (same rule as scenarios.py)
BREAK = pd.Timestamp("2026-04-02")       # same as analysis_confirmatory.py
BW_END = pd.Timestamp("2026-11-04")      # last Blockworks day; Amendment 8a: S1 2026-11-10 not used
S2_EXCLUDE = pd.Timestamp("2026-11-11")  # Amendment 8a: partial day of the pull

# ---------- integrity: raw files must match RAW_PULLS.sha256 ----------
for line in open(os.path.join(D, "RAW_PULLS.sha256"), encoding="utf-8"):
    h, name = line.strip().split("  ", 1)
    assert hashlib.sha256(open(os.path.join(D, name), "rb").read()).hexdigest() == h, f"hash mismatch: {name}"


def s1(name):
    j = json.load(open(os.path.join(D, name), encoding="utf-8"))
    return pd.Series({pd.Timestamp(dt.datetime.fromtimestamp(t, dt.timezone.utc).date()): float(v) for t, v in j["totalDataChart"]}).sort_index()


S1_START = "2024-12-10"  # first day of the original S1 pull; pinned so a re-pull with more history gives the same inputs (Amendment 8b)
vol = s1("raw_defillama_intents.json").loc[S1_START:BW_END]
dl_rev = s1("raw_defillama_intents_revenue.json").loc[:BW_END]  # only used where Blockworks Intents revenue exists (from 2025-09-23)
s2 = pd.read_csv(os.path.join(D, "raw_bigquery_daily_usage.csv"), parse_dates=["block_date"]).set_index("block_date")
s2 = s2[s2.index != S2_EXCLUDE]
signers = s2.active_signers.astype(float)

nd = pd.read_csv(os.path.join(D, "near_daily.csv"), parse_dates=["date"]).set_index("date")
nd["rev_c"] = nd.rev.where(~((nd.index >= INTENTS) & ((nd.rev - nd.fees).abs() < 1)))  # identical to scenarios.py
nd["intents"] = (nd.rev_c - nd.fees).clip(lower=0)
nd.loc[nd.index < INTENTS, "intents"] = np.nan  # before 2025-09-23 retained Intents revenue does not exist (not zero)

out = {"inputs": {"s1_volume_days": [str(vol.index.min().date()), str(vol.index.max().date())],
                  "s2_days": [str(signers.index.min().date()), str(signers.index.max().date())],
                  "blockworks_days": [str(nd.index.min().date()), str(nd.index.max().date())]}}
P = print
P("EXTENSION TESTS E1-E5 (pre-registered: PREREGISTRATION.md Amendment 8 and 8a)")
P(f"S1 DefiLlama volume used {out['inputs']['s1_volume_days'][0]} to {out['inputs']['s1_volume_days'][1]} | "
  f"S2 BigQuery used {out['inputs']['s2_days'][0]} to {out['inputs']['s2_days'][1]} (2026-11-11 excluded, Amendment 8a) | "
  f"Blockworks {out['inputs']['blockworks_days'][0]} to {out['inputs']['blockworks_days'][1]}")

# ---------- E1 ----------
e1 = pd.concat([vol, nd.intents], axis=1, keys=["vol", "rev"]).dropna()
P("\nE1 (pre-registered) revenue as a proxy for Intents activity")
P("   rule: Spearman(daily S1 volume, daily retained Intents revenue) >= 0.50 on >= 120 overlapping days -> usable proxy")
if len(e1) < 120:
    r1, v1 = None, f"cannot test (only {len(e1)} overlapping days)"
else:
    r1 = float(spearmanr(e1.vol, e1.rev)[0])
    v1 = "usable proxy" if r1 >= 0.5 else "not a usable proxy"
P(f"   days {len(e1)} ({e1.index.min().date()} to {e1.index.max().date()}) | Spearman {r1:.3f}" if r1 is not None else f"   days {len(e1)}")
P(f"   VERDICT E1: {v1}")
out["E1"] = {"n_days": len(e1), "spearman": r1, "threshold": 0.5, "verdict": v1}

# ---------- E2 ----------
A, B = ("2026-08-07", "2026-09-02"), ("2026-09-17", "2026-10-15")
P("\nE2 (pre-registered) volume or take rate")
P("   rule: share = ln(volume ratio) / ln(revenue ratio), window B (2026-09-17..10-15) over A (2026-08-07..09-02), mean daily values;")
P("         >= 0.70 volume-driven | <= 0.30 take-rate-driven | otherwise mixed")
cov = all(len(vol.loc[a:b]) == (pd.Timestamp(b) - pd.Timestamp(a)).days + 1 for a, b in (A, B))
if not cov:
    v2, e2 = "cannot test (S1 does not cover both windows)", {}
else:
    vA, vB = vol.loc[A[0]:A[1]].mean(), vol.loc[B[0]:B[1]].mean()
    rA, rB = nd.intents.loc[A[0]:A[1]].mean(), nd.intents.loc[B[0]:B[1]].mean()
    nanA, nanB = int(nd.intents.loc[A[0]:A[1]].isna().sum()), int(nd.intents.loc[B[0]:B[1]].isna().sum())
    vr, rr = vB / vA, rB / rA
    share = float(np.log(vr) / np.log(rr)) if rr > 0 and vr > 0 and abs(np.log(rr)) > 1e-12 else None
    v2 = ("cannot test (revenue ratio is 1 or non-positive)" if share is None else
          "volume-driven" if share >= 0.7 else "take-rate-driven" if share <= 0.3 else "mixed")
    P(f"   window A: volume ${vA:,.0f}/day, revenue ${rA:,.0f}/day, take rate {rA / vA * 1e4:.2f} bp (revenue days missing: {nanA})")
    P(f"   window B: volume ${vB:,.0f}/day, revenue ${rB:,.0f}/day, take rate {rB / vB * 1e4:.2f} bp (revenue days missing: {nanB})")
    P(f"   volume ratio {vr:.3f} | revenue ratio {rr:.3f} | volume share {share:.3f}" if share is not None else f"   volume ratio {vr:.3f} | revenue ratio {rr:.3f}")
    e2 = {"vol_A": vA, "vol_B": vB, "rev_A": rA, "rev_B": rB, "take_rate_bp_A": rA / vA * 1e4, "take_rate_bp_B": rB / vB * 1e4,
          "volume_ratio": vr, "revenue_ratio": rr, "volume_share": share, "rev_missing_days_A": nanA, "rev_missing_days_B": nanB}
P(f"   VERDICT E2: {v2}")
out["E2"] = {**e2, "thresholds": [0.3, 0.7], "verdict": v2}

# ---------- E3 ----------
P("\nE3 (pre-registered, exploratory per Amendment 8) does Intents volume lead on-chain usage better than price?")
P("   rule: rho(4-wk log change in volume, next 4-wk log change in usage) - rho(4-wk NEAR price return, same) >= 0.15")
P("         and 7-day block-bootstrap 95% interval of the difference excludes zero -> leads better than price; otherwise not supported")
wk_end_first, wk_end_last = pd.Timestamp("2024-12-22"), pd.Timestamp("2026-11-01")  # complete Mon-Sun weeks covered by all inputs
def weekly(s, how):
    g = s.loc[wk_end_first - pd.Timedelta(days=6):wk_end_last].resample("W-SUN")
    w = getattr(g, how)()
    return w[g.count() == 7]
use_s2 = signers.index.min() <= wk_end_first - pd.Timedelta(days=6) and signers.index.max() >= wk_end_last
usage = weekly(signers, "mean") if use_s2 else weekly(nd.tx.astype(float), "mean")
V, U = weekly(vol, "sum"), usage
Pw = nd.price.loc[:wk_end_last].resample("W-SUN").last().loc[wk_end_first:wk_end_last]
w = pd.concat([V, U, Pw], axis=1, keys=["V", "U", "P"]).dropna()
f = pd.DataFrame({"dv": np.log(w.V / w.V.shift(4)), "dp": np.log(w.P / w.P.shift(4)), "fu": np.log(w.U.shift(-4) / w.U)}).dropna()
rv, rp = float(spearmanr(f.dv, f.fu)[0]), float(spearmanr(f.dp, f.fu)[0])
diff = rv - rp
rng = np.random.default_rng(SEED)
x = f[["dv", "dp", "fu"]].to_numpy()
bd = np.empty(NBOOT)
for i in range(NBOOT):  # block length 7 days = 1 weekly observation
    s = x[rng.integers(0, len(x), len(x))]
    bd[i] = spearmanr(s[:, 0], s[:, 2])[0] - spearmanr(s[:, 1], s[:, 2])[0]
lo, hi = (float(q) for q in np.nanpercentile(bd, [2.5, 97.5]))
v3 = "leads better than price" if diff >= 0.15 and (lo > 0 or hi < 0) else "not supported"
P(f"   usage series: {'S2 distinct signers (weekly mean)' if use_s2 else 'Blockworks transactions'} | weeks ending {f.index.min().date()} to {f.index.max().date()} | n={len(f)} (overlapping windows)")
P(f"   rho volume {rv:+.3f} | rho price {rp:+.3f} | difference {diff:+.3f} | bootstrap 95% interval [{lo:+.3f}, {hi:+.3f}] ({NBOOT} draws, seed {SEED})")
P("   significance is not claimed (overlapping windows)")
P(f"   VERDICT E3: {v3}")
out["E3"] = {"usage": "S2 active_signers" if use_s2 else "Blockworks tx", "n_weeks": len(f), "rho_volume": rv, "rho_price": rp,
             "difference": diff, "boot_ci95": [lo, hi], "threshold_diff": 0.15, "verdict": v3}

# ---------- E4 ----------
P("\nE4 (pre-registered) is the 2026-04-02 break real on-chain?")
P("   rule: median daily S2 distinct signers, 28 days after vs 28 days before 2026-04-02: drop >= 50% real on-chain;")
P("         drop < 20% probably a Blockworks definition change; otherwise inconclusive; cannot test if S2 lacks 2026-03-01..05-31")
if signers.loc["2026-03-01":"2026-05-31"].size != 92:
    v4, e4 = "cannot test", {}
else:
    pre = signers.loc[BREAK - pd.Timedelta(days=28):BREAK - pd.Timedelta(days=1)]
    post = signers.loc[BREAK:BREAK + pd.Timedelta(days=27)]
    mb, ma = float(pre.median()), float(post.median())
    drop = 1 - ma / mb
    v4 = "real on-chain" if drop >= 0.5 else "probably a Blockworks definition change" if drop < 0.2 else "inconclusive"
    P(f"   before {pre.index.min().date()}..{pre.index.max().date()} median {mb:,.0f} | after {post.index.min().date()}..{post.index.max().date()} median {ma:,.0f} | drop {drop:.1%}")
    e4 = {"median_before": mb, "median_after": ma, "drop": drop}
P(f"   VERDICT E4: {v4}")
out["E4"] = {**e4, "thresholds": [0.2, 0.5], "verdict": v4}

# ---------- E5 ----------
P("\nE5 (pre-registered) definition check")
P("   rule: Spearman(daily change in S2 distinct signers, daily change in Blockworks active addresses) >= 0.60 -> consistent definitions")
e5 = pd.concat([signers, nd.active.astype(float)], axis=1, keys=["s2", "bw"]).dropna()
e5 = e5.asfreq("D")
dd = e5.diff().dropna()
r5 = float(spearmanr(dd.s2, dd.bw)[0])
v5 = "consistent definitions" if r5 >= 0.6 else "inconsistent"
P(f"   days {len(dd)} of daily changes ({dd.index.min().date()} to {dd.index.max().date()}) | Spearman {r5:.3f}")
P(f"   VERDICT E5: {v5}")
out["E5"] = {"n_days": len(dd), "spearman": r5, "threshold": 0.6, "verdict": v5}

# ---------- F1 / F2 (pre-registered, Amendment 9) ----------
S4_PULL_DAY = pd.Timestamp("2026-11-11")  # UTC day of the S4 pull (file saved 2026-11-11 23:34 UTC); excluded per Amendment 9
s4 = pd.read_csv(os.path.join(D, "raw_bigquery_intents_contract.csv"), parse_dates=["block_date"]).set_index("block_date")
s4 = s4[s4.index != S4_PULL_DAY]
calls = s4.intents_calls.astype(float)
P("\nF1 (pre-registered, Amendment 9) do daily intents.near calls (S4) track DefiLlama Intents volume (S1)?")
P(f"   S4 BigQuery used {calls.index.min().date()} to {calls.index.max().date()} (pull day {S4_PULL_DAY.date()} UTC excluded)")
P("   caveat declared in advance: calls to the settlement contract are a proxy for swap activity, not swaps; one call may settle several intents")
P("   rule: Spearman(daily S4 call count, daily S1 DefiLlama volume) over >= 120 overlapping days; >= 0.50 -> S4 tracks volume, otherwise S4 does not track volume")
f1 = pd.concat([calls, s1("raw_defillama_intents.json")], axis=1, keys=["calls", "vol"]).dropna()
if len(f1) >= 120:
    rf1 = float(spearmanr(f1.calls, f1.vol)[0])
    vf1 = "S4 tracks volume" if rf1 >= 0.50 else "S4 does not track volume"
    P(f"   days {len(f1)} ({f1.index.min().date()} to {f1.index.max().date()}) | Spearman {rf1:.3f}")
else:
    rf1, vf1 = None, "cannot test (fewer than 120 overlapping days)"
    P(f"   days {len(f1)}")
P(f"   VERDICT F1: {vf1}")
out["F1"] = {"n_days": len(f1), "days": [str(f1.index.min().date()), str(f1.index.max().date())], "spearman": rf1, "threshold": 0.5, "verdict": vf1}

P("\nF2 (pre-registered, Amendment 9) did on-chain Intents calls rise with the Sep-Oct revenue jump?")
P("   rule: mean daily S4 call count, window B (2026-09-17..10-15) over window A (2026-08-07..09-02); >= 2.0 on-chain Intents calls rose broadly")
P("         with revenue | <= 1.3 calls did not rise materially | otherwise in between; labelled proxy not validated if F1 says S4 does not track volume")
cA, cB = calls.loc["2026-08-07":"2026-09-02"], calls.loc["2026-09-17":"2026-10-15"]
assert len(cA) == 27 and len(cB) == 29, "F2: S4 does not cover both windows"
rf2 = cB.mean() / cA.mean()
vf2 = "on-chain Intents calls rose broadly with revenue" if rf2 >= 2.0 else "calls did not rise materially" if rf2 <= 1.3 else "in between"
if vf1 == "S4 does not track volume":
    vf2 += " (proxy not validated)"
P(f"   window A mean {cA.mean():,.0f} calls/day ({len(cA)} days) | window B mean {cB.mean():,.0f} calls/day ({len(cB)} days) | ratio {rf2:.3f}")
P(f"   VERDICT F2: {vf2}")
out["F2"] = {"calls_A": cA.mean(), "calls_B": cB.mean(), "ratio": rf2, "thresholds": [1.3, 2.0], "verdict": vf2}

# ---------- Exploratory (post-hoc, not in Amendment 8; no effect on any verdict) ----------
P("\nExploratory (post-hoc, not pre-registered; does not change any E1-E5 verdict)")
x1 = pd.concat([dl_rev, nd.intents], axis=1, keys=["dl", "bw"]).dropna()
rx1 = float(spearmanr(x1.dl, x1.bw)[0])
ratio = float(x1.dl.sum() / x1.bw.sum())
P(f"   X1 DefiLlama daily revenue vs Blockworks retained Intents revenue: days {len(x1)} ({x1.index.min().date()} to {x1.index.max().date()}) | "
  f"Spearman {rx1:.3f} | DefiLlama total / Blockworks total {ratio:.3f}")
bwa = nd.active.astype(float)
bpre, bpost = bwa.loc[BREAK - pd.Timedelta(days=28):BREAK - pd.Timedelta(days=1)], bwa.loc[BREAK:BREAK + pd.Timedelta(days=27)]
bdrop = 1 - float(bpost.median()) / float(bpre.median())
P(f"   X2 Blockworks active addresses over the E4 windows: median before {bpre.median():,.0f} | after {bpost.median():,.0f} | drop {bdrop:.1%}")

# X3: same three windows as scenarios.py section 7 (dashboard section 3)
PH = {"pre (Aug 7-Sep 2)": ("2026-08-07", "2026-09-02"), "rally (Sep 17-Oct 15)": ("2026-09-17", "2026-10-15"),
      "pullback (Oct 16-Nov 3)": ("2026-10-16", "2026-11-03")}
x3 = pd.DataFrame({lab: {"s2_signers": signers.loc[a:b].mean(), "intents_usd": nd.intents.loc[a:b].mean(), "s1_volume_usd": vol.loc[a:b].mean()}
                   for lab, (a, b) in PH.items()})
x3i = x3.div(x3.iloc[:, 0], axis=0) * 100
P("   X3 (Exploratory, not pre-registered, not a forecast) mean daily values in the dashboard section 3 windows, indexed to pre = 100:")
for k, lab in (("s2_signers", "S2 distinct signers"), ("intents_usd", "Intents revenue (USD)"), ("s1_volume_usd", "S1 Intents volume (USD)")):
    P(f"      {lab:24s} " + " | ".join(f"{c.split(' ')[0]} {x3.loc[k, c]:,.0f} = {x3i.loc[k, c]:.0f}" for c in x3.columns))

# X4: arithmetic only, using the break-even revenue in scenario_numbers.json
S = json.load(open(os.path.join(D, "scenario_numbers.json"), encoding="utf-8"))
target = S["breakeven_rev_M"] * 1e6
trA, trB = out["E2"]["rev_A"] / out["E2"]["vol_A"], out["E2"]["rev_B"] / out["E2"]["vol_B"]
needA, needB = target / 365 / trA, target / 365 / trB
P(f"   X4 (Exploratory, not pre-registered, not a forecast; arithmetic only) daily Intents volume needed for ${S['breakeven_rev_M']}M/yr of retained revenue "
  f"(the scenarios.py break-even):")
P(f"      at window A take rate ({trA * 1e4:.2f} bp): ${needA / 1e9:.2f}B/day = {needA / out['E2']['vol_B']:.1f}x window B volume")
P(f"      at window B take rate ({trB * 1e4:.2f} bp): ${needB / 1e9:.2f}B/day = {needB / out['E2']['vol_B']:.1f}x window B volume")
# X5: gross Intents fees (DefiLlama) vs retained revenue to NEAR (Blockworks), same window as scenarios.py run-rates
RR_END = pd.Timestamp("2026-11-01")
w91 = slice(RR_END - pd.Timedelta(days=90), RR_END)
fees = s1("raw_defillama_intents_fees.json").loc[w91]
assert len(fees) == 91 and fees.notna().all(), "X5: DefiLlama fees do not cover the 91-day window"
gross_ann, retained_ann, dl_rev_ann = fees.mean() * 365, nd.intents.loc[w91].mean() * 365, dl_rev.loc[w91].mean() * 365
P(f"   X5 (Exploratory, not pre-registered, not a forecast) trailing-91-day annualised, {w91.start.date()} to {w91.stop.date()} (the scenarios.py run-rate window):")
P(f"      DefiLlama gross Intents fees ${gross_ann / 1e6:.1f}M/yr | Blockworks retained Intents revenue ${retained_ann / 1e6:.1f}M/yr | "
  f"DefiLlama revenue ${dl_rev_ann / 1e6:.1f}M/yr | retained / gross {retained_ann / gross_ann:.1%}")
out["exploratory_X5"] = {"window": [str(w91.start.date()), str(w91.stop.date())], "gross_fees_annualised_defillama": gross_ann,
                         "retained_revenue_annualised_blockworks": retained_ann, "revenue_annualised_defillama": dl_rev_ann,
                         "retained_over_gross": retained_ann / gross_ann}
# X6: on-chain usage trend from S2 (committed file), 28-day means as of the last complete day
X6_ASOF, X6_PREV = pd.Timestamp("2026-11-10"), pd.Timestamp("2025-11-10")
assert s2.index.max() == X6_ASOF, "X6: S2 must end on 2026-11-10"
P(f"   X6 (Exploratory, not pre-registered, not a forecast) S2 on-chain usage, 28-day means as of {X6_ASOF.date()} (S2 2026-11-11 excluded):")
out["exploratory_X6"] = {"asof": str(X6_ASOF.date()), "year_earlier": str(X6_PREV.date())}
for col, label in (("active_signers", "distinct signers"), ("transactions", "transactions")):
    m28 = s2[col].astype(float).rolling(28).mean().dropna()
    now, prev, pk, pkd = m28[X6_ASOF], m28[X6_PREV], m28.max(), m28.idxmax()
    P(f"      {label}: {now:,.0f} vs {prev:,.0f} a year earlier ({now / prev - 1:+.1%}) | peak {pk:,.0f} on {pkd.date()} ({now / pk - 1:+.1%} from peak)")
    out["exploratory_X6"].update({f"{col}_mean28_asof": now, f"{col}_mean28_year_earlier": prev, f"{col}_change_yoy": now / prev - 1,
                                  f"{col}_peak": pk, f"{col}_peak_date": str(pkd.date()), f"{col}_change_from_peak": now / pk - 1})
# X7: arithmetic only; break-even if 100% of revenue were spent on buybacks (scenario_numbers.json values)
supply_usd_M, rr_total, rr_intents = S["issuance"]["usd_M_at_spot"], S["runrate_91d"]["total"], S["runrate_91d"]["intents"]
P(f"   X7 (Exploratory, not pre-registered, not a forecast; arithmetic only) revenue that offsets net new supply if 100% were spent on buybacks"
  f" (observed share {S['buyback_share']:.2f} gives ${S['breakeven_rev_M']}M/yr, {S['breakeven_multiple']}x):")
P(f"      ${supply_usd_M}M/yr = {supply_usd_M / rr_total:.1f}x the trailing-91-day revenue run-rate (${rr_total}M/yr) "
  f"| {supply_usd_M / rr_intents:.1f}x the retained Intents run-rate (${rr_intents}M/yr)")
out["exploratory_X7"] = {"breakeven_rev_M_at_100pct": supply_usd_M, "multiple_of_runrate_total": supply_usd_M / rr_total,
                         "multiple_of_runrate_intents": supply_usd_M / rr_intents, "observed_buyback_share": S["buyback_share"],
                         "observed_breakeven_rev_M": S["breakeven_rev_M"], "observed_breakeven_multiple": S["breakeven_multiple"]}
out["exploratory"] = {"X1_spearman_defillama_rev_vs_blockworks_intents": rx1, "X1_total_ratio": ratio, "X1_n_days": len(x1),
                      "X2_blockworks_active_drop": bdrop, "X2_median_before": float(bpre.median()), "X2_median_after": float(bpost.median()),
                      "X3_means": {c: x3[c].to_dict() for c in x3.columns}, "X3_index": {c: x3i[c].to_dict() for c in x3i.columns},
                      "X4_target_usd_per_year": target, "X4_volume_needed_per_day_at_A": needA, "X4_volume_needed_per_day_at_B": needB,
                      "X4_multiple_of_B_volume_at_A": needA / out["E2"]["vol_B"], "X4_multiple_of_B_volume_at_B": needB / out["E2"]["vol_B"]}

P("\nSUMMARY " + " | ".join(f"{k}: {out[k]['verdict']}" for k in ["E1", "E2", "E3", "E4", "E5", "F1", "F2"]))


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return round(float(o), 6)
    if isinstance(o, np.integer):
        return int(o)
    return o


with open(os.path.join(D, "extension_numbers.json"), "w", newline="\n", encoding="utf-8") as fh:
    json.dump(clean(out), fh, indent=2)
    fh.write("\n")
