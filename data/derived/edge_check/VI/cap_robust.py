"""cap_robust.py (reviewer I): how solid is BUNDLE_MAX_ETH = 3.0? (a) the range of caps that select exactly the same fires;
(b) the fires it removes, one line each, and whether each sits at the fee floor at every exit; (c) leave one launch out;
(d) its effect at h11 on rec+late (exact: the removed late fires are flat at the fee floor from h15 to h600, so their h11 is
the floor too); (e) the effect if the minOut guard refuses those fills (tonight's two 4.233 ETH bursts: no fill, $0.38 of gas
for both, docs/REPORT.md 24.38), where the cap saves only the burst's gas.
    python3 data/derived/edge_check/I/cap_robust.py > data/derived/edge_check/I/cap_robust.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
CAP = 3.0; GAS_REFUSED = 0.19                                   # a refused burst's gas, 24.38 ($0.38 for the two template bursts)
for pop in ("engine", "tables"):
    print(f"\n=== {pop} population")
    for per in ("fit", "rec+late"):
        F = c.fires(pop, per); b = sorted(d["bundle"] for d in F)
        below = max(x for x in b if x <= CAP); above = min((x for x in b if x > CAP), default=float("inf"))
        print(f"  {per}: every cap in [{below:.3f}, {above:.3f}) ETH keeps the same fires as 3.0 (highest kept bundle {below:.3f}, lowest removed {above:.3f})")
    for per in ("fit", "rec", "late"):
        for d in c.fires(pop, per):
            if d["bundle"] > CAP:
                r = d["r"]; fl = r[15] is not None and r[300] is not None and abs(r[15] - r[300]) < 1e-9
                print(f"   removes {c.hms(d['T0'])} {d['cv'][:10]} {d['win']:10s} bundle {d['bundle']:.3f} named {len(d['named']):2d}  h11 {'  n/a' if r[11] is None else f'{r[11]:+6.1%}'} h15 {r[15]:+6.1%} h300 {r[300]:+6.1%}  {'flat 15-300' if fl else ''}")
    for h in (11, 15):
        F = c.fires(pop, "fit"); rm = [d for d in F if d["bundle"] > CAP]; g = -sum(c.usd(d, h) for d in rm)
        loo = min(g + c.usd(d, h) for d in rm) if rm else 0.0
        print(f"  fit h{h}: gain ${g:+.2f} total = ${g / 96.0 * 24:+.2f}/day; leave one launch out: the smallest remaining gain ${loo:+.2f} = ${loo / 96.0 * 24:+.2f}/day;"
              f" if the guard refuses every one: ${len(rm) * GAS_REFUSED / 96.0 * 24:+.2f}/day (gas only)")
    Hr = c.period_hours("rec+late")
    for h in (11, 15):
        rm = [d for d in c.fires(pop, "rec+late") if d["bundle"] > CAP]
        v = [(d["r"][h] if d["r"][h] is not None else d["r"][15]) for d in rm]   # late removed fires: flat, h11 = h15 (checked above)
        assert all(d["r"][h] is not None or abs(d["r"][15] - d["r"][300]) < 1e-9 for d in rm)
        g = -sum(x * d["g"] * c.E - c.GAS for x, d in zip(v, rm))
        print(f"  rec+late h{h}: removes {len(rm)}, gain ${g:+.2f} total = ${g / Hr * 24:+.2f}/day over {Hr:.1f} h; guard refuses all: ${len(rm) * GAS_REFUSED / Hr * 24:+.2f}/day")
