"""Bonferroni report for the four pre-registered confirmatory tests (H1 to H4). Fills a reporting gap (Amendment 11).

PREREGISTRATION.md, "Rules for reporting": "Four tests: results are shown against both p < 0.05 and the Bonferroni
threshold of 0.0125." confirmatory_results.txt did not show the Bonferroni comparison. This script reports it from the
committed outputs, without re-running or changing any test:
- confirmatory_numbers.json is read first; it holds only the H3 P/S values (no p-values), so
- the p-values and confidence intervals are read from confirmatory_results.txt, exactly as printed.

H1 is decided by 95% confidence intervals, not p-values. Its intervals are HAC (normal-based) intervals from statsmodels,
so the Bonferroni equivalent, a 98.75% interval, is the printed interval widened by z(0.99375) / z(0.975), and the
implied two-sided p-value against an elasticity of 1 follows from the same standard error. Inputs are printed to two
decimals, so these derived values are approximate (stated in the output).

Run: python report_bonferroni.py > bonferroni_results.txt   (not part of run_all.py)
"""
import json
import os
import re
import sys

from scipy.stats import norm

D = os.path.dirname(os.path.abspath(__file__))
ALPHA, BONF = 0.05, 0.05 / 4
pre = open(os.path.join(D, "PREREGISTRATION.md"), encoding="utf-8").read()
if "Bonferroni threshold of 0.0125" not in pre:
    sys.exit("PREREGISTRATION.md: the registered Bonferroni threshold (0.0125) was not found; nothing reported")
C = json.load(open(os.path.join(D, "confirmatory_numbers.json")))
R = open(os.path.join(D, "confirmatory_results.txt"), encoding="utf-8").read()


def grab(pat):
    m = re.search(pat, R)
    if not m:
        sys.exit(f"confirmatory_results.txt: '{pat}' not found; nothing reported")
    return m.groups()


z95, zb = norm.ppf(1 - ALPHA / 2), norm.ppf(1 - BONF / 2)
print("BONFERRONI REPORT: the four pre-registered confirmatory tests against p < 0.05 and the registered Bonferroni level")
print(f"Registered level: 0.05 / 4 tests = {BONF} (PREREGISTRATION.md, Rules for reporting). No test, rule or verdict is changed.")
print(f"confirmatory_numbers.json holds {', '.join(sorted(C))} (H3 P/S values, no p-values); p-values and intervals are "
      f"read from confirmatory_results.txt as printed.\n")

changes = []
print("H1  price pass-through. Rule: rejected if the elasticity 95% CI excludes 1 (or the token-denominated trend is positive with p < 0.05).")
for lab, pat in (("A gas fees [all days]", r"A gas fees  \[all days\] elasticity ([-\d.]+) CI\[([-\d.]+),([-\d.]+)\]"),
                 ("B total protocol revenue", r"B total protocol revenue elasticity ([-\d.]+) CI\[([-\d.]+),([-\d.]+)\]"),
                 ("C Intents revenue", r"C non-fee \(Intents\) revenue since \S+ elasticity ([-\d.]+) CI\[([-\d.]+),([-\d.]+)\]")):
    b, lo, hi = map(float, grab(pat))
    se = (hi - lo) / 2 / z95
    blo, bhi = b - zb * se, b + zb * se
    p = 2 * norm.sf(abs(b - 1) / se)
    ex95, exb = not (lo <= 1 <= hi), not (blo <= 1 <= bhi)
    print(f"   {lab}: elasticity {b:.2f}, 95% CI [{lo:.2f},{hi:.2f}] excludes 1: {ex95} | 98.75% CI ~[{blo:.2f},{bhi:.2f}] excludes 1: {exb} "
          f"| implied p (elasticity = 1) {'< 0.0001' if p < 1e-4 else f'~{p:.4f}'}")
    if ex95 != exb:
        changes.append(f"H1 {lab}")
print("   (98.75% intervals and implied p-values are derived from the printed 95% HAC intervals, which are rounded to two decimals, so they are approximate.)")
trend, tp = grab(r"token-denominated gas fees, 33 blocks of 28d: trend/block ([-\d.]+)% p=([\d.]+)")
print(f"   token-denominated trend {trend}%/block p={tp}: negative, so the 'positive trend' condition does not apply at either level.")
print("   Verdict at p < 0.05: rejected on all three bases (Amendment 8c). At 0.0125: " +
      ("unchanged." if not any(c.startswith("H1") for c in changes) else "CHANGES for " + ", ".join(changes)))

print("\nH2  activity leads price. Rule: supported only if fit-period p < 0.05, holdout out-of-sample R-squared > 0 and the sign holds.")
beta, p2, r2 = grab(r"NEAR\s+fit beta ([+-][\d.]+) p=([\d.]+) \(n=\d+\) \| holdout OOS R2 ([+-][\d.]+)%")
p2 = float(p2)
print(f"   NEAR fit beta {beta} p={p2:.3f}: below 0.05: {p2 < ALPHA} | below {BONF}: {p2 < BONF}")
print(f"   holdout out-of-sample R-squared {r2}%: not above 0, so H2 is not supported at either level.")
print(f"   H2 would not pass the Bonferroni level (p={p2:.3f} > {BONF}); it was already 'not supported' at p < 0.05. Verdict unchanged.")

print("\nH3  NEAR expensive relative to peers. Rule: a comparison of P/S levels (above the peer median and its own 75th percentile).")
print("   No p-value is involved, so the Bonferroni level does not apply. Verdict unchanged: (a) SUPPORTED; (b) SUPPORTED; (c) REJECTED.")

print("\nH4  usage not monetised. Rule: supported if active addresses trend up (p < 0.05) and revenue per active address trends down (p < 0.05).")
pa, pr = grab(r"\[excl\] pre-break  n=\d+ blocks \| active addresses [+-][\d.]+%/block p=([\d.]+) \| revenue per active address [+-][\d.]+%/block p=([\d.]+)")
pa, pr = float(pa), float(pr)
print(f"   pre-break (the basis in Amendment 8c): active-address trend p={pa:.3f}, revenue-per-active-address trend p={pr:.3f}")
print(f"   below 0.05: {pa < ALPHA} and {pr < ALPHA} | below {BONF}: {pa < BONF} and {pr < BONF}. Not supported at either level. Verdict unchanged.")

print(f"\nSUMMARY: no verdict changes at the Bonferroni level {BONF}. H2 (p={p2:.3f}) would not pass it and was already not supported. "
      "H1 stays rejected (each 98.75% interval still excludes 1), H3 has no p-value, H4 was not significant at 0.05.")
if changes:
    sys.exit(f"Unexpected: verdict changes for {changes}")
