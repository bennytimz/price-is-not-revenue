# Pre-registration: NEAR investment thesis

Written 2026-11-05, before the long-history data was loaded or inspected. This file was committed to git only after the analysis was finished, so the repository history cannot independently prove that order. The dated amendments below record what was decided at each stage, including claims that were withdrawn.

## What is exploratory and what is confirmatory

- **Exploratory window: 2026-08-07 to 2026-11-04.** The first hypotheses (H1, H2) came from looking at this window, so it cannot confirm them. It is reported separately.
- **Confirmatory sample: 2024-01-01 to 2026-08-06.** None of this data had been inspected when this file was written. NEAR protocol revenue in Blockworks starts 2024-01-01, so this is the longest usable window.
- **Fit period: 2024-01-01 to 2025-06-30. Holdout: 2025-07-01 to 2026-08-06.** Models are fitted on the fit period and judged on the holdout.

## Data and fixed choices

- NEAR: daily price, circulating market cap, protocol revenue, transaction fees, active addresses, transactions, stablecoin supply (Blockworks).
- Peers, fixed in advance: SOL, ETH, SUI, APT, AVAX. Weekly price, market cap and revenue (Blockworks).
- Protocol revenue is the USD value of revenue retained by the protocol, priced on the day it is earned (Blockworks definition). "Token-denominated revenue" below means USD revenue divided by that day's price. This is exact only for revenue earned in the native token and is an approximation otherwise.
- P/S = circulating market cap divided by trailing 90-day revenue, annualised. Circulating, not fully diluted. Revenue definitions differ across chains, so P/S is used for relative comparison only.
- Windows: 7, 14, 28 and 90 days. Standard errors: Newey-West (5 daily lags, 4 weekly lags). Block bootstrap uses 7-day blocks.
- Missing days stay missing. No interpolation.

## Hypotheses and decision rules

**H1. USD revenue growth is mostly price pass-through.**
Test: elasticity of ln(USD revenue) to ln(price), and the trend in 28-day average token-denominated revenue.
Rejected if the elasticity 95% CI excludes 1, or the token-denominated trend is positive with p < 0.05. Otherwise not rejected.

**H2. Activity leads price.**
Test: 4-week change in token-denominated revenue predicting the next 4-week NEAR return. Fit on the fit period, evaluate out-of-sample R-squared on the holdout against a zero-mean benchmark. Repeat on the peer panel.
Supported only if fit-period p < 0.05, the holdout out-of-sample R-squared is above 0, and the sign is unchanged in the holdout. If it holds for NEAR but not for peers, it is reported as likely spurious.

**H3. NEAR is expensive relative to peers.**
Test: NEAR's P/S on 2026-11-04 against the peer median, and against NEAR's own history.
Supported if NEAR is above the peer median and above its own 75th percentile. Rejected if below the peer median.

**H4. NEAR usage is not being monetised.**
Test: trends in active addresses and in revenue per active address (30-day) over the confirmatory sample.
Supported if active addresses trend up (p < 0.05) and revenue per active address trends down (p < 0.05). Rejected if revenue per active address is flat or rising.

## Rules for reporting

- All four results are reported, including null and contrary ones.
- Four tests: results are shown against both p < 0.05 and the Bonferroni threshold of 0.0125.
- Any analysis not listed here is labelled post-hoc.
- Conclusions are worded at the strength the tests support: supported, not supported, or inconclusive.
- No price targets. This is research for a hackathon, not investment advice.

## Tentative falsification watch (from the exploratory window)

- 28-day average token-denominated revenue above about 19,000 NEAR/day would contradict a story of decaying usage. Below about 13,000 for 28 days would support it.
- These thresholds come from the exploratory window and are tentative.

## Amendment 1 (2026-11-05): data-quality rules, written after inspecting the 2024 batch for data quality only

No hypothesis test had been run when this amendment was written. The 2024 NEAR batch was checked only for completeness and internal consistency (row count, revenue sum against the source's own total, duplicate and missing days, price against market cap).

**Findings from that check**
- 366 rows, no duplicate or missing days. The revenue sum matched the source's total.
- Circulating market cap is missing on 2024-01-29. It stays missing.
- Implied circulating supply (market cap divided by price) has single-day spikes that reverse the next day (2024-05-19, 2024-07-13) and two persistent steps (2024-10-13, about +10%; 2024-12-30, about -4%). These look like changes in how circulating supply is reported, not price moves.
- In the 2024 batch, protocol revenue and transaction fees look identical on every row. For NEAR this suggests "protocol revenue" is total gas fees, which are paid in NEAR. That makes dividing USD revenue by price a good approximation of revenue in NEAR for 2024. Whether the two columns diverge later (for example when NEAR Intents revenue appears) must be checked in the 2026 batch.

**Rules fixed now**
1. A day whose implied circulating supply differs by more than 3% from the median of the surrounding 7 days, and reverts, is set to missing for market-cap-based metrics. Price and revenue are untouched.
2. Persistent supply steps are kept, but any P/S or market-cap result is also reported using total market cap computed from a fixed supply, labelled as a robustness check.
3. If protocol revenue and transaction fees diverge in any period, the H1 test is run separately on each.
4. No hypothesis test is run until all NEAR and peer batches are loaded and verified.

## Amendment 2 (2026-11-05): revenue composition and incomplete-day flags, written after inspecting the 2025 batch for data quality only

No hypothesis test had been run when this amendment was written. The 2025 batch was checked for completeness and internal consistency only (365 rows, no duplicate or missing days, revenue sum matched the source's total exactly).

**Findings**
- Protocol revenue equals transaction fees on every row through 2025-09-22 (checked programmatically for 2025, by reading for 2024). From 2025-09-23 the two diverge. Non-fee revenue was about 11% of revenue in late September 2025, 53% in October, 74% in November and 65% in December.
- Transaction fees (gas) are paid in NEAR, so dividing them by price gives fees in NEAR. The non-fee component's source and currency are not documented in the data. No conversion to NEAR units will be asserted for it.
- A few days have active addresses far below normal alongside unusually low revenue (for example 2024-01-21 and 2025-07-13). These look like incomplete or interrupted data days rather than real collapses in activity.

**Rules fixed now**
1. H1 is run three ways: on transaction fees alone for the full confirmatory sample; on total protocol revenue for the full sample; and on non-fee revenue alone from 2025-09-23, where it is described only in USD.
2. The exploratory finding that revenue in NEAR terms returned to its August level used total revenue divided by price. It is conditional on the 2026 revenue composition and will be re-examined once the 2026 batch is loaded.
3. A day with active addresses below 50% of the centred 14-day median is flagged as a likely incomplete day. Every test is reported with and without flagged days.
4. Rule 4 of Amendment 1 still applies: no hypothesis test is run until all NEAR and peer batches are loaded and verified.

## Amendment 3 (2026-11-05): revenue composition resolved, one exploratory hypothesis added, written after the 2026 batch was checked for data quality only

No hypothesis test on the confirmatory sample (2024-01-01 to 2026-08-06) had been run when this amendment was written. All three NEAR batches are verified (row counts and revenue sums match the source's own totals exactly).

**Composition of NEAR protocol revenue (resolved from public sources, not from the data)**
- Through 2025-09-22, protocol revenue equals transaction fees (gas, paid in NEAR). Afterwards the extra component is retained NEAR Intents revenue: Blockworks' own NEAR financials page describes network revenue as base-chain fees plus retained Intents protocol revenue.
- Cross-check: Blockworks non-fee revenue for the 30 days to 2026-10-23 is $2.15M; DefiLlama's NEAR Intents page shows about $2.12M of revenue for 30 days. In 2026 the non-fee component is 79% to 94% of monthly protocol revenue, and 93% of the exploratory window (2026-08-07 to 2026-11-04).
- Retained Intents revenue comes from swap volume in many assets. It is not gas, so converting it to NEAR units is not meaningful.

**Withdrawn exploratory claims**
- "Revenue in NEAR terms returned to its August level" and "USD revenue growth was mostly price pass-through" are withdrawn. Both assumed all revenue was NEAR-denominated. That assumption is false after 2025-09-22.

**Clarifications to existing hypotheses (decision rules unchanged)**
- H1: the token-denominated analysis applies to gas fees only. Total revenue and non-fee revenue get the elasticity test only, with no NEAR-unit interpretation.
- H2: the primary predictor is the 4-week change in gas fees measured in NEAR. The secondary predictor is 4-week growth in retained Intents revenue in USD. Both are reported.
- H3: NEAR's P/S is reported on total revenue and on gas fees alone. Peer revenue definitions probably exclude app-layer revenue, so the comparison is indicative only and the definition for each peer is recorded.
- H4: active addresses, transactions and gas fees drop sharply starting 2026-04-02 and stay low. Comparing March with April 3-30 medians: active addresses fall 89% (2.35M to 248K), transactions fall 76% and gas fees fall 69%. The cause is not documented. H4 is tested separately before and after that date, with and without a break term.

**New hypothesis, labelled exploratory because the 2026 implied supply series had already been seen**
- H5: retained revenue covers a small fraction of the dollar value of new token issuance. Test: monthly ratio of trailing-90-day annualised revenue to annualised issuance (growth in implied circulating supply, market cap divided by price, times price). Supported if the ratio is below 50% in at least 80% of months in the confirmatory sample. Exploratory value on 2026-11-04: about 17% to 21%.

**Data rules fixed now**
1. Days after 2025-09-23 where revenue exactly equals fees (2025-09-28 and 2026-04-22) are treated as missing retained-revenue data. Total revenue is set to missing for those days.
2. The last two days (2026-11-03 and 2026-11-04) are provisional: the second pull moved the 2026-11-04 price by about 0.02% and added a revenue value that the first pull lacked. They sit in the exploratory window only.
3. Rule 4 of Amendment 1 still applies: no hypothesis test is run until the peer batches are loaded and verified.

## Amendment 4 (2026-11-05): definitions checked against Blockworks' methodology page, written before any peer data was loaded

**Verified directly on Blockworks' NEAR financials page**
- Network revenue for NEAR includes base-chain transaction fees and retained Intents protocol revenue.
- Retained Intents revenue is value that intents.near sends to NEAR-owned wallets, counted once when it arrives, in NEAR or USDC. USDC is converted to NEAR at the daily NEAR price.
- Retained Intents fees held in the treasury wallets are excluded from token-holder income because they are neither burned nor distributed. NEAR bought back with Intents revenue is counted as token-holder income. The share of retained revenue spent on buybacks is not in the daily series pulled so far.

**Correction to Amendment 3**
- Amendment 3 said retained Intents revenue is not NEAR-denominated. The methodology says it arrives in NEAR or USDC, in an unknown mix. The decision stands: total revenue is not given a NEAR-unit interpretation. Transaction fees (gas) remain the only cleanly NEAR-denominated series.

**Not verified by me (reported by the data source's chat assistant)**
- That "receipt conversion fees" are a separate Network REV component for NEAR. The cross-check in Amendment 3 (non-gas revenue about $2.15M against DefiLlama's about $2.12M for 30 days) suggests any such component is small.
- The peers' revenue definitions: network-level only (transaction or base fees, priority fees, MEV or tips, blob or storage fees, burn-related components), with application revenue tracked separately. The peer batches will include transaction fees as well as protocol revenue, so any gap between the two can be seen directly.

**Decisions fixed now**
1. H3 primary comparison is like-for-like: NEAR transaction fees against each peer's protocol revenue (network level). The secondary comparison uses NEAR total protocol revenue, which includes Intents revenue, and is labelled as not like-for-like.
2. Stablecoin supply is excluded from every analysis. Two pulls of the same 2026 batch disagreed (values present for January to September in one, blank in the other).
3. Two pulls of the 2026 batch otherwise agree on row count (308) and revenue sum. A few long values differ in the tenth significant digit, which is immaterial. Analysis uses the first verified pull.
4. H5 uses Blockworks' own token issuance and burn series if they can be pulled. Otherwise it uses the implied circulating supply growth already specified.

## Amendment 5 (2026-11-05): peer batch 1 verified, written before any peer result was analysed

**Verified**
- Peer batch 1 (weeks ending 2024-01-07 to 2025-06-29): 390 rows, 78 weeks for each of the five peers, no missing weeks. Per-asset revenue sums match the source's totals to within $0.05 (rounding in my copy).

**Findings from the data-quality check**
- Peers' protocol revenue is not the same as transaction fees. Share of revenue outside transaction fees over the batch: SOL 56%, ETH 15%, SUI 9%, APT 0%, AVAX 0%. This is consistent with network-level revenue that includes tips, MEV or similar components for some chains.
- Implied circulating supply moves a lot for some peers: SUI jumps about 80% in a single week (2024-04-28 to 2024-05-05, from about 1.30B to 2.34B), and APT roughly doubles over the batch. Circulating market cap comparisons are therefore sensitive to supply definitions.

**Decisions fixed now**
1. H3 is reported on three like-for-like bases, all fixed before any peer result is seen: (a) NEAR transaction fees against each peer's protocol revenue (Amendment 4's primary); (b) transaction fees only for every asset, which removes MEV and tip differences; (c) NEAR total protocol revenue against peers' protocol revenue, labelled not like-for-like.
2. Every P/S result is also reported with market cap recomputed from price and a fixed supply (Amendment 1, rule 2), and SUI's 2024-05-05 supply step is flagged wherever SUI appears.
3. Blockworks does not expose NEAR token issuance or burn series. Buybacks (USD) start 2026-04-23. H5 keeps its pre-registered denominator (implied circulating supply growth). Total supply growth, which is net of burn, is added as a second denominator. Buybacks are used only descriptively, as a share of retained revenue after 2026-04-23.

## Amendment 5 (2026-11-05): peer batch 1 checked and NEAR series availability confirmed, written before peer batch 2 was loaded

No hypothesis test had been run when this amendment was written.

**Peer batch 1 (390 rows, 2024-01-07 to 2025-06-29)**
- Row counts and per-asset revenue sums match the source's own totals. No duplicate or missing weeks.
- Protocol revenue equals transaction fees for APT and AVAX in every week. It exceeds fees for ETH, SOL and SUI (on average about 20%, 50% and 5% of revenue), consistent with priority fees, MEV and tips for ETH and SOL, and storage and MEV payments for SUI.
- NEAR has no tips, blob or data-cost line items (Blockworks methodology), so NEAR transaction fees remain the like-for-like measure against peers' protocol revenue, as fixed in Amendment 4.
- Implied circulating supply has large steps: APT jumps about 7% to 8% in one week each month (consistent with scheduled unlocks) and SUI jumps about 80% in the week ending 2024-05-05. Market-cap-based results use the fixed-supply robustness check from Amendment 1.

**NEAR series availability (as reported by the source's chat assistant, not checked against documentation by me)**
- Token issuance and token burn are not available through the data interface. The fallback in Amendment 4, rule 4 applies: H5 uses implied circulating supply growth. Blockworks' total supply series (from 2024-01-01) is added as a robustness check.
- An Intents buybacks series (USD) exists from 2026-04-23. DefiLlama reports buybacks from 2026-02-23. The two start dates disagree. Buyback data is used descriptively only, because it covers under seven months.

## Amendment 6 (2026-11-05): total supply and buyback series verified, written before any hypothesis test

**Verified**
- NEAR total supply, weekly: 148 rows (2024-01-07 to 2026-11-01); sum matches the source's total exactly.
- NEAR Intents buybacks, daily: 196 rows (2026-04-23 to 2026-11-04); sum matches the source's total exactly.

**Findings from the data-quality check**
- Total supply is exactly unchanged for 27 consecutive weeks (2024-04-07 to 2024-10-06), then steps up by 31.6M NEAR (2.67%) in the week ending 2024-10-13, the same week as the circulating-supply step recorded in Amendment 1. The 2024 total supply series cannot be used for net issuance before 2024-10-13.
- Weekly total supply growth falls from about 1.15M to 1.2M NEAR per week (about 4.8% a year) to about 0.6M per week (about 2.4% a year) between the weeks ending 2025-10-26 and 2025-11-09. The cause is not in the data.
- Buybacks equal about 71% of retained (non-gas) revenue on the median day (interquartile range 0.67 to 0.77), with a daily correlation of 0.96, and never exceed it. The ratio is stable across the phases of the exploratory window (0.65 to 0.72).

**Decisions fixed now**
1. Total supply from 2024-04-07 to 2024-10-06 is treated as missing. Any total-supply-based figure starts from the week ending 2024-10-13. Total supply growth is analysed separately before and after 2025-11-02.
2. H5 as written compares retained revenue with issuance, and retained revenue is zero before 2025-09-23. It will pass by construction, so it is reported as descriptive, not as a test. The informative quantities are reported instead: buybacks as a share of retained revenue and as a share of the dollar value of net new supply.
3. Rule 4 of Amendment 1 still applies: no hypothesis test is run until the second peer batch is loaded and verified.

## Amendment 7 (2026-11-06): results recorded, stale watch thresholds withdrawn, written after the confirmatory tests were run

**Status of the pre-registered hypotheses (full output in confirmatory_results.txt)**
- H1 rejected on all three bases (the elasticity confidence intervals exclude 1). H2 not supported. H3 supported on the two like-for-like bases (NEAR gas fees against peers) and rejected on the not-like-for-like basis (NEAR total revenue). H4 not supported. H5 reported as descriptive.
- Every result is reported in the thesis, including the ones against the exploratory ideas that motivated H1 and H2.

**Withdrawn**
- The "tentative falsification watch" above (28-day average token-denominated revenue of about 19,000 and 13,000 NEAR per day) was derived from the exploratory claim withdrawn in Amendment 3. It is withdrawn.

**Replacement monitor (judgement calls, fixed now, before any later data is seen)**
- Strengthens the thesis: 28-day average retained Intents revenue of at least $100,000 per day for 84 consecutive days. That is about 1.5 times the latest 28-day average of $67,000.
- Weakens the thesis: 28-day average retained Intents revenue of at most $30,000 per day for 56 consecutive days. That is about the level before the September 2026 surge ($25,800 per day, 2026-08-07 to 2026-09-02).
- Reference point: buybacks fully offset net new supply at today's price only if revenue is about 9.4 times the trailing 91-day run-rate (about $191 million a year).

**Post-hoc analyses (not in this document before the tests; exploratory)**
- Monthly revenue composition, the link between Intents revenue and absolute daily price moves, the concentration of Intents revenue in the top 10% of days, and the revenue-multiple and price sensitivity grid. All are in scenarios.py and labelled there.

## Data correction log (2026-11-11)

Appended after the confirmatory tests. No earlier text in this document is changed.

- The committed clean data files were first typed by hand from the raw exports.
- On 2026-11-11 they were rebuilt from the seven raw files (`raw_*.csv`) with `build_clean_data.py`. This fixed the blank 2024 `tx` column in `near_daily.csv` (366 days now filled; 2025 and 2026 values unchanged) and the rounded peer values in `peers_weekly.csv` from the week ending 2025-07-06 (now full precision).
- Results are unchanged apart from one SUI p-value: the SUI holdout p-value in `confirmatory_results.txt` moves from 0.938 to 0.939. The unrounded peer P/S values in `confirmatory_numbers.json` move by less than 1 part in 10 million. `scenarios_results.txt` and `dashboard.html` are unchanged.
- No hypothesis, threshold or verdict changed.
- `build_clean_data.py` now writes LF line endings, so `MANIFEST.sha256` matches on every operating system. No cleaning rule changed.

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

## Amendment 8a (2026-11-11)

S2 excludes 2026-11-11, the day of the pull, because it is a partial day; this was decided before any extension test was run. S1’s last day (2026-11-10) is not used in any test, since Blockworks data ends 2026-11-04.

## Amendment 8b (2026-11-11): DefiLlama raw data no longer published

DefiLlama’s terms do not allow its data to be republished or mirrored without permission, so the raw DefiLlama responses (S1) are removed from the repository and from its git history. This changes rule 1 of Amendment 8 for S1 only: the raw S1 responses are no longer kept in the repository with SHA-256 hashes. Instead pull_defillama_intents.py pulls them locally (free API, no key), erify_data.py checks their row counts and date coverage, and the E1 to E3 and X1 numbers are compared with the values first committed, within stated tolerances (extension_expected.json). The test windows were already fixed by date and are unchanged; the S1 volume series is now also cut to start on 2024-12-10, the first day of the original pull. No test, threshold or verdict rule changes. S2 (BigQuery) is unaffected and keeps its hash.

## Amendment 8c (2026-11-12)

confirmatory_results.txt prints no verdict line for H1 or H4. The verdicts below apply the rules written in H1 and H4 to the printed numbers; no result, threshold or rule changes. H1: rejected on all three bases (A gas fees, B total revenue, C Intents revenue), because each elasticity 95% CI excludes 1. H4: not supported, because the support conditions are not met (active-address trend p=0.376; revenue-per-active-address trend p=0.082).

## Amendment 9 (2026-11-12)

S4: NEAR public BigQuery bigquery-public-data.crypto_near_mainnet_us.transactions, daily count of transactions with receiver_account_id = 'intents.near' and distinct signer_account_id, from 2025-01-01 to the latest complete day (the day of the pull is excluded), with a block_date filter. Caveat declared in advance: calls to the settlement contract are a proxy for swap activity, not swaps; one call may settle several intents. F1: Spearman(daily S4 call count, daily S1 DefiLlama volume) over at least 120 overlapping days; 0.50 or higher means ‘S4 tracks volume’, otherwise ‘S4 does not track volume’. F2: ratio of mean daily S4 call count in window B (2026-09-17 to 2026-10-15) to window A (2026-08-07 to 2026-09-02); 2.0 or higher means ‘on-chain Intents calls rose broadly with revenue’, 1.3 or lower means ‘calls did not rise materially’, otherwise ‘in between’. If F1 says ‘does not track volume’, F2 is still reported but labelled ‘proxy not validated’. No other thresholds or tests are added.
