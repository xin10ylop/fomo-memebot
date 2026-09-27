"""choose.py (edge_check/F), task 2: choose the hold on one set alone (argmax of the fires' mean over h = 1..600) and read it on the
other: fit -> recent, recent -> fit, Sep 18-21 -> Sep 22-27 (and the two reverse directions for completeness). The plateau of a
choice is every h whose mean on the choosing set is within one standard error (sd/sqrt(n) at the optimum) of the optimum's mean;
printed as the contiguous run around the optimum, plus how many of the 600 holds qualify anywhere and their extent.
    python3 data/derived/edge_check/F/choose.py > data/derived/edge_check/F/choose.txt"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from load import *
HMAXC = 600
def curve(s):
    f = mask(s) & FIRE; return stats(P2[f], G[f])
def runs(ok):
    out = []; a = None
    for h in range(1, len(ok)):
        if ok[h] and a is None: a = h
        if not ok[h] and a is not None: out.append((a, h - 1)); a = None
    if a is not None: out.append((a, len(ok) - 1))
    return out
def choose(src, dst, hmax=HMAXC):
    A = curve(src); B = curve(dst); m = A["mean"][: hmax + 1].copy(); m[0] = -9; h = int(np.argmax(m)); thr = A["mean"][h] - A["se"][h]
    ok = np.zeros(hmax + 1, bool); ok[1:] = A["mean"][1: hmax + 1] >= thr; R = runs(ok); run = next(r for r in R if r[0] <= h <= r[1])
    pl = list(range(run[0], run[1] + 1))
    print(f"\nchoose on {src} ({A['n']} fires), read on {dst} ({B['n']} fires), h in 1..{hmax}")
    print(f"  optimum h = {h}: {src} mean {A['mean'][h]:+.1%} (se {A['se'][h]:.1%}, median {A['median'][h]:+.1%}, win {A['win'][h]:.0%}, $ {A['usd'][h]:+.2f}/fire)  ->  {dst} mean {B['mean'][h]:+.1%} (median {B['median'][h]:+.1%}, win {B['win'][h]:.0%}, $ {B['usd'][h]:+.2f}/fire)")
    print(f"  plateau (mean >= {thr:+.1%}): contiguous h {run[0]}-{run[1]} ({len(pl)} holds); anywhere: {int(ok.sum())} of {hmax} holds, runs {R if len(R) <= 12 else R[:12] + ['...']}")
    print(f"  {dst} over that contiguous plateau: mean of the means {np.mean(B['mean'][pl]):+.1%}, range {B['mean'][pl].min():+.1%} .. {B['mean'][pl].max():+.1%}; {dst} at h = 15: {B['mean'][15]:+.1%}; {src} at h = 15: {A['mean'][15]:+.1%}")
    return h, run
res = {}
for src, dst in (("fit", "rec"), ("rec", "fit"), ("early", "late"), ("late", "early"), ("rec18", "fit")): res[(src, dst)] = choose(src, dst)
print("\nthe same choices over h = 1..1200 (tapes reach every launch to 1,200 blocks after the seat):")
for src, dst in (("fit", "rec"), ("rec", "fit"), ("early", "late")): choose(src, dst, 1200)
# the choice on each set's own curve smoothed over +-5 blocks (a spike-resistant optimum)
print("\noptimum of the 11-block running mean of the curve (h 6..595), each set:")
for s in ("fit", "rec", "early", "late", "all"):
    c = curve(s)["mean"]; sm = np.array([c[h - 5: h + 6].mean() for h in range(6, 596)]); h = int(np.argmax(sm)) + 6
    print(f"  {s:5s} smoothed optimum h = {h} (smoothed {sm[h-6]:+.1%}, raw {c[h]:+.1%})")
