"""K2/q6_size.py: second place at h11 by stake ($13..$500), our own impact and the 3% cap included, later buys folded by their ETH
(fixed-ETH buyers: the conservative fold; the token fold of model_path shown for the total) on the taped usual-view fires (guard
ignored: every burst), by period, by bundle ETH and by crowd."""
import os, sys, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from sim import *
P = json.load(gzip.open(os.path.join(HERE, "prices.json.gz"), "rt")); PR = P["rows"]
F = [r["x"] for r in run(guard=False) if r.get("fired") and r["x"]["cv"] in PR]
S = (13, 25, 50, 100, 200, 300, 500)
def row(sub, fold, lab):
    c = []
    for s in S:
        v = [PR[x["cv"]][f"s{s}_{fold}"][1] for x in sub]; usd = [PR[x["cv"]][f"s{s}_{fold}"][1] * PR[x["cv"]][f"s{s}_{fold}"][3] - 0.33 for x in sub]
        c.append(f"{mean(v):+6.1%} ${mean(usd):+6.2f}")
    return f"  {lab:34s} n {len(sub):3d} " + " ".join(f"{z:>16s}" for z in c)
print("stakes: " + " ".join(f"{'$'+str(s):>16s}" for s in S) + "   (mean return, mean $ per fire at h11)")
for per in ("fit", "read"):
    sub = [x for x in F if period(x) == per]
    print(f"== {per} ==")
    print(row(sub, "tk", "all, token fold (model_path)"))
    print(row(sub, "eth", "all, ETH fold"))
    for lab, f in (("bundle <= 1 ETH", lambda x: x["bundle"] <= 1.0), ("bundle > 1 ETH", lambda x: x["bundle"] > 1.0), ("fleets = 2", lambda x: x["f_k1r"] == 2), ("fleets >= 3", lambda x: x["f_k1r"] >= 3)):
        print(row([x for x in sub if f(x)], "eth", lab + ", ETH fold"))
    cap = [PR[x["cv"]]["s500_eth"][3] for x in sub]; print(f"  effective stake at $500 after the 3% cap: median ${sorted(cap)[len(cap)//2]:.0f}, min ${min(cap):.0f}; at $300 min ${min(PR[x['cv']]['s300_eth'][3] for x in sub):.0f}")
