"""check_pricing.py (K3): common.path against the hold grids (model_path) and reviewer G's r2/r3 on every launch that has both.
    python3 data/derived/edge_check/K3/check_pricing.py > data/derived/edge_check/K3/check_pricing.txt"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
X = load_dump(); d = {"g_r2": [], "g_r3": [], "grid_b1": [], "grid_first": [], "tk_seat1": []}
for x in X:
    L = tape(x["cv"])
    if not L: continue
    p1 = path(L, 1, hmax=60); p0 = path(L, 0, hmax=60); p2 = path(L, 2, hmax=60)
    for h in (9, 11, 13, 15, 30, 60):
        if x.get("g_r2") and x["g_r2"][h] is not None: d["g_r2"].append(abs(p1["v"][h] - x["g_r2"][h]))
        if x.get("g_r3") and x["g_r3"][h] is not None: d["g_r3"].append(abs(p2["v"][h] - x["g_r3"][h]))
        if x["src"] == "grid" and ret(x, h) is not None: d["grid_b1"].append(abs(p1["v"][h] - ret(x, h)))
        if ret(x, h, "first") is not None: d["grid_first"].append(abs(p0["v"][h] - ret(x, h, "first")))
    if x.get("tk_seat1"): d["tk_seat1"].append(abs(p1["tk"] / x["tk_seat1"] - 1))
for k, v in d.items():
    v = sorted(v); print(f"{k:11s} pairs {len(v):5d}  median |diff| {median(v):.5f}  p95 {v[int(0.95*len(v))] if v else float('nan'):.4f}  max {max(v) if v else float('nan'):.4f}")
