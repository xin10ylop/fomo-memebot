"""q2_filters.py (K3): each pre-gate filter switched off alone, everything else as live (usual view k-1 with registration, 2 fleets,
7% guard, h11, $13): the launches it alone removes, what they would do at the gate and after the guard, per period. Also with the
guard at 25% (q1's alternative), since the guard decides what a readmitted launch is worth.
    python3 data/derived/edge_check/K3/q2_filters.py > data/derived/edge_check/K3/q2_filters.txt"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
X = load_dump(); VIEW = dict(view="k-1", reg=1)
print("filters that never bind on this population (the tables' qualifying rule already applies them): tier 100-200 bps (all 632 inside),")
print("bundle >= 0.3 ETH (minimum 0.300), creator buy <= 2 ETH (none above). No launch outside them is on disk with a return: untestable here.\n")
for F in ALL_F:
    only = [x for x in X if F in (x["pre"] + x["gates"]) and passes_filters(x, off=(F,))]
    anyF = [x for x in X if F in (x["pre"] + x["gates"])]
    print(f"== {F}: removes {len(anyF)} launches, {len(only)} of them by this filter alone")
    for slip in (0.07, 0.25):
        for p in ("A", "B"):
            xs = [x for x in only if period(x) == p]; d = [engine(x, off=(F,), slip=slip, **VIEW) for x in xs]
            f = [ret(x) for x, dd in zip(xs, d) if dd == "fill"]; fired_ret = [ret(x) for x, dd in zip(xs, d) if dd in ("fill", "guard")]
            print(f"   slip {slip:.2f} {p}: launches {len(xs):3d} fired {sum(dd in ('fill','guard') for dd in d):3d} fills {len(f):3d} {fmt(f)}  $ {dollars(xs, d):+7.2f}  | all fired at second place: {fmt(fired_ret)}")
        # the filtered launches' return regardless of the gate (population view)
    for p in ("A", "B"):
        v = [ret(x) for x in only if period(x) == p]; w = [ret(x) for x in X if period(x) == p and passes_filters(x)]
        print(f"   population (no gate) {p}: removed {fmt(v)} | kept {fmt(w)}")
# the supply filter's threshold: what if 1% were 0.5% or 2%?
print("\n== creator supply threshold (tk0 / 1e9), filter alone varied, the rest live, slip 7% and 25%")
for thr in (0.0, 0.0025, 0.005, 0.01, 0.02, 0.03):
    cells = []
    for slip in (0.07, 0.25):
        for p in ("A", "B"):
            xs = [x for x in X if period(x) == p and passes_filters(x, off=("supply",)) and (x["tk0"] or 0) >= thr * 1e9]
            d = [engine(x, off=("supply",), slip=slip, **VIEW) for x in xs]; f = [ret(x) for x, dd in zip(xs, d) if dd == "fill"]
            cells.append(f"{p}@{int(slip*100)}%: fills {len(f):3d} mean {mean(f):+6.1%} ${dollars(xs, d):+7.2f}")
    print(f"  supply >= {thr:.2%}: " + "  ".join(cells))
