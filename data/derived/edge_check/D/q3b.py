"""q3b.py (reviewer D): the ETH attached to the shots aimed at the curve by block k-2 (D/shots.json.gz), inside each stratum of the
rule's own count (fleets at k-2 = 0, 1, 2+), fit against recent, at 15 and 300 blocks; and per fit window. Answers whether the ETH
shot carries information beyond the fleet count, and whether that holds in both periods.
    python3 data/derived/edge_check/D/q3b.py > data/derived/edge_check/D/q3b.txt"""
import sys, os, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c, kit as K
raw = {r["cv"]: r for r in c.all_records()}; ETH = {}
for s in json.load(gzip.open(c.DD + "shots.json.gz", "rt")):
    r = raw[s["cv"]]; k = r["k"]; e = 0.0
    for off in range(0, max(0, k - 1)):
        for t, x in zip(s["blocks"][off], r["blocks"][off]):
            if x["to"] in c.US or x["to_token"] or x["fr"] in c.US: continue
            if (x["direct"] and x["named_fr"]) or (not x["direct"] and x["named_data"]): continue
            e += t["value"]
    ETH[s["cv"]] = e
def cell(T, h):
    if not T: return "   0            "
    v = [f["path"][h] for f in T]; return f"{len(T):4d} {c.mean(v):+6.1%} w{sum(x>0 for x in v)/len(v):4.0%}"
for h in (15, 300):
    print(f"hold {h}: n, mean, win   [ETH shot by k-2 >= 0.01 | < 0.01]")
    for lab, sel in (("fleets@k-2 = 0", lambda f: f["k2"]["f"] == 0), ("fleets@k-2 = 1", lambda f: f["k2"]["f"] == 1), ("fleets@k-2 >= 2 (the rule)", lambda f: f["k2"]["f"] >= 2), ("all", lambda f: True)):
        out = []
        for g, S in (("fit", K.FIT), ("recent", K.REC)):
            T = [f for f in S if sel(f)]; hi = [f for f in T if ETH[f["cv"]] >= 0.01]; lo = [f for f in T if ETH[f["cv"]] < 0.01]
            out.append(f"{g}: {cell(hi, h)} | {cell(lo, h)}")
        print(f"  {lab:28s} " + "   ".join(out))
    print("  by fit window, ETH >= 0.01 (any fleets): " + "  ".join(f"{w} {cell([f for f in K.FIT if f['win']==w and ETH[f['cv']]>=0.01], h)}" for w in c.FIT))
    print()
