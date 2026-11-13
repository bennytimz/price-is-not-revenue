"""Cross-document consistency check: every key figure must agree everywhere it appears.

Canonical values are read from the generated JSON files (scenario_numbers.json, confirmatory_numbers.json,
extension_numbers.json, scorecard.json) and from PREREGISTRATION.md (Amendment 7 thresholds). The script then finds
each figure wherever it is mentioned in THESIS.md, README.md, SUBMISSION_DRAFT.md, PREDICTIONS.md, SCORECARD.md and
dashboard.html, using the wording around it (for example "N times the run-rate", "N% of NEAR's protocol revenue",
"| E3 | ... | **verdict** |"), and fails if any mention disagrees after rounding ("$20M" agrees with 20.32; "$67,000"
with 67,116). A figure written as a bare number with no recognisable wording is not checked.

Run:  python check_consistency.py            (exit 1 on any mismatch)
      python check_consistency.py --verbose  (also list every mention found)
CI runs it after run_all.py.
"""
import html
import json
import os
import re
import statistics
import sys

D = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: open(os.path.join(D, f), encoding="utf-8").read()
S, C, E = (json.loads(rd(f)) for f in ("scenario_numbers.json", "confirmatory_numbers.json", "extension_numbers.json"))
SC = {r["id"]: r for r in json.loads(rd("scorecard.json"))}
PRE = rd("PREREGISTRATION.md")
VERBOSE = "--verbose" in sys.argv

# ---------- canonical values ----------
oct26 = S["monthly"]["2026-10"]
x4, x6, x7 = E["exploratory"], E["exploratory_X6"], E["exploratory_X7"]
a7_hi = re.search(r"at least \$([\d,]+) per day for (\d+) consecutive days", PRE)
a7_lo = re.search(r"at most \$([\d,]+) per day for (\d+) consecutive days", PRE)
K = {
    "break-even multiple": [S["breakeven_multiple"]],
    "break-even multiple at 100% buybacks (X7)": [x7["multiple_of_runrate_total"]],
    "break-even revenue $M": [S["breakeven_rev_M"], x7["breakeven_rev_M_at_100pct"]],
    "net new supply $M a year": [S["issuance"]["usd_M_at_spot"]],
    "P/S on total revenue": [C["near_ps_total"]],
    "P/S on gas fees": [C["near_ps_gas"]],
    "peer median P/S": [statistics.median(C["peers_ps_rev"].values()), statistics.median(C["peers_ps_fees"].values())],
    "buyback share %": [S["buyback_share"] * 100],
    "Intents share of revenue, Oct 2026 %": [oct26["intents"] / (oct26["gas"] + oct26["intents"]) * 100],
    "trailing-91-day run-rate $M": [S["runrate_91d"]["total"], S["runrate_91d"]["intents"]],
    "coverage of new supply %": [S["grid"]["1"]["cover@4.28"] * 100, S["grid"]["1"]["bb_cover@4.28"] * 100],
    "X4 volume needed $B a day": [x4["X4_volume_needed_per_day_at_A"] / 1e9, x4["X4_volume_needed_per_day_at_B"] / 1e9],
    "X4 multiple of window B volume": [x4["X4_multiple_of_B_volume_at_A"], x4["X4_multiple_of_B_volume_at_B"]],
    "E2 volume ratio": [E["E2"]["volume_ratio"]],
    "E2 revenue ratio": [E["E2"]["revenue_ratio"]],
    "E2 take rates (bp)": [E["E2"]["take_rate_bp_A"], E["E2"]["take_rate_bp_B"]],
    "F2 call ratio": [E["F2"]["ratio"]],
    "Spearman (E1, E5, F1, X1, and the 0.50/0.60 thresholds)": [E["E1"]["spearman"], E["E5"]["spearman"], E["F1"]["spearman"],
                                  x4["X1_spearman_defillama_rev_vs_blockworks_intents"], E["E1"]["threshold"], E["E5"]["threshold"], E["F1"]["threshold"]],
    "X6 28-day means (signers, transactions)": [x6["active_signers_mean28_asof"], x6["active_signers_mean28_year_earlier"],
                                                x6["transactions_mean28_asof"], x6["transactions_mean28_year_earlier"]],
    "latest 28-day Intents revenue $/day": [S["intents_28d_last"]],
    "pre-surge Intents revenue $/day": [S["phase_intents"]["pre"]],
    "Amendment 7 thresholds $/day": [float(a7_hi.group(1).replace(",", "")), float(a7_lo.group(1).replace(",", ""))],
    "Amendment 7 consecutive days": [float(a7_hi.group(2)), float(a7_lo.group(2))],
}

# ---------- where each figure is recognised (case-insensitive, per line) ----------
N = r"(\d[\d,]*(?:\.\d+)?)"
PAT = [
    ("break-even multiple", rf"the {N}x question"),
    ("break-even multiple", rf"grow (?:about |roughly )?{N} times"),
    ("break-even multiple", rf"{N}x revenue growth needed"),
    ("RUNRATE-MULTIPLE", rf"{N}(?:x| times),? (?:today's|the trailing-91-day|the) (?:revenue )?run-rate"),
    ("break-even revenue $M", rf"(?:break-even|offset|buybacks fully)[^\n]*?\$(\d{{3}})M"),
    ("net new supply $M a year", rf"new (?:token )?supply is worth \${N}M"),
    ("P/S on total revenue", rf"{N}(?:x| times) sales"),
    ("P/S on total revenue", rf"p/s on total {N}x"),
    ("P/S on total revenue", rf"{N}x price to sales on total"),
    ("P/S on gas fees", rf"on gas fees(?: alone)?,? (?:though, )?it is {N} times"),
    ("peer median P/S", rf"peer median (?:of )?{N}"),
    ("buyback share %", rf"{N}% (?:of (?:retained )?intents revenue|buyback share)"),
    ("buyback share %", rf"observed {N}%"),
    ("Intents share of revenue, Oct 2026 %", rf"{N}% of near's protocol revenue"),
    ("Intents share of revenue, Oct 2026 %", rf"{N}% intents share of protocol revenue"),
    ("trailing-91-day run-rate $M", rf"\${N}M(?: a year|/yr)?,? (?:of )?(?:trailing-91-day|run-rate)"),
    ("trailing-91-day run-rate $M", rf"trailing[- ]91-day (?:revenue )?(?:run-rate )?(?:is |of )?(?:about )?\${N}M"),
    ("trailing-91-day run-rate $M", rf"protocol revenue[^\n]{{0,60}}?\(about \${N}M a year\)"),
    ("trailing-91-day run-rate $M", rf"\${N}M/yr protocol revenue"),
    ("coverage of new supply %", rf"cover(?:s|ing)? about {N}%"),
    ("coverage of new supply %", rf"offsetting about {N}%"),
    ("X4 volume needed $B a day", rf"\${N}B a day"),
    ("X4 multiple of window B volume", rf"{N}(?:x| times),? window B's volume"),
    ("E2 volume ratio", rf"volume rose (?:about )?{N}(?:x| times)"),
    ("E2 revenue ratio", rf"revenue (?:rose )?{N}(?:x| times)"),
    ("E2 take rates (bp)", r"(\d+\.\d\d) (?:bp )?to \d+\.\d\d (?:basis points|bp)"),
    ("E2 take rates (bp)", r"\d+\.\d\d (?:bp )?to (\d+\.\d\d) (?:basis points|bp)"),
    ("E2 take rates (bp)", r"(?:window [AB]'s|take rate of) (\d+\.\d\d) (?:basis points|bp)"),
    ("F2 call ratio", rf"calls (?:rose )?(?:only )?(?:about |~)?{N}(?:x| times)"),
    ("Spearman (E1, E5, F1, X1, and the 0.50/0.60 thresholds)", rf"spearman (?:of daily changes )?(\d\.\d+)"),
    ("Spearman (E1, E5, F1, X1, and the 0.50/0.60 thresholds)", rf"rank correlation of (\d\.\d+)"),
    ("X6 28-day means (signers, transactions)", rf"(?:distinct signers|transactions): {N}"),
    ("X6 28-day means (signers, transactions)", rf"against {N} a year earlier"),
    ("X6 28-day means (signers, transactions)", rf"28-day mean (?:of )?{N}"),
    ("X6 28-day means (signers, transactions)", r"at or (?:below|above) (\d{2,3},\d{3})\b"),
    ("latest 28-day Intents revenue $/day", rf"latest(?: 28-day average)?(?: was)?:? \${N}"),
    ("pre-surge Intents revenue $/day", rf"(?:surge|pre-surge level) was \${N}"),
    ("Amendment 7 thresholds $/day", rf"at (?:least|most|or below|or above) \${N}(?: a| per) day"),
    ("Amendment 7 consecutive days", rf"{N} consecutive days"),
]


def num(s):
    return float(s.replace(",", ""))


def agrees(text, canon):
    """True if `text` is `canon` rounded to the precision written (decimals, or trailing zeros of an integer)."""
    v = num(text)
    if "." in text:
        d = len(text.split(".")[1])
        return any(round(c, d) == v for c in canon) or any(abs(round(c, d) - v) < 10 ** -d / 2 + 1e-9 for c in canon)
    z = len(text.replace(",", "")) - len(text.replace(",", "").rstrip("0"))
    return any(round(c, -k) == v for c in canon for k in range(0, min(z, 3) + 1))


def doc_lines(name):
    t = rd(name)
    if name.endswith(".html"):
        t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
        t = html.unescape(re.sub(r"</(p|div|h\d|li|tr)>", "\n", t))
        t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("**", "").replace("`", "")
    return [re.sub(r"[ \t]+", " ", ln) for ln in t.split("\n")]


DOCS = ["THESIS.md", "README.md", "SUBMISSION_DRAFT.md", "PREDICTIONS.md", "SCORECARD.md", "dashboard.html"]
fails, found = [], {}
for doc in DOCS:
    for i, ln in enumerate(doc_lines(doc), 1):
        if doc == "SUBMISSION_DRAFT.md" and ln.startswith("| ") and re.match(r"\| \d+ \|", ln):
            continue  # claims-audit rows quote line references and file names, not claims
        for concept, pat in PAT:
            for m in re.finditer(pat, ln, re.I):
                c = concept
                if c == "RUNRATE-MULTIPLE":
                    before = ln[max(0, m.start() - 80):m.start()].lower()
                    c = "break-even multiple at 100% buybacks (X7)" if any(w in before for w in ("100%", "all revenue", "$137m")) else "break-even multiple"
                    if re.search(r"retained intents run-rate", ln[m.start():m.end() + 30], re.I):
                        continue
                ok = agrees(m.group(1), K[c])
                found.setdefault(c, []).append((doc, i, m.group(1), ok))
                if not ok:
                    fails.append(f"{doc}:{i}: {c}: '{m.group(1)}' does not match {', '.join(f'{x:g}' for x in K[c])} | {ln.strip()[:110]}")

# ---------- verdicts: results files vs every table, card and scorecard section ----------
canon_v = {k: E[k]["verdict"] for k in ("E1", "E2", "E3", "E4", "E5", "F1", "F2")}
canon_v.update({k: SC[k]["verdict"].split(" (Amendment 8c")[0] for k in ("H1", "H2", "H3", "H4", "H5")})
for k in ("E1", "E2", "E3", "E4", "E5", "F1", "F2"):
    if SC[k]["verdict"] != canon_v[k]:
        fails.append(f"scorecard.json: {k} verdict '{SC[k]['verdict']}' differs from extension_numbers.json '{canon_v[k]}'")
vfound = 0
for doc in DOCS:
    raw = rd(doc)
    rows = re.findall(r"^\|\s*([EFH]\d)\s*\|.*\|\s*\*\*(.+?)\*\*(?: \([^|]*\))?\s*\|\s*$", raw, re.M)
    rows += re.findall(r"^## ([EFH]\d): .*?\n(?:.*\n)*?- \*\*Verdict:\*\* \*\*(.+?)\*\*", raw, re.M)
    rows += re.findall(r"<h3>([EFH]\d): .*?<span>Verdict</span> <b>(.*?)</b>", raw)
    for k, v in rows:
        vfound += 1
        v = html.unescape(v).split(" (Amendment 8c")[0]
        if v != canon_v[k]:
            fails.append(f"{doc}: {k} verdict '{v}' differs from the results files '{canon_v[k]}'")
for k, phrase in (("H1", "rejected on all three bases"), ("H4", "not supported")):
    if canon_v[k] != phrase or not re.search(rf"{k} \([^)]*\) was {phrase}", rd("THESIS.md")):
        fails.append(f"THESIS.md: {k} is not described as '{canon_v[k]}'")

# ---------- predictions: each anchor must equal its source ----------
P = rd("PREDICTIONS.md")
anchors = [("P1", f"${S['intents_28d_last']:,}"), ("P1", f"${a7_hi.group(1)} a day"), ("P1", f"{a7_hi.group(2)} consecutive days"),
           ("P2", f"${S['phase_intents']['pre']:,}"), ("P2", f"${a7_lo.group(1)} a day"), ("P2", f"{a7_lo.group(2)} consecutive days"),
           ("P3", f"{E['E2']['take_rate_bp_A']:.2f} bp"), ("P3", f"{E['E2']['take_rate_bp_B']:.2f} bp"),
           ("P4", f"${E['exploratory_X5']['revenue_annualised_defillama'] / 1e6:.1f}M"),
           ("P5", f"{x6['active_signers_mean28_asof']:,.0f}"), ("P5", f"{x6['active_signers_mean28_year_earlier']:,.0f}"),
           ("P6", "0.50"), ("P6", f"{E['F1']['spearman']:.3f}")]
blocks = dict(re.findall(r"\*\*(P\d)\. .*?\*\*\n(.*?)(?=\n\*\*P\d\. |\Z)", P, re.S))
for p, a in anchors:
    if a not in blocks.get(p, ""):
        fails.append(f"PREDICTIONS.md: {p} does not contain the anchor '{a}' from the results files")
if "Spearman(daily S4 call count, daily S1 DefiLlama volume) over at least 120 overlapping days; 0.50 or higher" not in PRE:
    fails.append("PREREGISTRATION.md: Amendment 9's F1 threshold (0.50) not found")

# ---------- interim prediction status: snapshot vs PREDICTIONS.md, dashboard vs snapshot ----------
import track_predictions as TP
PSN = json.loads(rd("predictions_status.json"))
PR = TP.read_predictions()
want = {"P1": [f"${PR['P1']['min']:,.0f} a day", f"{PR['P1']['days']} consecutive days", PR["P1"]["start"], PR["P1"]["end"]],
        "P2": [f"${PR['P2']['max']:,.0f} a day", f"{PR['P2']['days']} consecutive days", PR["P2"]["start"], PR["P2"]["end"]],
        "P3": [f"at or below {PR['P3']['low']:.2f} bp", f"at or above {PR['P3']['high']:.2f} bp", PR["P3"]["start"], PR["P3"]["end"]],
        "P4": [f"below ${PR['P4']['low'] / 1e6:.1f}M", f"at or above ${PR['P4']['high'] / 1e6:.1f}M", f"{PR['P4']['days']} days ending {PR['P4']['end']}"],
        "P5": [f"at or below {PR['P5']['low']:,.0f}", f"at or above {PR['P5']['high']:,.0f}", f"{PR['P5']['days']}-day mean"],
        "P6": [f"at or above {PR['P6']['min']:.2f}", PR["P6"]["start"], PR["P6"]["end"], f"({PR['P6']['window_days']} days)"]}
pstat = 0
TW = TP.threshold_windows()
bw_last = rd("near_daily.csv").strip().splitlines()[-1].split(",")[0]
BW_NOTE = f"DefiLlama series; the ${S['intents_28d_last']:,} in the thesis is Blockworks data to {bw_last}."
if PSN.get("label") != TP.LABEL:
    fails.append(f"predictions_status.json: label is '{PSN.get('label')}', not '{TP.LABEL}'")
snap = {p["id"]: p for p in PSN["predictions"]}
if sorted(snap) != sorted(want):
    fails.append(f"predictions_status.json: expected P1 to P6, found {sorted(snap)}")
dash = rd("dashboard.html")
sec = dash[dash.find("8. Where the predictions stand today"):] if "8. Where the predictions stand today" in dash else ""
if not sec:
    fails.append("dashboard.html: section 'Where the predictions stand today' not found")
for need in (f"Snapshot of {PSN['snapshot_date']}", html.escape(TP.LABEL)):
    if sec and need not in sec:
        fails.append(f"dashboard.html: predictions section does not show '{need}'")
for k, items in want.items():
    p = snap.get(k, {})
    if p.get("title") != PR[k]["title"] or p.get("resolution_date") != PR[k]["resolution_date"]:
        fails.append(f"predictions_status.json: {k} title or resolution date differs from PREDICTIONS.md")
    for it in items:
        pstat += 1
        if it not in p.get("threshold", ""):
            fails.append(f"predictions_status.json: {k} threshold '{p.get('threshold')}' does not contain '{it}' from PREDICTIONS.md")
    if p.get("status") not in ("on track", "not yet", "cannot resolve", TP.BASELINE):
        fails.append(f"predictions_status.json: {k} status '{p.get('status')}' is not one of the four allowed")
    tw = TW.get(k)
    pstat += 1
    if tw and p.get("as_of", "9999") <= tw[1] and (p.get("status") != TP.BASELINE or tw[1] not in p.get("note", "")):
        fails.append(f"predictions_status.json: {k} threshold was set from data to {tw[1]} and the reading ends {p.get('as_of')}: status must be '{TP.BASELINE}' with a note")
    if p.get("status") == TP.BASELINE and not (tw and p.get("as_of", "") <= tw[1]):
        fails.append(f"predictions_status.json: {k} is labelled baseline but its reading includes new data")
    card = re.search(rf'<h3>{k}: .*?</div>', sec, re.S)
    if k in ("P1", "P2"):
        pstat += 1
        if not card or html.escape(BW_NOTE) not in card.group(0):
            fails.append(f"dashboard.html: {k} card does not show the note '{BW_NOTE}'")
    for field in ("threshold", "current_value", "status", "as_of", "note"):
        if field == "note" and not p.get("note"):
            continue
        pstat += 1
        if not card or html.escape(str(p.get(field))) not in card.group(0):
            fails.append(f"dashboard.html: {k} card does not show the snapshot's {field} '{p.get(field)}'")

# ---------- README expected output vs the built dashboard ----------
# build_dashboard.py prints len(html) as "dashboard.html written N bytes"; rd() reads with universal newlines,
# so this is the same count on Windows (CRLF on disk) and Linux.
dash_len = len(rd("dashboard.html"))
readme_sizes = re.findall(r"dashboard\.html written (\d+) bytes", rd("README.md"))
if not readme_sizes:
    fails.append("README.md: expected-output line 'dashboard.html written N bytes' not found")
for n in readme_sizes:
    if int(n) != dash_len:
        fails.append(f"README.md: expected output says 'dashboard.html written {n} bytes' but the built dashboard.html is {dash_len}")

# ---------- report ----------
print(f"Consistency check: {sum(len(v) for v in found.values())} figure mentions and {vfound} verdicts in {len(DOCS)} documents; "
      f"{len(anchors)} prediction anchors; {pstat} interim-status checks (snapshot {PSN['snapshot_date']}).")
for c in K:
    hits = found.get(c, [])
    print(f"   {c}: {len(hits)} mentions" + (f", all agree with {', '.join(f'{x:g}' for x in K[c])}" if hits and all(h[3] for h in hits) else ""))
    if VERBOSE:
        for doc, i, v, ok in hits:
            print(f"      {'ok  ' if ok else 'FAIL'} {doc}:{i} {v}")
if fails:
    print(f"\nFAIL: {len(fails)} mismatch(es):")
    for f in fails:
        print("   " + f)
    sys.exit(1)
print("All key figures, verdicts and prediction anchors agree across documents.")
print(f"README expected output matches the built dashboard.html ({dash_len} bytes, line endings normalised).")
print(f"Interim prediction status: predictions_status.json uses the PREDICTIONS.md thresholds and the dashboard shows the {PSN['snapshot_date']} snapshot.")
