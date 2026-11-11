"""Rebuilds the analysis CSVs from the raw Blockworks exports saved in this folder as raw_*.csv.

Run:  python build_clean_data.py     (then python run_all.py)

Raw files are the CSV text exactly as exported (extra lines such as row counts are ignored). Expected names:
  raw_near_daily_2024.csv  raw_near_daily_2025.csv  raw_near_daily_2026.csv   (date, price_usd, ..., stablecoin_supply_usd)
  raw_peers_batch1.csv     raw_peers_batch2.csv                               (week_ending, asset, ...)
  raw_near_total_supply_weekly.csv   raw_near_buybacks_daily.csv
Stablecoin supply is dropped on purpose (two pulls disagreed on it).
"""
import hashlib
import os
import re
import sys
from io import StringIO

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = HERE
RAW = HERE
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def read_raw(name, first_col):
    path = os.path.join(RAW, "raw_" + name)
    if not os.path.exists(path):
        sys.exit(f"missing raw file: {path}")
    lines = [ln.rstrip("\r\n") for ln in open(path, encoding="utf-8")]
    h = next(i for i, ln in enumerate(lines) if ln.startswith(first_col))
    body = [ln for ln in lines[h + 1:] if DATE.match(ln)]
    return pd.read_csv(StringIO("\n".join([lines[h]] + body)))


daily = pd.concat([read_raw(f"near_daily_{y}.csv", "date") for y in (2024, 2025, 2026)], ignore_index=True)
daily = daily.rename(columns={"price_usd": "price", "circulating_market_cap_usd": "mcap", "protocol_revenue_usd": "rev",
                              "transaction_fees_usd": "fees", "active_addresses": "active", "total_transactions": "tx"})
daily["date"] = pd.to_datetime(daily["date"])
daily = daily.sort_values("date")
assert daily.date.is_unique and (daily.date.diff().dropna() == pd.Timedelta(days=1)).all(), "daily dates not contiguous"
daily[["date", "price", "mcap", "rev", "fees", "active", "tx"]].to_csv(f"{D}/near_daily.csv", index=False, date_format="%Y-%m-%d")

peers = pd.concat([read_raw(f"peers_batch{i}.csv", "week_ending") for i in (1, 2)], ignore_index=True)
peers = peers.rename(columns={"week_ending": "week", "close_price_usd": "price", "close_market_cap_usd": "mcap",
                              "weekly_protocol_revenue_usd": "rev", "weekly_transaction_fees_usd": "fees"})
peers = peers.sort_values(["asset", "week"])
assert peers.duplicated(["asset", "week"]).sum() == 0
peers[["week", "asset", "price", "mcap", "rev", "fees"]].to_csv(f"{D}/peers_weekly.csv", index=False)

sup = read_raw("near_total_supply_weekly.csv", "week_ending")[["week_ending", "total_supply"]]
sup.to_csv(f"{D}/near_total_supply_weekly.csv", index=False)
bb = read_raw("near_buybacks_daily.csv", "date")[["date", "buybacks_usd"]]
bb.to_csv(f"{D}/near_buybacks_daily.csv", index=False)

files = ["near_daily.csv", "peers_weekly.csv", "near_total_supply_weekly.csv", "near_buybacks_daily.csv"]
with open(f"{D}/MANIFEST.sha256", "w") as f:
    for name in files:
        f.write(f"{hashlib.sha256(open(os.path.join(D, name), 'rb').read()).hexdigest()}  {name}\n")
print(f"daily {len(daily)} rows | peers {len(peers)} rows | supply {len(sup)} rows | buybacks {len(bb)} rows | manifest written")
