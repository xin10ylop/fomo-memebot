"""VH verification 1: big-bundle launches, named-wallet overlaps, sign of every >3 ETH launch, ties in T0."""
import sys, os, json, gzip, itertools, time, collections
sys.path.insert(0, "/home/user/fomo-memebot/data/derived/edge_check/VH/rerun"); from common import *
P = load()
print("population", len(P))
# T0 ties
c = collections.Counter(x["T0"] for x in P); print("T0 ties:", sum(v > 1 for v in c.values()))
big = [x for x in P if x["bundle"] > 3.0]
print(f"\nlaunches with bundle > 3.0: {len(big)}")
for x in big:
    r11 = "None" if x["r11"] is None else f"{x['r11']:+.3f}"
    print(f"  {hms(x['T0'])} {x['set']} {x['win']:10s} {x['cv'][:10]} b {x['bundle']:.3f} src {x['bundle_src']:13s} r11 {r11} r15 {x['r15']:+.3f} eng {x['fire_eng']} tab {x['fire_tab']} named {len(x['named'])} ret_src {x['ret_src']}")
v11 = [x["r11"] for x in big if x["r11"] is not None]; v15 = [x["r15"] for x in big]
print("all negative h11:", all(v < 0 for v in v11), len(v11), "range", min(v11), max(v11))
print("all negative h15:", all(v < 0 for v in v15), len(v15), "range", min(v15), max(v15))
ge4 = [x for x in P if x["bundle"] >= 4.0]
print("ge4:", len(ge4), "flat (r11==r15, r11 known)", sum(x["r11"] is not None and abs(x["r11"] - x["r15"]) < 1e-9 for x in ge4))
# operator's sizes
op = [x for x in P if 4.13 <= x["bundle"] <= 4.31 or abs(x["bundle"] - 2.507) < 0.002 or 1.635 <= x["bundle"] <= 1.655 or abs(x["bundle"] - 1.37) < 0.005]
print(f"\nlaunches at the operator's sizes: {len(op)}")
for x in op: print(f"  {hms(x['T0'])} {x['cv'][:10]} b {x['bundle']:.4f} named {len(x['named'])} creator {str(x['creator'])[:10]}")
print("pairwise named overlaps > 0:")
for a, b in itertools.combinations(op, 2):
    s = set(a["named"]) & set(b["named"])
    if s: print(f"  {hms(a['T0'])} {a['cv'][:10]} x {hms(b['T0'])} {b['cv'][:10]}: {len(s)} shared")
cr = collections.Counter(x["creator"] for x in op); print("creators repeated among operator launches:", [(k[:10], v) for k, v in cr.items() if v > 1])
