"""Post-hoc provenance cross-check: Blockworks daily NEAR transactions against NEAR's public BigQuery dataset.

The Blockworks files' row-count and sum checks (verify_data.py, SOURCE_TOTALS.json) compare the hand-copied files with
totals ChatGPT reported in the same chat, so they confirm the copy, not Blockworks' own figures. This script compares
one Blockworks series, daily transactions (near_daily.csv, column tx), with an independent count: daily transactions
in the committed BigQuery pull (raw_bigquery_daily_usage.csv, query pull_bigquery_daily_usage.sql). Post-hoc; it
changes no test or verdict and is not part of run_all.py.

Run: python provenance_crosscheck.py > provenance_crosscheck_results.txt
"""
import os

import pandas as pd
from scipy.stats import spearmanr

D = os.path.dirname(os.path.abspath(__file__))
bw = pd.read_csv(f"{D}/near_daily.csv", parse_dates=["date"]).set_index("date").tx
bq = pd.read_csv(f"{D}/raw_bigquery_daily_usage.csv", parse_dates=["block_date"]).set_index("block_date").transactions
d = pd.concat([bw, bq], axis=1, keys=["bw", "bq"], sort=True).loc[:"2026-11-04"].dropna()  # 2026-11-04: last Blockworks day
r = (d.bw / d.bq - 1).abs()
print("PROVENANCE CROSS-CHECK (post-hoc): Blockworks daily transactions vs NEAR BigQuery daily transactions")
print(f"overlapping days {len(d)} ({d.index.min().date()} to {d.index.max().date()}); Blockworks days without a BigQuery value: "
      f"{int(bw.loc[:'2026-11-04'].notna().sum() - len(d))}")
print(f"total ratio (Blockworks / BigQuery): {d.bw.sum() / d.bq.sum():.4f}")
print(f"daily absolute difference: median {r.median() * 100:.2f}% | days within 1%: {(r < 0.01).mean() * 100:.1f}% | "
      f"within 5%: {(r < 0.05).mean() * 100:.1f}% | largest {r.max() * 100:.1f}% on {r.idxmax().date()}")
print(f"Spearman of daily counts: {spearmanr(d.bw, d.bq)[0]:.3f}")
print("Other Blockworks series: Intents revenue level is checked against DefiLlama (X1, extension_results.txt); active addresses "
      "were checked against BigQuery signers and disagree (E4, E5). No independent check in this repository: NEAR price, market cap "
      "and gas fees (near_daily.csv), peers (peers_weekly.csv), total supply (near_total_supply_weekly.csv) and buybacks "
      "(near_buybacks_daily.csv).")
