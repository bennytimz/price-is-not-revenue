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

# Verdict scorecard (build_scorecard.py), rendered as static HTML so it reads without JavaScript
import html as H
cards = []
for r in json.load(open(os.path.join(HERE, "scorecard.json"), encoding="utf-8")):
    cards.append(f'<div class="card"><h3>{r["id"]}: {H.escape(r["claim"])}</h3>'
                 f'<p><span>Threshold</span> {H.escape(r["threshold"])}</p><p><span>Result</span> {H.escape(r["result"])}</p>'
                 f'<p><span>Verdict</span> <b>{H.escape(r["verdict"])}</b>' + (f' ({H.escape(r["gloss"])})' if r.get("gloss") else '') + f'</p><p class="src">{H.escape(r["source"])}</p></div>')
score_html = "\n".join(cards)

# Section 8: interim status of the forward predictions, from the committed snapshot written by track_predictions.py
# (not recomputed here, so run_all.py needs no network for it)
PSF = os.path.join(HERE, "predictions_status.json")
if os.path.exists(PSF):
    PS_ = json.load(open(PSF, encoding="utf-8"))
    pcards = "\n".join(
        f'<div class="card"><h3>{p["id"]}: {H.escape(p["title"])}</h3>'
        f'<p><span>Threshold</span> {H.escape(p["threshold"])}</p><p><span>Now</span> {H.escape(p["current_value"])}</p>'
        f'<p><span>Status</span> <b>{H.escape(p["status"])}</b> (as of {p["as_of"]}; resolves {p["resolution_date"]})</p></div>'
        for p in PS_["predictions"])
    pred_html = (f'<h2>8. Where the predictions stand today ({H.escape(PS_["label"])})</h2>\n'
                 f'<p class="sub">Snapshot of {PS_["snapshot_date"]}: <b>{H.escape(PS_["label"])}</b>. The six predictions in PREDICTIONS.md resolve on '
                 f'2027-03-31 from data pulled on or after 2027-04-07; this applies the same rules to the data available on the snapshot date. '
                 f'&ldquo;On track&rdquo;: {H.escape(PS_["status_definitions"]["on track"])}; &ldquo;not yet&rdquo;: {H.escape(PS_["status_definitions"]["not yet"])}; '
                 f'&ldquo;cannot resolve&rdquo;: {H.escape(PS_["status_definitions"]["cannot resolve"])}.</p>\n<div class="sc">\n{pcards}\n</div>\n'
                 f'<p class="src">Code: <code>track_predictions.py</code>. Snapshot: <code>predictions_status.json</code> (derived values only). '
                 f'DefiLlama: {H.escape(PS_["sources"]["defillama"])}. BigQuery: {H.escape(PS_["sources"]["bigquery"])}.</p>\n'
                 f'<p class="links">Data and code: <a href="https://github.com/bennytimz/price-is-not-revenue/blob/main/track_predictions.py">track_predictions.py</a>, '
                 f'<a href="https://github.com/bennytimz/price-is-not-revenue/blob/main/predictions_status.json">predictions_status.json</a>, '
                 f'<a href="https://github.com/bennytimz/price-is-not-revenue/blob/main/PREDICTIONS.md">PREDICTIONS.md</a></p>')
else:
    pred_html = '<h2>8. Where the predictions stand today</h2>\n<p class="sub">No snapshot yet: run <code>python track_predictions.py</code>.</p>'

html = open(os.path.join(HERE, "dashboard_template.html")).read()
html = html.replace("__SCOREHTML__", score_html).replace("__PREDHTML__", pred_html)

# Headline tiles, read from scenario_numbers.json (scenarios.py); no typed numbers
oct26 = S["monthly"]["2026-10"]
tiles = [(f"${S['runrate_91d']['total']:.1f}M/yr", "Protocol revenue, trailing-91-day run-rate"),
         (f"{S['breakeven_multiple']}x", f"Revenue growth needed for buybacks to offset new supply (at the observed {S['buyback_share']:.0%} buyback share)"),
         (f"{S['grid']['1']['ps_at_current_mcap']:.0f}x", "Price to sales on total protocol revenue"),
         (f"{oct26['intents'] / (oct26['gas'] + oct26['intents']):.0%}", "Intents share of protocol revenue, October 2026")]
html = html.replace("__TILES__", "\n".join(f'<div class="tile"><b>{v}</b><span>{H.escape(t)}</span></div>' for v, t in tiles))
for k, v in (("__MONTHS__", months), ("__SERIES__", series), ("__PS__", ps), ("__MODEL__", model), ("__PHASE__", phase),
             ("__EXT2__", ext2), ("__EXT4__", ext4)):
    html = html.replace(k, json.dumps(v))
open(os.path.join(HERE, "dashboard.html"), "w").write(html)
print("dashboard.html written", len(html), "bytes")
