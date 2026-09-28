"""K1/q6_size.py: return per fire by stake ($13, $50, $100, $200: G's curve on the tapes, second place, exit 11, the 3% cap and our
own impact included), overall and by bundle ETH and by crowd (fleets at k-1); the fires that fill at the usual view with the live
7% guard and with a 20% guard. $ per fire = stake x return - $0.33 gas."""
import sys, os, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from k1 import *
R = load()
ST = (("13", "p2", 13), ("50", "p2_50", 50), ("100", "p2_100", 100), ("200", "p2_200", 200))
for slip in (0.07, 0.20):
    D = decide(R, view="k-1", slip=slip); P = [d["r"] for d in D if d["why"] == "FILL" and d["r"].get("p2_200")]
    print(f"== guard {slip:.2f}: fills at k-1 with tapes (fit {sum(r['set']=='fit' for r in P)}, read {sum(r['set']=='read' for r in P)})")
    groups = [("all", lambda r: True), ("bundle < 0.6 ETH", lambda r: r["bundle"] < 0.6), ("bundle 0.6-1.2", lambda r: 0.6 <= r["bundle"] < 1.2), ("bundle >= 1.2", lambda r: r["bundle"] >= 1.2),
              ("fleets@k-1 = 2", lambda r: r["f_k1r"] == 2), ("fleets@k-1 3-4", lambda r: 3 <= r["f_k1r"] <= 4), ("fleets@k-1 >= 5", lambda r: r["f_k1r"] >= 5)]
    for lab, sel in groups:
        cells = []
        for part in ("fit", "read"):
            s = [r for r in P if r["set"] == part and sel(r)]
            cells.append(f"{part} n={len(s):2d} " + " ".join(f"${nm}: {mean([r[k][11] for r in s]):+6.1%} (${mean([r[k][11] * v - GAS for r in s]):+6.2f})" for nm, k, v in ST))
        print(f"  {lab:16s} " + " | ".join(cells))
    print()
