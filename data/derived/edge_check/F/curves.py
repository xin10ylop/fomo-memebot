"""curves.py (edge_check/F), task 1: the rule's fires priced at every hold h = 1..1200 blocks after the seat (second place, $13,
gas $0.33 a burst, model_eff), per set: fit, recent (with the gap fire; rec18 = the committed 11 windows), each fit window, Sep 18-21
and Sep 22-27, each UTC day Sep 18-27. For every h: fires n, mean, median, win rate, dead rate (< -40%), sd, $ a fire after gas,
the refused launches' mean at the same h (every block) and the fires' lift over them. Full grid in curves.csv; the report's grid
(every 5 to 60, every 20 to 300, every 50 to 600, every 100 to 1200) in curves.txt.
    python3 data/derived/edge_check/F/curves.py > data/derived/edge_check/F/curves.txt"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from load import *
HS = np.arange(0, 1201); GRID = [1] + list(range(5, 61, 5)) + list(range(80, 301, 20)) + list(range(350, 601, 50)) + list(range(700, 1201, 100))
SETS = ["fit", "rec", "rec18", "all"] + FITW + ["early", "late"] + DAYS
rows = []; S = {}
for s in SETS:
    m = mask(s); f = m & FIRE; r = m & ~FIRE
    if f.sum() == 0: continue
    st = stats(P2[f], G[f]); rf = P2[r].mean(0) if r.sum() else np.full(len(HS), np.nan); S[s] = (st, rf, int(r.sum()))
    for h in range(1, 1201):
        rows.append(f"{s},{h},{st['n']},{st['mean'][h]:.6f},{st['median'][h]:.6f},{st['win'][h]:.4f},{st['dead'][h]:.4f},{st['sd'][h]:.6f},{st['usd'][h]:.4f},{int(r.sum())},{rf[h]:.6f},{st['mean'][h]-rf[h]:.6f}")
open(os.path.dirname(os.path.abspath(__file__)) + "/curves.csv", "w").write("set,h,fires,mean,median,win,dead,sd,usd_per_fire,refused_n,refused_mean,lift\n" + "\n".join(rows) + "\n")
print("second place in E1, $13 at 2570 $/ETH, gas $0.33 a burst; h = blocks after the seat block E1, the exit folds every buy and sell up to E1+h")
for s, lab in (("fit", "FIT Sep 18-23"), ("rec", "RECENT Sep 24-27")):
    st, rf, nr = S[s]
    print(f"\n{lab}: {st['n']} fires, {nr} refused")
    print(f"{'h':>5s} {'mean':>7s} {'median':>7s} {'win':>4s} {'dead':>4s} {'sd':>6s} {'$/fire':>7s} {'refused':>7s} {'lift':>6s}")
    for h in GRID: print(f"{h:5d} {st['mean'][h]:+7.1%} {st['median'][h]:+7.1%} {st['win'][h]:4.0%} {st['dead'][h]:4.0%} {st['sd'][h]:6.2f} {st['usd'][h]:+7.2f} {rf[h]:+7.1%} {100*(st['mean'][h]-rf[h]):+6.1f}")
SHORT = [1, 5, 10, 15, 20, 30, 40, 60, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1200]
for title, group in (("the four fit windows, Sep 18-21 / Sep 22-27, the committed recent (rec18)", FITW + ["early", "late", "rec18", "all"]), ("day by day (UTC day of the creation)", [d for d in DAYS if d in S])):
    for what in ("mean", "win", "usd"):
        print(f"\n{title}: {what} by hold" + ("  (lift over the same set's refused in the next table)" if what == "mean" else ""))
        print(f"{'h':>5s} " + " ".join(f"{g + ' n' + str(S[g][0]['n']):>14s}" for g in group))
        for h in SHORT:
            fmt = (lambda v: f"{v:+14.1%}") if what == "mean" else (lambda v: f"{v:14.0%}") if what == "win" else (lambda v: f"{v:+14.2f}")
            print(f"{h:5d} " + " ".join(fmt(S[g][0][what][h]) for g in group))
    print(f"\n{title}: lift over the refused (points) and refused n")
    print(f"{'h':>5s} " + " ".join(f"{g + ' r' + str(S[g][2]):>14s}" for g in group))
    for h in SHORT: print(f"{h:5d} " + " ".join(f"{100*(S[g][0]['mean'][h]-S[g][1][h]):+14.1f}" for g in group))
