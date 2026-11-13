# Submission draft (not posted, not submitted)

Drafts for Benny to review. Nothing here has been posted or submitted. Placeholders in square brackets are for Benny to fill in.

## (a) X post

**Main post** (257 characters in the intended case: the video uploaded directly to X, which adds no characters, and [REPO LINK] as a link, which X counts as 23 characters; this case must stay under 270. For information: 253 as written with both placeholders; 281 if the video were also a link, which is over X's 280 limit, so upload the video to X):

> Does revenue back NEAR's price? Tests written down in advance, cross-checked on public data: NEAR is an option on Intents revenue, not cash flow. Revenue must grow ~9.4x before buybacks offset new supply. @NEARProtocol #NEARHackathon [VIDEO] [REPO LINK]

**Optional reply thread** (208, 275, 241 and 207 characters; X's limit is 280):

> 1/ The numbers: retained Intents revenue was 92% of NEAR's protocol revenue in Oct 2026. New supply is worth $137M/yr at $4.28; trailing-91-day revenue is $20.3M/yr. Buybacks offset dilution only at $191M/yr.

> 2/ Public cross-checks (DefiLlama, NEAR BigQuery), pre-registered before each pull: the Sep-Oct revenue jump was mixed. Volume rose 1.63x and revenue 3.20x, but intents.near contract calls only ~1.16x (calls track volume, Spearman 0.774; one call can settle several intents).

> 3/ What failed: Intents volume did not lead on-chain usage better than price (E3), and Blockworks active addresses don't match on-chain signers (E5). Their 89.4% drop on 2026-04-02 is probably a definition change: on-chain signers fell 8.1%.

> 4/ Data note: the baseline is Blockworks data (re-pulling it needs a Blockworks API key). Revenue is cross-checked against DefiLlama (0.998), and the on-chain data re-pulls from BigQuery with an exact match.

## (b) Project description for the form field "What did you build?"

1,991 characters (the field takes 20 to 2,000).

```
Price Is Not Revenue: the 9.4x Question asks whether NEAR Intents revenue can carry NEAR's valuation. Every result is reported, including failures. The original hypotheses were written before the confirmatory data was analysed, but the repository came later, so git history can't prove that order. The public-data extension tests (E1 to E5) are different: they were committed to git (Amendment 8, commit 30ea2ce) before the DefiLlama and BigQuery data was pulled.

Main finding: NEAR is best treated as an option on Intents revenue, not a business valued on cash flow. Retained Intents revenue was 92% of NEAR's protocol revenue in October 2026. But new token supply is worth $137M a year at $4.28, against $20.3M a year of trailing-91-day revenue, so buybacks offset dilution only if revenue reaches $191M a year, 9.4 times today's run-rate.

Public-source cross-checks, pre-registered before the data was pulled, use DefiLlama and NEAR's public BigQuery dataset. The September-October revenue jump was mixed: the take rate went from 2.61 to 5.13 basis points. Daily calls to the intents.near settlement contract track volume (Spearman 0.774) but rose only about 1.16x while volume rose 1.63x and revenue 3.20x (F1, F2; one call can settle several intents). Two tests failed: Intents volume did not lead on-chain usage better than price (E3), and Blockworks active addresses are inconsistent with on-chain signers (E5). Blockworks' 89.4% drop in active addresses on 2026-04-02 is probably a definition change, since on-chain signers fell 8.1% (E4). An exploratory check finds DefiLlama's Intents revenue totals 0.998 of Blockworks' figure.

Everything rebuilds with one command (python run_all.py), and each dashboard chart links the script and data behind it. Six dated predictions resolve on 2027-03-31. Limits: one market regime, an Intents volume series whose definition DefiLlama does not document, and Blockworks data that needs an API key to re-pull. Research, not investment advice.
```

## (c) Claims audit

Line numbers refer to commit `T10: judges summary and submission draft`.

| # | Claim (used in) | Supporting file and line |
|---|---|---|
| 1 | NEAR is an option on Intents revenue, not a cash-flow story (a, b) | `THESIS.md:5` (the thesis statement; an interpretation of rows 5 to 8) |
| 2 | The original hypotheses were written down before the confirmatory data was analysed, but the repository was created afterwards, so git history can't prove that order (a "tests written down in advance", b) | `PREREGISTRATION.md:1` onward (dated amendments); `THESIS.md:129` ("The repository was created after the baseline analysis, so git history cannot prove that order") |
| 3 | Every result is reported, including failures (b) | `PREREGISTRATION.md:38` (Rules for reporting); failures in rows 11 to 13 below |
| 4 | Retained Intents revenue was 92% of protocol revenue in October 2026 (a thread 1, b) | `scenarios_results.txt:18` (share_intents 0.92) |
| 5 | New supply is worth $137M a year at $4.28 (a thread 1, b) | `scenarios_results.txt:30` |
| 6 | Trailing-91-day revenue is $20.3M a year (a thread 1, b) | `scenarios_results.txt:26` |
| 7 | Buybacks offset dilution only at $191M a year, 9.4 times the run-rate (a, b) | `scenarios_results.txt:43` |
| 8 | The cross-checks use DefiLlama and NEAR's public BigQuery dataset (a thread 2, b) | `extension_results.txt:2`; `pull_defillama_intents.py`; `pull_bigquery_daily_usage.sql` |
| 9 | The extension tests E1 to E5 were committed to git (Amendment 8, commit 30ea2ce) before the DefiLlama and BigQuery data was pulled (a thread 2, b) | `PREREGISTRATION.md:199` (Amendment 8); `git log`: `30ea2ce` (Amendment 8, 2026-11-11T19:30:13+01:00) precedes the commits that added the data, `035462b` (DefiLlama, 20:23:11+01:00) and `51212bb` (BigQuery, 20:25:56+01:00); these two hashes changed when the raw DefiLlama files were purged from history (Amendment 8b), with dates preserved. Git records commit times, not pull times: the DefiLlama pull ran at 2026-11-11T19:22:58Z (20:22:58+01:00, printed by `pull_defillama_intents.py`); the BigQuery console run time is not recorded in the repo (Benny can confirm it in BigQuery's query history) |
| 10 | Sep-Oct jump mixed: take rate 2.61 to 5.13 bp (b); volume rose 1.63x and revenue 3.20x (a thread 2, b; rounded from 1.627 and 3.204) | `extension_results.txt:12-15` (E2) |
| 11 | E3 failed: volume did not lead on-chain usage better than price (a thread 3, b) | `extension_results.txt:21,23` |
| 12 | E5 failed: Blockworks active addresses inconsistent with on-chain signers (a thread 3, b) | `extension_results.txt:33-34` |
| 13 | Blockworks active addresses dropped 89.4% on 2026-04-02 (a thread 3, b) | `extension_results.txt:38` (X2, exploratory) |
| 14 | On-chain signers fell 8.1%, so the drop is probably a definition change (a thread 3, b) | `extension_results.txt:28-29` (E4) |
| 15 | DefiLlama's Intents revenue totals 0.998 of Blockworks' (b, labelled exploratory) | `extension_results.txt:37` (X1) |
| 16 | Everything rebuilds with `python run_all.py` from files in the repo (b) | `run_all.py`; `README.md:47` |
| 17 | Each dashboard chart names the script and data behind it (b) | `dashboard_template.html`, the `class="src"` line under each chart |
| 18 | Limit: one market regime (b) | `THESIS.md:125` |
| 19 | Limit: DefiLlama does not document its Intents volume definition (b) | `THESIS.md:121`; the `methodology` field is empty in DefiLlama's `/summary/dexs/near-intents` response (pulled locally by `pull_defillama_intents.py`, which flags it; the raw file is not redistributed) |
| 20 | Limit: Blockworks data needs an API key to re-pull (b) | `THESIS.md:129` |
| 21 | Research, not investment advice (b) | `THESIS.md:7` |
| 22 | Daily `intents.near` settlement-contract calls track Intents volume, Spearman 0.774 (a thread 2, b) | `extension_results.txt:40-41` (F1); `PREREGISTRATION.md` Amendment 9 |
| 23 | Calls rose only about 1.16x from window A to window B (a thread 2, b; rounded from ratio 1.157), and one call can settle several intents | `extension_results.txt:46-47` (F2); the caveat is quoted from Amendment 9 |
| 24 | The S4 tests were pre-registered before the pull (a thread 2 "before each pull", b) | The Amendment 9 commit `f7667df` was committed at 2026-11-12T00:31:34 Lagos time (+01:00) and pushed within seconds. The S4 query text did not exist until it was given to Benny after that push. The CSV was saved at 00:34:46 Lagos time (23:34:46 UTC). BigQuery's query history was not checked, so this order rests on the conversation timeline and is not independently verifiable from the repo. The pull commit `5434954` is 00:44:56+01:00 |
| 25 | On-chain usage fell: 28-day distinct signers 62,660 vs 261,846 a year earlier (-76.1%), -96.9% from the 2024-07-06 peak; transactions -85.2% year on year, -92.2% from the 2025-01-01 peak; separate from the 2026-04-02 Blockworks break (THESIS only, exploratory X6; not yet in a or b) | `extension_results.txt:61-63` (X6); separation from the break: `extension_results.txt:28-29` (E4, signers fell 8.1%) |
| 26 | The 9.4x break-even assumes the observed 72% buyback share; at 100% it is $137M a year, 6.7x the run-rate (THESIS only, exploratory X7; not yet in a or b) | `extension_results.txt:64-65` (X7); `scenarios_results.txt:31` (buyback share 0.72) and `:43` (9.4x, $191M) |
| 27 | "My call": NEAR's protocol revenue, mostly retained Intents revenue (about $20M a year), covers about 15% of the value of new token supply; do not value NEAR on cash flow until revenue approaches about $191M a year (9.4x) (THESIS and README top; an opinion, not in a or b) | `THESIS.md:3`, `README.md:5`; $20.3M total run-rate `scenarios_results.txt:26` (retained Intents alone is $18.9M, same line); 15% coverage at $4.28 `scenarios_results.txt:37`; $191M and 9.4x `scenarios_results.txt:43`; thresholds in `THESIS.md` "What would change my mind" and `PREDICTIONS.md` |
| 28 | Bull case: revenue must reach $191M a year (9.4x) at the observed 72% buyback share, or $137M (6.7x) at 100%; $191M needs about $1.02B a day of Intents volume at window B's take rate, 6.3x window B's volume (THESIS:23) | `scenarios_results.txt:43` (9.4x, $191M), `:31` (0.72); `extension_results.txt:64-65` (X7); `:58` (X4, window B) |
| 29 | Bear case: at window A's 2.61 bp the same revenue needs $2.01B a day, 12.5x window B's volume (THESIS:24) | `extension_results.txt:12` (2.61 bp), `:57` (X4, window A) |
| 30 | Valuation: 276x sales on total revenue, below the peer median of 647x; 3,928x on gas fees alone (THESIS:25) | `confirmatory_results.txt:29-30`, `:33`, `:35` (H3) |
| 31 | Dashboard tiles: $20.3M/yr run-rate, 9.4x, 276x, 92% Intents share in Oct 2026 (read from `scenario_numbers.json` by `build_dashboard.py`) | `scenarios_results.txt:26` ($20.3M, 276x), `:43` (9.4x), `:18` (0.92) |
| 32 | Six dated forward predictions (P1 to P6), resolved on 2027-03-31 and published whatever the outcome (b) | `PREDICTIONS.md`; `PREREGISTRATION.md` Amendment 10; both committed together in `808c329` (2026-11-12T02:10:07+01:00). Anchors: `scenarios_results.txt:47-48`, `extension_results.txt:12-13`, `:40`, `:50`, `:60`, `:62`; P4's upper threshold is a judgement call |
| 33 | All Blockworks data was pulled through ChatGPT's Blockworks MCP with fixed rules (raw CSV only, no interpolation, gaps blank, row count and sum reported); every raw file matches its recorded row count and sum (not yet in a or b) | `DATA_PROVENANCE.md` (verbatim prompts; peer files match prompt B by their headers); `SOURCE_TOTALS.json`; `verify_data.py` ("All data checks passed.") |
| 34 | The BigQuery series can be re-pulled and the re-pull matches the committed pulls (a thread 4) | `pull_bigquery.py`; README reproduce section. Run on 2026-11-12: dry run 132.3 GB (`pull_bigquery_daily_usage.sql`) and 125.9 GB (`pull_bigquery_intents_contract.sql`), both under the 150 GB cap and both with the end date capped at 2026-11-04; `--run` printed MATCH for both (1,039 and 673 rows, identical first and last dates, identical column sums, 0 differing days). The re-pull files (`repull_*.csv`) are git-ignored, not committed |
| 35 | Key figures, verdicts and prediction anchors agree across all documents | `check_consistency.py` (CI gate 3); "All key figures, verdicts and prediction anchors agree across documents." Tested by planting three errors in a copy (a 9.5x, a wrong E3 verdict, a wrong P5 anchor): all three were caught |
| 36 | Data note: the baseline is Blockworks data, and re-pulling it needs a Blockworks API key; revenue is cross-checked against DefiLlama (0.998); the on-chain data re-pulls from BigQuery with an exact match (a thread 4) | `extension_results.txt:37` at the T10 commit, line 50 in the current file (X1, exploratory: DefiLlama total / Blockworks total 0.998); BigQuery re-pull MATCH: row 34; API key: `THESIS.md:129`, row 20 |
| 37 | Interim status of P1 to P6, snapshot 2026-11-13 (interim status, not a resolution): P1 to P4 and P6 "not yet", P5 "on track" (28-day mean of distinct signers ending 2026-11-10 at the 62,660 threshold, the same day the anchor was taken); shown in dashboard section 8 (not yet in a or b) | `track_predictions.py` (thresholds read from `PREDICTIONS.md`); `predictions_status.json` (derived values only; DefiLlama pulled 2026-11-13T13:38:21Z, BigQuery committed pulls to 2026-11-10). `check_consistency.py` checks the snapshot against `PREDICTIONS.md` and the dashboard against the snapshot; tested by planting one error in a copy (P5 threshold 62,660 changed to 62,600 in the snapshot): caught, exit 1 |

## (d) Form-fields checklist

Fields as listed by Benny from the live submission form. Values in square brackets are for Benny to fill in; nothing has been submitted.

- **Deadline:** 2026-11-14 23:59 UTC.
- **Fixing mistakes:** after submitting, the form's "Request changes" link can be used to fix mistakes.

| Field | Value | Status |
|---|---|---|
| Project name | Price Is Not Revenue: the 9.4x Question | ready (spelled identically in README.md, THESIS.md, the dashboard title and this file) |
| Team lead | [TEAM LEAD] | Benny supplies |
| Email | [EMAIL] | Benny supplies (not stored in this public repo) |
| Team size | [TEAM SIZE] | Benny supplies |
| Tracks | Investment Thesis | ready; select it in the form |
| NEAR wallet address | [WALLET ADDRESS] | Benny supplies; a named account such as `your-team.near` |
| Repository link (must be public) | https://github.com/bennytimz/price-is-not-revenue | ready; the repo is public |
| Demo post link | [X POST LINK] | Benny supplies after posting (a); must be a public X post with the demo video or screenshots |
| What did you build? (20 to 2,000 characters) | Section (b), 1,991 characters | ready |
| Consent checkbox | [Benny ticks it] | Benny reads and ticks it on the form |
