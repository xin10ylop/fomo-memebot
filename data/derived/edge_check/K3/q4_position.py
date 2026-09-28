"""q4_position.py (K3): return by landing position in E1 and by the size of the buy ahead, on the engine's fires (usual view, guard off)
and on the gated population, per period (tapes: 103 of 129 fires).
    python3 data/derived/edge_check/K3/q4_position.py > data/derived/edge_check/K3/q4_position.txt"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
X = load_dump()
fires = [x for x in X if engine(x, slip=None) == "fill" and tape(x["cv"])]
refused = [x for x in X if engine(x, slip=None) == "gate" and tape(x["cv"])]
for x in fires + refused:
    L = tape(x["cv"]); x["P"] = {n: path(L, n, hmax=15)["v"][11] for n in (0, 1, 2, 3, 4, 10 ** 6)}
print("1. h11 return by landing position (n buys ahead in E1), $13")
for lab, S in (("fires", fires), ("gate-refused", refused)):
    for p in ("A", "B"):
        xs = [x for x in S if period(x) == p]
        print(f"  {lab:12s} {p} n={len(xs):3d}: " + "  ".join(f"{('last' if n > 99 else f'{n} ahead')}: {mean([x['P'][n] for x in xs]):+6.1%} (med {median([x['P'][n] for x in xs]):+5.1%})" for n in (0, 1, 2, 3, 4, 10 ** 6)))
print("\n2. fires: second place (behind the first E1 buy) by the size of that buy; first place alongside, and the 7% guard's verdict at second")
for lo, hi in ((0, 0.01), (0.01, 0.03), (0.03, 0.06), (0.06, 0.12), (0.12, 0.25), (0.25, 99)):
    for p in ("A", "B"):
        xs = [x for x in fires if period(x) == p and lo <= x["e1_first_eth"] < hi]
        if not xs: print(f"  ahead {lo:.2f}-{hi:.2f} ETH {p}: n=0"); continue
        rev = sum(1 for x in xs if x["tk_seat1"] < 0.93 * x["tk_build"])
        print(f"  ahead {lo:.2f}-{hi:.2f} ETH {p}: n={len(xs):3d} second {mean([x['P'][1] for x in xs]):+6.1%} (med {median([x['P'][1] for x in xs]):+5.1%}, win {win([x['P'][1] for x in xs]):3.0%})  first {mean([x['P'][0] for x in xs]):+6.1%}  third {mean([x['P'][2] for x in xs]):+6.1%}  7% guard reverts {rev}")
print("\n3. E1 crowd size (buys in the seat block) and position: fires")
for lo, hi in ((0, 3), (3, 6), (6, 10), (10, 99)):
    for p in ("A", "B"):
        xs = [x for x in fires if period(x) == p and lo <= x["e1_nbuy"] < hi]
        if xs: print(f"  E1 buys {lo}-{hi-1} {p}: n={len(xs):3d} first {mean([x['P'][0] for x in xs]):+6.1%} second {mean([x['P'][1] for x in xs]):+6.1%} third {mean([x['P'][2] for x in xs]):+6.1%} last {mean([x['P'][10**6] for x in xs]):+6.1%}")
print("\n4. behind a big buy: second place when the buy ahead is >= 0.06 ETH vs < 0.06, all launches passing the filters (gate or not)")
pop = [x for x in X if passes_filters(x) and tape(x["cv"])]
for x in pop:
    if "P" not in x: L = tape(x["cv"]); x["P"] = {n: path(L, n, hmax=15)["v"][11] for n in (0, 1, 2)}
for p in ("A", "B"):
    for lab, sel in (("big >= 0.06", lambda x: x["e1_first_eth"] >= 0.06), ("small < 0.06", lambda x: 0 < x["e1_first_eth"] < 0.06), ("no E1 buy", lambda x: x["e1_first_eth"] == 0)):
        xs = [x for x in pop if period(x) == p and sel(x)]
        print(f"  {p} {lab:12s}: n={len(xs):3d} second {mean([x['P'][1] for x in xs]):+6.1%} first {mean([x['P'][0] for x in xs]):+6.1%}")
