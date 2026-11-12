# Data provenance: the Blockworks pulls

All Blockworks data was pulled through ChatGPT's Blockworks MCP, by prompting. Every prompt set the same rules: raw CSV only, no interpolation, leave gaps blank, and report the row count and sum.

ChatGPT output was copied into the raw files by hand; the committed raw files are the reproducible input. Blockworks needs an API key to re-pull.

## Prompts and checks

The prompts below are verbatim. The NEAR daily prompt was sent three times, once per year, with `[range]` replaced by that year's date range.

**NEAR daily prompt:**

> Yes, split into batches. Start with Batch 1 only: NEAR daily data for [range], with these columns: date, price_usd, circulating_market_cap_usd, protocol_revenue_usd, transaction_fees_usd, active_addresses, total_transactions, stablecoin_supply_usd. Rules: - Output the raw CSV only, no commentary. - Do not interpolate, estimate or fill missing values. Leave them blank. - If you can't fetch a value, leave it blank. Don't invent one. - After the CSV, give me the row count and the sum of protocol_revenue_usd. I'll ask for the next batch after this one.

**Peers prompt (prompt B):**

> Next, peers: SOL, ETH, SUI, APT, AVAX. Weekly rows (week ending Sunday) from 2024-01-01 to 2026-11-04. Columns: week_ending, asset, close_price_usd, close_market_cap_usd, weekly_protocol_revenue_usd, weekly_transaction_fees_usd, days_with_revenue_data. Same rules: raw CSV only, no filling gaps, then row count and the revenue sum per asset. Split into two batches if needed.

There were two versions of the peers prompt: A without `weekly_transaction_fees_usd` and B with it, after `weekly_protocol_revenue_usd`. Both raw peer files have the header `week_ending,asset,close_price_usd,close_market_cap_usd,weekly_protocol_revenue_usd,weekly_transaction_fees_usd,days_with_revenue_data`, so they match prompt B.

**Supply and buybacks prompt:**

> Two more NEAR series from Blockworks. (1) Asset Supply, Total Supply for NEAR, weekly (week ending Sunday, last value of the week), from 2024-01-07 to 2026-11-01. (2) Project Tokenholder Distributions, Buybacks (USD) for NEAR, daily from 2026-04-23 to 2026-11-04. Raw CSV only, no filling gaps, then the row count and the sum of each value column.

| Raw file | Prompt | Dates in file | Row count and sum check (recorded in `SOURCE_TOTALS.json`, checked by `verify_data.py`) |
|---|---|---|---|
| `raw_near_daily_2024.csv` | NEAR daily, range 2024-01-01 to 2024-12-31 | 2024-01-01 to 2024-12-31 | 366 rows; protocol_revenue_usd sum $8,509,860.75; both match. Blank cells left as blank: 1 (circulating_market_cap_usd) |
| `raw_near_daily_2025.csv` | NEAR daily, range 2025-01-01 to 2025-12-31 | 2025-01-01 to 2025-12-31 | 365 rows; sum $4,857,982.55; both match. No blank cells |
| `raw_near_daily_2026.csv` | NEAR daily, range 2026-01-01 to 2026-11-04 | 2026-01-01 to 2026-11-04 | 308 rows; sum $9,133,652.78; both match. Blank cells left as blank: 3 (price_usd) and 3 (circulating_market_cap_usd) |
| `raw_peers_batch1.csv` | Peers, prompt B, batch 1 | weeks ending 2024-01-07 to 2025-06-29 | 390 data rows (78 per asset). The file also keeps ChatGPT's own row-count and revenue-sum lines after the CSV, as received; `build_clean_data.py` skips them |
| `raw_peers_batch2.csv` | Peers, prompt B, batch 2 | weeks ending 2025-07-06 to 2026-11-01 | 350 data rows (70 per asset). Both batches together give 740 rows, and per-asset revenue sums SOL $3,579,053,364.68, ETH $3,898,154,988.80, SUI $18,501,766.87, APT $1,838,225.62, AVAX $27,816,603.00; all match |
| `raw_near_total_supply_weekly.csv` | Supply and buybacks, series (1) | weeks ending 2024-01-07 to 2026-11-01 | 148 rows; total_supply sum 184,402,163,850.81; both match |
| `raw_near_buybacks_daily.csv` | Supply and buybacks, series (2) | 2026-04-23 to 2026-11-04 | 196 rows; buybacks_usd sum $4,606,429.15; both match |

"Both match" means the file equals the row count and sum recorded from the pull, within $1 for sums (`SOURCE_TOTALS.json`, `tolerance_usd`). `verify_data.py` checks the rebuilt CSV files against these totals on every run, and `MANIFEST.sha256` fixes their hashes.

Orientation prompts (not used as data): a 90-day price and revenue chart, an Aug 7 to Nov 4 correlation check, a maximum-history catalogue, and a metric-name discovery question.
