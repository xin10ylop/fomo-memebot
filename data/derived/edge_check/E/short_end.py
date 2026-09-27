"""short_end.py (edge_check/E): the short end in detail. The engine's HOLD_BLOCKS = s sells at the block E1+s+d, d the landing
delay (2-4 blocks measured; 0-8 shown): setting 9 against setting 15 at every delay, per fit window, per day, leave-one-fire-out;
and the long-hold bump of the recent set (h 130-270) with its best fire removed.
    python3 data/derived/edge_check/E/short_end.py > data/derived/edge_check/E/short_end.txt"""
import sys, os, json, gzip
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
P = json.load(gzip.open(c.EE + "paths.json.gz", "rt")); F = [x for x in P if x["fire"]]
def A(sel): return np.array([x["p1"][:701] for x in F if sel(x)], dtype=float)
def se(v): return v.std(ddof=1) / np.sqrt(len(v)) if len(v) > 1 else float("nan")
def land(M, s): return (M[:, s + 2] + M[:, s + 3] + M[:, s + 4]) / 3
print("=== setting s against setting 15 when both sells land d blocks late (paired mean +- se)")
for k, sel in (("fit", lambda x: x["set"] == "fit"), ("rec", lambda x: x["set"] == "rec")):
    M = A(sel)
    for s in (8, 9, 10, 11):
        print(f"  {k} setting {s:2d}: " + "  ".join(f"d{d} {M[:, s+d].mean():+.1%} vs {M[:, 15+d].mean():+.1%} ({(M[:, s+d]-M[:, 15+d]).mean():+.1%}+-{se(M[:, s+d]-M[:, 15+d]):.1%})" for d in range(0, 9, 2)))
    for s in (9,):
        print(f"  {k} setting 9, d uniform on 2..8 (a slow sell): {np.mean([M[:, s+d].mean() for d in range(2, 9)]):+.1%} against setting 15 {np.mean([M[:, 15+d].mean() for d in range(2, 9)]):+.1%}")
print("\n=== setting 9 against 15, landing 2-4 blocks late, by fit window and by day (n fires; mean 9, mean 15, difference)")
for g, sel in [(w, (lambda w: lambda x: x["win"] == w)(w)) for w in c.FIT] + [(d, (lambda d: lambda x: x["day"] == d)(d)) for d in [f"Sep {i}" for i in range(18, 28)]]:
    M = A(sel)
    if len(M) == 0: continue
    a, b = land(M, 9), land(M, 15); print(f"  {g:9s} {len(M):3d}  {a.mean():+6.1%} {b.mean():+6.1%}  {(a-b).mean():+6.1%}  (fires better {int((a-b>1e-9).sum())}, worse {int((a-b<-1e-9).sum())})")
print("\n=== leave one fire out: the smallest and largest paired gain of setting 9 over 15 (landing 2-4)")
for k, sel in (("fit", lambda x: x["set"] == "fit"), ("rec", lambda x: x["set"] == "rec")):
    M = A(sel); d = land(M, 9) - land(M, 15); loo = [(np.delete(d, i)).mean() for i in range(len(d))]
    print(f"  {k}: {d.mean():+.2%}; leave-one-out min {min(loo):+.2%} max {max(loo):+.2%}; without the two largest gains {np.sort(d)[:-2].mean():+.2%}")
print("\n=== the recent set's bump at h 130-270, and the short end, without the best fire at each h")
M = A(lambda x: x["set"] == "rec")
for h in (11, 15, 150, 200, 220, 260, 300):
    v = M[:, h]; i = int(v.argmax()); cv = [x["cv"] for x in F if x["set"] == "rec"][i]
    print(f"  h {h:3d}: {v.mean():+6.1%}; without its best fire ({cv[:10]} {v[i]:+.0%}) {np.delete(v, i).mean():+6.1%}; median {np.median(v):+6.1%}")
print("\n=== the short end chosen on one set (settings 1..60, landing 2-4), read on another against setting 15 there (paired mean +- se)")
DAYS = [f"Sep {d}" for d in range(18, 28)]
SETS = {"fit": lambda x: x["set"] == "fit", "rec": lambda x: x["set"] == "rec", "Sep18-21": lambda x: x["day"] in DAYS[:4], "Sep22-27": lambda x: x["day"] in DAYS[4:]}
for w in c.FIT: SETS[w] = (lambda w: lambda x: x["win"] == w)(w); SETS["fit-" + w] = (lambda w: lambda x: x["set"] == "fit" and x["win"] != w)(w)
pairs = [("fit", "rec"), ("rec", "fit"), ("Sep18-21", "Sep22-27")] + [("fit-" + w, w) for w in c.FIT]
for a, b in pairs:
    Ma, Mb = A(SETS[a]), A(SETS[b]); cv = {s: land(Ma, s).mean() for s in range(1, 61)}; s = max(cv, key=cv.get)
    d = land(Mb, s) - land(Mb, 15)
    print(f"  choose on {a:12s} -> setting {s:2d} ({cv[s]:+.1%}); read on {b:9s}: {land(Mb, s).mean():+.1%} against 15 {land(Mb, 15).mean():+.1%}  ({d.mean():+.1%} +- {se(d):.1%})")
