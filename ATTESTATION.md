# On-chain timestamp of PREDICTIONS.md and MANIFEST.sha256 (NEAR testnet)

On 2026-11-13 the SHA-256 hashes of `PREDICTIONS.md` and `MANIFEST.sha256`, plus the git commit they were taken from, were written into a NEAR **testnet** transaction. Anyone can check them against the files in this repository without an account or a key.

## The record

| | |
|---|---|
| Transaction | `B2iUPpDuhskucJv5xWmRbrgZoFPf5jXqsiwveHp1tncR` |
| Network | NEAR testnet |
| Signer | `price-is-not-revenue.testnet` (an account created for this on 2026-11-13 with near-cli-rs 0.31.1 and the testnet faucet; its key stays on the author's PC) |
| Call | `set_greeting` on `hello.near-examples.testnet` (NEAR's public example contract), no deposit |
| Block | 277520136, 2026-11-13 14:07:41 UTC |
| Cost | 1.9 Tgas, fee 0.000163 testnet NEAR (testnet NEAR has no monetary value) |

The string in the transaction's arguments, exactly:

```
price-is-not-revenue sha256 PREDICTIONS.md=a026775cc3a3f7b3db7112b614037cc4241d4a55e213a41237887df726473de4 MANIFEST.sha256=fa54f13bceab390a084fc653c36f3057398c6ce42bffbae186516d1add953360 commit=fb06a52e336c25a4724f572ad5c0cec59ca9fbab
```

The hashes are of the files as stored in git at commit `fb06a52` (LF line endings).

## How to verify

1. **Script (no account, no key, Python standard library only):** `python verify_attestation.py`. It fetches the transaction from two independent public archival RPCs (`archival-rpc.testnet.fastnear.com`, `archival-rpc.testnet.near.org`), checks the signer, contract, method and success status, decodes the string, hashes the two files in this folder after normalising line endings to LF, and prints the block height, the UTC block time and MATCH or DIFFER for each file.
2. **Block explorer:** open https://testnet.nearblocks.io/txns/B2iUPpDuhskucJv5xWmRbrgZoFPf5jXqsiwveHp1tncR (or https://explorer.testnet.near.org/transactions/B2iUPpDuhskucJv5xWmRbrgZoFPf5jXqsiwveHp1tncR). It shows the signer, the `set_greeting` call with the string above in its arguments, and the block time.
3. **By hand:** in a clone, `git show fb06a52:PREDICTIONS.md | sha256sum` and `git show fb06a52:MANIFEST.sha256 | sha256sum`, and compare with the string. On Linux or macOS `sha256sum PREDICTIONS.md MANIFEST.sha256` on a checkout gives the same values; on Windows a checkout may have CRLF line endings, so use `git show` or the script.

The value the contract currently stores does not matter: anyone can call `set_greeting` and overwrite it. The evidence is the transaction itself (its arguments, signer and block), which stays in the chain's history.

## What this proves

- `PREDICTIONS.md` and `MANIFEST.sha256`, byte for byte as in commit `fb06a52` (after LF normalisation), existed **no later than 2026-11-13 14:07:41 UTC**. The record is outside GitHub and outside the author's control after it was sent.
- From that time on, any edit to either file is detectable. In particular the six predictions, their thresholds and their resolution rules cannot be changed before they resolve on 2027-03-31 without `verify_attestation.py` reporting DIFFER.
- The string also names commit `fb06a52e336c25a4724f572ad5c0cec59ca9fbab`. A git commit id is a hash over the whole repository tree at that commit, so it ties the attestation to one exact state of the repository. That hash is SHA-1, which is weaker than SHA-256.

## What this does not prove

- **`PREDICTIONS.md` is frozen as attested, including two flaws.** It is still titled "(draft, 2026-11-12)", and P4's claim quotes "My call" as "it earns a position only if retained revenue keeps compounding toward the break-even", a sentence reworded in `d03a1e9` that is no longer in `THESIS.md`. Both are left unchanged because the file is hashed on testnet; the thresholds and resolution rules are what count, and they are unchanged (Amendment 11).
- **It does not prove when the predictions were written.** `PREDICTIONS.md` was first committed in `808c329` at 2026-11-12T02:10:07+01:00 (2026-11-12 01:10:07 UTC). The on-chain timestamp is about 37 hours **later** than that commit. For the time between the two, only git history supports the dates, and git history can be rewritten. The timestamp also says nothing about when the pre-registration or the baseline analysis was done; `PREREGISTRATION.md` is not covered by a SHA-256 hash in the string.
- **It is testnet, not mainnet.** Testnet tokens have no value, so the network has little economic security. Its history is kept by archival nodes; on 2026-11-13 two independent operators still served testnet blocks from December 2023, but nothing guarantees that testnet history will be kept forever.
- **`MANIFEST.sha256` covers only the four clean baseline data files:** `near_daily.csv`, `peers_weekly.csv`, `near_total_supply_weekly.csv` and `near_buybacks_daily.csv`. Through the manifest, the attestation does not cover the raw exports (`raw_*.csv`), the BigQuery pulls, the code, the results files, `THESIS.md`, `README.md`, the dashboard or `PREREGISTRATION.md`. Those are covered only by the commit id above.
- **It does not prove who wrote anything.** It shows that whoever held the key of `price-is-not-revenue.testnet` sent these hashes at that time.
- **It does not make any number in the analysis more correct.** It only fixes the content of the two files in time.

## Files

- `ATTESTATION.md`: this file.
- `verify_attestation.py`: the verification script. It reads the two files and public RPCs and changes nothing.

No existing file was changed to add this, and no key or credential is in the repository.
