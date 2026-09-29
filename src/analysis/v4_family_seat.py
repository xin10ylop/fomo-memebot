#!/usr/bin/env python3
"""First-block seat on chosen v4 launch families, both days, rugs as -100%, exits by hold or after the first crowd buy.
extra_fee: a hook fee per leg the Swap event does not show (Pons graduation pools charge through their hook).

    python3 src/analysis/v4_family_seat.py day1.json day2.json
"""
import json, sys, collections, statistics as st
ZERO = "0"*40; Q = 2**96; ETHUSD, GAS = 2650.0, 0.05
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
FAMS = {"pools.trade 0.25%": ("00000000", 2500, 25, 0.0), "Pons graduation (hook fee 1% assumed)": ("e5e70264", 0, 200, 0.01),
        "slow-rug 2.45%": ("00000000", 24500, 200, 0.0), "slow-rug 2.0%": ("00000000", 20000, 200, 0.0), "slow-rug 2.35%": ("00000000", 23500, 200, 0.0)}
for path in sys.argv[1:]:
    D = json.load(open(path)); pools = D["pools"]; swaps = D["swaps"]; RUG = json.load(open(path.replace(".json", "_rug_all.json")))["removals"]
    print(f"\n=== {path}")
    for name, (hook, fee, ts, xfee) in FAMS.items():
        ps = [pid for pid, p in pools.items() if p["hook"].startswith(hook) and p["fee"] == fee and p["ts"] == ts and ZERO in (p["c0"], p["c1"])]
        if not ps: continue
        res = collections.defaultdict(list)
        for pid in ps:
            p = pools[pid]; sw = sorted(swaps.get(pid, []), key=lambda x: (x[0], x[1])); e0 = p["c0"] == ZERO; b0 = p["bn"]
            if not sw: continue
            f = (sw[0][7] if sw[0][7] is not None else fee) / 1e6 + xfee
            eth = lambda x: -(x[3] if e0 else x[4]) / 1e18
            rug = min(RUG[pid]) if RUG.get(pid) else None
            def state(bn_last):
                prev = [x for x in sw if x[0] <= bn_last]
                return (prev[-1][5], prev[-1][6]) if prev else (p["sqrtP0"], sw[0][6])
            for seat, entry_after in (("b1-first", b0), ("b1-last", b0 + 1)):
                sp, L = state(entry_after)
                crowd_after = next((x for x in sw if x[0] > entry_after + (0 if seat == "b1-first" else 0) and eth(x) >= 1e-4 and x[0] > b0 + 1), None)
                for stake in (25, 50):
                    X = stake / ETHUSD * 1e18; tok = buy(e0, sp, L, X * (1 - f))
                    rules = {f"hold {h}": entry_after + 1 + h for h in (11, 30, 60, 100, 300)}
                    rules["after first crowd buy +1"] = (crowd_after[0] + 1) if crowd_after else entry_after + 31
                    for rn, exit_bn in rules.items():
                        if rug is not None and b0 + rug <= exit_bn: r = -1.0 - GAS / stake
                        else:
                            sp2, L2 = state(exit_bn); r = (sell(e0, sp2, L2, tok) * (1 - f) - X) / X - GAS / stake
                        res[(seat, stake, rn)].append(r)
        print(f"  {name}: {len(ps)} launches")
        for key in [k for k in res if k[1] == 25] + [k for k in res if k[1] == 50 and k[0] == "b1-first"]:
            v = sorted(res[key]); trim = v[int(0.01 * len(v)): max(int(0.99 * len(v)), 1)]
            if not v: continue
            print(f"     {key[0]:8s} ${key[1]:3d} {key[2]:26s} n={len(v):4d} trim.mean {st.mean(trim):+6.1%} median {st.median(v):+6.1%} win {sum(1 for x in v if x > 0)/len(v):4.0%} rugs {sum(1 for x in v if x <= -0.99):3d}  $ a day {st.mean(trim) * key[1] * len(v):+7.0f}")
