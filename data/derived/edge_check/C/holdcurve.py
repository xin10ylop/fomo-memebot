"""holdcurve.py (edge_check/C): the rule's fires priced at every hold from 1 to 300 blocks (second place, $13), fit against recent,
to see whether the 15-block number is a plateau or a spike, and how much a late sell (the engine's sell lands 2-3 blocks after
its decision) costs. Offline from the tapes.
    python3 data/derived/edge_check/C/holdcurve.py > data/derived/edge_check/C/holdcurve.txt"""
import sys, json
sys.path.insert(0, "data/derived/edge_check/C"); from common import *
R = [r for r in load_all() if is_fire(r)]
H = (1, 3, 5, 8, 10, 12, 15, 18, 20, 25, 30, 40, 60, 100, 150, 200, 250, 300)
res = {"fit": [], "rec": []}
for r in R:
    L = tape(r["cv"]); res[r["set"]].append([price(L, h, 1) for h in H])
print("hold (blocks after E1)   " + " ".join(f"{h:>6d}" for h in H))
for per in ("fit", "rec"):
    rows = res[per]
    print(f"{per:4s} {len(rows):3d} fires mean     " + " ".join(f"{mean([x[i] for x in rows]):+6.1%}" for i in range(len(H))))
    print(f"{per:4s}           win      " + " ".join(f"{sum(x[i] > 0 for x in rows)/len(rows):6.0%}" for i in range(len(H))))
    print(f"{per:4s}           $/fire   " + " ".join(f"{mean([usd(x[i]) for x in rows]):+6.2f}" for i in range(len(H))))

# the refused launches at the same holds (the rule's lift = fires minus refused)
ref = {"fit": [], "rec": []}
for r in load_all():
    if is_fire(r): continue
    L = tape(r["cv"])
    if L is None or seat_block(L) is None: continue
    ref[r["set"]].append([price(L, h, 1) for h in H])
for per in ("fit", "rec"):
    print(f"{per:4s} {len(ref[per]):3d} refused mean  " + " ".join(f"{mean([x[i] for x in ref[per]]):+6.1%}" for i in range(len(H))))
    print(f"{per:4s}     lift (fires-ref) " + " ".join(f"{mean([x[i] for x in res[per]]) - mean([x[i] for x in ref[per]]):+6.1%}" for i in range(len(H))))
