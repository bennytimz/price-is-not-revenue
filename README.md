# Price Is Not Revenue: the 9.4x Question

A pre-registered, reproducible test of whether NEAR Intents can carry NEAR's valuation. NEAR is an option on Intents revenue, not yet a cash-flow story.

Submission for the NEAR Hackathon, Investment Thesis track. Built by Benny (GitHub: Bennytimz) with AI assistance. Research only, not investment advice.

## Start here (2 minutes)

1. `THESIS.md`: the claim, the evidence for and against, what would change my mind, and what I could not compute.
2. `dashboard.html`: four charts and an interactive dilution sensitivity. Open it in a browser; it needs no server.
3. `confirmatory_results.txt` and `scenarios_results.txt`: the exact script output behind every number.
4. `PREREGISTRATION.md`: hypotheses and rejection rules written before the long history was loaded, plus seven dated amendments, including claims I withdrew.

## What is in this repo

| File | What it is |
|---|---|
| `THESIS.md` | The written thesis |
| `dashboard.html` | Static dashboard with data embedded |
| `analysis_confirmatory.py` | The four pre-registered tests, plus descriptive H5 |
| `scenarios.py` | Revenue composition, run-rates, dilution, sensitivity grid and the post-hoc usage check |
| `build_clean_data.py` | Rebuilds the CSV files from the raw exports in `raw_*.csv` files |
| `run_all.py`, `verify_data.py`, `build_dashboard.py`, `dashboard_template.html`, `requirements.txt`, `chart.umd.js` | One-command rebuild: data check, tests, scenarios and dashboard (Chart.js bundled) |
| the `optional_*` files | Optional BigQuery and Intents Explorer checks. Written from the docs, not yet run |
| `PREREGISTRATION.md` | Pre-registration with amendments 1 to 7 |
| `near_daily.csv` | NEAR daily: price, circulating market cap, protocol revenue, transaction fees, active addresses, transactions (2024-01-01 to 2026-11-04) |
| `peers_weekly.csv` | SOL, ETH, SUI, APT, AVAX weekly: price, market cap, protocol revenue, transaction fees |
| `near_total_supply_weekly.csv` | NEAR total supply, weekly |
| `near_buybacks_daily.csv` | NEAR Intents buybacks (USD), daily from 2026-04-23 |

## Reproduce (one command)

```
pip install pandas numpy statsmodels scipy
python run_all.py
```

This runs `analysis_confirmatory.py`, `scenarios.py` and `build_dashboard.py`, rewrites `confirmatory_results.txt`, `scenarios_results.txt` and `dashboard.html`, and reads only from this folder. The source for the data is Blockworks, which needs an API key to re-pull, so the committed CSVs are the reproducible input. Each dashboard chart names the code and data file behind it.

On Windows, Python may write CRLF line endings; the outputs are byte-identical to the committed ones after normalising to LF (tested: all five match).

## What is and is not reproducible

| Question | Status |
|---|---|
| Do the committed files rebuild every number and chart? | Yes. `python run_all.py` was run from a clean copy in a fresh virtual environment with the pinned `requirements.txt`, and every output file was byte-identical to the committed one. |
| Do the data files match what the source reported? | Yes, checked by `verify_data.py` (row counts, date continuity, revenue totals) and by `MANIFEST.sha256` (file hashes). The totals in `SOURCE_TOTALS.json` are the ones reported at pull time. |
| Can a stranger re-pull the data? | Only with a Blockworks API key. Blockworks is a third-party source and the pull went through a chat assistant. |
| Is there an independent public-source check? | Not yet. the `optional_*` files has a BigQuery query and an Intents Explorer sampler; neither has been run. |
| Does the dashboard work offline? | Yes. Chart.js is bundled in `chart.umd.js`. |
| Are the raw exports in the repo? | Yes, in `raw_*.csv` files, exactly as received. `python build_clean_data.py` rebuilds every CSV in this folder from them, so no value was typed by hand. |

## Where the data came from and how it was checked

All series come from Blockworks, pulled through the Blockworks MCP in ChatGPT and copied into the CSV files here. Because values passed through a chat assistant, every series was checked against the row counts and revenue totals the assistant reported, and against a second independent pull where one existed.

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
- Limitations are listed in `THESIS.md`. The largest are a single regime, no Intents volume series, and an unexplained break in activity metrics on 2026-04-02.

## AI use

Claude was used for the statistical analysis, scripts, dashboard and drafting. ChatGPT with the Blockworks MCP was used to pull data. The hypotheses, data checks, corrections and decisions are documented in the pre-registration amendments.
