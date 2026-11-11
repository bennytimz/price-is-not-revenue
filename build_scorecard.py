"""Verdict scorecard for H1-H5, E1-E5 and F1-F2, generated from the results files (no typed numbers).

Thresholds are quoted from PREREGISTRATION.md (H1-H5) and from the "rule:" lines of extension_results.txt (E1-E5, F1-F2).
Results and verdicts are copied from confirmatory_results.txt and extension_results.txt. confirmatory_results.txt
prints no verdict line for H1 or H4; their verdicts are taken from PREREGISTRATION.md Amendment 8c, which applies the
written H1 and H4 rules to the printed numbers. In the scorecard only, p-values printed as 0.000 are shown as p<0.001.
Writes scorecard.json (read by build_dashboard.py) and the block between the scorecard markers in README.md.
"""
import json
import os
import re

D = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: open(os.path.join(D, f), encoding="utf-8").read()
CONF, EXT, PRE = rd("confirmatory_results.txt"), rd("extension_results.txt"), rd("PREREGISTRATION.md")
_a8c = PRE.split("## Amendment 8c", 1)
if len(_a8c) != 2:
    raise SystemExit("scorecard: Amendment 8c not found in PREREGISTRATION.md")
A8C = _a8c[1]  # verdict wording for H1 and H4, which confirmatory_results.txt does not print


def line(text, pattern):
    m = re.search(pattern, text, re.M)
    if not m:
        raise SystemExit(f"scorecard: pattern not found: {pattern}")
    return m.group(0).strip()


def grab(text, pattern, group=1):
    m = re.search(pattern, text, re.M | re.S)
    if not m:
        raise SystemExit(f"scorecard: pattern not found: {pattern}")
    return " ".join(m.group(group).split())


def pre_rule(h):  # the decision-rule line under "**Hn. ...**" in PREREGISTRATION.md
    return grab(PRE, rf"\*\*{h}\..*?\*\*\nTest:.*?\n(.*?)\n")


def ext_rule(e):  # "rule:" line(s) of test e in extension_results.txt, continuation lines joined
    return grab(EXT, rf"^{e} \(pre-registered.*?\n\s+rule: (.*?)\n(?=\s+(?:days|window|usage|before)\b)")


def ext_verdict(e):
    return grab(EXT, rf"VERDICT {e}: (.*?)$")


rows = []
# ---- H1 (no verdict line in confirmatory_results.txt) ----
h1 = [grab(CONF, r"^A gas fees  \[all days\] (elasticity [^|]*?)\s*\|"), grab(CONF, r"^B total protocol revenue (elasticity .*?) n="),
      grab(CONF, r"^C non-fee \(Intents\) revenue since \S+ (elasticity .*?) n="), grab(CONF, r"^A token-denominated gas fees, .*?: (trend/block \S+ p=\S+)")]
rows.append(dict(id="H1", claim="USD revenue growth is mostly the NEAR price passing through.", threshold=pre_rule("H1"),
                 result=f"gas fees {h1[0]}; total revenue {h1[1]}; Intents revenue {h1[2]}; token-denominated gas fees {h1[3]}",
                 verdict=grab(A8C, r"H1: (rejected on all three bases)") + " (Amendment 8c applies the H1 rule to the printed numbers)",
                 source="confirmatory_results.txt (H1); PREREGISTRATION.md Amendment 8c"))
# ---- H2 ----
near = line(CONF, r"^NEAR\s+fit beta.*$")
peers = re.findall(r"^(?:APT|AVAX|ETH|SOL|SUI)\s+fit beta.*meets all conditions: (\w+)$", CONF, re.M)
rows.append(dict(id="H2", claim="On-chain activity leads the NEAR price.", threshold=pre_rule("H2"),
                 result="NEAR " + " ".join(near.split()[1:]).split(" | meets")[0] + f"; peers meeting all conditions: {peers.count('True')} of {len(peers)}",
                 verdict="meets all conditions: " + grab(near, r"meets all conditions: (\w+)"), source="confirmatory_results.txt (H2)"))
# ---- H3 ----
h3 = re.findall(r"^\s+\((a|b|c)\) (.*?) -> (SUPPORTED|REJECTED)$", CONF, re.M)
rows.append(dict(id="H3", claim="NEAR is expensive relative to peers.", threshold=pre_rule("H3"),
                 result="; ".join(f"({k}) {t}" for k, t, _ in h3), verdict="; ".join(f"({k}) {v}" for k, _, v in h3),
                 source="confirmatory_results.txt (H3)"))
# ---- H4 (no verdict line) ----
rows.append(dict(id="H4", claim="NEAR usage is not being monetised.", threshold=pre_rule("H4"),
                 result=grab(CONF, r"^\[excl\] (pre-break .*?)$") + " (Blockworks active addresses, before the 2026-04-02 definition break)",
                 verdict=grab(A8C, r"H4: (not supported)") + " (Amendment 8c applies the H4 rule to the printed numbers)",
                 source="confirmatory_results.txt (H4); PREREGISTRATION.md Amendment 8c"))
# ---- H5 (descriptive) ----
h5 = re.findall(r"^(\d{4}-\d{2}-\d{2}): trailing-90d annualised revenue .*? -> (\d+%)$", CONF, re.M)
rows.append(dict(id="H5", claim="Retained revenue covers only a small fraction of the value of new token supply.",
                 threshold=grab(PRE, r"^- H5: .*?(Supported if [^.]*\.)") + " Amendment 7: " + grab(PRE, r"(reported as descriptive, not as a test)"),
                 result="revenue / net new supply: " + ", ".join(f"{d} {p}" for d, p in h5),
                 verdict=grab(CONF, r"^==== H5 \((descriptive)\)"), source="confirmatory_results.txt (H5); PREREGISTRATION.md Amendment 7"))
# ---- E1-E5 ----
claims = {"E1": "Blockworks Intents revenue tracks DefiLlama Intents volume, so it is a fair proxy for Intents activity.",
          "E2": "The Sep-Oct revenue jump came from volume rather than the take rate.",
          "E3": "Intents volume leads on-chain usage better than the NEAR price does.",
          "E4": "The 2026-04-02 drop in Blockworks active addresses is real on chain.",
          "E5": "Blockworks active addresses and on-chain signers measure the same thing."}
results = {"E1": grab(EXT, r"^\s+(days \d+ \(.*?\) \| Spearman \S+)$"),
           "E2": grab(EXT, r"^\s+(volume ratio .*?)$") + "; take rate " + " to ".join(re.findall(r"^\s+window [AB]: .*?take rate (\S+ bp)", EXT, re.M)),
           "E3": grab(EXT, r"^\s+(rho volume .*?) \(\d+ draws"),
           "E4": grab(EXT, r"^\s+before 2026-03-05.*?\| (drop \S+)$") + " in on-chain distinct signers (Blockworks active addresses: "
                 + grab(EXT, r"X2 Blockworks active addresses .*?\| (drop \S+)$") + ", exploratory X2)",
           "E5": grab(EXT, r"^\s+(days \d+ of daily changes .*?Spearman \S+)$")}
for e in ("E1", "E2", "E3", "E4", "E5"):
    rows.append(dict(id=e, claim=claims[e], threshold=ext_rule(e), result=results[e], verdict=ext_verdict(e),
                     source=f"extension_results.txt ({e})"))
# ---- F1-F2 (Amendment 9) ----
claims = {"F1": "Daily calls to the Intents settlement contract (intents.near) track DefiLlama Intents volume.",
          "F2": "On-chain Intents calls rose with the Sep-Oct revenue jump."}
results = {"F1": grab(EXT, r"^F1 \(pre-registered.*?^\s+(days \d+ \(.*?\) \| Spearman \S+)$"),
           "F2": grab(EXT, r"^\s+(window A mean .*? calls/day.*?ratio \S+)$")}
for e in ("F1", "F2"):
    rows.append(dict(id=e, claim=claims[e], threshold=ext_rule(e), result=results[e], verdict=ext_verdict(e),
                     source=f"extension_results.txt ({e}); PREREGISTRATION.md Amendment 9"))

# Display only: a p-value printed as 0.000 means it rounds to zero at three decimals, so show it as p<0.001
for r in rows:
    r["result"] = re.sub(r"p=0\.000\b", "p<0.001", r["result"])

json.dump(rows, open(os.path.join(D, "scorecard.json"), "w", encoding="utf-8", newline="\n"), indent=1)

# ---- full scorecard: SCORECARD.md ----
full = ["# Verdict scorecard", "",
        "*Generated by `build_scorecard.py` from `confirmatory_results.txt`, `extension_results.txt` and `PREREGISTRATION.md`; do not edit by hand.*", "",
        "H1 to H5 are the confirmatory tests, E1 to E5 the public-source cross-checks (Amendment 8) and F1 to F2 the intents.near contract checks (Amendment 9). Thresholds are quoted from the pre-registration; results and verdicts are copied from the results files (H1 and H4 verdicts from Amendment 8c). In this scorecard, p-values printed as 0.000 are shown as p<0.001.", ""]
for r in rows:
    full += [f"## {r['id']}: {r['claim']}", "", f"- **Threshold:** {r['threshold']}", f"- **Result:** {r['result']}",
             f"- **Verdict:** **{r['verdict']}**", f"- **Source:** {r['source']}", ""]
open(os.path.join(D, "SCORECARD.md"), "w", encoding="utf-8", newline="\n").write("\n".join(full))

# ---- compact table for README: one key result per row, extracted from the result text (no typed numbers) ----
KEY = {"H1": lambda s: "elasticity 95% CIs: " + ", ".join(re.findall(r"CI(\[[^\]]+\])", s)),
       "H2": lambda s: "NEAR holdout " + grab(s, r"(OOS R2 \S+)"),
       "H3": lambda s: (lambda m: f"NEAR {m[0]} on gas fees (a), {m[2]} on total revenue (c); peer median " + grab(s, r"peer median (\d+x)"))(re.findall(r"NEAR (\d+x) vs", s)),
       "H4": lambda s: "active " + grab(s, r"active addresses (\S+ p=\S+)") + "; revenue/address " + grab(s, r"revenue per active address (\S+ p=\S+)"),
       "H5": lambda s: ", ".join(re.findall(r"(\d+%)", s)),
       "E1": lambda s: grab(s, r"(Spearman \S+)"), "E2": lambda s: grab(s, r"(volume share [-+]?[\d.]+\d)"),
       "E3": lambda s: grab(s, r"(difference \S+)"), "E4": lambda s: "signers " + grab(s, r"^(drop \S+)"),
       "E5": lambda s: grab(s, r"(Spearman \S+)"), "F1": lambda s: grab(s, r"(Spearman \S+)"),
       "F2": lambda s: "calls B/A " + grab(s, r"ratio (\S+)")}
esc = lambda s: s.replace("|", "\\|")
md = ["<!-- scorecard:start (generated by build_scorecard.py from the results files; do not edit by hand) -->",
      "**Verdict scorecard** (full thresholds and sources: [SCORECARD.md](SCORECARD.md))", "",
      "| ID | Claim | Key result | Verdict |", "|---|---|---|---|"]
for r in rows:
    verdict = r["verdict"].split(" (Amendment 8c")[0] + (" (Amendment 8c)" if "Amendment 8c" in r["verdict"] else "")
    md.append(f"| {r['id']} | {esc(r['claim'])} | {esc(KEY[r['id']](r['result']))} | **{esc(verdict)}** |")
md.append("<!-- scorecard:end -->")
readme = rd("README.md")
new = re.sub(r"<!-- scorecard:start.*?<!-- scorecard:end -->", lambda _: "\n".join(md), readme, flags=re.S)
if new == readme and "<!-- scorecard:start" not in readme:
    raise SystemExit("scorecard: README markers not found")
open(os.path.join(D, "README.md"), "w", encoding="utf-8", newline="\n").write(new)
print(f"scorecard: {len(rows)} rows written to scorecard.json, SCORECARD.md and README.md")
