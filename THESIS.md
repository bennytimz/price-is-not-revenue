# Price Is Not Revenue: the 9.4x Question

**NEAR is an option on Intents revenue, not yet a cash-flow story.**

*Investment Thesis track. Data as of 2026-11-04. Research, not investment advice. Every number here is in `confirmatory_results.txt`, `scenarios_results.txt` or `extension_results.txt`; `python run_all.py` rebuilds them and the dashboard from the data files in this folder.*

## The claim

About 93% of NEAR's protocol revenue now comes from one source, revenue retained from NEAR Intents, which recently grew about fourfold. That revenue is real, but it is volatile, it does not move one-for-one with NEAR's price, and at today's rate of new token supply it would have to grow roughly nine times before buybacks offset dilution. NEAR is therefore best treated as an **option on Intents monetisation**, not a business valued on cash flow. The numbers that would change this view are fixed in advance.

## Evidence for

**1. The revenue base changed, and the new source is large.** Until 2025-09-22 protocol revenue equals gas fees exactly. Afterwards retained Intents revenue appears and dominates: 53% of revenue in October 2025, 91% or more from April 2026. Blockworks' methodology describes network revenue as base-chain fees plus retained Intents revenue. Retained Intents revenue averaged about $0.48M a month from October 2025 to August 2026, then $1.78M in September 2026 and $2.20M in October. An independent public source agrees on the level (post-hoc check X1): over 406 days, DefiLlama's daily Intents revenue sums to 0.998 of Blockworks' retained Intents revenue, with a daily rank correlation of 0.71.

**2. Chain-level monetisation is weak, so the thesis cannot rest on gas.** Annualised gas fees are about $1.4M, so market cap is about 3,900 times chain fees, above every peer (next highest is SUI at 2,327 times). Gas fees measured in NEAR fell about 3.9% every four weeks across the sample (p<0.001). H3 on the two like-for-like bases (NEAR gas fees against peers) was supported.

**3. Revenue is behaviourally driven, not mechanically price-driven.** Total revenue rises less than one-for-one with price (elasticity 0.48, CI 0.37 to 0.59). Post-hoc, Intents revenue tracks absolute daily price moves (correlation 0.38, n=401) and is concentrated: the top 10% of days produce 37% of it.

## Evidence against

**1. Dilution dwarfs revenue.** Net new supply is about 31.9 million NEAR a year (2.43% of supply, about $137M at $4.28), after halving in late 2025. Trailing 91-day revenue is about $20M a year, covering about 15% of it. Buybacks have been about 72% of Intents revenue since 2026-04-23, offsetting about 11%. Buybacks fully offset new supply only at about $191M a year of revenue, 9.4 times today's run-rate.

**2. The valuation signal flips with the definition.** On total revenue NEAR is 276 times sales, below the peer median of 647 and at the 12th percentile of its own history. On gas fees it is 3,928 times. H3 was supported on the first and rejected on the second. So "expensive" is a statement about which revenue counts, not about the price.

**3. Intents revenue does not come with more on-chain accounts (post-hoc).** From the pre-rally window to the rally window (index = 100): Intents revenue 320, gas fees in USD 494, gas fees in NEAR 178, transactions 130, active addresses 87. In the pullback: 218, 251, 96, 86, 71. Weekly rank correlations after the April 2026 break (31 weeks): Intents revenue with gas fees 0.91, with transactions 0.15, with active addresses -0.76. The negative active-address figure is confounded by a steady decline in active addresses over those months, so read it as "no support for usage growth", not as an inverse effect. Blockworks' active-address series has a definition break on 2026-04-02 (see below), but every window and week here is after it, so these comparisons stay within one definition. The public on-chain count points the same way (exploratory X3, same windows, pre = 100): distinct signers 95 in the rally and 65 in the pullback, while Intents volume was 163 and 122.

**4. Several of my own ideas failed.** H1 (revenue is price pass-through) was rejected on all three bases. H2 (activity leads price) looked significant in the fit period (p=0.018) but flipped sign out of sample (R-squared -76%) and appeared for no peer. H4 (usage not monetised) was not supported (active addresses flat before April 2026, p=0.38; revenue per address falling, p=0.08, not significant). Two early exploratory claims were withdrawn when the revenue source turned out not to be NEAR-denominated.

**5. Value capture is partial.** Retained Intents revenue goes to NEAR-owned wallets; Blockworks counts only NEAR bought back with it as token-holder income. The 28% not bought back is not distributed.

## Public-source cross-checks (pre-registered, Amendment 8)

So the thesis does not rest on Blockworks alone, I added two free public sources: DefiLlama's API for NEAR Intents daily volume and revenue, and NEAR's public BigQuery dataset for daily transactions and distinct signing accounts. The five tests and their thresholds were committed in Amendment 8 before any of this data was pulled, and Amendment 8a fixed which days are used (it drops the partial day of the BigQuery pull) before any test ran. Results are in `extension_results.txt` and are reported whatever they show.

| Test | Question | Result | Verdict |
|---|---|---|---|
| E1 | Does Blockworks revenue track Intents activity? | Spearman 0.813 over 406 days (needs 0.50) | **usable proxy** |
| E2 | Did the Sep-Oct revenue jump come from volume or take rate? | volume share 0.418 (volume-driven needs 0.70, take-rate-driven 0.30 or less) | **mixed** |
| E3 | Does Intents volume lead on-chain usage better than price? | difference -0.158 (needs +0.15) | **not supported** |
| E4 | Is the 2026-04-02 drop in activity real on chain? | on-chain signers fell 8.1% (under 20%) | **probably a Blockworks definition change** |
| E5 | Do Blockworks active addresses and on-chain signers measure the same thing? | Spearman of daily changes 0.479 (needs 0.60) | **inconsistent** |

**What this means in plain English.**

- **E1:** Blockworks' retained Intents revenue moves with DefiLlama's Intents volume, so it is a fair stand-in for Intents activity.
- **E2:** From the August window (2026-08-07 to 09-02) to the rally window (09-17 to 10-15), volume rose 1.627 times but revenue rose 3.204 times, because the take rate went from 2.61 to 5.13 basis points. Less than half of the jump came from more volume.
- **E3: the track's example idea is not supported here.** The 4-week change in Intents volume was a weaker guide to the next 4 weeks of on-chain signers (rank correlation +0.178) than the 4-week NEAR price return was (+0.336).
  - **Caveat on E3's interval.** Its 95% bootstrap interval, -0.445 to +0.124, resamples single weeks, while the 4-week windows overlap. That interval is probably too narrow, which is why Amendment 8 claims no significance. The verdict fails on the size condition in any case.
- **E5:** Blockworks' active addresses and on-chain distinct signers do not move together closely enough, day to day, to be treated as the same measure.

**Blockworks active addresses has a definition break at 2026-04-02.** Three results support this:
- **E4:** across the 28 days either side of the date, the public on-chain count of distinct signers fell 8.1%.
- **X2 (exploratory):** over the same days, Blockworks active addresses fell 89.4% (median 2,363,792 to 250,503).
- **E5:** over the whole period the two series are inconsistent.

**Which earlier statements depend on that series, and whether they still hold:**

- **H4** (usage not monetised) was fitted separately before the break (29 blocks), after it (3 blocks), and on the full sample with a break term. The pre-break result lies within one definition and still holds: active addresses +0.9% per block, p=0.376; revenue per active address -2.8% per block, p=0.082. The post-break fit has only 3 blocks and was never used for a conclusion.
- **Evidence against 3** (index table and the 31-week correlations) uses only days after the break. It still holds as a statement about Blockworks' post-break series, and the on-chain count agrees in direction (X3).
- **The incomplete-day flags** use active addresses but are computed separately on each side of the break.
- **H2** uses gas fees in NEAR, not active addresses, so it is unaffected.

**Exploratory, not pre-registered, not a forecast.**

- **X1:** DefiLlama's daily Intents revenue sums to 0.998 of Blockworks' total over 406 days, with a daily rank correlation of 0.710. This is the independent cross-check of the revenue level.
- **X3:** in the section-3 windows, Intents volume indexed to 163 in the rally and 122 in the pullback, and distinct signers to 95 and 65.
- **X4** (arithmetic only): the $191M a year of retained revenue that offsets dilution would take about $1.02B a day of Intents volume at window B's take rate (6.3 times window B's volume), or $2.01B a day at window A's (12.5 times).

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

- **A documented definition of Intents volume.** Volume is now computed from DefiLlama (E1 to E3), but DefiLlama's methodology field for the NEAR Intents volume series is empty, so I cannot say exactly what it counts. The Intents Explorer sampling (S3, `optional_intents_explorer_sample.py`) was not run, so there is no second volume source.
- **What Blockworks changed on 2026-04-02.** The extension shows the break is probably a definition change rather than a fall in on-chain activity (E4, X2, E5), but I have not found what changed in Blockworks' active-address definition.
- **The NEAR/USDC split of retained revenue.** Blockworks says it arrives in NEAR or USDC; the mix is not in the data.
- **Like-for-like peer revenue.** Peers' revenue is reported to be network-level only, and I could not verify each definition myself.
- **Anything beyond 949 confirmatory days.** One regime; the Intents period is about 14 months.

## Method and provenance

Hypotheses and rejection rules were written before the long history was loaded (`PREREGISTRATION.md`, dated amendments 1 to 8a including claims I withdrew, plus a data correction log). The repository was created after the baseline analysis, so git history cannot prove that order; the dated amendments are the record. The public-source extension is different: Amendment 8 was pushed before its data was pulled, so git history does show that order. Confirmatory sample 2024-01-01 to 2026-08-06; the last three months are an exploratory window. Baseline data is from Blockworks, pulled through its MCP in ChatGPT, checked against row counts and the source's own revenue totals for every series, and rebuilt from the raw exports with `build_clean_data.py`. Blockworks is a third-party source that needs an API key to re-pull, so the committed CSV files are the reproducible input. The cross-checks use DefiLlama's free API and NEAR's public BigQuery dataset, saved unmodified with SHA-256 hashes in `RAW_PULLS.sha256`.

*Built by Benny (GitHub: Bennytimz) with AI assistance: Claude for analysis and drafting, ChatGPT with the Blockworks MCP for data pulls.*
