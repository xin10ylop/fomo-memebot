"""choose.py (edge_check/G): task 2. Choose the hold on one set, read it on the other: fit -> recent, recent -> fit, Sep 18-21 ->
Sep 22-27 (and rec18 -> fit as a check). Choice = argmax of the fires' mean over h = 1..600 (also over 1..60, the discovery's
horizon, and over 1..1200); plateau = every h whose mean is within one standard error (of the optimum's mean) of the optimum, on the
choosing set: the contiguous run around the optimum and the whole set. Paired differences against h = 15 (same fires) with their
standard errors. Also the argmax of the 11-block moving average (h-5..h+5), which a one-block spike cannot win.
    python3 data/derived/edge_check/G/choose.py > data/derived/edge_check/G/choose.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
from sweep import C, sets
S = sets()
def paths(name): return [x["r2"] for x in C if x["fire"] and S[name](x)]
def mcurve(P, lo=1, hi=600): return {h: mean([p[h] for p in P]) for h in range(lo, hi + 1)}
def securve(P, lo=1, hi=600): return {h: se([p[h] for p in P]) for h in range(lo, hi + 1)}
def pdiff(P, a, b):
    d = [p[a] - p[b] for p in P]; return mean(d), se(d)
def choose(P, lo=1, hi=600):
    m = mcurve(P, lo, hi); hs = max(m, key=lambda h: m[h]); s = se([p[hs] for p in P]); thr = m[hs] - s
    on = sorted(h for h in m if m[h] >= thr); a = b = hs
    while a - 1 in m and m[a - 1] >= thr: a -= 1
    while b + 1 in m and m[b + 1] >= thr: b += 1
    return hs, m[hs], s, (a, b), on
def smooth_choice(P, lo=1, hi=600, w=5):
    m = mcurve(P, 1, min(HMAX, hi + w)); sm = {h: mean([m[j] for j in range(max(1, h - w), h + w + 1) if j in m]) for h in range(lo, hi + 1)}
    return max(sm, key=lambda h: sm[h])
def runs(on):
    out = []; 
    for h in on:
        if out and h == out[-1][1] + 1: out[-1][1] = h
        else: out.append([h, h])
    return ", ".join(f"{a}-{b}" if a != b else f"{a}" for a, b in out)
if __name__ == "__main__":
    for name in ("Sep22-23", "rec"):
        Q = paths(name); mq = mcurve(Q, 1, 600)
        print(f"Sep 22-27 split: {name} ({len(Q)} fires): h334 {mq[334]:+.1%}, h337 {mq[337]:+.1%}, h300 {mq[300]:+.1%}, h15 {mq[15]:+.1%}, h11 {mq[11]:+.1%}, h9 {mq[9]:+.1%}")
    for cs, rs in (("fit", "rec"), ("rec", "fit"), ("Sep18-21", "Sep22-27"), ("rec18", "fit"), ("Sep22-27", "Sep18-21")):
        P, Q = paths(cs), paths(rs)
        print(f"\n=== choose on {cs} ({len(P)} fires), read on {rs} ({len(Q)} fires)")
        for lo, hi in ((1, 600), (1, 60), (1, 1200)):
            hs, ms, s, (a, b), on = choose(P, lo, hi); mq = mcurve(Q, 1, 1200)
            dP = pdiff(P, hs, 15); dQ = pdiff(Q, hs, 15); hsm = smooth_choice(P, lo, hi)
            print(f" range {lo}-{hi}: optimum h = {hs}: {ms:+.1%} (se {s:.1%}) on {cs}; plateau (within 1 se, >= {ms-s:+.1%}) contiguous {a}-{b}; all h within: {len(on)} of {hi-lo+1} ({runs(on)})")
            print(f"    read on {rs}: h{hs} {mq[hs]:+.1%}; plateau {a}-{b} averaged on {rs} {mean([mq[h] for h in range(a, b+1)]):+.1%} (range {min(mq[h] for h in range(a,b+1)):+.1%} to {max(mq[h] for h in range(a,b+1)):+.1%}); h15 {mq[15]:+.1%}")
            print(f"    paired h{hs} - h15: {cs} {dP[0]*100:+.1f} pts (se {dP[1]*100:.1f}), {rs} {dQ[0]*100:+.1f} pts (se {dQ[1]*100:.1f}); 11-block smoothed optimum h = {hsm}: {cs} {mcurve(P,1,1200)[hsm]:+.1%}, {rs} {mq[hsm]:+.1%}")
