"""check_path.py (edge_check/E): (1) path() in common.py equals stake_scale.model_eff (imported, not copied) on every launch of
the population at holds 1, 2, 5, 15, 37, 60, 150, 300, 599 and, where the extended tape reaches, 900 and 1200, at second and third
place; (2) the yardstick reproduces rounds 1-2: fit 73 fires h300 +26.32%, h15 +16.22%; recent 18 committed fires h300 +3.46%,
h15 +12.81%; with the gap fire 19 fires h300 +3.01%, h15 +12.56%; (3) where the tapes come from and how far they reach.
    python3 data/derived/edge_check/E/check_path.py > data/derived/edge_check/E/check_path.txt"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
R = c.load_all(); H = (1, 2, 5, 15, 37, 60, 150, 300, 599, 900, 1200); dmax = 0.0; n = 0; nolaunch = 0; src = collections.Counter(); reach = collections.Counter()
fires = {"fit": [], "rec": [], "rec_committed": []}
for r in R:
    L = c.tape(r["cv"]); src[L["src"]] += 1; e1 = c.seat_block(L)
    if e1 is None or L["tier"] is None: nolaunch += 1; continue
    reach[(L["hi"] - e1) >= 1200] += 1
    for na in (1, 2):
        p, g = c.path(L, na)
        for h in H:
            if p[h] is None: continue
            m = c.model_eff(L, c.STAKE / c.E, e1, na, h)[0]; dmax = max(dmax, abs(m - p[h])); n += 1
    if c.is_fire(r):
        p, g = c.path(L, 1); fires[r["set"]].append(p)
        if r["set"] == "rec" and r["committed"]: fires["rec_committed"].append(p)
print(f"path() against model_eff: {n} comparisons on {len(R) - nolaunch} launches, max |difference| {dmax:.2e}; launches without a seat block or tier: {nolaunch}")
print("tape sources (A, C real stamps; B, D some synthesised):", dict(src), "; extended to E1+1200:", dict(reach))
for k, v in fires.items():
    print(f"{k:14s} {len(v):3d} fires  h15 {c.mean([p[15] for p in v]):+.2%}  h300 {c.mean([p[300] for p in v]):+.2%}" + (f"  h1200 {c.mean([p[1200] for p in v]):+.2%} on {sum(p[1200] is not None for p in v)}" if all(p[1200] is not None for p in v) else ""))
