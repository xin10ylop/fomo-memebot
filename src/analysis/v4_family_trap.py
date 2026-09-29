#!/usr/bin/env python3
"""Every ETH-paired v4 launch family (hook|fee|tick spacing), measured for what a sniper needs to know: launches a day, the crowd's
timing, liquidity pulls within 20 minutes, and the trap test (what happens after an outsider buys before the crowd: does the crowd
still come, and how fast is the liquidity pulled). Pulls the ModifyLiquidity events itself.

    python3 src/analysis/v4_family_trap.py data/derived/edge_check/O/v4_24h.json
"""
import json, sys, collections, statistics as st, urllib.request, urllib.error, time
from eth_utils import keccak
D = json.load(open(sys.argv[1])); pools = D["pools"]; swaps = D["swaps"]; ZERO = "0"*40
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 Chrome/128", "Accept": "application/json"}
def rpc(m, p):
    for i in range(12):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(), H), timeout=90))
            if "error" in r: raise RuntimeError(str(r["error"]))
            return r["result"]
        except urllib.error.HTTPError: time.sleep(4 * (i + 1))
        except RuntimeError: raise
        except Exception: time.sleep(3)
def sgn(x): return x - (1 << 256) if x >= (1 << 255) else x
T_ML = "0x" + keccak(text="ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)").hex(); PM = "0x8366a39cc670b4001a1121b8f6a443a643e40951"
eth_pools = sorted([pid for pid, p in pools.items() if ZERO in (p["c0"], p["c1"]) and p["fee"] <= 30000], key=lambda p: pools[p]["bn"])
RUG = collections.defaultdict(list)
for i in range(0, len(eth_pools), 100):
    b = eth_pools[i:i+100]; lo = min(pools[p]["bn"] for p in b); hi = max(pools[p]["bn"] for p in b) + 12000
    for a in range(lo, hi, 29999):
        for l in rpc("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(min(a + 29998, hi)), "address": PM, "topics": [T_ML, b]}]):
            pid = l["topics"][1]
            if sgn(int(l["data"][2+128: 2+192], 16)) < 0 and int(l["blockNumber"], 16) <= pools[pid]["bn"] + 12000: RUG[pid].append(int(l["blockNumber"], 16) - pools[pid]["bn"])
json.dump({"removals": RUG}, open(sys.argv[1].replace(".json", "_rug_all.json"), "w"))
fams = collections.defaultdict(list)
for pid in eth_pools:
    p = pools[pid]; fams[f"{p['hook'][:8]}|{p['fee']}|{p['ts']}"].append(pid)
print(f"{sys.argv[1]}: {len(eth_pools)} ETH-paired launches")
print(f"{'family':22s} {'n':>5s} {'w/ buyers':>9s} {'crowd@':>6s} {'crowd30s':>8s} {'ETH30s':>6s} {'rug20m':>6s} {'rug<10s':>7s} | trap test: early outsider buys, crowd after, rug gap")
for f, ps in sorted(fams.items(), key=lambda x: -len(x[1]))[:14]:
    rows = []; traps = []
    for pid in ps:
        p = pools[pid]; sw = sorted(swaps.get(pid, []), key=lambda x: (x[0], x[1])); e0 = p["c0"] == ZERO; b0 = p["bn"]
        eth = lambda x: -(x[3] if e0 else x[4]) / 1e18
        reals = [x for x in sw if eth(x) >= 1e-4 and x[0] > b0]
        rug = min(RUG[pid]) if RUG.get(pid) else None
        if not reals: rows.append({"buyers": False, "rug": rug}); continue
        offs = [x[0] - b0 for x in reals]
        # the crowd's usual arrival: the family's median first-buy offset is computed after; here keep the first two
        rows.append({"buyers": True, "first": offs[0], "n30": sum(1 for o in offs if o <= 300), "eth30": sum(eth(x) for x in reals if x[0] - b0 <= 300), "rug": rug, "reals": offs, "small_first": eth(reals[0]) < 0.005})
    wb = [r for r in rows if r["buyers"]]
    if not wb: print(f"{f:22s} {len(ps):5d} no buyers"); continue
    crowd_at = st.median(r["first"] for r in wb)
    for r in wb:                                                  # trap test: a small buy clearly before the family's usual crowd time
        if r["small_first"] and r["first"] <= max(1, crowd_at - 4):
            later = [o for o in r["reals"][1:] if o <= 300]
            traps.append({"crowd": len(later), "gap": (r["rug"] - r["first"]) if r["rug"] is not None else None})
    tg = [t["gap"] for t in traps if t["gap"] is not None]
    trap_txt = f"n={len(traps)}, crowd median {st.median(t['crowd'] for t in traps) if traps else '-'}, rugged {len(tg)}/{len(traps)}, gap median {st.median(tg) if tg else '-'} blocks" if traps else "no early outsider buys"
    print(f"{f:22s} {len(ps):5d} {len(wb):9d} {crowd_at:6.0f} {st.median(r['n30'] for r in wb):8.0f} {st.median(r['eth30'] for r in wb):6.2f} {sum(1 for r in rows if r['rug'] is not None)/len(rows):6.0%} {sum(1 for r in rows if r['rug'] is not None and r['rug'] <= 100)/len(rows):7.0%} | {trap_txt}")
