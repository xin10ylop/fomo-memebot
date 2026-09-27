"""stake15.py (edge_check/C): context for question 4, the rule's fires at 15 and 300 blocks at larger stakes (model_eff: our own
impact, the 3% cap, later buyers folded by their ETH), second place, $ after $0.33 gas, fit against recent.
    python3 data/derived/edge_check/C/stake15.py > data/derived/edge_check/C/stake15.txt"""
import sys
sys.path.insert(0, "data/derived/edge_check/C"); from common import *
R = [r for r in load_all() if is_fire(r)]
for h in (15, 300):
    for per in ("fit", "rec"):
        cells = []
        for s in (13, 50, 100, 200):
            v = []
            for r in R:
                if r["set"] != per: continue
                L = tape(r["cv"]); ret, g = model_eff(L, s / E, seat_block(L), 1, h); v.append((ret, ret * g * E - GAS))
            cells.append(f"${s:>3d}: {mean([a for a, _ in v]):+6.1%} ${mean([b for _, b in v]):+6.2f}/fire")
        print(f"h{h:3d} {per:3s} ({sum(r['set'] == per for r in R)} fires)  " + "   ".join(cells))
