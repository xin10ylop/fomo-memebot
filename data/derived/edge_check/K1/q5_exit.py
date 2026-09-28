"""K1/q5_exit.py: exit rules against the fixed exit at block 11 (the live setting 9 as it lands), on second place's value path
(G's curve on the tapes, block by block to E1+60). A rule sees block h and its sell lands LAG blocks later (value at h+LAG);
LAG 2 (the live median) and 4 (slow). Rules: take-profit, stop, the seat-block buyers' first sell, a second-block read, a
momentum extension. Parameters chosen on one half and read on the other. Population: the fires at the usual view that fill
(guard 7% and guard 20%), taped only."""
import sys, os, statistics as st, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from k1 import *
R = load()
def path(r):
    p = r.get("p2")
    return p if p and all(x is not None for x in p[:41]) else None
def run(rule, P, lag):
    out = []
    for r in P:
        p = path(r); out.append(rule(r, p, lag))
    return out
BASE = lambda r, p, lag: p[11]
def tp(x, hmax):
    def f(r, p, lag):
        for h in range(1, hmax + 1):
            if p[h] >= x: return p[h + lag]
        return p[11]
    return f
def stop(x, hmax):
    def f(r, p, lag):
        for h in range(1, hmax + 1):
            if p[h] <= -x: return p[h + lag]
        return p[11]
    return f
def tpstop(a, b, hmax):
    def f(r, p, lag):
        for h in range(1, hmax + 1):
            if p[h] >= a or p[h] <= -b: return p[h + lag]
        return p[11]
    return f
def seatsell(hmax):
    def f(r, p, lag):
        s = r.get("seat_first_sell")
        if s is not None and 1 <= s <= hmax: return p[s + lag]
        return p[11]
    return f
def early_read(h0, x, ext):
    """at block h0: below x -> sell now (lands h0+lag); else hold to ext"""
    def f(r, p, lag):
        return p[h0 + lag] if p[h0] < x else p[ext]
    return f
def momentum(h0, ext):
    """at block h0 (the live trigger 9): if the value rose over the last 3 blocks hold to ext, else sell (lands h0+lag)"""
    def f(r, p, lag):
        return p[ext] if p[h0] > p[h0 - 3] else p[h0 + lag]
    return f
FAM = {"take-profit": [(f"tp {x:.0%} by {hm}", tp(x, hm)) for x in (0.1, 0.2, 0.3, 0.5, 0.75, 1.0) for hm in (3, 6, 9)],
       "stop": [(f"stop -{x:.0%} by {hm}", stop(x, hm)) for x in (0.05, 0.1, 0.15, 0.2, 0.3) for hm in (3, 6, 9)],
       "tp+stop": [(f"tp {a:.0%} / stop -{b:.0%} by 9", tpstop(a, b, 9)) for a in (0.2, 0.3, 0.5, 1.0) for b in (0.1, 0.2, 0.3)],
       "seat-block sellers": [(f"sell on their first sell by {hm}", seatsell(hm)) for hm in (3, 5, 7, 9)],
       "second-block read": [(f"at h{h0}: below {x:+.0%} sell, else hold to {ext}", early_read(h0, x, ext)) for h0 in (1, 2, 3) for x in (-0.1, -0.05, 0.0) for ext in (11, 13, 20)],
       "momentum": [(f"at h9 rising over 3 blocks: hold to {ext}", momentum(9, ext)) for ext in (13, 15, 20, 30)]}
for slip in (0.07, 0.20):
    D = decide(R, view="k-1", slip=slip); P = [d["r"] for d in D if d["why"] == "FILL" and path(d["r"])]
    S = {p: [r for r in P if r["set"] == p] for p in ("fit", "read")}
    for lag in (2, 4):
        b = {p: mean(run(BASE, S[p], lag)) for p in S}
        print(f"== guard {slip:.2f}, lag {lag}: fixed exit 11: fit n={len(S['fit'])} {b['fit']:+.2%} | read n={len(S['read'])} {b['read']:+.2%}")
        for fam, rules in FAM.items():
            sc = [(nm, mean(run(fn, S["fit"], lag)), mean(run(fn, S["read"], lag))) for nm, fn in rules]
            bf = max(sc, key=lambda x: x[1]); br = max(sc, key=lambda x: x[2])
            beat_both = sum(1 for x in sc if x[1] > b["fit"] and x[2] > b["read"])
            print(f"  {fam:18s} chosen on fit: {bf[0]:36s} fit {bf[1]:+6.2%} -> read {bf[2]:+6.2%} ({bf[2]-b['read']:+.2%}) | chosen on read: {br[0]:36s} read {br[2]:+6.2%} -> fit {br[1]:+6.2%} ({br[1]-b['fit']:+.2%}) | beat fixed on both: {beat_both}/{len(sc)}")
        print()
# fixed holds on the same fills (the plateau), guard 20%, lag 0 (the exit block itself)
D = decide(R, view="k-1", slip=0.20); P = [d["r"] for d in D if d["why"] == "FILL" and path(d["r"])]
print("fixed exit block h (guard 0.20 fills, taped): " + "  ".join(f"h{h}: {mean([r['p2'][h] for r in P if r['set']=='fit']):+.1%}/{mean([r['p2'][h] for r in P if r['set']=='read']):+.1%}" for h in (3, 5, 7, 9, 11, 13, 15, 20, 30, 40, 60)))
