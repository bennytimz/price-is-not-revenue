# Price Is Not Revenue: the 9.4x Question

## Summary for judges

**Claim:** NEAR is an option on NEAR Intents revenue, not yet a cash-flow story: the revenue is real but would need to grow about 9.4 times before buybacks offset new token supply.

- **Revenue is now Intents:** retained Intents revenue was 92% of NEAR's protocol revenue in October 2026, and an independent DefiLlama pull totals 0.998 of Blockworks' figure (X1).
- **Dilution dwarfs revenue:** new supply is worth $137M a year at $4.28, against $20.3M a year of trailing-91-day revenue. Buybacks offset it only at 9.4 times that run-rate ($191M a year).
- **Valuation depends on the definition:** NEAR is 276 times sales on total revenue (peer median 647x) but 3928 times on gas fees alone.
- **The Sep-Oct revenue jump was only partly volume (E2: mixed):** volume rose 1.627 times, revenue 3.204 times, because the take rate went from 2.61 to 5.13 basis points.
- **Tests that failed:**
  - E3: Intents volume did not lead on-chain usage better than price (+0.178 against +0.336), so it is not supported.
  - E5: Blockworks active addresses and on-chain signers are inconsistent (0.479 against a 0.60 bar).
  - H2: activity led price in the fit period but failed out of sample (R-squared -76.2%).
- **A data-definition break:** on 2026-04-02 Blockworks active addresses fell 89.4% while on-chain signers fell 8.1%, so the drop is probably a Blockworks definition change (E4).

**Reproduce:** `pip install -r requirements.txt` then `python run_all.py` (rebuilds every number and the dashboard from the files in this repo). **Read:** [THESIS.md](THESIS.md) · [live dashboard](https://bennytimz.github.io/price-is-not-revenue/dashboard.html)

---

A pre-registered, reproducible test of whether NEAR Intents can carry NEAR's valuation. NEAR is an option on Intents revenue, not yet a cash-flow story.

Submission for the NEAR Hackathon, Investment Thesis track. Built by Benny (GitHub: Bennytimz) with AI assistance. Research only, not investment advice.

## Start here (2 minutes)

1. `THESIS.md`: the claim, the evidence for and against, what would change my mind, and what I could not compute.
2. `dashboard.html`: six charts and an interactive dilution sensitivity; sections 6 and 7 are the public-source cross-checks. Open it in a browser; it needs no server.
3. `confirmatory_results.txt`, `scenarios_results.txt` and `extension_results.txt`: the exact script output behind every number.
4. `PREREGISTRATION.md`: hypotheses and rejection rules written before the long history was loaded, plus dated amendments 1 to 8a (including claims I withdrew) and a data correction log.

## What is in this repo

| File | What it is |
|---|---|
| `THESIS.md` | The written thesis |
| `dashboard.html` | Static dashboard with data embedded |
| `analysis_confirmatory.py` | The four pre-registered tests, plus descriptive H5 |
| `scenarios.py` | Revenue composition, run-rates, dilution, sensitivity grid and the post-hoc usage check |
| `build_clean_data.py` | Rebuilds the CSV files from the raw exports in `raw_*.csv` files |
| `run_all.py`, `verify_data.py`, `build_dashboard.py`, `dashboard_template.html`, `requirements.txt`, `chart.umd.js` | One-command rebuild: data check, tests, scenarios and dashboard (Chart.js bundled) |
| `analysis_extension.py` | Public-source cross-checks E1 to E5 (pre-registered, Amendment 8) plus labelled exploratory checks; writes `extension_results.txt` and `extension_numbers.json` |
| `pull_defillama_intents.py` | Pulls NEAR Intents daily volume, fees and revenue from DefiLlama's free API into `raw_defillama_intents*.json` |
| `pull_bigquery_daily_usage.sql` | The BigQuery query behind `raw_bigquery_daily_usage.csv` (daily transactions and distinct signers) |
| `RAW_PULLS.sha256` | SHA-256 hashes of the public-source raw files, checked by `analysis_extension.py` before it runs |
| `optional_intents_explorer_sample.py` | Intents Explorer sampler (S3). Written from the docs, not run |
| `optional_bigquery_daily_usage.sql` | Earlier draft of the BigQuery query, with a freshness check; superseded by `pull_bigquery_daily_usage.sql` |
| `PREREGISTRATION.md` | Pre-registration with amendments 1 to 8a and a data correction log |
| `LICENSE` | MIT licence for the code and writing (see data rights below) |
| `near_daily.csv` | NEAR daily: price, circulating market cap, protocol revenue, transaction fees, active addresses, transactions (2024-01-01 to 2026-11-04) |
| `peers_weekly.csv` | SOL, ETH, SUI, APT, AVAX weekly: price, market cap, protocol revenue, transaction fees |
| `near_total_supply_weekly.csv` | NEAR total supply, weekly |
| `near_buybacks_daily.csv` | NEAR Intents buybacks (USD), daily from 2026-04-23 |

## Reproduce (one command)

```
pip install -r requirements.txt
python run_all.py
```

This runs `verify_data.py`, `analysis_confirmatory.py`, `scenarios.py`, `analysis_extension.py` and `build_dashboard.py`, rewrites `confirmatory_results.txt`, `scenarios_results.txt`, `extension_results.txt` and `dashboard.html` (plus the three `*_numbers.json` files), and reads only from this folder. It never re-pulls data. The source for the data is Blockworks, which needs an API key to re-pull, so the committed CSVs are the reproducible input. Each dashboard chart names the code and data file behind it.

On Windows, Python may write CRLF line endings; the outputs are byte-identical to the committed ones after normalising to LF (tested: all seven output files match).

## What is and is not reproducible

| Question | Status |
|---|---|
| Do the committed files rebuild every number and chart? | Yes. `python run_all.py` was run from a clean copy in a fresh virtual environment with the pinned `requirements.txt`, and every output file was byte-identical to the committed one. |
| Do the data files match what the source reported? | Yes, checked by `verify_data.py` (row counts, date continuity, revenue totals) and by `MANIFEST.sha256` (file hashes). The totals in `SOURCE_TOTALS.json` are the ones reported at pull time. |
| Can a stranger re-pull the data? | Blockworks: only with a Blockworks API key; it is a third-party source and the pull went through a chat assistant. Public sources: yes, see below. |
| Is there an independent public-source check? | Yes, two sources (tests E1 to E5 in `extension_results.txt`). The third planned source, Intents Explorer sampling (S3), was not run. |
| Does the dashboard work offline? | Yes. Chart.js is bundled in `chart.umd.js`. |
| Are the raw exports in the repo? | Yes. Blockworks exports are in the `raw_near_*.csv` and `raw_peers_*.csv` files exactly as received, and `python build_clean_data.py` rebuilds every baseline CSV from them. Public-source pulls are saved unmodified as `raw_defillama_intents*.json` and `raw_bigquery_daily_usage.csv`, with hashes in `RAW_PULLS.sha256`. |

### Public sources and how to re-pull them

| Source | What | Raw file | How to re-pull |
|---|---|---|---|
| S1, DefiLlama free API (no key) | NEAR Intents daily volume, fees and revenue | `raw_defillama_intents.json`, `raw_defillama_intents_fees.json`, `raw_defillama_intents_revenue.json` | `python pull_defillama_intents.py --force` (endpoints `api.llama.fi/summary/dexs/near-intents` and `api.llama.fi/summary/fees/near-intents`) |
| S2, NEAR public BigQuery dataset | Daily transactions and distinct `signer_account_id` | `raw_bigquery_daily_usage.csv` | Run `pull_bigquery_daily_usage.sql` in the BigQuery web console and download the result as CSV (see below) |
| S3, Intents Explorer API | Sampled swaps | none | Not run |

The BigQuery query (it processed 123 GB when run on 2026-11-11; the `block_date` filter matters because the table is partitioned on it, and without it the query scans the whole table):

```sql
SELECT block_date, COUNT(*) AS transactions, COUNT(DISTINCT signer_account_id) AS active_signers
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date >= '2024-01-01'
GROUP BY block_date ORDER BY block_date
```

A re-pull returns later days and possibly revised history, so its hashes will not match `RAW_PULLS.sha256`. The committed raw files are what the results were computed from. `--force` overwrites them, so copy them first if you want to compare.

## Where the data came from and how it was checked

The baseline series come from Blockworks, pulled through the Blockworks MCP in ChatGPT; the CSV files here are rebuilt from the raw exports by `build_clean_data.py`. The public-source cross-checks are described above. Because values passed through a chat assistant, every series was checked against the row counts and revenue totals the assistant reported, and against a second independent pull where one existed.

| Series | Rows | Check |
|---|---|---|
| NEAR daily, 2024 | 366 | Revenue sum $8,509,860.75 matches the source |
| NEAR daily, 2025 | 365 | Revenue sum $4,857,982.55 matches the source |
| NEAR daily, 2026 | 308 | Revenue sum $9,133,652.78 matches the source (two pulls agree) |
| Peers weekly | 740 (148 weeks x 5) | Per-asset revenue sums match to within cents; no missing weeks |
| NEAR total supply | 148 | Sum matches the source |
| NEAR buybacks | 196 | Sum matches the source |

Known gaps and choices:

- Transaction fees for 2024 were not transcribed. They equal protocol revenue on every 2024 row by inspection, and the file uses revenue for both columns in 2024.
- Stablecoin supply is excluded. Two pulls of the same batch disagreed on it.
- Prices and market caps for 2026-09-07 to 2026-09-09 are blank in the source and left blank.
- The two most recent days (2026-11-03 and 2026-11-04) are provisional; the source revised one of them between pulls. They sit in the exploratory window only.
- Data-cleaning rules (single-day market-cap spikes, days where revenue equals fees after 2025-09-23, incomplete-day flags) were fixed in the pre-registration before any hypothesis test and are applied in `analysis_confirmatory.py`.

## Honesty notes

- Hypotheses were written before the confirmatory data was analysed, and all four are reported, including the ones that failed. This repository was created after the analysis, so its history cannot prove that order; the dated amendments in `PREREGISTRATION.md` are the record.
- Two exploratory claims I made early on (revenue in NEAR terms was flat; revenue growth was mostly price) were withdrawn when the revenue source turned out not to be NEAR-denominated. The withdrawal is dated in `PREREGISTRATION.md`.
- Analyses added after the tests are labelled post-hoc in `scenarios.py` and in the thesis.
- The public-source tests E1 to E5 are reported as they came out, including E3 (not supported) and E5 (inconsistent). Checks added afterwards are labelled exploratory in `extension_results.txt` and do not change any verdict.
- Limitations are listed in `THESIS.md`. The largest are a single regime, an Intents volume series whose definition DefiLlama does not document, and a break in Blockworks active addresses on 2026-04-02 that is probably a definition change (E4).

## License and data rights

The MIT licence in `LICENSE` covers the code and the writing in this repository. It does not grant any rights to the data. The Blockworks-derived CSV files (`near_*.csv`, `peers_weekly.csv` and the `raw_near_*` and `raw_peers_*` exports) are included only so the analysis can be reproduced; Blockworks' own terms apply to that data. The DefiLlama and BigQuery pulls are subject to their providers' terms.

## AI use

Claude was used for the statistical analysis, scripts, dashboard and drafting. ChatGPT with the Blockworks MCP was used to pull data. The hypotheses, data checks, corrections and decisions are documented in the pre-registration amendments.
