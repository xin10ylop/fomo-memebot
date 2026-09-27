"""sellers.py (edge_check/G): why the fires' value falls after block 11. For every fire, the tokens sold in each block E1+1..E1+30, split
by where the seller bought: in the creation second (the bundle and the snipers), in the seat block E1 (the first seats, ours excluded),
in E1+1..E1+10, later, or never on the tape; as a share of the curve's sold tokens, summed over the fires of each period.
    python3 data/derived/edge_check/G/sellers.py > data/derived/edge_check/G/sellers.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
import collections
cats = ("creation", "E1", "E1+1..10", "later", "none")
for per in ("fit", "rec"):
    tot = {o: collections.Counter() for o in range(1, 31)}; nE1sell = collections.Counter(); nfires = 0
    for r in load_all():
        if not is_fire(r) or r["set"] != per: continue
        L = tape(r["cv"]); e1 = seat_block(L); ts = L["ts"]; T0 = L["T0"]; nfires += 1; first = {}
        for x in L["rows"]:
            if x["who"] in OURS: continue
            if x["k"] == "B" and x["who"] not in first:
                first[x["who"]] = "creation" if ts.get(x["bn"], 9e18) == T0 else "E1" if x["bn"] == e1 else "E1+1..10" if x["bn"] <= e1 + 10 else "later"
            if x["k"] == "S" and e1 < x["bn"] <= e1 + 30:
                c = first.get(x["who"], "none"); tot[x["bn"] - e1][c] += x["tk"]
                if c == "E1": nE1sell[x["bn"] - e1] += 1
    print(f"\n=== {per}: {nfires} fires; tokens sold by block after E1 (millions, summed over the fires) by where the seller bought; E1 buyers' sell count")
    print(f"{'blk':>3s} " + " ".join(f"{c:>9s}" for c in cats) + f" {'E1 share':>8s} {'E1 sells':>8s}")
    for o in range(1, 31):
        t = tot[o]; s = sum(t.values()) or 1
        print(f"{o:3d} " + " ".join(f"{t[c]/1e6:9.1f}" for c in cats) + f" {t['E1']/s:8.0%} {nE1sell[o]:8d}")
