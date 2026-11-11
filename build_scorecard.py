"""Verdict scorecard for H1-H5 and E1-E5, generated from the results files (no typed numbers).

Thresholds are quoted from PREREGISTRATION.md (H1-H5) and from the "rule:" lines of extension_results.txt (E1-E5).
Results and verdicts are copied from confirmatory_results.txt and extension_results.txt. Where a results file prints
no verdict line (H1, H4), the scorecard says so and quotes the verdict as worded in THESIS.md, labelled as such.
Writes scorecard.json (read by build_dashboard.py) and the block between the scorecard markers in README.md.
"""
import json
import os
import re

D = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: open(os.path.join(D, f), encoding="utf-8").read()
CONF, EXT, PRE, THESIS = rd("confirmatory_results.txt"), rd("extension_results.txt"), rd("PREREGISTRATION.md"), rd("THESIS.md")


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
                 verdict="no verdict line in confirmatory_results.txt; THESIS.md: " + grab(THESIS, r"H1 \(revenue is price pass-through\) was (rejected[^.]*)\."),
                 source="confirmatory_results.txt (H1); THESIS.md"))
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
                 verdict="no verdict line in confirmatory_results.txt; THESIS.md: " + grab(THESIS, r"H4 \(usage not monetised\) was (not supported)"),
                 source="confirmatory_results.txt (H4); THESIS.md"))
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

json.dump(rows, open(os.path.join(D, "scorecard.json"), "w", encoding="utf-8", newline="\n"), indent=1)

md = ["<!-- scorecard:start (generated by build_scorecard.py from the results files; do not edit by hand) -->",
      "**Verdict scorecard.** H1 to H5 are the confirmatory tests and E1 to E5 the public-source cross-checks. Thresholds are quoted from the pre-registration, and results and verdicts are copied from the results files.", ""]
for r in rows:
    md += [f"- **{r['id']}: {r['claim']}**",
           f"  - Threshold: {r['threshold']}",
           f"  - Result: {r['result']}",
           f"  - Verdict: **{r['verdict']}** ({r['source']})"]
md.append("<!-- scorecard:end -->")
readme = rd("README.md")
new = re.sub(r"<!-- scorecard:start.*?<!-- scorecard:end -->", lambda _: "\n".join(md), readme, flags=re.S)
if new == readme and "<!-- scorecard:start" not in readme:
    raise SystemExit("scorecard: README markers not found")
open(os.path.join(D, "README.md"), "w", encoding="utf-8", newline="\n").write(new)
print(f"scorecard: {len(rows)} rows written to scorecard.json and README.md")
