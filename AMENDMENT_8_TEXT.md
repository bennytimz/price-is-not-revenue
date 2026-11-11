
## Amendment 8 (2026-11-11): public-source extension, written before any DefiLlama, BigQuery or Explorer data was pulled or inspected

Purpose: add first-party public data so the thesis does not rest on Blockworks alone, and test the track's own example idea (Intents volume as a leading indicator of network usage). These tests are small and several are underpowered. They are reported whatever they show.

**Sources**
- S1: DefiLlama free API, NEAR Intents daily volume (USD), and daily fees or revenue if offered without a paid key.
- S2: NEAR public BigQuery dataset `bigquery-public-data.crypto_near_mainnet_us.transactions`, daily transaction count and distinct `signer_account_id`, from 2024-01-01 to the latest block_date available.
- S3 (stretch, only if a JWT is obtained by 2026-11-12): Intents Explorer API sampling with `optional_intents_explorer_sample.py`. Descriptive only.
- If a source is unavailable or paywalled, that is recorded under "What I could not compute" and no other source is substituted without a new amendment.

**Tests and decision rules**
- **E1, revenue as a proxy for Intents activity.** On days where S1 volume and Blockworks retained Intents revenue both exist (at least 120 days), the Spearman correlation of the two daily series is 0.5 or higher. Otherwise "not a usable proxy".
- **E2, volume or take rate.** Take rate = retained Intents revenue divided by S1 volume. Compare 2026-08-07 to 2026-09-02 with 2026-09-17 to 2026-10-15. Volume share of the revenue change = ln(volume ratio) / ln(revenue ratio). "Volume-driven" if 0.7 or higher, "take-rate-driven" if 0.3 or lower, otherwise "mixed". Needs S1 coverage of both windows.
- **E3, the track's example hypothesis (exploratory).** Weekly data over the period S1 covers. Compare the Spearman correlation of the 4-week log change in Intents volume with the next 4-week log change in on-chain usage (S2 distinct signers if S2 reaches that period, otherwise Blockworks transactions) against the same correlation for the 4-week NEAR price return. Volume "leads better than price" only if its correlation is higher by at least 0.15 and a 7-day block-bootstrap 95% interval excludes zero. Otherwise "not supported". Overlapping windows mean significance is not claimed.
- **E4, the 2026-04-02 break.** If S2 covers 2026-03-01 to 2026-05-31, compare median daily distinct signers in the 28 days before with the 28 days after 2026-04-02. A drop of 50% or more means the break is real on-chain. A drop under 20% means it is probably a Blockworks definition change. In between is inconclusive. If S2 does not cover the dates, "cannot test".
- **E5, definition check.** Over the overlap of S2 and Blockworks, the Spearman correlation of daily changes in S2 distinct signers and Blockworks active addresses is 0.6 or higher means "consistent definitions". Otherwise "inconsistent".

**Rules**
1. Raw pulls are saved unmodified with SHA-256 hashes in the manifest. No outlier removal.
2. New analysis lives in `analysis_extension.py` and `extension_results.txt`. The confirmatory scripts and results are not changed.
3. This amendment is committed and pushed before any new data is pulled, so the git timestamp can show the order.
