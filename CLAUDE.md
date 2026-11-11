# CLAUDE.md: project guide for Claude Code (v2, 2026-11-11)

**Project:** "Price Is Not Revenue: the 9.4x Question" (NEAR Hackathon, Investment Thesis track) (nearhackathon.com), by Benny (GitHub: Bennytimz). Deadline 2026-11-14 (submit by the morning of 11-14; the submission cannot be edited).
**Status:** baseline analysis, thesis and dashboard are FINISHED (see rules). Remaining work: publish, add a small pre-registered public-source extension, polish the presentation, submit.
**Constraints:** Benny follows step by step and has a limited usage budget. Explain each command before running it. Keep each task short and stop after it.

## Hard rules
1. Never invent or adjust numbers. If something cannot be computed, say so.
2. `PREREGISTRATION.md` may only be changed by appending a new dated Amendment at the end. Never rewrite earlier text.
3. Never edit data CSVs by hand. Baseline data changes only via `python build_clean_data.py` from `raw_*.csv`.
4. Do not print or open large CSVs in full. Use `head -3` and `wc -l`.
5. Do not change `analysis_confirmatory.py`, `scenarios.py` or their results. After any change run `python run_all.py` and show `git diff` of the result files; the baseline result files must stay byte-identical after line-ending normalisation.
6. Every number in `THESIS.md`, `README.md` and dashboard captions must match `confirmatory_results.txt`, `scenarios_results.txt` or `extension_results.txt`. If not, list every mismatch before editing.
7. Never commit `.env`, tokens or secrets. Use `gh auth login` (browser). Never ask Benny to paste a token into any chat.
8. New analysis goes only in new files (`pull_defillama_intents.py`, `analysis_extension.py`, `extension_results.txt`, `raw_defillama_*.json`, `raw_bigquery_daily_usage.csv`, `RAW_PULLS.sha256`). Label each result as pre-registered (Amendment 8) or post-hoc.
9. If a data source is unavailable or paywalled, record it under "What I could not compute" in THESIS.md and stop. Do not swap in another source without a new amendment.
10. Report results exactly as they come out, including ones against the thesis. Never make the thesis more bullish.

## Commands
```
pip install -r requirements.txt
python verify_data.py
python run_all.py
python build_clean_data.py    # only when raw_*.csv are present
```

## Tasks in order. Stop and report after each.
- **T1 Environment.** Python 3.12 recommended. Install requirements, run `verify_data.py` then `run_all.py`. Report PASS/FAIL.
- **T2 Git.** `git init`, `.gitignore` (`__pycache__/`, `*.pyc`, `venv/`, `.env`), first commit.
- **T3 GitHub.** Public repo `price-is-not-revenue` under Bennytimz, push `main`.
- **T4 Pages.** Enable Pages (main, root). Confirm `https://bennytimz.github.io/price-is-not-revenue/dashboard.html` loads and charts render.
- **T5 Raw check.** If `raw_*.csv` are present: commit first, run `build_clean_data.py` and `run_all.py`, show `git diff --stat`, handle any change by rule 6.
- **T6 Pre-register the extension.** Append the text of `AMENDMENT_8_TEXT.md` verbatim to `PREREGISTRATION.md`. Commit and push. Show `git log -1 --format=%cI`. Do NOT pull any new data before this is pushed.
- **T7 Data pulls (free, public).**
  - S1: write `pull_defillama_intents.py` using DefiLlama's free API docs to fetch NEAR Intents daily volume (and fees/revenue if free). Test with `curl` first. If paywalled (402/403), apply rule 9. Save raw responses untouched as `raw_defillama_*.json`, add hashes to `RAW_PULLS.sha256`.
  - S2: Benny runs `optional_bigquery_daily_usage.sql` in the BigQuery web console (freshness query first) and saves results as `raw_bigquery_daily_usage.csv` (query saved as `pull_bigquery_daily_usage.sql`, hash in `RAW_PULLS.sha256`). Do not install gcloud unless asked.
- **T8 Extension analysis.** Write `analysis_extension.py` implementing E1 to E5 exactly as Amendment 8 states, reading only the `raw_defillama_*.json` and `raw_bigquery_daily_usage.csv` files and existing data. Write `extension_results.txt`. Extend `run_all.py` to run it last. Baseline outputs must remain identical.
- **T9 Update thesis and dashboard.** Add a clearly marked "Public-source cross-checks" section to `THESIS.md` and one or two new dashboard charts (each with a one-line takeaway and its code and data source). Update "What I could not compute". Apply rule 6.
- **T10 Presentation.** Add an 8-line summary at the top of `README.md` and a link to the live dashboard. Draft (do not post) the X post and the 20 to 2,000 character submission description in `SUBMISSION_DRAFT.md`.
- **T11 Final check.** Fresh clone into a temp folder, `pip install -r requirements.txt`, `python run_all.py`, confirm it passes and the result files match. List anything inaccurate in README or THESIS. Tag `v1-submission`.

## Done means
Repo public, Pages live, fresh-clone run passes, README and THESIS accurate, nothing secret committed, submission draft ready.
