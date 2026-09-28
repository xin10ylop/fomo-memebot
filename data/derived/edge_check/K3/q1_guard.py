"""q1_guard.py (K3): the minOut guard (BURST_SLIP 7%) on the engine's fires at the usual view (k-1 with the registration block).
What the reverted bursts would have paid, a looser guard (slip sweep) chosen on one period and read on the other, guards keyed to the
fleet count / the bundle, what the guard is actually measuring (the curve's move before E1 against the buy ahead), gas.
    python3 data/derived/edge_check/K3/q1_guard.py > data/derived/edge_check/K3/q1_guard.txt"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
X = load_dump(); VIEW = dict(view="k-1", reg=1)
fired = [x for x in X if engine(x, slip=None, **VIEW) == "fill"]
for x in fired:
    x["ratio"] = x["tk_seat1"] / x["tk_build"]; L = tape(x["cv"])
    if L:
        p0 = path(L, 0, hmax=15); p2 = path(L, 2, hmax=15); x["tk_first"] = p0["tk"]; x["r_first"] = p0["v"][11]; x["r3"] = p2["v"][11]
        x["pre_move"] = x["tk_first"] / x["tk_build"]; x["ahead_move"] = x["tk_seat1"] / x["tk_first"]
print(f"fires at the usual view (guard off): {len(fired)}; A {sum(period(x)=='A' for x in fired)}, B {sum(period(x)=='B' for x in fired)}; with tapes {sum('tk_first' in x for x in fired)}")
print("\n1. the 7% guard: what the reverted bursts would have returned (h11, $13)")
for p in ("A", "B", "all"):
    for lab, sel in (("filled", lambda x: x["ratio"] >= 0.93), ("reverted", lambda x: x["ratio"] < 0.93)):
        v = [ret(x) for x in fired if sel(x) and (p == "all" or period(x) == p)]
        vt = [x for x in fired if sel(x) and (p == "all" or period(x) == p) and "r3" in x]
        print(f"  {p:3s} {lab:9s} second {fmt(v, sum(r*13-0.33 for r in v))}   | tapes n={len(vt)}: first {mean([x['r_first'] for x in vt]):+6.1%} second {mean([ret(x) for x in vt]):+6.1%} third {mean([x['r3'] for x in vt]):+6.1%}")
print("\n2. the reverted, by how far the price moved (tokens at second place / tokens sized at the build), h11 second place")
for lo, hi in ((0.85, 0.93), (0.75, 0.85), (0.6, 0.75), (0.4, 0.6), (0.0, 0.4)):
    for p in ("A", "B"):
        v = [ret(x) for x in fired if lo <= x["ratio"] < hi and period(x) == p]
        print(f"  ratio {lo:.2f}-{hi:.2f} {p}: {fmt(v, sum(r*13-0.33 for r in v))}")
print("\n3. what moved the price (tapes): the curve before E1 (bundle / creation-second buys after the build's view) vs the one buy ahead in E1")
for p in ("A", "B"):
    vt = [x for x in fired if "pre_move" in x and period(x) == p and x["ratio"] < 0.93]
    pre_dom = [x for x in vt if (1 - x["pre_move"]) >= (1 - x["ahead_move"])]
    print(f"  {p} reverted with tapes {len(vt)}: move mostly before E1 {len(pre_dom)} ({fmt([ret(x) for x in pre_dom])}); mostly the buy ahead {len(vt)-len(pre_dom)} ({fmt([ret(x) for x in vt if x not in pre_dom])})")
print("\n4. slip sweep: $ over the period (fills ret*13-0.33, reverts -0.33), fills, mean per fill; the rule chosen on one period read on the other")
SL = (0.07, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.70, None)
res = {}
for s in SL:
    row = []
    for p in ("A", "B"):
        xs = [x for x in X if period(x) == p]; sm = summary(xs, slip=s, **VIEW); res[(s, p)] = sm
        row.append(f"{p}: fired {sm['fired']:3d} rev {sm['guard']:3d} fills {sm['fills']:3d} mean {sm['mean']:+6.1%} ${sm['usd']:+7.2f}")
    print(f"  slip {'off' if s is None else f'{s:.2f}':>5s}  " + "   ".join(row))
for fit, read in (("A", "B"), ("B", "A")):
    best = max(SL, key=lambda s: res[(s, fit)]["usd"])
    print(f"  chosen on {fit}: slip {best}; on {read} ${res[(best, read)]['usd']:+.2f} against ${res[(0.07, read)]['usd']:+.2f} at 7% (difference ${res[(best, read)]['usd']-res[(0.07, read)]['usd']:+.2f})")
print("\n   the fills a looser guard adds (the marginal bursts), at second place and (tapes) third place:")
for s in (0.15, 0.30, None):
    for p in ("A", "B"):
        m = [x for x in fired if period(x) == p and x["ratio"] < 0.93 and (s is None or x["ratio"] >= 1 - s)]
        mt = [x for x in m if "r3" in x]
        print(f"  7% -> {'off' if s is None else s}: {p} added {fmt([ret(x) for x in m], sum(ret(x)*13 for x in m))}  | third place on tapes n={len(mt)} mean {mean([x['r3'] for x in mt]):+6.1%} ${sum(x['r3']*13 for x in mt):+.2f}")
print("\n5. guard keyed to the crowd: fleets at the gate's view >= F fire with no guard (or a looser one), else 7%")
def fl(x): return fleets_at(x, "k-1", 1)
for F in (3, 4, 5, 6):
    out = []
    for p in ("A", "B"):
        xs = [x for x in X if period(x) == p]; d = [engine(x, slip=(None if fleets_at(x, 'k-1', 1) >= F else 0.07), **VIEW) for x in xs]
        f = [ret(x) for x, dd in zip(xs, d) if dd == "fill"]; out.append(f"{p}: fills {len(f):3d} mean {mean(f):+6.1%} ${dollars(xs, d):+7.2f}")
    print(f"  fleets >= {F} unguarded: " + "   ".join(out))
print("   the reverted bursts by the gate's fleet count (second place h11):")
for lo, hi in ((2, 3), (3, 5), (5, 99)):
    for p in ("A", "B"):
        v = [ret(x) for x in fired if x["ratio"] < 0.93 and lo <= fl(x) < hi and period(x) == p]; print(f"    fleets {lo}-{hi-1} {p}: {fmt(v)}")
print("\n   the reverted bursts by the bundle ETH (second place h11):")
for lo, hi in ((0.3, 0.6), (0.6, 1.0), (1.0, 3.01)):
    for p in ("A", "B"):
        v = [ret(x) for x in fired if x["ratio"] < 0.93 and lo <= x["bundle"] < hi and period(x) == p]; print(f"    bundle {lo}-{hi} {p}: {fmt(v)}")
print("\n6. gas: 7% guard, the week: reverted bursts", sum(1 for x in fired if x["ratio"] < 0.93), "x $0.33 =", f"${0.33*sum(1 for x in fired if x['ratio'] < 0.93):.2f}")
