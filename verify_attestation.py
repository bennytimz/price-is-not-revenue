"""Verify the NEAR testnet attestation of PREDICTIONS.md and MANIFEST.sha256 (see ATTESTATION.md).

Fetches the attestation transaction from public archival RPCs (no account, no key, no install beyond Python),
decodes the string it carried, and compares the SHA-256 hashes in it with the files in this folder. Line endings
are normalised to LF before hashing (the files are stored in git with LF; a Windows checkout may have CRLF).
Prints the block height and UTC block time, and MATCH or DIFFER for each file. Changes nothing.

  python verify_attestation.py          exit 0 if both files match on at least one RPC and no RPC disagrees
"""
import base64
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.request

D = os.path.dirname(os.path.abspath(__file__))
TX_HASH = "B2iUPpDuhskucJv5xWmRbrgZoFPf5jXqsiwveHp1tncR"
SIGNER = "price-is-not-revenue.testnet"
RECEIVER = "hello.near-examples.testnet"
METHOD = "set_greeting"
RPCS = ["https://archival-rpc.testnet.fastnear.com", "https://archival-rpc.testnet.near.org"]  # two independent operators
FILES = ["PREDICTIONS.md", "MANIFEST.sha256"]


def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": "verify", "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "verify-attestation/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.load(r)
    if "error" in j:
        raise RuntimeError(json.dumps(j["error"])[:200])
    return j["result"]


def local_sha256(name):
    data = open(os.path.join(D, name), "rb").read().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def check(url):
    r = rpc(url, "tx", {"tx_hash": TX_HASH, "sender_account_id": SIGNER, "wait_until": "FINAL"})
    t = r["transaction"]
    fc = t["actions"][0]["FunctionCall"]
    if (t["signer_id"], t["receiver_id"], fc["method_name"]) != (SIGNER, RECEIVER, METHOD):
        raise RuntimeError(f"unexpected transaction: {t['signer_id']} -> {t['receiver_id']}.{fc['method_name']}")
    if "SuccessValue" not in r["status"]:
        raise RuntimeError(f"transaction did not succeed: {r['status']}")
    text = json.loads(base64.b64decode(fc["args"]))["greeting"]
    hdr = rpc(url, "block", {"block_id": r["transaction_outcome"]["block_hash"]})["header"]
    when = dt.datetime.fromtimestamp(hdr["timestamp"] / 1e9, dt.timezone.utc)
    return text, hdr["height"], when


def main():
    print(f"Attestation transaction {TX_HASH} by {SIGNER} ({METHOD} on {RECEIVER}, NEAR testnet)")
    results = []
    for url in RPCS:
        try:
            text, height, when = check(url)
        except Exception as e:  # report and try the next RPC
            print(f"   {url}: could not verify ({e})")
            continue
        print(f"   {url}: block {height}, {when:%Y-%m-%d %H:%M:%S} UTC")
        results.append((text, height, when))
    if not results:
        sys.exit("No RPC returned the transaction; nothing verified.")
    if len({r[:2] for r in results}) > 1:
        sys.exit("The RPCs disagree about the transaction; not verified.")
    text, height, when = results[0]
    print(f"   on-chain string: {text}")
    ok = True
    for name in FILES:
        m = re.search(rf"{re.escape(name)}=([0-9a-f]{{64}})", text)
        if not m:
            print(f"   {name}: no hash in the on-chain string")
            ok = False
            continue
        mine = local_sha256(name)
        same = mine == m.group(1)
        ok &= same
        print(f"   {name}: on chain {m.group(1)} | this folder {mine} | {'MATCH' if same else 'DIFFER'}")
    c = re.search(r"commit=([0-9a-f]{40})", text)
    if c:
        print(f"   commit in the string: {c.group(1)}")
    if ok:
        print(f"MATCH: both files are byte-identical (after LF normalisation) to what was hashed on NEAR testnet "
              f"no later than {when:%Y-%m-%d %H:%M:%S} UTC (block {height}).")
    else:
        sys.exit("DIFFER: at least one file differs from the attested version (or the string could not be read).")


if __name__ == "__main__":
    main()
