"""curves.py (edge_check/G): every launch of the population priced at every hold h = 0..1200 blocks after E1, second place (n_ahead=1,
the yardstick) and third place (n_ahead=2, for the live mix of the $ a day), one pass per launch (common.curve = model_eff, see
check_curve.txt). Output G/curves.json.gz: per launch cv, window, set, rec18, T0, k, fleets at k-2, fire, g (ETH), r2[h], r3[h]
(None past the tape's reach).
    python3 data/derived/edge_check/G/curves.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
out = []; t0 = time.time()
for r in load_all():
    L = tape(r["cv"]); v2, g = curve(L, 1); v3, g3 = curve(L, 2)
    if v2 is None: print("no seat block", r["cv"]); continue
    rd = lambda v: [None if x is None else round(x, 7) for x in v]
    out.append({"cv": r["cv"], "win": r["win"], "set": r["set"], "rec18": r["rec18"], "T0": r["T0"], "k": r["k"], "f_k2": fleets_k2(r), "fire": is_fire(r), "g": g, "g3": g3, "r2": rd(v2), "r3": rd(v3)})
json.dump(out, gzip.open(G + "curves.json.gz", "wt")); print(len(out), "launches", sum(x["fire"] for x in out), "fires", f"{time.time()-t0:.0f} s")
