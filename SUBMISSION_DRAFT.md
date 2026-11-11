# Submission draft (not posted, not submitted)

Drafts for Benny to review. Nothing here has been posted or submitted. Placeholders in square brackets are for Benny to fill in.

## (a) X post

**Main post** (238 characters as written; 242 if the video is uploaded to X and [REPO LINK] is a link; 266 if both are links, since X counts every link as 23 characters):

> Does revenue back NEAR's price? Pre-registered tests, checked on public data: NEAR is an option on Intents revenue, not cash flow. Revenue must grow ~9.4x before buybacks offset new supply. @NEARProtocol #NEARHackathon [VIDEO] [REPO LINK]

**Optional reply thread** (208, 201 and 241 characters):

> 1/ The numbers: retained Intents revenue was 92% of NEAR's protocol revenue in Oct 2026. New supply is worth $137M/yr at $4.28; trailing-91-day revenue is $20.3M/yr. Buybacks offset dilution only at $191M/yr.

> 2/ Public cross-checks (DefiLlama, NEAR BigQuery), pre-registered before the pull: the Sep-Oct revenue jump was mixed. Volume rose 1.627x and revenue 3.204x, as the take rate went from 2.61 to 5.13 bp.

> 3/ What failed: Intents volume did not lead on-chain usage better than price (E3), and Blockworks active addresses don't match on-chain signers (E5). Their 89.4% drop on 2026-04-02 is probably a definition change: on-chain signers fell 8.1%.

## (b) Project description for the form field "What did you build?"

1,838 characters (the field takes 20 to 2,000).

```
Price Is Not Revenue: the 9.4x Question asks whether NEAR Intents revenue can carry NEAR's valuation. Every result is reported, including the ones that failed. The original hypotheses were written down before the confirmatory data was analysed, but the repository was created afterwards, so git history can't prove that order. The public-data extension tests (E1 to E5) are different: they were committed to git (Amendment 8, commit 30ea2ce) before the DefiLlama and BigQuery data was pulled.

Main finding: NEAR is best treated as an option on Intents revenue, not a business valued on cash flow. Retained Intents revenue was 92% of NEAR's protocol revenue in October 2026. But new token supply is worth $137M a year at $4.28, against $20.3M a year of trailing-91-day revenue, so buybacks offset dilution only if revenue reaches $191M a year, 9.4 times today's run-rate.

Public-source cross-checks, pre-registered before the data was pulled, use DefiLlama and NEAR's public BigQuery dataset. The September-October revenue jump was mixed: volume rose 1.627 times while the take rate went from 2.61 to 5.13 basis points. Two tests failed: Intents volume did not lead on-chain usage better than price (E3), and Blockworks active addresses are inconsistent with on-chain signers (E5). Blockworks' 89.4% drop in active addresses on 2026-04-02 is probably a definition change, since on-chain signers fell 8.1% (E4). An exploratory check finds DefiLlama's Intents revenue totals 0.998 of Blockworks' figure.

Everything rebuilds with one command (python run_all.py) from files in the public repo, and each dashboard chart names the script and data behind it. Limits: one market regime, an Intents volume series whose definition DefiLlama does not document, and Blockworks data that needs an API key to re-pull. Research, not investment advice.
```

## (c) Claims audit

Line numbers refer to commit `T10: judges summary and submission draft`.

| # | Claim (used in) | Supporting file and line |
|---|---|---|
| 1 | NEAR is an option on Intents revenue, not a cash-flow story (a, b) | `THESIS.md:3` (the thesis statement; an interpretation of rows 5 to 8) |
| 2 | The original hypotheses were written down before the confirmatory data was analysed, but the repository was created afterwards, so git history can't prove that order (a "pre-registered tests", b) | `PREREGISTRATION.md:1` onward (dated amendments); `THESIS.md:96` ("The repository was created after the baseline analysis, so git history cannot prove that order") |
| 3 | Every result is reported, including failures (b) | `PREREGISTRATION.md:38` (Rules for reporting); failures in rows 11 to 13 below |
| 4 | Retained Intents revenue was 92% of protocol revenue in October 2026 (a thread 1, b) | `scenarios_results.txt:18` (share_intents 0.92) |
| 5 | New supply is worth $137M a year at $4.28 (a thread 1, b) | `scenarios_results.txt:30` |
| 6 | Trailing-91-day revenue is $20.3M a year (a thread 1, b) | `scenarios_results.txt:26` |
| 7 | Buybacks offset dilution only at $191M a year, 9.4 times the run-rate (a, b) | `scenarios_results.txt:43` |
| 8 | The cross-checks use DefiLlama and NEAR's public BigQuery dataset (a thread 2, b) | `extension_results.txt:2`; `pull_defillama_intents.py`; `pull_bigquery_daily_usage.sql` |
| 9 | The extension tests E1 to E5 were committed to git (Amendment 8, commit 30ea2ce) before the DefiLlama and BigQuery data was pulled (a thread 2, b) | `PREREGISTRATION.md:199` (Amendment 8); `git log`: `30ea2ce` (Amendment 8, 2026-11-11T19:30:13+01:00) precedes the commits that added the data, `0be3e49` (DefiLlama, 20:23:11+01:00) and `0734af6` (BigQuery, 20:25:56+01:00). Git records commit times, not pull times: the DefiLlama pull ran at 2026-11-11T19:22:58Z (20:22:58+01:00, printed by `pull_defillama_intents.py`); the BigQuery console run time is not recorded in the repo (Benny can confirm it in BigQuery's query history) |
| 10 | Sep-Oct jump mixed: volume 1.627x, revenue 3.204x, take rate 2.61 to 5.13 bp (a thread 2, b) | `extension_results.txt:12-15` |
| 11 | E3 failed: volume did not lead on-chain usage better than price (a thread 3, b) | `extension_results.txt:21,23` |
| 12 | E5 failed: Blockworks active addresses inconsistent with on-chain signers (a thread 3, b) | `extension_results.txt:33-34` |
| 13 | Blockworks active addresses dropped 89.4% on 2026-04-02 (a thread 3, b) | `extension_results.txt:38` (X2, exploratory) |
| 14 | On-chain signers fell 8.1%, so the drop is probably a definition change (a thread 3, b) | `extension_results.txt:28-29` (E4) |
| 15 | DefiLlama's Intents revenue totals 0.998 of Blockworks' (b, labelled exploratory) | `extension_results.txt:37` (X1) |
| 16 | Everything rebuilds with `python run_all.py` from files in the repo (b) | `run_all.py`; `README.md:17` |
| 17 | Each dashboard chart names the script and data behind it (b) | `dashboard_template.html`, the `class="src"` line under each chart |
| 18 | Limit: one market regime (b) | `THESIS.md:92` |
| 19 | Limit: DefiLlama does not document its Intents volume definition (b) | `THESIS.md:88`; the `methodology` field is empty in DefiLlama's `/summary/dexs/near-intents` response (pulled locally by `pull_defillama_intents.py`, which flags it; the raw file is not redistributed) |
| 20 | Limit: Blockworks data needs an API key to re-pull (b) | `THESIS.md:96` |
| 21 | Research, not investment advice (b) | `THESIS.md:5` |

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
| What did you build? (20 to 2,000 characters) | Section (b), 1,838 characters | ready |
| Consent checkbox | [Benny ticks it] | Benny reads and ticks it on the form |
