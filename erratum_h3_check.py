"""Post-hoc check for Amendment 11 (erratum): would H3 change if run exactly as registered?

H3 was registered as "NEAR's P/S on 2026-11-04" with trailing 90-day revenue (PREREGISTRATION.md, H3 and Definitions),
but analysis_confirmatory.py ran it on 2026-11-01 with trailing 91-day revenue. This script recomputes NEAR's side as
registered (2026-11-04, 90 days) from near_daily.csv with the same cleaning rules (Amendments 1-2), and applies the
registered H3 rule. It does not change analysis_confirmatory.py or any results file.

Limits, stated in the output:
- Peers: peers_weekly.csv is weekly and ends 2026-11-01, so peer P/S on 2026-11-04 cannot be computed. The peer
  medians are taken from confirmatory_numbers.json (2026-11-01, 13 weeks).
- Own history: recomputed as NEAR's daily P/S with trailing 90-day revenue (the confirmatory run used weekly points
  with 13-week sums), percentile and 75th percentile over all earlier days.

Run: python erratum_h3_check.py > erratum_h3_results.txt   (post-hoc; not part of run_all.py)
"""
import json
import os
import statistics

import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
nd = pd.read_csv(f"{D}/near_daily.csv", parse_dates=["date"]).set_index("date")
C = json.load(open(f"{D}/confirmatory_numbers.json"))
INTENTS = pd.Timestamp("2025-09-23")
DATE, DAYS = pd.Timestamp("2026-11-04"), 90

# cleaning rules, copied from analysis_confirmatory.py (Amendments 1-2)
nd["rev_c"] = nd.rev.where(~((nd.index >= INTENTS) & ((nd.rev - nd.fees).abs() < 1)))
s = nd.mcap / nd.price
med7 = s.rolling(7, center=True, min_periods=4).median()
dev = (s / med7 - 1).abs()
spike = (dev > 0.03) & (dev.shift(1) <= 0.03) & (dev.shift(-1) <= 0.03)
nd["mcap_c"] = nd.mcap.where(~spike)

k = 365 / DAYS
mc = nd.mcap_c.ffill()
win = nd.loc[DATE - pd.Timedelta(days=DAYS - 1):DATE]
print(f"H3 as registered (POST-HOC CHECK, Amendment 11): NEAR P/S on {DATE.date()} with trailing {DAYS}-day revenue, annualised")
print(f"window {win.index.min().date()} to {win.index.max().date()}: {len(win)} days | missing gas-fee days {int(win.fees.isna().sum())} | missing revenue days {int(win.rev_c.isna().sum())}")
near = {"fees": mc.loc[DATE] / (win.fees.sum() * k), "total": mc.loc[DATE] / (win.rev_c.sum() * k)}
print(f"NEAR: on gas fees {near['fees']:.0f}x | on total protocol revenue {near['total']:.0f}x")

med_rev = statistics.median(C["peers_ps_rev"].values())
med_fees = statistics.median(C["peers_ps_fees"].values())
print(f"peer median (from confirmatory_numbers.json, 2026-11-01, 13 weeks; peers cannot be computed on 2026-11-04): "
      f"protocol revenue {med_rev:.0f}x | fees only {med_fees:.0f}x")

hist = {}
for lab, col in (("fees", "fees"), ("total", "rev_c")):
    ps = (mc / (nd[col].rolling(DAYS, min_periods=DAYS).sum() * k)).loc[:DATE].dropna()
    now, h = ps.iloc[-1], ps.iloc[:-1]
    hist[lab] = (now, (h < now).mean(), h.quantile(0.75))
    print(f"NEAR own history ({lab}, daily, {DAYS}-day): now {now:.0f}x | percentile {(h < now).mean() * 100:.0f}% | 75th pct {h.quantile(0.75):.0f}x | {len(h)} earlier days")

print("registered rule: SUPPORTED if above the peer median and above its own 75th percentile; REJECTED if below the peer median")
for lab, num, peer, hh in (("(a) NEAR fees vs peers' revenue", near["fees"], med_rev, hist["fees"]),
                           ("(b) fees vs fees", near["fees"], med_fees, hist["fees"]),
                           ("(c) NEAR total vs peers' revenue [not like-for-like]", near["total"], med_rev, hist["total"])):
    verdict = "SUPPORTED" if (num > peer and hh[0] > hh[2]) else ("REJECTED" if num < peer else "not supported")
    print(f"  {lab}: NEAR {num:.0f}x vs peer median {peer:.0f}x; above own 75th pct: {hh[0] > hh[2]} -> {verdict}")
print("confirmatory run (2026-11-01, 91 days): (a) SUPPORTED; (b) SUPPORTED; (c) REJECTED")
