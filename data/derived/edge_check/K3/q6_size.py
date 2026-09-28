"""q6_size.py (K3): the return per fire by stake (second place, E1+11, 3% cap, later buys folded by their ETH), on the engine's fills with
tapes (usual view; guard 7% and 25%), per period, and split by bundle ETH and by fleets at the gate.
    python3 data/derived/edge_check/K3/q6_size.py > data/derived/edge_check/K3/q6_size.txt"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
X = load_dump(); ST = (13, 25, 50, 100, 200, 400, 800)
for slip in (0.07, 0.25):
    fills = [x for x in X if engine(x, slip=slip) == "fill" and tape(x["cv"])]
    for x in fills:
        L = tape(x["cv"]); x["S"] = {}
        for s in ST:
            p = path(L, 1, stake=s, hmax=13); x["S"][s] = (p["v"][11], p["g"] * E)
    print(f"\n=== fills at guard {slip:.0%} with tapes: A {sum(period(x)=='A' for x in fills)}, B {sum(period(x)=='B' for x in fills)}")
    print("  stake:   " + "".join(f"{s:>22d}" for s in ST))
    for p in ("A", "B"):
        xs = [x for x in fills if period(x) == p]
        print(f"  {p} mean   " + "".join(f"{mean([x['S'][s][0] for x in xs]):>+22.1%}" for s in ST))
        print(f"  {p} $/fill " + "".join(f"{mean([x['S'][s][0]*x['S'][s][1]-GAS for x in xs]):>+22.2f}" for s in ST))
        print(f"  {p} capped " + "".join(f"{sum(1 for x in xs if x['S'][s][1] < s*0.999):>22d}" for s in ST))
    for lab, key, cuts in (("bundle ETH", lambda x: x["bundle"], ((0.3, 0.7), (0.7, 1.2), (1.2, 3.01))), ("fleets at k-1", lambda x: fleets_at(x, "k-1", 1), ((2, 3), (3, 5), (5, 99)))):
        for lo, hi in cuts:
            for p in ("A", "B"):
                xs = [x for x in fills if period(x) == p and lo <= key(x) < hi]
                if xs: print(f"  {lab} {lo}-{hi} {p} n={len(xs):2d} mean at stake: " + "  ".join(f"${s}: {mean([x['S'][s][0] for x in xs]):+6.1%}" for s in ST))
