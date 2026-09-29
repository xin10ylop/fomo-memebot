#!/usr/bin/env python3
"""Every Uniswap v4 pool initialized on Robinhood Chain in a window (all launchpads that launch into v4: Doppler/LONG, the
pools.trade-style launchers, the Multicall-driven ones, Pons graduations), with every swap on each pool in its first 20
minutes and a launcher sample per pool family. Public RPC: 429 backoff, 10,000-log and 100-topic limits handled by splitting.

    python3 src/analysis/v4_launch_pull.py "2026-09-28 21:00" "2026-09-29 21:00" data/derived/edge_check/O/v4_24h.json
"""
import json, sys, time, calendar, urllib.request, urllib.error, collections
from eth_utils import keccak
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 Chrome/128", "Accept": "application/json"}
PM = "0x8366a39cc670b4001a1121b8f6a443a643e40951"; AIRLOCK = "0xeb7c034704ef8dcd2d32324c1545f62fb4ad0862"
T_INIT = "0x" + keccak(text="Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)").hex(); T_SWAP = "0x" + keccak(text="Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)").hex()
HORIZON = 12000; BATCH = 100
W = lambda d, i: int(d[2 + 64*i: 2 + 64*(i+1)], 16); A = lambda d, i: d[2 + 64*i + 24: 2 + 64*(i+1)]
def signed(x): return x - (1 << 256) if x >= (1 << 255) else x
calls = [0]
def rpc(m, p):
    for i in range(10):
        try:
            calls[0] += 1
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(), H), timeout=90))
            if "error" in r:
                msg = str(r["error"])
                if "exceeds limit" in msg or "max topics" in msg: raise OverflowError(msg)
                raise RuntimeError(msg[:160])
            return r["result"]
        except OverflowError:
            raise
        except urllib.error.HTTPError as e:
            time.sleep(min(60, 4 * (i + 1)) if e.code == 429 else 2 + i)
        except Exception:
            if i == 9: raise
            time.sleep(2 + 2 * i)
    raise RuntimeError("rpc gave up")
def logs(flt, a, b):
    """getLogs over [a, b], split in halves when a range returns more than the node allows"""
    try:
        return rpc("eth_getLogs", [dict(flt, fromBlock=hex(a), toBlock=hex(b))])
    except OverflowError:
        if b <= a: raise
        m = (a + b) // 2; return logs(flt, a, m) + logs(flt, m + 1, b)
def block_at(ts):
    lo, hi = 1, int(rpc("eth_blockNumber", []), 16)
    while lo < hi:
        mid = (lo + hi) // 2
        if int(rpc("eth_getBlockByNumber", [hex(mid), False])["timestamp"], 16) < ts: lo = mid + 1
        else: hi = mid
    return lo
def main():
    t_lo = calendar.timegm(time.strptime(sys.argv[1], "%Y-%m-%d %H:%M")); t_hi = calendar.timegm(time.strptime(sys.argv[2], "%Y-%m-%d %H:%M")); out = sys.argv[3]
    b_lo, b_hi = block_at(t_lo), block_at(t_hi); t0 = time.time(); print(f"blocks {b_lo}-{b_hi}", flush=True)
    pools = {}
    for a in range(b_lo, b_hi, 29999):
        for l in logs({"address": PM, "topics": [T_INIT]}, a, min(a + 29998, b_hi)):
            d = l["data"]; pools[l["topics"][1]] = {"bn": int(l["blockNumber"], 16), "tx": l["transactionHash"], "c0": l["topics"][2][-40:], "c1": l["topics"][3][-40:], "fee": W(d, 0), "ts": signed(W(d, 1)), "hook": A(d, 2), "sqrtP0": W(d, 3), "tick0": signed(W(d, 4))}
    print(f"{len(pools)} pools initialized ({time.time()-t0:.0f} s, {calls[0]} calls)", flush=True)
    doppler = set()
    for a in range(b_lo, b_hi, 29999):
        for l in logs({"address": AIRLOCK}, a, min(a + 29998, b_hi)): doppler.add(A(l["data"], 0))
    swaps = collections.defaultdict(list); pids = sorted(pools, key=lambda p: pools[p]["bn"])
    for i in range(0, len(pids), BATCH):
        batch = pids[i:i+BATCH]; lo_b = min(pools[p]["bn"] for p in batch); hi_b = max(pools[p]["bn"] for p in batch) + HORIZON
        for a in range(lo_b, hi_b, 29999):
            for l in logs({"address": PM, "topics": [T_SWAP, batch]}, a, min(a + 29998, hi_b)):
                pid = l["topics"][1]; bn = int(l["blockNumber"], 16)
                if bn <= pools[pid]["bn"] + HORIZON:
                    d = l["data"]; swaps[pid].append([bn, int(l["logIndex"], 16), l["topics"][2][-40:], signed(W(d, 0)), signed(W(d, 1)), W(d, 2), W(d, 3), W(d, 5), l["transactionHash"]])
        if (i // BATCH) % 10 == 0: print(f"  swaps for {i + len(batch)} of {len(pids)} pools: {sum(len(v) for v in swaps.values())} ({time.time()-t0:.0f} s, {calls[0]} calls)", flush=True)
    fam = collections.defaultdict(list)
    for p, v in pools.items():
        eth = "eth" if "0" * 40 in (v["c0"], v["c1"]) else "other"
        fam[(v["hook"][:10], v["fee"], v["ts"], eth, "doppler" if (v["c0"] in doppler or v["c1"] in doppler) else "")].append(p)
    launchers = {}
    for k, ps in sorted(fam.items(), key=lambda x: -len(x[1]))[:25]:
        seen = collections.Counter()
        for p in ps[:4]:
            try: seen[(rpc("eth_getTransactionByHash", [pools[p]["tx"]]).get("to") or "").lower()] += 1
            except Exception: pass
        launchers["|".join(map(str, k))] = {"n": len(ps), "to": seen.most_common(3)}
    json.dump({"window": [sys.argv[1], sys.argv[2]], "blocks": [b_lo, b_hi], "pools": pools, "doppler_assets": sorted(doppler), "swaps": dict(swaps), "families": launchers,
               "swap_fields": ["bn", "logIndex", "sender", "amount0", "amount1", "sqrtPriceX96", "liquidity", "fee", "tx"]}, open(out, "w"))
    print(f"wrote {out}: {len(pools)} pools, {sum(len(v) for v in swaps.values())} swaps ({time.time()-t0:.0f} s, {calls[0]} calls)", flush=True)
    for k, v in sorted(launchers.items(), key=lambda x: -x[1]["n"])[:12]: print(f"  family {k}: {v['n']} pools, launcher {v['to']}", flush=True)
main()
