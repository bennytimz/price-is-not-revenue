-- NEAR daily on-chain usage from the public BigQuery dataset.
-- STATUS: written from NEAR's documentation, NOT YET RUN by the author. Run in the BigQuery console and
-- check the "bytes processed" estimate before pressing Run (the first 1 TB of queries a month is free).
-- Always filter on block_date (the table is partitioned on it).

-- 1) Freshness check. NEAR's docs say NEAR Lake stopped indexing on 2026-03-24 and that the dataset "remains available".
--    If MAX(block_date) is before 2026-04-02 the dataset cannot be used to check the April 2026 break in activity.
SELECT MAX(block_date) AS latest_block_date
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date >= '2026-01-01';

-- 2) Daily transactions and distinct signing accounts, 2024-01-01 onwards.
--    Compare the trend and the timing of breaks with Blockworks' active_addresses and total_transactions.
--    Definitions can differ from Blockworks' (signers vs any participating account), so compare shapes, not levels.
SELECT
  block_date,
  COUNT(*) AS transactions,
  COUNT(DISTINCT signer_account_id) AS active_signers
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date >= '2024-01-01'
GROUP BY block_date
ORDER BY block_date;
-- Export the result as CSV and save it as bigquery_daily_usage.csv.
