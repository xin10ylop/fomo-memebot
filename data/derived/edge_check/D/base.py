"""base.py (reviewer D): the rule's fires, the refused and every launch, by hold, fit against recent; the lift.
    python3 data/derived/edge_check/D/base.py > data/derived/edge_check/D/base.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kit as K, common as c
for h in (0, 15, 30, 60, 150, 300, 600):
    print(K.line(f"rule (fleets>=2 @k-2), hold {h}", K.evaluate(lambda f, h=h: h if f["fire"] else None)))
print()
print(f"{'hold':>5s} {'fit fired':>10s} {'fit refused':>12s} {'lift':>6s} | {'rec fired':>10s} {'rec refused':>12s} {'lift':>6s}")
for h in (0, 15, 30, 60, 150, 300, 600):
    fa = [f["path"][h] for f in K.FIT if f["fire"]]; fr = [f["path"][h] for f in K.FIT if not f["fire"]]
    ra = [f["path"][h] for f in K.REC if f["fire"]]; rr = [f["path"][h] for f in K.REC if not f["fire"]]
    print(f"{h:5d} {c.mean(fa):+10.1%} {c.mean(fr):+12.1%} {100*(c.mean(fa)-c.mean(fr)):+6.1f} | {c.mean(ra):+10.1%} {c.mean(rr):+12.1%} {100*(c.mean(ra)-c.mean(rr)):+6.1f}")
