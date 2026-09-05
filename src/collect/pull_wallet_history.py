#!/usr/bin/env python3
"""Full on-chain trade history of fomo-app wallets over weeks (report section 17).

For each wallet: UserOperationEvent logs with the wallet as sender (EntryPoint, indexed topic) give every transaction
the wallet made; the receipts of those transactions carry the Pons V2 curve Buy/Sell events, Uniswap v4 Swap events
and Uniswap v3 Swap events. Writes rh/history/{wallet}.jsonl with one line per event:
[block, txHash, kind, address_or_poolId, fields...] where kind is "curve_buy"/"curve_sell" (curve, quoteRaw, tokenRaw),
"v4" (poolId, amount0, amount1) or "v3" (pool, amount0, amount1). Read-only public RPC, batched receipts.

usage: python3 pull_wallet_history.py WALLETS.json FROM_BLOCK TO_BLOCK   (run from the data root)
"""
import json, urllib.request, time, sys, os

RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/history"}
EP = "0x0000000071727de22e5e9d8baf0edac6f37da032"; UOP = "0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
V4SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"; V3SWAP = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
PM = "0x8366a39cc670b4001a1121b8f6a443a643e40951"


def call(p, timeout=180):
    for i in range(8):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(p).encode(), headers=H); d = json.load(urllib.request.urlopen(req, timeout=timeout))
            if isinstance(d, dict) and "error" in d:
                raise RuntimeError(d["error"])
            return d
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def s256(x):
    return x - 2 ** 256 if x >= 2 ** 255 else x


wallets = json.load(open(sys.argv[1])); b_from = int(sys.argv[2]); b_to = int(sys.argv[3])
os.makedirs("rh/history", exist_ok=True)
for wi, w in enumerate(wallets):
    w = w.lower(); out_f = f"rh/history/{w}.jsonl"
    if os.path.exists(out_f + ".done"):
        continue
    txs = []; b = b_from; step = 4_000_000
    while b < b_to:
        e = min(b_to, b + step)
        r = call({"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [{"fromBlock": hex(b), "toBlock": hex(e - 1), "address": EP, "topics": [UOP, None, "0x" + w[2:].rjust(64, "0")]}]})
        if r is None:
            step = max(50_000, step // 2); continue
        for l in r["result"]:
            txs.append((int(l["blockNumber"], 16), l["transactionHash"]))
        b = e
        if len(r["result"]) < 500:
            step = min(16_000_000, step * 2)
        time.sleep(0.15)
    txs = sorted(set(txs)); out = open(out_f, "w"); n_ev = 0
    for i in range(0, len(txs), 20):
        ch = txs[i:i + 20]
        r = call([{"jsonrpc": "2.0", "id": j, "method": "eth_getTransactionReceipt", "params": [tx]} for j, (bb, tx) in enumerate(ch)])
        if not r:
            continue
        for x in r:
            rc = x.get("result") or {}; tx = rc.get("transactionHash"); bb = int(rc.get("blockNumber", "0x0"), 16)
            for l in rc.get("logs", []):
                t0 = l["topics"][0] if l.get("topics") else ""; d = l["data"][2:]; ws = [int(d[k:k + 64], 16) for k in range(0, len(d), 64)]
                if t0 in (BUY, SELL) and len(ws) >= 2:
                    out.write(json.dumps([bb, tx, "curve_buy" if t0 == BUY else "curve_sell", l["address"].lower(), ws[0], ws[1]]) + "\n"); n_ev += 1
                elif t0 == V4SWAP and l["address"].lower() == PM and len(ws) >= 2:
                    out.write(json.dumps([bb, tx, "v4", l["topics"][1], s256(ws[0]), s256(ws[1])]) + "\n"); n_ev += 1
                elif t0 == V3SWAP and len(ws) >= 2:
                    out.write(json.dumps([bb, tx, "v3", l["address"].lower(), s256(ws[0]), s256(ws[1])]) + "\n"); n_ev += 1
        time.sleep(0.2)
    out.close(); open(out_f + ".done", "w").write(str(len(txs)))
    print(f"{wi + 1}/{len(wallets)} {w[:12]} txs {len(txs)} events {n_ev}", file=sys.stderr, flush=True)
