#!/usr/bin/env python3
"""Doppler (LONG and the other Airlock front-ends) on Robinhood Chain: every launch, its pool, and every swap on that pool in
its first 20 minutes, over a window. Public RPC, 30,000-block log chunks, topic filters so the swap volume of the rest of the
chain is never downloaded. Output: one JSON per window with creates, pools and swaps (raw fields), for the seat study.

    python3 src/analysis/doppler_pull.py "2026-09-26 21:00" "2026-09-29 21:00" data/derived/edge_check/O/doppler_3d.json
"""
import json, sys, time, calendar, urllib.request, collections
from eth_utils import keccak
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 Chrome/128", "Accept": "application/json"}
AIRLOCK = "0xeb7c034704ef8dcd2d32324c1545f62fb4ad0862"; PM = "0x8366a39cc670b4001a1121b8f6a443a643e40951"
T_INIT = "0x" + keccak(text="Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)").hex(); T_SWAP = "0x" + keccak(text="Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)").hex()
W = lambda d, i: int(d[2 + 64*i: 2 + 64*(i+1)], 16); A = lambda d, i: d[2 + 64*i + 24: 2 + 64*(i+1)]
def signed(x): return x - (1 << 256) if x >= (1 << 255) else x
def rpc(m, p):
    for i in range(6):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(), H), timeout=90))
            if "error" in r: raise RuntimeError(str(r["error"])[:120])
            return r["result"]
        except Exception as e:
            if i == 5: raise
            time.sleep(2 + 2 * i)
def block_at(ts):
    """binary search the first block at or after a unix time"""
    lo, hi = 1, int(rpc("eth_blockNumber", []), 16)
    while lo < hi:
        mid = (lo + hi) // 2; t = int(rpc("eth_getBlockByNumber", [hex(mid), False])["timestamp"], 16)
        if t < ts: lo = mid + 1
        else: hi = mid
    return lo
def main():
    t_lo = calendar.timegm(time.strptime(sys.argv[1], "%Y-%m-%d %H:%M")); t_hi = calendar.timegm(time.strptime(sys.argv[2], "%Y-%m-%d %H:%M")); out = sys.argv[3]
    b_lo = block_at(t_lo); b_hi = block_at(t_hi); print(f"blocks {b_lo}-{b_hi} ({b_hi - b_lo} blocks)", flush=True); t0 = time.time()
    creates = []
    for a in range(b_lo, b_hi, 29999):
        for l in rpc("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(min(a + 29998, b_hi)), "address": AIRLOCK}]):
            creates.append({"bn": int(l["blockNumber"], 16), "tx": l["transactionHash"], "numeraire": l["topics"][1][-40:] if len(l["topics"]) > 1 else None, "asset": A(l["data"], 0), "initializer": A(l["data"], 1), "w2": A(l["data"], 2)})
    print(f"{len(creates)} creates ({time.time()-t0:.0f} s)", flush=True)
    assets = {c["asset"] for c in creates}; pools = {}
    topics_assets = ["0x" + "0"*24 + a for a in assets]
    for a in range(b_lo, b_hi, 29999):
        for which in (2, 3):
            tp = [T_INIT, None, None]; tp[which - 1] = topics_assets
            for l in rpc("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(min(a + 29998, b_hi)), "address": PM, "topics": tp}]):
                d = l["data"]; pools[l["topics"][1]] = {"bn": int(l["blockNumber"], 16), "c0": l["topics"][2][-40:], "c1": l["topics"][3][-40:], "fee": W(d, 0), "tick_spacing": signed(W(d, 1)), "hook": A(d, 2), "sqrtP0": W(d, 3), "tick0": signed(W(d, 4)), "tx": l["transactionHash"]}
    print(f"{len(pools)} pools ({time.time()-t0:.0f} s)", flush=True)
    swaps = collections.defaultdict(list); pids = sorted(pools, key=lambda p: pools[p]["bn"])
    for i in range(0, len(pids), 300):
        batch = pids[i:i+300]; lo_b = min(pools[p]["bn"] for p in batch); hi_b = max(pools[p]["bn"] for p in batch) + 12000
        for a in range(lo_b, hi_b, 29999):
            for l in rpc("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(min(a + 29998, hi_b)), "address": PM, "topics": [T_SWAP, batch]}]):
                d = l["data"]; pid = l["topics"][1]
                if int(l["blockNumber"], 16) <= pools[pid]["bn"] + 12000:
                    swaps[pid].append({"bn": int(l["blockNumber"], 16), "ix": int(l["logIndex"], 16), "tx": l["transactionHash"], "a0": signed(W(d, 0)), "a1": signed(W(d, 1)), "sqrtP": W(d, 2), "liq": W(d, 3), "tick": signed(W(d, 4)), "fee": W(d, 5)})
        print(f"  swaps for {i + len(batch)} pools: {sum(len(v) for v in swaps.values())} ({time.time()-t0:.0f} s)", flush=True)
    launchers = collections.Counter()
    for c in creates[:400]:                                              # the front-end behind each create: the transaction's target (a sample of 400)
        try: c["launcher"] = (rpc("eth_getTransactionByHash", [c["tx"]]).get("to") or "").lower()
        except Exception: c["launcher"] = None
        launchers[c["launcher"]] += 1
    print("launchers (sample of 400):", launchers.most_common(6), flush=True)
    json.dump({"window": [sys.argv[1], sys.argv[2]], "blocks": [b_lo, b_hi], "creates": creates, "pools": pools, "swaps": dict(swaps)}, open(out, "w"))
    print(f"wrote {out} ({time.time()-t0:.0f} s)", flush=True)
main()
