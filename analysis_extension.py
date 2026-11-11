"""Extension tests E1-E5, pre-registered in PREREGISTRATION.md Amendment 8 (pushed 2026-11-11T19:30:13+01:00)
and Amendment 8a (pushed 2026-11-11T20:28:58+01:00). Thresholds are copied from Amendment 8 unchanged.

Inputs (read only): raw_defillama_intents*.json (S1), raw_bigquery_daily_usage.csv (S2), near_daily.csv (Blockworks).
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


vol = s1("raw_defillama_intents.json").loc[:BW_END]
dl_rev = s1("raw_defillama_intents_revenue.json").loc[:BW_END]
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
out["exploratory"] = {"X1_spearman_defillama_rev_vs_blockworks_intents": rx1, "X1_total_ratio": ratio, "X1_n_days": len(x1),
                      "X2_blockworks_active_drop": bdrop}

P("\nSUMMARY " + " | ".join(f"{k}: {out[k]['verdict']}" for k in ["E1", "E2", "E3", "E4", "E5"]))


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
