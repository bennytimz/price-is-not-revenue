"""Checks that the data files match the row counts and totals reported by the source at pull time.

Run:  python verify_data.py          (run_all.py calls it first and stops if anything fails)
Limits: the totals themselves come from the Blockworks pulls, so this proves the committed files equal what the
source reported on 2026-11-05, not that Blockworks is right. A Blockworks key is needed to re-pull independently.
"""
import hashlib
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = HERE
T = json.load(open(f"{D}/SOURCE_TOTALS.json"))
tol = T["tolerance_usd"]
fails = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))
    if not ok:
        fails.append(name)


nd = pd.read_csv(f"{D}/near_daily.csv", parse_dates=["date"]).set_index("date")
check("near_daily: contiguous daily dates", (nd.index.to_series().diff().dropna() == pd.Timedelta(days=1)).all() and nd.index[0] == pd.Timestamp("2024-01-01") and nd.index[-1] == pd.Timestamp("2026-11-04"))
for y, v in T["near_daily"].items():
    s = nd.loc[y]
    check(f"near_daily {y}: rows", len(s) == v["rows"], f"{len(s)}")
    check(f"near_daily {y}: revenue sum", abs(s.rev.sum() - v["revenue_sum"]) <= tol, f"{s.rev.sum():,.2f} vs {v['revenue_sum']:,.2f}")
pw = pd.read_csv(f"{D}/peers_weekly.csv", parse_dates=["week"])
check("peers_weekly: rows", len(pw) == T["peers_weekly_rows"], str(len(pw)))
check("peers_weekly: 148 contiguous weeks per asset", all((g.sort_values("week").week.diff().dropna() == pd.Timedelta(days=7)).all() and len(g) == 148 for _, g in pw.groupby("asset")))
for a, v in T["peers_weekly_revenue_sum"].items():
    s = pw[pw.asset == a].rev.sum()
    check(f"peers_weekly {a}: revenue sum", abs(s - v) <= tol, f"{s:,.2f} vs {v:,.2f}")
sp = pd.read_csv(f"{D}/near_total_supply_weekly.csv")
check("near_total_supply_weekly: rows and sum", len(sp) == T["near_total_supply_weekly"]["rows"] and abs(sp.total_supply.sum() - T["near_total_supply_weekly"]["sum"]) <= tol)
bb = pd.read_csv(f"{D}/near_buybacks_daily.csv")
check("near_buybacks_daily: rows and sum", len(bb) == T["near_buybacks_daily"]["rows"] and abs(bb.buybacks_usd.sum() - T["near_buybacks_daily"]["sum_usd"]) <= tol)
man = os.path.join(D, "MANIFEST.sha256")
if os.path.exists(man):
    for line in open(man):
        h, f = line.split()
        check(f"sha256 {f}", hashlib.sha256(open(os.path.join(D, f), "rb").read()).hexdigest() == h)
if fails:
    sys.exit(f"{len(fails)} data check(s) failed")
print("All data checks passed.")
