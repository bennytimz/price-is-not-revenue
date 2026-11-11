"""S1 (Amendment 8): pull NEAR Intents daily volume, fees and revenue from DefiLlama's free API.

Saves each HTTP response body byte-for-byte (no parsing before saving) into a LOCAL file and prints a
data-quality summary. No analysis is done here.

The raw files are not committed or redistributed: DefiLlama's terms (https://defillama.com/terms) do not allow
republishing or mirroring its data without permission (PREREGISTRATION.md Amendment 8b; the files are in
.gitignore). run_all.py calls this script when the files are missing. Because DefiLlama can revise history, a
fresh pull can differ from the original; verify_data.py checks coverage and compares the results with tolerances.

Rule 9: on HTTP 402/403 the script stops and reports; it never substitutes another source.
Existing raw files are not overwritten unless --force is given, so a pull is never silently replaced.
"""
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

D = os.path.dirname(os.path.abspath(__file__))
BASE = "https://api.llama.fi/summary"
PULLS = [  # (raw file, URL)
    ("raw_defillama_intents.json", f"{BASE}/dexs/near-intents?dataType=dailyVolume"),
    ("raw_defillama_intents_fees.json", f"{BASE}/fees/near-intents?dataType=dailyFees"),
    ("raw_defillama_intents_revenue.json", f"{BASE}/fees/near-intents?dataType=dailyRevenue"),
]
EXPECTED_KEYS = ["name", "slug", "chains", "totalDataChart", "methodology"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-script/1.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def summarise(name, body):
    j = json.loads(body)
    missing = [k for k in EXPECTED_KEYS if k not in j or j[k] in (None, [], {})]
    rows = j.get("totalDataChart") or []
    print(f"{name}: protocol={j.get('name')!r} slug={j.get('slug')!r}")
    if not rows:
        print("   totalDataChart is empty or missing")
    else:
        days = [dt.datetime.fromtimestamp(t, dt.timezone.utc).date() for t, _ in rows]
        full = (days[-1] - days[0]).days + 1
        gaps = sorted(set(days[0] + dt.timedelta(n) for n in range(full)) - set(days))
        dups = len(days) - len(set(days))
        empty = [str(d) for d, (_, v) in zip(days, rows) if v is None or v == ""]
        print(f"   rows {len(rows)} | first {days[0]} | last {days[-1]} | calendar days in range {full}")
        print(f"   missing dates: {len(gaps)}{' ' + str([str(g) for g in gaps[:10]]) if gaps else ''}"
              f" | duplicate dates: {dups} | null/empty values: {len(empty)}{' ' + str(empty[:10]) if empty else ''}")
    print(f"   expected fields missing or empty: {missing if missing else 'none'}")


def main():
    force = "--force" in sys.argv
    for name, url in PULLS:
        path = os.path.join(D, name)
        if os.path.exists(path) and not force:
            print(f"{name}: already exists, not re-pulled (use --force to replace)")
            body = open(path, "rb").read()
        else:
            status, body = fetch(url)
            if status in (402, 403):
                sys.exit(f"STOP (rule 9): {url} returned HTTP {status}. Record under 'What I could not compute'; "
                         f"do not substitute another source without a new amendment.")
            if status != 200:
                sys.exit(f"STOP: {url} returned HTTP {status}; nothing saved for {name}.")
            with open(path, "wb") as f:
                f.write(body)
            print(f"{name}: saved {len(body)} bytes from {url} at {dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ}")
        print(f"   local sha256 {hashlib.sha256(body).hexdigest()} (not stored; for comparing pulls)")
        summarise(name, body)
    print(f"DefiLlama pull done: {len(PULLS)} local files (not committed)")


if __name__ == "__main__":
    main()
