"""q1b_guard_position.py (K3): the guard is position-aware. For every fire (usual view) with a tape, the burst's first shot in E1 lands
at position p (first, second, third, fifth, last); the relay fills iff the tokens at p are >= (1 - slip) x the tokens sized at the build
(k-2 view), else the burst is gas. $ by slip, by landing position, per period. The guard's second-place pass/fail (the replay's) is only
one column of this table.
    python3 data/derived/edge_check/K3/q1b_guard_position.py > data/derived/edge_check/K3/q1b_guard_position.txt"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
X = load_dump()
fired = [x for x in X if engine(x, slip=None, view="k-1", reg=1) == "fill" and tape(x["cv"])]
POS = {"first": 0, "second": 1, "third": 2, "fifth": 4, "last": 10 ** 6}
for x in fired:
    L = tape(x["cv"]); x["pos"] = {}
    for nm, n in POS.items():
        p = path(L, n, hmax=15); x["pos"][nm] = (p["tk"], p["v"][11])
print(f"fires with tapes: {len(fired)} (A {sum(period(x)=='A' for x in fired)}, B {sum(period(x)=='B' for x in fired)}); E1 buys per fire: median {median([x['e1_nbuy'] for x in fired])}")
print(f"\n$ per period at $13 by landing position (rows) and slip (columns); fills/bursts in brackets")
SL = (0.07, 0.10, 0.15, 0.20, 0.25, 0.30, 0.50)
print(f"{'':16s}" + "".join(f"{('slip %.2f' % s):>20s}" for s in SL))
for nm in POS:
    for p in ("A", "B"):
        xs = [x for x in fired if period(x) == p]; cells = []
        for s in SL:
            usd = 0.0; nf = 0
            for x in xs:
                tk, r = x["pos"][nm]
                if tk >= (1 - s) * x["tk_build"]: usd += r * 13 - GAS; nf += 1
                else: usd -= GAS
            cells.append(f"{usd:+8.2f} ({nf:2d}/{len(xs)})")
        print(f"{nm:7s} {p:8s}" + "".join(f"{c:>20s}" for c in cells))
print("\nmean return of the fills at each position, slip 7% vs 25% (h11):")
for nm in POS:
    for p in ("A", "B"):
        xs = [x for x in fired if period(x) == p]
        a = [x["pos"][nm][1] for x in xs if x["pos"][nm][0] >= 0.93 * x["tk_build"]]; b = [x["pos"][nm][1] for x in xs if x["pos"][nm][0] >= 0.75 * x["tk_build"]]
        extra = [x["pos"][nm][1] for x in xs if 0.75 * x["tk_build"] <= x["pos"][nm][0] < 0.93 * x["tk_build"]]
        print(f"  {nm:7s} {p}: 7% {fmt(a)} | 25% {fmt(b)} | added by 25%: {fmt(extra)}")
# the live bursts of Sep 26-28 that the replay holds: where did they land?
