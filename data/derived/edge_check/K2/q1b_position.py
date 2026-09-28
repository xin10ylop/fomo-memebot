"""K2/q1b_position.py: the guard and the landing position together, on the fires that have a tape. The replay prices every fill
at second place and checks the guard there; a burst that trips the guard at second place often has a crowd in E1, so a looser guard
may fill deeper. Each fire is priced with the guard checked AT the position it lands (tokens there vs tokens sized at the build) and
the return taken there: first, second, third, last place in E1. Also Q4: the return by position and by the size of the buy ahead."""
import os, sys, json, gzip, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from sim import *
P = json.load(gzip.open(os.path.join(HERE, "prices.json.gz"), "rt")); PR = P["rows"]; HS = P["HS"]; I = HS.index(11)
base = run(); fired = [r for r in base if r.get("fired")]
tap = [r for r in fired if r["x"]["cv"] in PR]
print(f"usual view: {len(fired)} fires, {len(tap)} with a tape (fit {sum(period(r['x'])=='fit' for r in tap)} of {sum(period(r['x'])=='fit' for r in fired)}, read {sum(period(r['x'])=='read' for r in tap)} of {sum(period(r['x'])=='read' for r in fired)})")
POS = (("first", "p1"), ("second", "p2"), ("third", "p3"), ("last", "plast"))
print("\n== the guard checked at the landing position; $ at $13, reverted = -$0.33; taped fires only ==")
print(f"{'slip':>5s} " + " ".join(f"{p:>30s}" for p, _ in POS))
for slip in (0.07, 0.10, 0.15, 0.20, 1.0):
    cells = []
    for per in ("fit", "read"):
        c = []
        for _, key in POS:
            usd = 0.0; nf = 0; v = []
            for r in tap:
                if period(r["x"]) != per: continue
                p = PR[r["x"]["cv"]]; tb = r["x"]["tk_build"]; ok = (not tb) or p["tk_" + key] >= (1 - slip) * tb
                if ok: usd += p[key][I] * 13 - 0.33; nf += 1; v.append(p[key][I])
                else: usd -= 0.33
            c.append(f"{nf:3d}f {mean(v):+6.1%} ${usd:+7.1f}")
        cells.append(c)
    print(f"{slip:5.2f} fit  " + " ".join(f"{c:>30s}" for c in cells[0]))
    print(f"{'':5s} read " + " ".join(f"{c:>30s}" for c in cells[1]))
# Q4: return at every position; by the ETH of the buy ahead of second place
print("\n== Q4: second place by the size of the buy ahead (the first E1 buy); taped usual-view fires, h11 ==")
for lo, hi in ((0, 0.005), (0.005, 0.02), (0.02, 0.05), (0.05, 0.15), (0.15, 99)):
    for per in ("fit", "read"):
        v = [PR[r["x"]["cv"]]["p2"][I] for r in tap if period(r["x"]) == per and PR[r["x"]["cv"]]["e1_buys"] and lo <= PR[r["x"]["cv"]]["e1_buys"][0][0] < hi]
        v1 = [PR[r["x"]["cv"]]["p1"][I] for r in tap if period(r["x"]) == per and PR[r["x"]["cv"]]["e1_buys"] and lo <= PR[r["x"]["cv"]]["e1_buys"][0][0] < hi]
        print(f"  buy ahead {lo:5.3f}-{hi:5.3f} ETH {per:4s}: n {len(v):3d} second {mean(v):+7.1%} (first {mean(v1):+7.1%})")
print("\n== Q4: by position, every taped launch that passed the pre-gates and the fleets gate (the guard ignored), h11 ==")
for per in ("fit", "read"):
    print(f"  {per}: " + "  ".join(f"{p} {mean([PR[r['x']['cv']][k][I] for r in tap if period(r['x']) == per]):+6.1%}" for p, k in POS) + f"   (n {sum(period(r['x'])==per for r in tap)})")
    nb = [len(PR[r['x']['cv']]['e1_buys']) for r in tap if period(r['x']) == per]
    print(f"        E1 buys per fire: median {st.median(nb)}, mean {mean(nb):.1f}; ETH ahead of second place median {st.median([PR[r['x']['cv']]['e1_buys'][0][0] if PR[r['x']['cv']]['e1_buys'] else 0 for r in tap if period(r['x'])==per]):.4f}")
# ETH in E1 overall (crowd size in the seat block) against second place
print("\n== second place h11 by total E1 buy ETH (ex post), taped usual-view fires ==")
for lo, hi in ((0, 0.02), (0.02, 0.1), (0.1, 0.3), (0.3, 99)):
    for per in ("fit", "read"):
        v = [PR[r["x"]["cv"]]["p2"][I] for r in tap if period(r["x"]) == per and lo <= sum(b[0] for b in PR[r["x"]["cv"]]["e1_buys"]) < hi]
        print(f"  E1 ETH {lo:4.2f}-{hi:4.2f} {per:4s}: n {len(v):3d} second {mean(v):+7.1%}")
