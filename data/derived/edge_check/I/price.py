"""price.py (reviewer I): every filter variant priced on the engine's population (fleet_variants.fleets_k2 engine=True >= 2)
and on the tables' (crowd_rules.cums/at >= 2 at k-2), at the exit block 11 (setting 9 as it lands) and 15, per period and
per fit window: fires, mean, median, win, dead (< -40%), $ total after $0.33 gas at $13, $ a day at the period's hours,
and what the filter removes.  Periods: fit (96.0 h); rec = the 11 recent files + gapA/gapB (curves.json, h11 and h15; 66.8 h
of window bounds); rec+late = rec + sep27pm/sep27eve (h15 only, hold_grid price; 76.2 h).
    python3 data/derived/edge_check/I/price.py > data/derived/edge_check/I/price.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
H = {"fit": c.period_hours("fit"), "rec": c.period_hours("rec"), "rec+late": c.period_hours("rec+late")}
print(f"hours: fit {H['fit']:.1f}; rec {H['rec']:.1f} (window bounds; the launches' own T0 spans give {c.hours([d for d in c.load() if d['per'] == 'rec']):.1f});"
      f" rec+late {H['rec+late']:.1f} (T0 spans {c.hours([d for d in c.load() if d['per'] != 'fit']):.1f})")
V = c.variants()
for pop in ("engine", "tables"):
    for h, pers in ((11, ("fit", "rec")), (15, ("fit", "rec", "rec+late"))):
        print(f"\n######## {pop.upper()} population, exit h{h} ########")
        for per in pers:
            F = c.fires(pop, per); base = c.stats(F, h, H[per])
            print(f"\n  -- {per} ({H[per]:.1f} h) --")
            for name, keep in V:
                k = [d for d in F if keep(d)]; x = [d for d in F if not keep(d)]; s = c.stats(k, h, H[per]); sx = c.stats(x, h, H[per])
                dx = f"   removes {sx['n']:2d}: mean {sx['mean']:+6.1%} ${sx['usd']:+6.2f}" if sx["n"] else "   removes  0"
                print(f"  {name:12s} {c.fmt(s)}   d$/day {s['day'] - base['day']:+6.2f}{dx}")
        print(f"\n  -- fit by window (hours = the window's T0 span) --")
        for w in c.FIT:
            F = c.fires(pop, "fit", w); hw = c.win_hours(w)
            for name, keep in V:
                if name not in ("none", "cap1.0", "cap1.5", "cap2.0", "cap3.0", "tmpl", "tmpl+cap2.0"): continue
                s = c.stats([d for d in F if keep(d)], h, hw)
                print(f"  {w:9s} ({hw:4.1f} h) {name:12s} {c.fmt(s)}")
