-- S2 (Amendment 8): NEAR daily on-chain usage from the public BigQuery dataset.
-- Run by the author in the BigQuery web console on 2026-11-11. Bytes processed: 123 GB.
-- The result was downloaded from the console as CSV and saved unmodified as raw_bigquery_daily_usage.csv
-- (SHA-256 in RAW_PULLS.sha256).
SELECT block_date, COUNT(*) AS transactions, COUNT(DISTINCT signer_account_id) AS active_signers FROM `bigquery-public-data.crypto_near_mainnet_us.transactions` WHERE block_date >= '2024-01-01' GROUP BY block_date ORDER BY block_date
