"""Checks that the data files match the row counts and totals reported by the source at pull time.

Run:  python verify_data.py              (run_all.py calls it first and stops if anything fails)
      python verify_data.py --extension  (run_all.py calls it after analysis_extension.py; warns, never fails)
Limits: the totals themselves come from the Blockworks pulls, so this proves the committed files equal what the
source reported on 2026-11-05, not that Blockworks is right. A Blockworks key is needed to re-pull independently.

DefiLlama raw files are not in the repository (DefiLlama's terms; Amendment 8b). They are pulled locally by
pull_defillama_intents.py, so they cannot be checked against a fixed hash. Instead this script checks that they
parse and cover the dates the tests use, and --extension compares the E1-E3, F1-F2, X1 and X5-X7 numbers with the values first
committed (extension_expected.json) within stated tolerances.
"""
import datetime as dt
import hashlib
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = HERE

if "--extension" in sys.argv:
    ref = json.load(open(f"{D}/extension_expected.json", encoding="utf-8"))
    cur = json.load(open(f"{D}/extension_numbers.json", encoding="utf-8"))
    warn = []
    for key, exp, kind, tol_ in ref["checks"]:
        a, b = key.split(".", 1)
        got = cur[a][b]
        dev = abs(got - exp) if kind == "abs" else abs(got - exp) / abs(exp)
        ok = dev <= tol_ + 1e-12
        print(f"{'PASS' if ok else 'WARN'} {key}: now {got} vs committed {exp} ({kind} tolerance {tol_})")
        if not ok:
            warn.append(key)
    for k, v in ref["verdicts"].items():
        ok = cur[k]["verdict"] == v
        print(f"{'PASS' if ok else 'WARN'} {k} verdict: now '{cur[k]['verdict']}' vs committed '{v}'")
        if not ok:
            warn.append(f"{k} verdict")
    print(f"Extension check: WARNING, {len(warn)} differ from the committed values: {', '.join(warn)}" if warn
          else "Extension check: E1-E3, F1-F2, X1 and X5-X7 within tolerance of the committed values; all verdicts unchanged.")
    sys.exit(0)

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

# DefiLlama (S1), pulled locally: plausibility instead of a hash (Amendment 8b)
NEED = {"raw_defillama_intents.json": ("2024-12-10", "2026-11-10"),          # E1-E3 volume; F1 to 2026-11-10
        "raw_defillama_intents_revenue.json": ("2025-09-23", "2026-11-04"),  # X1
        "raw_defillama_intents_fees.json": ("2026-08-03", "2026-11-01")}     # X5 (exploratory)
for name, (lo, hi) in NEED.items():
    path = os.path.join(D, name)
    if not os.path.exists(path):
        check(f"{name}: present", False, "missing; run python pull_defillama_intents.py (run_all.py does this)")
        continue
    try:
        j = json.load(open(path, encoding="utf-8"))
        rows = j["totalDataChart"]
        s = pd.Series({pd.Timestamp(dt.datetime.fromtimestamp(t, dt.timezone.utc).date()): v for t, v in rows}).sort_index()
    except Exception as e:  # noqa: BLE001
        check(f"{name}: parses", False, str(e))
        continue
    check(f"{name}: NEAR Intents, {len(s)} rows {s.index.min().date()} to {s.index.max().date()}", j.get("slug") == "near-intents" and len(s) > 0)
    if lo:
        w = s.loc[lo:hi]
        need = (pd.Timestamp(hi) - pd.Timestamp(lo)).days + 1
        check(f"{name}: covers {lo} to {hi} with no missing or empty days",
              len(w) == need and w.notna().all() and (w >= 0).all(), f"{len(w)} of {need} days")
if fails:
    sys.exit(f"{len(fails)} data check(s) failed")
print("All data checks passed.")
