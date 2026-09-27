"""robust.py (edge_check/E): (a) every candidate hold at h, h+2, h+4 and the landing average (h+2..h+4: what the engine's
HOLD_BLOCKS = h delivers) on both periods, with the per-fire paired difference against 15 at the same delay; (b) the setting
chosen on the landing-averaged curve (choose on one set, read on the other, plateau at one standard error); (c) the bootstrap:
2,000 resamples of the fires of each set (seed 7): where the optimal h falls (1..600), the optimal setting on the landing-averaged
curve, and the mean at 15 and at the candidates.
    python3 data/derived/edge_check/E/robust.py > data/derived/edge_check/E/robust.txt"""
import sys, os, json, gzip
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
P = json.load(gzip.open(c.EE + "paths.json.gz", "rt")); DAYS = [f"Sep {d}" for d in range(18, 28)]
def M(sel): return np.array([x["p1"][:1201] for x in P if x["fire"] and sel(x)], dtype=float)
S = {"fit": M(lambda x: x["set"] == "fit"), "rec": M(lambda x: x["set"] == "rec"), "pooled": M(lambda x: True),
     "Sep18-21": M(lambda x: x["day"] in DAYS[:4]), "Sep22-27": M(lambda x: x["day"] in DAYS[4:]), "Sep22-23": M(lambda x: x["day"] in ("Sep 22", "Sep 23"))}
def land(A): return (A[:, 2:-2] + A[:, 3:-1] + A[:, 4:]) / 3.0          # column s = setting s: mean of landing at s+2, s+3, s+4
def se(v): return v.std(ddof=1) / np.sqrt(len(v))
CAND = [5, 7, 8, 9, 10, 11, 12, 13, 15, 18, 20, 25, 30, 60, 150, 220, 300, 337]
print("=== (a) candidates at h, h+2, h+4 and the landing average (h+2..h+4); paired difference against 15 at the same delay (mean +- se)")
for k in ("fit", "rec"):
    A = S[k]; L = land(A); print(f"--- {k} ({len(A)} fires)")
    print(f"{'h':>5s} {'at h':>7s} {'h+2':>7s} {'h+4':>7s} {'land':>7s}   {'vs 15 at h':>14s} {'vs 15 at +2':>14s} {'vs 15 at +4':>14s} {'vs 15 land':>14s}  {'sd land':>7s}")
    for h in CAND:
        d = [A[:, h + j] - A[:, 15 + j] for j in (0, 2, 4)] + [L[:, h] - L[:, 15]]
        print(f"{h:5d} {A[:, h].mean():+7.1%} {A[:, h+2].mean():+7.1%} {A[:, h+4].mean():+7.1%} {L[:, h].mean():+7.1%}   " + " ".join(f"{x.mean():+6.1%}+-{se(x):4.1%}" for x in d) + f"  {L[:, h].std(ddof=1):7.3f}")
print("\n=== (b) the setting chosen on the landing-averaged curve (settings 1..596), plateau = within one se of the optimum")
def ranges(hs):
    out = []
    for h in hs:
        if out and h == out[-1][1] + 1: out[-1][1] = h
        else: out.append([h, h])
    return ", ".join(f"{a}-{b}" if a != b else f"{a}" for a, b in out)
for a, b in (("fit", "rec"), ("rec", "fit"), ("Sep18-21", "Sep22-27"), ("Sep18-21", "Sep22-23"), ("Sep18-21", "rec")):
    La, Lb = land(S[a])[:, :597], land(S[b])[:, :597]; ma = La.mean(0); ma[0] = -9; s = int(ma.argmax()); e = se(La[:, s])
    for lo, hi in ((1, 596), (1, 60)):
        seg = ma.copy(); seg[:lo] = -9; seg[hi + 1:] = -9; s = int(seg.argmax()); e = se(La[:, s]); on = [g for g in range(lo, hi + 1) if ma[g] >= ma[s] - e]
        print(f"  choose on {a:8s} (settings {lo}..{hi}): setting {s:3d} {ma[s]:+.1%} (se {e:.1%}) plateau {ranges(on)}; read on {b}: {Lb[:, s].mean():+.1%} (setting 15 there {Lb[:, 15].mean():+.1%}, here {ma[15]:+.1%})")
print("\n=== (c) bootstrap, 2,000 resamples of the fires of each set (seed 7)")
rng = np.random.default_rng(7); NB = 2000
BINS = [(1, 9), (10, 13), (14, 20), (21, 30), (31, 100), (101, 200), (201, 300), (301, 400), (401, 600)]
for k in ("fit", "rec", "pooled"):
    A = S[k][:, :605]; n = len(A); L = land(A)[:, :597]; hs = []; ss = []; m = {h: [] for h in (9, 11, 15, 220, 300, 337)}; ml = {h: [] for h in (8, 9, 11, 15)}
    for _ in range(NB):
        i = rng.integers(0, n, n); cv = A[i, 1:601].mean(0); hs.append(int(cv.argmax()) + 1)
        lv_ = L[i, 1:597].mean(0); ss.append(int(lv_.argmax()) + 1)
        for h in m: m[h].append(cv[h - 1])
        for h in ml: ml[h].append(lv_[h - 1])
    hs = np.array(hs); ss = np.array(ss)
    print(f"--- {k} ({n} fires): optimal h (1..600) median {int(np.median(hs))}, 5-95% {int(np.percentile(hs,5))}-{int(np.percentile(hs,95))}; share by range: " + "  ".join(f"{a}-{b} {np.mean((hs>=a)&(hs<=b)):.0%}" for a, b in BINS))
    print(f"    optimal setting on the landing-averaged curve (1..596): median {int(np.median(ss))}, 5-95% {int(np.percentile(ss,5))}-{int(np.percentile(ss,95))}; share by range: " + "  ".join(f"{a}-{b} {np.mean((ss>=a)&(ss<=b)):.0%}" for a, b in BINS))
    for h, v in m.items():
        v = np.array(v); print(f"    mean at h {h:3d}: {np.mean(v):+.1%} (2.5-97.5% {np.percentile(v,2.5):+.1%} to {np.percentile(v,97.5):+.1%}); P(below 0) {np.mean(v<0):.1%}; P(above h15) {np.mean(v>np.array(m[15])):.0%}")
    for h, v in ml.items():
        v = np.array(v); print(f"    landing average, setting {h:3d}: {np.mean(v):+.1%} (2.5-97.5% {np.percentile(v,2.5):+.1%} to {np.percentile(v,97.5):+.1%}); P(above setting 15) {np.mean(v>np.array(ml[15])):.0%}")
