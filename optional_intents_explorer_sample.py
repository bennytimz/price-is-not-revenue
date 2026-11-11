"""Sample NEAR Intents (1Click) swap volume from the public Explorer API.

STATUS: written from the OpenAPI spec (https://explorer.near-intents.org/api/v0/openapi.yaml), NOT YET RUN by the author.

What it does: for each chosen day it fetches successful swaps in ONE time window (default 1 hour at 12:00 UTC),
paging until the window is exhausted, and writes counts and USD volume to intents_sample.csv.

Limits you should know about:
- The API needs a JWT from https://partners.near-intents.org/ . Put it in a .env file: INTENTS_JWT=...
- Rate limit is 1 request every 5 seconds, 1000 swaps per request, so a full-day pull is slow. Sampling is deliberate.
- It covers 1Click swaps only, not all Intents activity. USD values are the API's own amountInUsd.
- A sampled hour is NOT a daily total. Treat any scaling to a daily figure as an estimate with unknown intraday bias.

Usage:  python intents_explorer_sample.py --start 2026-08-01 --days 5 --window-minutes 60
"""
import argparse
import csv
import datetime as dt
import os
import time

import requests

BASE = "https://explorer.near-intents.org/api/v0/transactions"


def load_token():
    if os.path.exists(".env"):
        for line in open(".env"):
            if line.startswith("INTENTS_JWT="):
                return line.split("=", 1)[1].strip()
    return os.environ["INTENTS_JWT"]


def fetch_window(token, start_unix, end_unix, max_pages):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"numberOfTransactions": 1000, "statuses": "SUCCESS", "startTimestampUnix": start_unix, "endTimestampUnix": end_unix, "direction": "next"}
    rows, pages = [], 0
    while pages < max_pages:
        r = requests.get(BASE, headers=headers, params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(6)
            continue
        r.raise_for_status()
        page = r.json()
        pages += 1
        rows += page
        time.sleep(5.1)
        if len(page) < 1000:
            return rows, False
        last = page[-1]
        params["lastDepositAddress"] = last["depositAddress"]
        if last.get("depositMemo"):
            params["lastDepositMemo"] = last["depositMemo"]
        else:
            params.pop("lastDepositMemo", None)
    return rows, True  # hit the page cap: window truncated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--hour", type=int, default=12)
    ap.add_argument("--window-minutes", type=int, default=60)
    ap.add_argument("--max-pages", type=int, default=30)
    a = ap.parse_args()
    token = load_token()
    with open("intents_sample.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "window_start_utc", "window_minutes", "swaps", "volume_in_usd", "volume_out_usd", "truncated"])
        for i in range(a.days):
            day = dt.datetime.strptime(a.start, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc) + dt.timedelta(days=i)
            s = day.replace(hour=a.hour)
            e = s + dt.timedelta(minutes=a.window_minutes)
            rows, trunc = fetch_window(token, int(s.timestamp()), int(e.timestamp()), a.max_pages)
            vin = sum(float(x["amountInUsd"]) for x in rows)
            vout = sum(float(x["amountOutUsd"]) for x in rows)
            w.writerow([day.date(), s.isoformat(), a.window_minutes, len(rows), round(vin, 2), round(vout, 2), trunc])
            print(day.date(), len(rows), "swaps", round(vin), "USD in", "(truncated)" if trunc else "")


if __name__ == "__main__":
    main()
