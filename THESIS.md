# Price Is Not Revenue: the 9.4x Question

**NEAR is an option on Intents revenue, not yet a cash-flow story.**

*Investment Thesis track. Data as of 2026-11-04. Research, not investment advice. Every number here is in `confirmatory_results.txt` or `scenarios_results.txt`; `python run_all.py` rebuilds them and the dashboard from the CSV files in this folder.*

## The claim

About 93% of NEAR's protocol revenue now comes from one source, revenue retained from NEAR Intents, which recently grew about fourfold. That revenue is real, but it is volatile, it does not move one-for-one with NEAR's price, and at today's rate of new token supply it would have to grow roughly nine times before buybacks offset dilution. NEAR is therefore best treated as an **option on Intents monetisation**, not a business valued on cash flow. The numbers that would change this view are fixed in advance.

## Evidence for

**1. The revenue base changed, and the new source is large.** Until 2025-09-22 protocol revenue equals gas fees exactly. Afterwards retained Intents revenue appears and dominates: 53% of revenue in October 2025, 91% or more from April 2026. Blockworks' methodology describes network revenue as base-chain fees plus retained Intents revenue, and DefiLlama's trailing-30-day Intents revenue to 2026-10-23 (about $2.12M) matches Blockworks' non-gas figure (about $2.15M). Retained Intents revenue averaged about $0.48M a month from October 2025 to August 2026, then $1.78M in September 2026 and $2.20M in October.

**2. Chain-level monetisation is weak, so the thesis cannot rest on gas.** Annualised gas fees are about $1.4M, so market cap is about 3,900 times chain fees, above every peer (next highest is SUI at 2,327 times). Gas fees measured in NEAR fell about 3.9% every four weeks across the sample (p<0.001). H3 on the two like-for-like bases (NEAR gas fees against peers) was supported.

**3. Revenue is behaviourally driven, not mechanically price-driven.** Total revenue rises less than one-for-one with price (elasticity 0.48, CI 0.37 to 0.59). Post-hoc, Intents revenue tracks absolute daily price moves (correlation 0.38, n=401) and is concentrated: the top 10% of days produce 37% of it.

## Evidence against

**1. Dilution dwarfs revenue.** Net new supply is about 31.9 million NEAR a year (2.43% of supply, about $137M at $4.28), after halving in late 2025. Trailing 91-day revenue is about $20M a year, covering about 15% of it. Buybacks have been about 72% of Intents revenue since 2026-04-23, offsetting about 11%. Buybacks fully offset new supply only at about $191M a year of revenue, 9.4 times today's run-rate.

**2. The valuation signal flips with the definition.** On total revenue NEAR is 276 times sales, below the peer median of 647 and at the 12th percentile of its own history. On gas fees it is 3,928 times. H3 was supported on the first and rejected on the second. So "expensive" is a statement about which revenue counts, not about the price.

**3. Intents revenue does not come with more on-chain accounts (post-hoc).** From the pre-rally window to the rally window (index = 100): Intents revenue 320, gas fees in USD 494, gas fees in NEAR 178, transactions 130, active addresses 87. In the pullback: 218, 251, 96, 86, 71. Weekly rank correlations after the April 2026 break (31 weeks): Intents revenue with gas fees 0.91, with transactions 0.15, with active addresses -0.76. The negative active-address figure is confounded by a steady decline in active addresses over those months, so read it as "no support for usage growth", not as an inverse effect.

**4. Several of my own ideas failed.** H1 (revenue is price pass-through) was rejected on all three bases. H2 (activity leads price) looked significant in the fit period (p=0.018) but flipped sign out of sample (R-squared -76%) and appeared for no peer. H4 (usage not monetised) was not supported (active addresses flat before April 2026, p=0.38; revenue per address falling, p=0.08, not significant). Two early exploratory claims were withdrawn when the revenue source turned out not to be NEAR-denominated.

**5. Value capture is partial.** Retained Intents revenue goes to NEAR-owned wallets; Blockworks counts only NEAR bought back with it as token-holder income. The 28% not bought back is not distributed.

## What would change my mind

Fixed before any later data (`PREREGISTRATION.md`, Amendment 7). These are judgement calls.

- **Strengthens:** 28-day average retained Intents revenue of at least $100,000 a day for 84 consecutive days (latest: $67,000).
- **Weakens:** at or below $30,000 a day for 56 consecutive days (the level before the September 2026 surge was $25,800).
- **Reference point:** about $191M a year for buybacks to offset today's dilution.

| Revenue vs trailing 91-day run-rate | Revenue a year | Price to sales now | Coverage of new supply at $2 / $4.28 / $8 |
|---|---|---|---|
| 1x | $20M | 276x | 32% / 15% / 8% |
| 4x | $81M | 69x | 127% / 59% / 32% |
| 8x | $163M | 35x | 255% / 119% / 64% |
| 12x | $244M | 23x | 382% / 178% / 96% |

A sensitivity, not a forecast. Revenue is held in dollars; a higher NEAR price makes coverage harder. The interactive version is in `dashboard.html`.

## What I could not compute

- **Intents swap volume and take rate.** Blockworks gives retained revenue but not volume, so I cannot say whether growth came from volume or fees, or test whether Intents volume leads on-chain usage better than price. `optional_intents_explorer_sample.py` is written to sample volume from the Explorer API but has not been run.
- **A public-chain cross-check.** I have not yet verified Blockworks' active-address and transaction series against NEAR's BigQuery dataset, so the 2026-04-02 break is unexplained. `optional_bigquery_daily_usage.sql` is written but not run, and NEAR's docs say the upstream indexer stopped on 2026-03-24, so the dataset may not cover the break.
- **The NEAR/USDC split of retained revenue.** Blockworks says it arrives in NEAR or USDC; the mix is not in the data.
- **Like-for-like peer revenue.** Peers' revenue is reported to be network-level only, and I could not verify each definition myself.
- **Anything beyond 949 confirmatory days.** One regime; the Intents period is about 14 months.

## Method and provenance

Hypotheses and rejection rules were written before the long history was loaded (`PREREGISTRATION.md`, seven dated amendments including claims I withdrew). The repository was created after the analysis, so git history cannot prove that order; the dated amendments are the record. Confirmatory sample 2024-01-01 to 2026-08-06; the last three months are an exploratory window. All data is from Blockworks, pulled through its MCP in ChatGPT, and checked against row counts and the source's own revenue totals for every series. Blockworks is a third-party source that needs an API key to re-pull, so the committed CSV files are the reproducible input.

*Built by Benny (GitHub: Bennytimz) with AI assistance: Claude for analysis and drafting, ChatGPT with the Blockworks MCP for data pulls.*
