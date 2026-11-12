# Forward predictions (draft, 2026-11-12)

Six predictions that anyone can resolve from free public data (DefiLlama's API or NEAR's public BigQuery dataset). Each anchor value is copied from a committed results file. Each prediction says which claim of the thesis it tests, and the outcome is reported whatever it shows.

## How every prediction is resolved

- **When:** pull the data on or after 2027-04-07, so that late-arriving days for the resolution window are in.
- **DefiLlama:** `python pull_defillama_intents.py --force` (the same endpoints as S1). Days are UTC dates of DefiLlama's daily timestamps.
- **BigQuery:** run the committed queries (`pull_bigquery_daily_usage.sql` for signers, `pull_bigquery_intents_contract.sql` for `intents.near` calls) and use only days up to the resolution date. `block_date` is UTC.
- **Missing data:** if more than 5% of the days in a window are missing or empty, the prediction is recorded as "cannot resolve", not as met or missed.
- **Series substitution (P1, P2):** Amendment 7 is written on Blockworks' retained Intents revenue, which needs an API key. Here it is restated on DefiLlama's NEAR Intents daily revenue. Over 406 days DefiLlama's total was 0.998 of Blockworks', with a daily rank correlation of 0.710 (X1, `extension_results.txt:50`).

## Predictions

**P1. Amendment 7 "strengthens" signal.**
- Claim: NEAR is an option on Intents monetisation; this outcome strengthens it.
- Series: DefiLlama NEAR Intents daily revenue.
- Threshold: a trailing 28-day average of at least $100,000 a day (Amendment 7; the latest 28-day average was $67,116 a day, `scenarios_results.txt:47`).
- Resolution date: 2027-03-31.
- Rule: compute the trailing 28-day average for every day from 2026-11-12 to 2027-03-31. Met if it is at least $100,000 on 84 consecutive days within that span. Otherwise not met.

**P2. Amendment 7 "weakens" signal.**
- Claim: the same option thesis; this outcome weakens it.
- Series: DefiLlama NEAR Intents daily revenue.
- Threshold: a trailing 28-day average of at most $30,000 a day (Amendment 7; the pre-surge level was $25,791 a day, `scenarios_results.txt:48`).
- Resolution date: 2027-03-31.
- Rule: as P1. Met if it is at most $30,000 on 56 consecutive days within 2026-11-12 to 2027-03-31.

**P3. Take rate (bull case vs bear case).**
- Claim: "What you would have to believe" (a) and (b). The break-even volume depends on the take rate staying near window B's level.
- Series: DefiLlama NEAR Intents daily revenue and daily volume.
- Threshold: window A's 2.61 bp and window B's 5.13 bp (`extension_results.txt:12-13`).
- Resolution date: 2027-03-31.
- Rule: the take rate is total revenue divided by total volume over 2027-01-01 to 2027-03-31. At or below 2.61 bp, the bear case holds (weakens). At or above 5.13 bp, the take rate held (supports). Anything between is in between.
- Note: E2's take rates used Blockworks revenue; this uses DefiLlama revenue on both sides.

**P4. Revenue keeps compounding.**
- Claim: "My call": it earns a position only if retained revenue keeps compounding toward the break-even.
- Series: DefiLlama NEAR Intents daily revenue.
- Threshold: X5's DefiLlama revenue run-rate of $19.1M a year (`extension_results.txt:60`), and twice that.
- Resolution date: 2027-03-31.
- Rule: the mean daily revenue over the 91 days ending 2027-03-31, times 365. At or above twice $19.1M, it is compounding (supports). Below $19.1M, it is not growing (weakens). Anything between is in between.
- The upper threshold (twice $19.1M) is a judgement call made on 2026-11-12; it is not a value printed in any results file.

**P5. On-chain usage does not recover.**
- Claim: Evidence against 3 and X6: Intents revenue does not come with more on-chain accounts.
- Series: BigQuery daily distinct signers (`pull_bigquery_daily_usage.sql`).
- Threshold: X6's 28-day mean of 62,660 on 2026-11-10, and 261,846 a year earlier (`extension_results.txt:62`).
- Resolution date: 2027-03-31.
- Rule: the 28-day mean of daily distinct signers ending 2027-03-31. At or below 62,660, there is no recovery (supports the claim). At or above 261,846, usage is back to a year earlier (weakens it). Anything between is in between.

**P6. Contract calls keep tracking volume.**
- Claim: F1, that `intents.near` calls are a usable on-chain proxy for Intents volume.
- Series: BigQuery daily `intents.near` calls (`pull_bigquery_intents_contract.sql`) and DefiLlama daily volume.
- Threshold: Spearman 0.50 (Amendment 9; F1 was 0.774, `extension_results.txt:40`).
- Resolution date: 2027-03-31.
- Rule: Spearman of the daily call count against daily volume over 2026-11-12 to 2027-03-31 (140 days). At or above 0.50, the proxy holds. Below 0.50, it does not.
