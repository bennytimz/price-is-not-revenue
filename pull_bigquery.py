"""Re-pull the two NEAR BigQuery series and compare them with the committed raw pulls.

Runs the committed queries pull_bigquery_daily_usage.sql (S2) and pull_bigquery_intents_contract.sql (S4) against the
public dataset bigquery-public-data.crypto_near_mainnet_us, with one change: the end date is capped at 2026-11-04
(the last Blockworks day), so the comparison with the committed files is like-for-like.

  python pull_bigquery.py                  dry run (default): prints the bytes each query would process, runs nothing
  python pull_bigquery.py --max-gb 200     change the cap (default 150 GB); it refuses if either query exceeds it
  python pull_bigquery.py --run            executes both queries (BigQuery bills the processed bytes to your project),
                                           writes repull_*.csv and compares them with the committed raw_*.csv files

Setup (not needed for run_all.py):
  pip install -r requirements-bigquery.txt
  Credentials: Google application-default credentials, e.g. `gcloud auth application-default login` (browser).
  Project: the GCP_PROJECT environment variable, or `gcloud config get-value project`.
Credentials are read by the Google client library from your machine and are never written by this script.
The committed raw files are never overwritten: output goes only to repull_*.csv (git-ignored).
"""
import argparse
import os
import shutil
import subprocess
import sys

import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
END = "2026-11-04"
QUERIES = [("pull_bigquery_daily_usage.sql", "raw_bigquery_daily_usage.csv", "repull_bigquery_daily_usage.csv"),
           ("pull_bigquery_intents_contract.sql", "raw_bigquery_intents_contract.csv", "repull_bigquery_intents_contract.csv")]


def capped_sql(sql_file):
    """The committed query, comments removed, with `AND block_date <= END` added before GROUP BY."""
    text = open(os.path.join(D, sql_file), encoding="utf-8").read()
    q = " ".join(ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("--"))
    if q.count(" GROUP BY ") != 1 or " WHERE " not in q:
        sys.exit(f"{sql_file}: expected one WHERE ... GROUP BY query; not changed, not run")
    return q.replace(" GROUP BY ", f" AND block_date <= '{END}' GROUP BY ", 1)


def project_id():
    p = os.environ.get("GCP_PROJECT", "").strip()
    if not p and shutil.which("gcloud"):
        p = subprocess.run(["gcloud", "config", "get-value", "project"], capture_output=True, text=True, shell=os.name == "nt").stdout.strip()
    if not p:
        sys.exit("No Google Cloud project: set GCP_PROJECT, or run `gcloud config set project <id>`.")
    return p


def compare(raw_file, repull_file):
    """Compare re-pull and committed pull over days up to END. Days the committed pull has after END are ignored."""
    a = pd.read_csv(os.path.join(D, raw_file))
    b = pd.read_csv(os.path.join(D, repull_file))
    a = a[a.block_date <= END].reset_index(drop=True)
    b = b[b.block_date <= END].reset_index(drop=True)
    ok = True
    print(f"   rows: committed {len(a)} | re-pull {len(b)}")
    print(f"   dates: committed {a.block_date.min()} to {a.block_date.max()} | re-pull {b.block_date.min()} to {b.block_date.max()}")
    ok &= len(a) == len(b) and a.block_date.min() == b.block_date.min() and a.block_date.max() == b.block_date.max()
    for c in [c for c in a.columns if c != "block_date"]:
        sa, sb = int(a[c].sum()), int(b[c].sum())
        print(f"   sum {c}: committed {sa:,} | re-pull {sb:,} | difference {sb - sa:+,}")
        ok &= sa == sb
    m = a.merge(b, on="block_date", how="outer", suffixes=("_c", "_r"), indicator=True)
    cols = [c for c in a.columns if c != "block_date"]
    differ = m[(m._merge != "both") | (m[[f"{c}_c" for c in cols]].to_numpy() != m[[f"{c}_r" for c in cols]].to_numpy()).any(axis=1)]
    print(f"   days that differ: {len(differ)}" + (f" (first: {', '.join(differ.block_date.astype(str).head(5))})" if len(differ) else ""))
    print(f"   {'MATCH' if ok and not len(differ) else 'DIFFER'}: {raw_file} vs {repull_file} up to {END}")
    return ok and not len(differ)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true", help="execute the queries (default: dry run only)")
    ap.add_argument("--max-gb", type=float, default=150.0, help="refuse if either query would process more than this (GB, default 150)")
    args = ap.parse_args()
    try:
        from google.cloud import bigquery
    except ImportError:
        sys.exit("google-cloud-bigquery is not installed: pip install -r requirements-bigquery.txt")
    client = bigquery.Client(project=project_id())
    queries = [(s, r, o, capped_sql(s)) for s, r, o in QUERIES]

    print(f"Dry run (nothing executed, nothing billed), end date capped at {END}, cap {args.max_gb:g} GB:")
    over = False
    for sql_file, _, _, q in queries:
        job = client.query(q, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
        gb = job.total_bytes_processed / 1e9
        over |= gb > args.max_gb
        print(f"   {sql_file}: {job.total_bytes_processed:,} bytes = {gb:,.1f} GB{'  OVER THE CAP' if gb > args.max_gb else ''}")
    if over:
        sys.exit(f"Refusing to run: a query exceeds --max-gb {args.max_gb:g}.")
    if not args.run:
        print("Dry run only. Add --run to execute (the bytes above are billed to your project).")
        return

    all_ok = True
    for sql_file, raw_file, out_file, q in queries:
        assert out_file.startswith("repull_") and out_file != raw_file
        rows = [dict(r) for r in client.query(q).result()]
        df = pd.DataFrame(rows)
        df["block_date"] = df.block_date.astype(str)
        df.sort_values("block_date").to_csv(os.path.join(D, out_file), index=False, lineterminator="\n")
        print(f"\n{sql_file}: wrote {out_file} ({len(df)} rows)")
        all_ok &= compare(raw_file, out_file)
    print("\nRe-pull " + ("matches the committed pulls up to " + END if all_ok else "differs from the committed pulls; see above") + ".")


if __name__ == "__main__":
    main()
