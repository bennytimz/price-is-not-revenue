"""Interim status of the six forward predictions P1 to P6 (PREDICTIONS.md). INTERIM STATUS, NOT A RESOLUTION.

Each prediction resolves on 2027-03-31 from data pulled on or after 2027-04-07. This script applies the same
resolution rules to the data available today, so anyone can see where each prediction stands. Nothing it prints
resolves a prediction.

Thresholds, windows and day counts are not typed here: they are read from the wording of PREDICTIONS.md (the
script stops if that wording cannot be found), and check_consistency.py checks the anchors against the results files.

Data:
  DefiLlama (P1-P4, P6 volume): a fresh pull through pull_defillama_intents.py's endpoints and fetch(), saved
    locally in predictions_pull/ (git-ignored, never committed; DefiLlama's terms, Amendment 8b). The day of the
    pull (UTC) and later days are dropped as possibly incomplete.
  BigQuery (P5, P6 calls): by default the committed pulls raw_bigquery_daily_usage.csv and
    raw_bigquery_intents_contract.csv. Both were run on 2026-11-11 UTC, so that partial day is dropped (as
    Amendment 9 does) and the last complete day is 2026-11-10.
    --run re-runs the two committed queries up to yesterday (UTC) into repull_predictions_*.csv (git-ignored). It
    always dry-runs first and refuses if either query would process more than --max-gb (default 150 GB).
    --dry-run prints the bytes and stops there. Setup as for pull_bigquery.py (requirements-bigquery.txt,
    application-default credentials, GCP_PROJECT).

Interim rules (the resolution rules, applied to the data so far):
  - Missing data: if more than 5% of the days the computation uses are missing or empty -> "cannot resolve".
  - P1, P2: trailing 28-day average for each day from the window start to the as-of date; the streak of
    consecutive days meeting the threshold is counted.
  - P3: take rate over the latest 90 days (the length of the 2027-01-01 to 2027-03-31 window) until that window
    opens, then over the part of the window so far.
  - P4: mean daily revenue over the latest 91 days, times 365.
  - P5: 28-day mean of daily distinct signers ending on the as-of date.
  - P6: Spearman of daily calls against daily volume over the window so far (at least 3 overlapping days).
Status:
  "on track"       the interim reading is in the outcome the prediction's title names (P1, P2: the threshold is
                   met today; P3: take rate held, at or above window B's level; P4: compounding; P5: no recovery;
                   P6: the proxy holds)
  "not yet"        it is not, or there is no reading in the window yet
  "cannot resolve" more than 5% of the days needed are missing or empty
  "baseline (threshold set from this window)"
                   the threshold was computed from data that ends on or after the last day of the current reading,
                   so the reading contains no new data and is not a test. Applied automatically wherever a
                   threshold comes from a data window (P3: E2 windows A and B; P4: X5's 91-day window; P5: X6's
                   28-day mean); P1, P2 (Amendment 7) and P6 (Amendment 9) have fixed thresholds. "On track" and
                   "not yet" appear only once the reading includes days after that window.

Output: a table on screen and a dated snapshot in predictions_status.json (derived values only). build_dashboard.py
shows the committed snapshot in the section "Where the predictions stand today".

  python track_predictions.py             fresh DefiLlama pull + committed BigQuery pulls
  python track_predictions.py --no-pull   reuse the last local DefiLlama pull in predictions_pull/
  python track_predictions.py --dry-run   also dry-run the BigQuery re-pull (bytes only, nothing billed)
  python track_predictions.py --run       also re-pull BigQuery (dry run first; refused above --max-gb)
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

import pandas as pd
from scipy.stats import spearmanr

import pull_defillama_intents as pdl

D = os.path.dirname(os.path.abspath(__file__))
PULL_DIR = os.path.join(D, "predictions_pull")
LABEL = "interim status, not a resolution"
DL = {"vol": "raw_defillama_intents.json", "rev": "raw_defillama_intents_revenue.json"}
BQ = {"usage": ("pull_bigquery_daily_usage.sql", "raw_bigquery_daily_usage.csv", "repull_predictions_daily_usage.csv"),
      "calls": ("pull_bigquery_intents_contract.sql", "raw_bigquery_intents_contract.csv", "repull_predictions_intents_contract.csv")}
BASELINE = "baseline (threshold set from this window)"
COMMITTED_PULL_DAY = "2026-11-11"  # both committed BigQuery pulls were run on this UTC day; it is partial
MAX_MISSING = 0.05


# ---------- thresholds and windows, read from PREDICTIONS.md ----------
def find(block, pat, pid):
    m = re.search(pat, block)
    if not m:
        sys.exit(f"PREDICTIONS.md: {pid}: wording not found ({pat}); nothing computed")
    return m.groups()


def money(s):
    return float(s.replace(",", ""))


def read_predictions():
    text = open(os.path.join(D, "PREDICTIONS.md"), encoding="utf-8").read()
    blocks = {p: (t, b) for p, t, b in re.findall(r"\*\*(P\d)\. (.*?)\*\*\n(.*?)(?=\n\*\*P\d\. |\Z)", text, re.S)}
    if sorted(blocks) != [f"P{i}" for i in range(1, 7)]:
        sys.exit(f"PREDICTIONS.md: expected P1 to P6, found {sorted(blocks)}")
    P = {}
    for p, (title, b) in blocks.items():
        P[p] = {"title": title.rstrip("."), "resolution_date": find(b, r"Resolution date: (\d{4}-\d\d-\d\d)", p)[0]}
    b = blocks["P1"][1]
    P["P1"]["min"] = money(find(b, r"at least \$([\d,]+) a day", "P1")[0])
    P["P1"]["start"], P["P1"]["end"] = find(b, r"for every day from (\d{4}-\d\d-\d\d) to (\d{4}-\d\d-\d\d)", "P1")
    P["P1"]["days"] = int(find(b, r"on (\d+) consecutive days", "P1")[0])
    b = blocks["P2"][1]
    hi, n, s, e = find(b, r"at most \$([\d,]+) on (\d+) consecutive days within (\d{4}-\d\d-\d\d) to (\d{4}-\d\d-\d\d)", "P2")
    P["P2"].update(max=money(hi), days=int(n), start=s, end=e)
    b = blocks["P3"][1]
    P["P3"]["start"], P["P3"]["end"] = find(b, r"total volume over (\d{4}-\d\d-\d\d) to (\d{4}-\d\d-\d\d)", "P3")
    P["P3"]["low"] = float(find(b, r"At or below (\d+\.\d+) bp", "P3")[0])
    P["P3"]["high"] = float(find(b, r"At or above (\d+\.\d+) bp", "P3")[0])
    b = blocks["P4"][1]
    n, P["P4"]["end"] = find(b, r"over the (\d+) days ending (\d{4}-\d\d-\d\d)", "P4")
    P["P4"]["days"] = int(n)
    base = float(find(b, r"At or above twice \$([\d.]+)M", "P4")[0])
    P["P4"]["low"] = float(find(b, r"Below \$([\d.]+)M", "P4")[0]) * 1e6
    P["P4"]["high"] = 2 * base * 1e6
    b = blocks["P5"][1]
    P["P5"]["low"] = money(find(b, r"At or below ([\d,]+), there is no recovery", "P5")[0])
    P["P5"]["high"] = money(find(b, r"At or above ([\d,]+), usage is back", "P5")[0])
    P["P5"]["days"] = int(find(b, r"the (\d+)-day mean of daily distinct signers", "P5")[0])
    b = blocks["P6"][1]
    s, e, n = find(b, r"over (\d{4}-\d\d-\d\d) to (\d{4}-\d\d-\d\d) \((\d+) days\)", "P6")
    P["P6"].update(start=s, end=e, window_days=int(n), min=float(find(b, r"At or above (\d\.\d+), the proxy holds", "P6")[0]))
    return P


def threshold_windows():
    """Last day of the data each window-derived threshold was computed from, read from the results files
    (extension_numbers.json) and, for E2's windows, which that file does not record, from analysis_extension.py."""
    E = json.load(open(os.path.join(D, "extension_numbers.json"), encoding="utf-8"))
    m = re.search(r'^A, B = \(("\d{4}-\d\d-\d\d"), ("\d{4}-\d\d-\d\d")\), \(("\d{4}-\d\d-\d\d"), ("\d{4}-\d\d-\d\d")\)',
                  open(os.path.join(D, "analysis_extension.py"), encoding="utf-8").read(), re.M)
    if not m:
        sys.exit("analysis_extension.py: E2 window definition not found; nothing computed")
    return {"P3": ("E2 windows A and B", m.group(4).strip('"')),
            "P4": ("X5's 91-day window", E["exploratory_X5"]["window"][1]),
            "P5": ("X6's 28-day mean", E["exploratory_X6"]["asof"])}


# ---------- data ----------
def pull_defillama(no_pull):
    os.makedirs(PULL_DIR, exist_ok=True)
    stamp = os.path.join(PULL_DIR, "pulled_at_utc.txt")
    if no_pull:
        if not (os.path.exists(stamp) and all(os.path.exists(os.path.join(PULL_DIR, f)) for f in DL.values())):
            sys.exit("--no-pull: no earlier pull in predictions_pull/; run without --no-pull first")
        return open(stamp).read().strip()
    for name, url in pdl.PULLS:
        if name not in DL.values():
            continue
        status, body = pdl.fetch(url)
        if status in (402, 403):
            sys.exit(f"STOP (rule 9): {url} returned HTTP {status}; no substitute source is used.")
        if status != 200:
            sys.exit(f"STOP: {url} returned HTTP {status}; nothing computed.")
        with open(os.path.join(PULL_DIR, name), "wb") as f:
            f.write(body)
    at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    open(stamp, "w").write(at)
    return at


def defillama(name, pulled_at):
    j = json.load(open(os.path.join(PULL_DIR, name), encoding="utf-8"))
    s = pd.Series({pd.Timestamp(dt.datetime.fromtimestamp(t, dt.timezone.utc).date()): (None if v in (None, "") else float(v))
                   for t, v in j["totalDataChart"]}, dtype=float).sort_index()
    return s[s.index < pd.Timestamp(pulled_at[:10])]  # the pull day may be incomplete


def bigquery(mode, max_gb):
    """Returns ({series: DataFrame}, source description). Committed pulls unless mode is 'run'."""
    if mode in ("dry-run", "run"):
        import pull_bigquery as pb
        try:
            from google.cloud import bigquery as gbq
        except ImportError:
            sys.exit("google-cloud-bigquery is not installed: pip install -r requirements-bigquery.txt")
        pb.END = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)).isoformat()  # last complete UTC day
        client = gbq.Client(project=pb.project_id())
        qs = {k: pb.capped_sql(sql) for k, (sql, _, _) in BQ.items()}
        print(f"BigQuery dry run (nothing executed, nothing billed), end date {pb.END}, cap {max_gb:g} GB:")
        over = False
        for k, q in qs.items():
            gb = client.query(q, job_config=gbq.QueryJobConfig(dry_run=True, use_query_cache=False)).total_bytes_processed / 1e9
            over |= gb > max_gb
            print(f"   {BQ[k][0]}: {gb:,.1f} GB{'  OVER THE CAP' if gb > max_gb else ''}")
        if over:
            sys.exit(f"Refusing to run: a query exceeds --max-gb {max_gb:g}.")
        if mode == "run":
            out = {}
            for k, q in qs.items():
                df = pd.DataFrame([dict(r) for r in client.query(q).result()])
                df["block_date"] = df.block_date.astype(str)
                df = df.sort_values("block_date")
                df.to_csv(os.path.join(D, BQ[k][2]), index=False, lineterminator="\n")
                out[k] = df
                print(f"   wrote {BQ[k][2]} ({len(df)} rows, git-ignored)")
            return out, f"BigQuery re-pull up to {pb.END} (repull_predictions_*.csv, not committed)"
        print("Dry run only; using the committed pulls. Add --run to execute (billed to your project).")
    out = {k: pd.read_csv(os.path.join(D, raw)) for k, (_, raw, _) in BQ.items()}
    out = {k: df[df.block_date < COMMITTED_PULL_DAY] for k, df in out.items()}
    return out, f"committed BigQuery pulls, complete days to {max(df.block_date.max() for df in out.values())} ({COMMITTED_PULL_DAY} is the partial pull day, dropped)"


def bq_series(df, col):
    return pd.Series(df[col].values, index=pd.to_datetime(df.block_date), dtype=float).sort_index()


def missing(s, start, end):
    """(missing or empty days, calendar days) of s over [start, end]."""
    days = pd.date_range(start, end, freq="D")
    if len(days) == 0:
        return 0, 0
    return int(s.reindex(days).isna().sum()), len(days)


def streaks(cond):
    longest = run = 0
    for c in cond:
        run = run + 1 if c else 0
        longest = max(longest, run)
    return longest, run


def d(ts):
    return ts.strftime("%Y-%m-%d")


# ---------- the six predictions ----------
def amendment7(p, P, rev, meets):
    q = P[p]
    start, end = pd.Timestamp(q["start"]), pd.Timestamp(q["end"])
    asof = min(rev.index.max(), end)
    look = start - pd.Timedelta(days=27)
    miss, n = missing(rev, look, asof)
    roll = rev.reindex(pd.date_range(look, asof, freq="D")).rolling(28, min_periods=1).mean()
    cur = float(roll.iloc[-1])
    inwin = roll.loc[start:asof]
    longest, run = streaks(meets(inwin)) if len(inwin) else (0, 0)
    bound = f"at least ${q['min']:,.0f} a day" if "min" in q else f"at most ${q['max']:,.0f} a day"
    r = dict(threshold=f"trailing 28-day average {bound} on {q['days']} consecutive days, {q['start']} to {q['end']}",
             current_value=f"${cur:,.0f} a day (trailing 28-day average); streak meeting it so far {run} days, longest {longest} days, of {q['days']} consecutive days needed",
             value=cur, streak=run, longest_streak=longest, days_in_window=len(inwin), as_of=d(asof), missing_days=miss, days_used=n)
    if miss > MAX_MISSING * n:
        r["status"] = "cannot resolve"
    elif longest >= q["days"] or (len(inwin) and meets(pd.Series([cur])).iloc[0]):
        r["status"] = "on track"
    else:
        r["status"] = "not yet"
    return r


def p3(P, rev, vol):
    q = P["P3"]
    start, end = pd.Timestamp(q["start"]), pd.Timestamp(q["end"])
    asof = min(rev.index.max(), vol.index.max(), end)
    length = (end - start).days + 1
    lo = start if asof >= start else asof - pd.Timedelta(days=length - 1)
    span = "window so far" if asof >= start else f"latest {length} days (window opens {q['start']})"
    m1, n = missing(rev, lo, asof)
    m2, _ = missing(vol, lo, asof)
    both = pd.concat([rev, vol], axis=1, keys=["rev", "vol"], sort=True).loc[lo:asof].dropna()
    tr = float(both.rev.sum() / both.vol.sum() * 1e4)
    reading = "take rate held (supports)" if tr >= q["high"] else "bear case (weakens)" if tr <= q["low"] else "in between"
    r = dict(threshold=f"at or below {q['low']:.2f} bp: bear case; at or above {q['high']:.2f} bp: take rate held; over {q['start']} to {q['end']}",
             current_value=f"{tr:.2f} bp over the {span}, {d(lo)} to {d(asof)}: {reading}",
             value=tr, reading=reading, as_of=d(asof), missing_days=max(m1, m2), days_used=n)
    r["status"] = "cannot resolve" if max(m1, m2) > MAX_MISSING * n else "on track" if tr >= q["high"] else "not yet"
    return r


def p4(P, rev):
    q = P["P4"]
    asof = min(rev.index.max(), pd.Timestamp(q["end"]))
    lo = asof - pd.Timedelta(days=q["days"] - 1)
    miss, n = missing(rev, lo, asof)
    ann = float(rev.loc[lo:asof].mean() * 365)
    reading = "compounding (supports)" if ann >= q["high"] else "not growing (weakens)" if ann < q["low"] else "in between"
    r = dict(threshold=f"below ${q['low'] / 1e6:.1f}M: not growing; at or above ${q['high'] / 1e6:.1f}M: compounding (mean daily revenue x 365, {q['days']} days ending {q['end']})",
             current_value=f"${ann / 1e6:.1f}M a year (mean daily revenue x 365), {q['days']} days {d(lo)} to {d(asof)}: {reading}",
             value=ann, reading=reading, as_of=d(asof), missing_days=miss, days_used=n)
    r["status"] = "cannot resolve" if miss > MAX_MISSING * n else "on track" if ann >= q["high"] else "not yet"
    return r


def p5(P, signers):
    q = P["P5"]
    asof = min(signers.index.max(), pd.Timestamp(q["resolution_date"]))
    lo = asof - pd.Timedelta(days=q["days"] - 1)
    miss, n = missing(signers, lo, asof)
    mean = float(signers.loc[lo:asof].mean())
    reading = "no recovery (supports)" if mean <= q["low"] else "back to a year earlier (weakens)" if mean >= q["high"] else "in between"
    r = dict(threshold=f"at or below {q['low']:,.0f}: no recovery; at or above {q['high']:,.0f}: back to a year earlier ({q['days']}-day mean of daily distinct signers)",
             current_value=f"{mean:,.0f} distinct signers a day, {q['days']}-day mean ending {d(asof)}: {reading}",
             value=mean, reading=reading, as_of=d(asof), missing_days=miss, days_used=n)
    r["status"] = "cannot resolve" if miss > MAX_MISSING * n else "on track" if mean <= q["low"] else "not yet"
    return r


def p6(P, calls, vol):
    q = P["P6"]
    start, end = pd.Timestamp(q["start"]), pd.Timestamp(q["end"])
    asof = min(calls.index.max(), vol.index.max(), end)
    th = f"Spearman at or above {q['min']:.2f}: the proxy holds; {q['start']} to {q['end']} ({q['window_days']} days)"
    if asof < start:
        last = f"BigQuery data ends {d(calls.index.max())}" if calls.index.max() < start else f"DefiLlama data ends {d(vol.index.max())}"
        return dict(threshold=th, current_value=f"no reading: no overlapping days in the window yet ({last})", value=None,
                    n_days=0, as_of=d(asof), missing_days=0, days_used=0, status="not yet")
    m1, n = missing(calls, start, asof)
    m2, _ = missing(vol, start, asof)
    f = pd.concat([calls, vol], axis=1, keys=["calls", "vol"], sort=True).loc[start:asof].dropna()
    rho = float(spearmanr(f.calls, f.vol)[0]) if len(f) >= 3 else None
    r = dict(threshold=th, n_days=len(f), as_of=d(asof), missing_days=max(m1, m2), days_used=n, value=rho)
    if rho is None:
        r.update(current_value=f"no reading: {len(f)} overlapping days so far (at least 3 needed)", status="not yet")
    else:
        r.update(current_value=f"{rho:.2f} (Spearman), {len(f)} overlapping days {q['start']} to {d(asof)}",
                 status="cannot resolve" if max(m1, m2) > MAX_MISSING * n else "on track" if rho >= q["min"] else "not yet")
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-pull", action="store_true", help="reuse the last DefiLlama pull in predictions_pull/")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="dry-run the BigQuery re-pull (bytes only)")
    g.add_argument("--run", action="store_true", help="re-pull BigQuery up to yesterday (dry run first, size cap)")
    ap.add_argument("--max-gb", type=float, default=150.0, help="refuse the BigQuery re-pull above this (GB, default 150)")
    args = ap.parse_args()

    P = read_predictions()
    pulled_at = pull_defillama(args.no_pull)
    rev, vol = defillama(DL["rev"], pulled_at), defillama(DL["vol"], pulled_at)
    bq, bq_source = bigquery("run" if args.run else "dry-run" if args.dry_run else "none", args.max_gb)
    signers = bq_series(bq["usage"], "active_signers")
    calls = bq_series(bq["calls"], "intents_calls")

    rows = {"P1": amendment7("P1", P, rev, lambda s: s >= P["P1"]["min"]),
            "P2": amendment7("P2", P, rev, lambda s: s <= P["P2"]["max"]),
            "P3": p3(P, rev, vol), "P4": p4(P, rev), "P5": p5(P, signers), "P6": p6(P, calls, vol)}
    preds = [dict(id=k, title=P[k]["title"], resolution_date=P[k]["resolution_date"], **v) for k, v in rows.items()]
    for p in preds:
        src = threshold_windows().get(p["id"])
        if src and p["as_of"] <= src[1]:
            p["status"] = BASELINE
            p["note"] = (f"Threshold set from {src[0]}, ending {src[1]}; the current value has no data after that day, "
                         f"so it is the baseline, not a test. It becomes a test once data after {src[1]} exists.")
        if isinstance(p.get("value"), float):
            p["value"] = round(p["value"], 6)

    snap = {"label": LABEL, "snapshot_date": pulled_at[:10], "generated_utc": pulled_at,
            "sources": {"defillama": f"DefiLlama free API via pull_defillama_intents.py endpoints, pulled {pulled_at}; days before {pulled_at[:10]} (UTC) used; raw data not committed",
                        "bigquery": bq_source},
            "status_definitions": {"on track": "the interim reading is in the outcome the prediction's title names",
                                   "not yet": "it is not, or there is no reading in the window yet",
                                   "cannot resolve": "more than 5% of the days needed are missing or empty",
                                   BASELINE: "the threshold was set from the same data as the current value, so there is no new data to test yet"},
            "predictions": preds}
    with open(os.path.join(D, "predictions_status.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(snap, f, indent=1, ensure_ascii=False)
        f.write("\n")

    print(f"PREDICTIONS P1 to P6: {LABEL.upper()}. Snapshot {snap['snapshot_date']}; every prediction resolves on 2027-03-31.")
    print(f"DefiLlama: {snap['sources']['defillama']}\nBigQuery: {bq_source}\n")
    for p in preds:
        print(f"{p['id']}. {p['title']}  [{p['status'].upper()}, as of {p['as_of']}]")
        print(f"    threshold: {p['threshold']}")
        print(f"    current:   {p['current_value']}")
        if p.get("note"):
            print(f"    note:      {p['note']}")
        if p["missing_days"]:
            print(f"    missing or empty days: {p['missing_days']} of {p['days_used']}")
    print(f"\n  {'Pred.':<7}{'Status':<44}As of")
    for p in preds:
        print(f"  {p['id']:<7}{p['status']:<44}{p['as_of']}")
    print(f"\nWritten predictions_status.json ({LABEL}).")


if __name__ == "__main__":
    main()
