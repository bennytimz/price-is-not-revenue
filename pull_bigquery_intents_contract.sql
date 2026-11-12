-- S4 (Amendment 9): daily calls to the NEAR Intents settlement contract (intents.near) from the public BigQuery dataset.
-- Run on 2026-11-12 00:3x Lagos time (2026-11-11 23:3x UTC); results run to 2026-11-11 UTC, and that partial day is excluded from the tests.
-- About 100 GB processed, exact figure not recorded.
-- The result was downloaded from the console as CSV and saved unmodified as raw_bigquery_intents_contract.csv
-- (SHA-256 in RAW_PULLS.sha256). The day of the pull is excluded in analysis_extension.py (Amendment 9).
SELECT block_date, COUNT(*) AS intents_calls, COUNT(DISTINCT signer_account_id) AS signers FROM bigquery-public-data.crypto_near_mainnet_us.transactions WHERE block_date >= '2025-01-01' AND receiver_account_id = 'intents.near' GROUP BY block_date ORDER BY block_date
