"""Builds dashboard.html from the data files and the two results JSON files.

Run order (or just `python run_all.py`): analysis_confirmatory.py, scenarios.py, analysis_extension.py, build_dashboard.py.
Each chart in the page states what it shows, the code that produces it and the data file it reads.
"""
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = HERE
S = json.load(open(os.path.join(HERE, "scenario_numbers.json")))
C = json.load(open(os.path.join(HERE, "confirmatory_numbers.json")))
nd = pd.read_csv(f"{D}/near_daily.csv", parse_dates=["date"]).set_index("date")
bb = pd.read_csv(f"{D}/near_buybacks_daily.csv", parse_dates=["date"]).set_index("date").buybacks_usd

INT = pd.Timestamp("2025-09-23")
rc = nd.rev.where(~((nd.index >= INT) & ((nd.rev - nd.fees).abs() < 1)))
intents = (rc - nd.fees).clip(lower=0)
intents[nd.index < INT] = 0.0
roll = intents.rolling(28, min_periods=24).mean().loc["2025-10-20":"2026-11-04"].dropna()
series = [[d.strftime("%Y-%m-%d"), round(float(v))] for d, v in roll.items()]
months = [[k, v["gas"], v["intents"]] for k, v in S["monthly"].items()]
peers = [[k, round(v)] for k, v in sorted(C["peers_ps_rev"].items(), key=lambda kv: -kv[1])]
ps = [["NEAR (gas fees only)", round(C["near_ps_gas"])], ["NEAR (total revenue)", round(C["near_ps_total"])]] + peers
model = dict(base_rev=S["runrate_91d"]["total"] * 1e6, iss_near=S["issuance"]["near_per_year_M"] * 1e6, bshare=S["buyback_share"],
             mcap=float(nd.mcap.loc["2026-11-01"]), price=float(nd.price.loc["2026-11-01"]))
phase = dict(labels=S["phase_index_labels"], idx=S["phase_index"])

# Sections 6-7: public-source cross-checks (analysis_extension.py, Amendment 8)
E = json.load(open(os.path.join(HERE, "extension_numbers.json")))
e2 = E["E2"]
ext2 = dict(labels=["Intents volume", "Retained revenue", "Take rate"],
            a=[100, 100, 100],
            b=[round(e2["volume_ratio"] * 100, 1), round(e2["revenue_ratio"] * 100, 1), round(e2["take_rate_bp_B"] / e2["take_rate_bp_A"] * 100, 1)],
            raw_a=[e2["vol_A"], e2["rev_A"], e2["take_rate_bp_A"]], raw_b=[e2["vol_B"], e2["rev_B"], e2["take_rate_bp_B"]])
s2 = pd.read_csv(f"{D}/raw_bigquery_daily_usage.csv", parse_dates=["block_date"]).set_index("block_date").active_signers
win = slice("2026-02-01", "2026-06-30")
s2i = (s2.loc[win] / E["E4"]["median_before"] * 100).round(1)
bwi = (nd.active.loc[win] / E["exploratory"]["X2_median_before"] * 100).round(1)
ext4 = dict(dates=[d.strftime("%Y-%m-%d") for d in s2i.index], s2=[None if pd.isna(v) else float(v) for v in s2i],
            bw=[None if pd.isna(v) else float(v) for v in bwi.reindex(s2i.index)])

html = open(os.path.join(HERE, "dashboard_template.html")).read()
for k, v in (("__MONTHS__", months), ("__SERIES__", series), ("__PS__", ps), ("__MODEL__", model), ("__PHASE__", phase),
             ("__EXT2__", ext2), ("__EXT4__", ext4)):
    html = html.replace(k, json.dumps(v))
open(os.path.join(HERE, "dashboard.html"), "w").write(html)
print("dashboard.html written", len(html), "bytes")
