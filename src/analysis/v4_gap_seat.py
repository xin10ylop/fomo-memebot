#!/usr/bin/env python3
"""The gap seat on the 1%-fee v4 launch family: fire only when the platform's dust test (a sub-0.0001 ETH buy from the test
wallet, blocks 2-7) appears, land in the first block after the test, sell one or two blocks after the first real crowd buy.
Our buy and sell are priced against the pool's real state (exact v4 single-range math, validated to the wei on 6,788 trades);
a liquidity pull before our sell is -100%. Stakes and landing delays are swept.

    python3 src/analysis/v4_gap_seat.py data/derived/edge_check/O/v4_24h.json [rug_json]
"""
import json, sys, collections, statistics as st, urllib.request, urllib.error, time
from eth_utils import keccak
D = json.load(open(sys.argv[1])); pools = D["pools"]; swaps = D["swaps"]; ZERO = "0"*40; Q = 2**96; ETHUSD, GAS = 2650.0, 0.05
TESTER = "e71a69f434a719cd5afa411568b69716aab3b84a"
def buy(e0, sp, L, x):
    s = sp / Q
    if L <= 0 or s <= 0: return 0.0
    if e0: s2 = 1.0 / (1.0 / s + x / L); return L * (s - s2)
    s2 = s + x / L; return L * (1.0 / s - 1.0 / s2)
def sell(e0, sp, L, t):
    s = sp / Q
    if L <= 0 or s <= 0 or t <= 0: return 0.0
    if e0: s2 = s + t / L; return L * (1.0 / s - 1.0 / s2)
    s2 = 1.0 / (1.0 / s + t / L); return L * (s - s2)
fam = [pid for pid, p in pools.items() if p["fee"] == 10000 and p["ts"] == 200 and p["hook"].startswith("00000000") and ZERO in (p["c0"], p["c1"])]
if len(sys.argv) > 2:
    RUG = json.load(open(sys.argv[2]))["removals"]
else:                                                            # pull the liquidity removals for this dataset
    RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 Chrome/128", "Accept": "application/json"}
    def rpc(m, p):
        for i in range(10):
            try:
                r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(), H), timeout=90))
                if "error" in r: raise RuntimeError(str(r["error"]))
                return r["result"]
            except urllib.error.HTTPError: time.sleep(4 * (i + 1))
    T_ML = "0x" + keccak(text="ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)").hex(); PM = "0x8366a39cc670b4001a1121b8f6a443a643e40951"
    def sgn(x): return x - (1 << 256) if x >= (1 << 255) else x
    RUG = collections.defaultdict(list); fs = sorted(fam, key=lambda p: pools[p]["bn"])
    for i in range(0, len(fs), 100):
        b = fs[i:i+100]; lo = min(pools[p]["bn"] for p in b); hi = max(pools[p]["bn"] for p in b) + 12000
        for a in range(lo, hi, 29999):
            for l in rpc("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(min(a + 29998, hi)), "address": PM, "topics": [T_ML, b]}]):
                if sgn(int(l["data"][2+128: 2+192], 16)) < 0 and int(l["blockNumber"], 16) <= pools[l["topics"][1]]["bn"] + 12000: RUG[l["topics"][1]].append(int(l["blockNumber"], 16) - pools[l["topics"][1]]["bn"])
    json.dump({"removals": RUG}, open(sys.argv[1].replace(".json", "_rug.json"), "w"))
res = collections.defaultdict(list); n_fire = 0; n_fam = len(fam)
for pid in fam:
    p = pools[pid]; sw = sorted(swaps.get(pid, []), key=lambda x: (x[0], x[1])); e0 = p["c0"] == ZERO; b0 = p["bn"]
    eth = lambda x: -(x[3] if e0 else x[4]) / 1e18
    test = next((x for x in sw if x[0] <= b0 + 7 and abs(eth(x)) < 1e-4), None)
    if not test: continue
    n_fire += 1; rug = min(RUG[pid]) if pid in RUG and RUG[pid] else None
    def state(bn_last):
        prev = [x for x in sw if x[0] <= bn_last]
        return (prev[-1][5], prev[-1][6]) if prev else (p["sqrtP0"], sw[0][6])
    crowd = [x for x in sw if x[0] > test[0] and eth(x) >= 1e-4]
    for stake in (10, 25, 50, 100):
        X = stake / ETHUSD * 1e18
        for land in (1, 2, 3):                                   # our buy lands this many blocks after the test's block
            entry_bn = test[0] + land
            ahead = [x for x in crowd if x[0] < entry_bn]           # crowd buys that beat us (we land behind them)
            sp, L = state(entry_bn - 1); tok = buy(e0, sp, L, X * 0.99)
            first_after = next((x for x in crowd if x[0] >= entry_bn), None)
            for lag in (1, 2):                                       # our sell lands this many blocks after the first crowd buy that follows our buy
                exit_bn = (first_after[0] + lag) if first_after else entry_bn + 30
                if rug is not None and b0 + rug <= exit_bn: r = -1.0 - GAS / stake
                else:
                    sp2, L2 = state(exit_bn); r = (sell(e0, sp2, L2, tok) * 0.99 - X) / X - GAS / stake
                res[(stake, land, lag, "behind" if ahead else "ahead")].append(r); res[(stake, land, lag, "all")].append(r)
print(f"{sys.argv[1]}: {n_fam} launches in the 1% family; the test trade appeared on {n_fire} ({100*n_fire/n_fam:.0f}%): the fire rule")
q = lambda v, a: sorted(v)[int(a * (len(v) - 1))]
print(f"{'stake':>5s} {'land':>4s} {'sell lag':>8s} {'n':>5s} {'trim.mean':>9s} {'median':>7s} {'p5':>6s} {'win':>4s} {'rugs':>4s} {'$ a day':>8s}")
for key in sorted(k for k in res if k[3] == "all"):
    v = res[key]; trim = sorted(v)[int(0.01 * len(v)): int(0.99 * len(v))]
    print(f"{key[0]:5d} {'+' + str(key[1]):>4s} {'+' + str(key[2]):>8s} {len(v):5d} {st.mean(trim):+9.2%} {st.median(v):+7.1%} {q(v, .05):+6.1%} {sum(1 for x in v if x > 0)/len(v):4.0%} {sum(1 for x in v if x <= -0.99):4d} {st.mean(trim) * key[0] * len(v):+8.0f}")
