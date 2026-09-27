"""perm3.py (reviewer B): two-sided permutation p values (20,000 shuffles of the 91 fires) for the fit-vs-recent differences
quoted in REPORT.md section 3. python3 data/derived/edge_check/B/perm3.py"""
import json, random, statistics as st, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
F = json.load(open(c.B + "features.json")); H = json.load(open(c.B + "holds_fires.json")); random.seed(3)
def share(f, cl, h=300):
    held = f["held"].get(cl, 0); s = f["sold"][str(h)].get(cl, 0); return min(1, s / held) if held > 0 else 0
for lab, fn in (("h15", lambda f: H[f["cv"]]["15"]), ("drift h300-h15", lambda f: H[f["cv"]]["300"] - H[f["cv"]]["15"]),
                ("bundle share sold by E1+300", lambda f: share(f, "bundle")), ("bundle ETH out in hold", lambda f: f["sell_eth"].get("bundle", 0)),
                ("outsider ETH after seat second", lambda f: f["buy_eth_after"].get("other", 0)), ("seat buys", lambda f: f["seat_n"]),
                ("seat ETH", lambda f: f["seat_eth"]), ("rival shots creation second", lambda f: f["shots_cs"])):
    a = [fn(f) for f in F if f["fire"] and f["grp"] == "fit"]; b = [fn(f) for f in F if f["fire"] and f["grp"] == "recent"]
    d = st.mean(b) - st.mean(a); pool = a + b; n = 0; N = 20000
    for _ in range(N):
        random.shuffle(pool)
        if abs(st.mean(pool[len(a):]) - st.mean(pool[:len(a)])) >= abs(d): n += 1
    print(f"{lab:32s} fit {st.mean(a):8.3f} recent {st.mean(b):8.3f} diff {d:+8.3f} two-sided perm p {n/N:.3f}")
from math import comb
fit = [f for f in F if f["fire"] and f["grp"] == "fit"]; rec = [f for f in F if f["fire"] and f["grp"] == "recent"]
p = sum(share(f, "bundle") > 0.1 for f in fit) / len(fit); k = sum(share(f, "bundle") > 0.1 for f in rec); n = len(rec)
print(f"bundle dumps (>10% sold by E1+300): fit {p:.3f}, recent {k}/{n}; binomial P(>= {k} of {n} | fit rate) = {sum(comb(n, j) * p**j * (1-p)**(n-j) for j in range(k, n + 1)):.3f}")
