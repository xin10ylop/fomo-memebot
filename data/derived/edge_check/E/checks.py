"""checks.py (edge_check/E): the summary facts the report quotes from the curves: the lift's range over hold ranges (from
curves.csv; run curves.py first), and the dip after block 11 (from paths.json.gz): the share of fires that lose more than 2 points
from their peak in blocks 11-15 to block 16, and the mean per-block change in blocks 9-20.
    python3 data/derived/edge_check/E/checks.py > data/derived/edge_check/E/checks.txt"""
import sys, os, csv, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
R = [r for r in csv.DictReader(open(c.EE + "curves.csv"))]
def lift(g, a, b):
    v = [(int(r["h"]), float(r["lift"])) for r in R if r["group"] == g and a <= int(r["h"]) <= b]
    lo = min(v, key=lambda t: t[1]); hi = max(v, key=lambda t: t[1]); return f"{g} lift h {a}-{b}: min {lo[1]:+.1%} (h {lo[0]}), max {hi[1]:+.1%} (h {hi[0]}), negative on {sum(x < 0 for _, x in v)} of {len(v)}"
for g, a, b in (("fit", 1, 1200), ("rec", 5, 20), ("rec", 35, 60), ("rec", 80, 279), ("rec", 280, 1200)): print(lift(g, a, b))
P = json.load(gzip.open(c.EE + "paths.json.gz", "rt"))
for s in ("fit", "rec"):
    F = [x["p1"] for x in P if x["fire"] and x["set"] == s]
    print(f"{s}: share of fires losing > 2 points from their block 11-15 peak to block 16: {sum((p[16] - max(p[11:16])) < -0.02 for p in F)/len(F):.0%};"
          " mean change per block: " + " ".join(f"{h}:{c.mean([p[h]-p[h-1] for p in F]):+.2%}" for h in range(9, 21)))
