"""q3_gate.py (K3): the crowd gate. Fleet threshold 0-4 at every view (k-2 without / with the registration block, k-1, k), at the live
guard (7%) and at 25%; then second signals added to the live gate (2 fleets at k-1), each threshold chosen on one period and read on the
other, with a null (the same number of fires dropped at random, 2,000 draws).
    python3 data/derived/edge_check/K3/q3_gate.py > data/derived/edge_check/K3/q3_gate.txt"""
import sys, os, random; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
X = load_dump()
print("1. fleet threshold x view (h11, $13, gas $0.33 a burst): per period fired / fills / mean per fill / $ ; B's $ a day in brackets")
for slip in (0.07, 0.25):
    print(f" guard {slip:.0%}")
    for view, reg in (("k-2", 0), ("k-2", 1), ("k-1", 1), ("k", 1)):
        for amin in (0, 1, 2, 3, 4):
            cells = []
            for p in ("A", "B"):
                sm = summary([x for x in X if period(x) == p], view=view, reg=reg, amin=amin, slip=slip)
                cells.append(f"{p}: {sm['fired']:3d} {sm['fills']:3d} {sm['mean']:+6.1%} ${sm['usd']:+7.2f}")
            print(f"   {view:3s} reg{reg} fleets>={amin}  " + "   ".join(cells) + f"  (${sm['usd']/DAYS_B:+.2f}/d)")
# second signals on top of the live gate
base = [x for x in X if passes_filters(x) and fleets_at(x, "k-1", 1) >= 2]
def feats(x):
    k = x["k"]; fb = x["fl_reg1"]; sh = x["shots"]
    return {"fleets_k-1": fleets_at(x, "k-1", 1), "growth k-2->k-1": fleets_at(x, "k-1", 1) - fleets_at(x, "k-2", 1), "shots_to_k-1": sum(sh[: k]),
            "bundle_eth": x["bundle"], "tier_bps": x["tier_bps"], "k_blocks": k, "named": x["named_n"], "creator_supply": (x["tk0"] or 0) / 1e9, "hour": x["hour"]}
for x in base: x["F"] = feats(x)
def usd_of(xs, slip): return sum((ret(x) * 13 - GAS) if engine(x, slip=slip) == "fill" else (-GAS if engine(x, slip=slip) == "guard" else 0.0) for x in xs)
print("\n2. a second signal on the live gate (fleets >= 2 at k-1): keep fires with feature >= t (or <= t); t chosen on one period, read on the other")
rnd = random.Random(11)
for slip in (0.07, 0.25):
    print(f" guard {slip:.0%}; base: A {sum(period(x)=='A' for x in base)} fires ${usd_of([x for x in base if period(x)=='A'], slip):+.2f}, B {sum(period(x)=='B' for x in base)} fires ${usd_of([x for x in base if period(x)=='B'], slip):+.2f}")
    for fn in base[0]["F"]:
        vals = sorted(set(x["F"][fn] for x in base))
        cands = [(op, t) for t in vals for op in (">=", "<=")]
        def sel(xs, op, t): return [x for x in xs if (x["F"][fn] >= t if op == ">=" else x["F"][fn] <= t)]
        out = []
        for fit, read in (("A", "B"), ("B", "A")):
            xf = [x for x in base if period(x) == fit]; xr = [x for x in base if period(x) == read]
            op, t = max(cands, key=lambda c: (usd_of(sel(xf, *c), slip), -abs(len(sel(xf, *c)) - len(xf))))
            kept = sel(xr, op, t); gain = usd_of(kept, slip) - usd_of(xr, slip); nd = len(xr) - len(kept)
            null = [usd_of(rnd.sample(xr, len(kept)), slip) - usd_of(xr, slip) for _ in range(300)] if nd else [0.0]
            pnull = sum(1 for g in null if g >= gain) / len(null)
            out.append(f"fit {fit} {op}{t:g}: drops {nd:2d} of {len(xr)} on {read}, $ {gain:+6.2f} (null P>= {pnull:.2f})")
        print(f"   {fn:17s} " + " | ".join(out))
