"""sweep.py (edge_check/E): every launch of the population priced at every hold h = 0..1200 blocks after the seat block E1, at
second place (the yardstick) and third place (for the live mix), $13; one cache for every other script.
    python3 data/derived/edge_check/E/sweep.py      -> data/derived/edge_check/E/paths.json.gz"""
import sys, os, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
out = []
for r in c.load_all():
    L = c.tape(r["cv"])
    p1, g = c.path(L, 1)
    if p1 is None: continue
    p2, g2 = c.path(L, 2); e1 = c.seat_block(L)
    out.append({"cv": r["cv"], "win": r["win"], "set": r["set"], "committed": r["committed"], "day": r["day"], "T0": r["T0"], "k": r["k"],
                "fire": c.is_fire(r), "e1": e1 - L["b0"], "reach": L["hi"] - e1, "g": g, "g2": g2,
                "p1": [None if x is None else round(x, 7) for x in p1], "p2": [None if x is None else round(x, 7) for x in p2]})
json.dump(out, gzip.open(c.EE + "paths.json.gz", "wt"))
print(len(out), "launches priced;", sum(x["fire"] for x in out), "fires;", sum(x["reach"] >= 1200 for x in out), "reach E1+1200")
