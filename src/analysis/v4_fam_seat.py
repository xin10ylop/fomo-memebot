#!/usr/bin/env python3
"""First-block seat on one v4 launch family with liquidity pulls as total losses (buy at the head of b0+1; exits by hold or
relative to the first real buy). Usage: python3 src/analysis/v4_fam_seat.py data/derived/edge_check/O/v4_24h.json data/derived/edge_check/O/fam1pct_rug.json [stake]"""
import json, sys, collections, statistics as st
D = json.load(open(sys.argv[1])); pools = D["pools"]; swaps = D["swaps"]; ZERO = "0"*40; Q = 2**96
RUG = json.load(open(sys.argv[2]))["removals"]; STAKE = float(sys.argv[3]) if len(sys.argv) > 3 else 25.0; ETHUSD, GAS = 2650.0, 0.05; X = STAKE / ETHUSD * 1e18
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
res = collections.defaultdict(list); per = []
for pid in fam:
    p = pools[pid]; sw = sorted(swaps.get(pid, []), key=lambda x: (x[0], x[1])); e0 = p["c0"] == ZERO; b0 = p["bn"]; f = 0.01
    rug = min(RUG[pid]) if pid in RUG else None
    L0 = sw[0][6] if sw else 25725498245903809899643
    def state(bn_last):
        prev = [x for x in sw if x[0] <= bn_last]
        return (prev[-1][5], prev[-1][6]) if prev else (p["sqrtP0"], L0)
    sp, L = state(b0); tok = buy(e0, sp, L, X * (1 - f))
    eth = lambda x: -(x[3] if e0 else x[4]) / 1e18
    fw = next((x[0] for x in sw if x[0] > b0 + 1 and eth(x) >= 1e-4), None)
    rules = {f"hold {h} blocks": b0 + 1 + h for h in (5, 8, 11, 15, 20, 30, 60, 100)}
    rules["sell 1 block after the first real buy"] = (fw + 1) if fw else b0 + 31
    rules["sell 3 blocks after the first real buy"] = (fw + 3) if fw else b0 + 31
    row = {"pid": pid, "rug": rug, "fw": (fw - b0) if fw else None}
    for name, exit_bn in rules.items():
        if rug is not None and b0 + rug <= exit_bn: r = -1.0 - GAS / STAKE
        else:
            sp2, L2 = state(exit_bn); r = (sell(e0, sp2, L2, tok) * (1 - f) - X) / X - GAS / STAKE
        res[name].append(r); row[name] = r
    per.append(row)
print(f"family 1%/200: {len(fam)} launches in 24 h; buy ${STAKE:.0f} at the head of block b0+1; a liquidity pull before our sell = -100%")
for name, v in res.items():
    print(f"  {name:40s} mean {st.mean(v):+6.1%}  median {st.median(v):+5.1%}  win {sum(1 for x in v if x > 0)/len(v):.0%}  rugs hit {sum(1 for x in v if x <= -0.99):3d}  $ a day {sum(v) * STAKE:+7.0f}")
json.dump(per, open(sys.argv[1].replace(".json", f"_fam1pct_seat{int(STAKE)}.json"), "w"))
