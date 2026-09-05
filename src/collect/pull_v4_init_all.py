#!/usr/bin/env python3
"""All Uniswap v4 PoolManager Initialize events since the chain's start (pool id -> currencies, fee, hooks), so that
trades on pools created before the replay day can be priced (report section 17). Writes rh/v4init_all.json.
usage: python3 pull_v4_init_all.py [toBlock]   (run from the data root)
"""
import json, urllib.request, time, sys, os

RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/v4init"}
PM = "0x8366a39cc670b4001a1121b8f6a443a643e40951"
INIT = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"


def call(p):
    for i in range(8):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(p).encode(), headers=H); d = json.load(urllib.request.urlopen(req, timeout=120))
            if "error" in d:
                raise RuntimeError(d["error"])
            return d["result"]
        except Exception:
            time.sleep(3 * (i + 1))
    raise RuntimeError("rpc failed")


b1 = int(sys.argv[1]) if len(sys.argv) > 1 else int(call({"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}), 16)
out_f = "rh/v4init_all.json"; out = json.load(open(out_f)) if os.path.exists(out_f) else {"to": 0, "pools": []}
b = out["to"]; step = 200_000; t0 = time.time()
while b < b1:
    e = min(b1, b + step)
    try:
        logs = call({"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [{"fromBlock": hex(b), "toBlock": hex(e - 1), "address": PM, "topics": [INIT]}]})
    except RuntimeError:
        step = max(2_000, step // 2); continue
    for l in logs:
        d = l["data"][2:]
        out["pools"].append({"b": int(l["blockNumber"], 16), "tx": l["transactionHash"], "pid": l["topics"][1], "c0": "0x" + l["topics"][2][-40:], "c1": "0x" + l["topics"][3][-40:], "fee": int(d[0:64], 16), "hooks": "0x" + d[128:192][-40:], "sqrtP": int(d[192:256], 16)})
    b = e; out["to"] = b
    if len(logs) < 1000:
        step = min(1_000_000, step * 2)
    if (b // step) % 5 == 0:
        json.dump(out, open(out_f, "w"))
    print(f"block {b}/{b1}, pools {len(out['pools'])}, {time.time() - t0:.0f}s", file=sys.stderr, flush=True)
    time.sleep(0.2)
json.dump(out, open(out_f, "w")); print(f"done: {len(out['pools'])} pools to block {b1}", file=sys.stderr)
