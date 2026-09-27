"""fine.py (edge_check/G): the first 40 blocks block by block, fit and recent: mean, median, win, the paired change from the block
before (mean and se over the same fires), how many fires lose more than 5 points in that one block, and the mean of the exit that
lands 2-4 blocks after the setting (avg of h+2, h+3, h+4: the engine's landing). Also the same for the refused launches' mean.
    python3 data/derived/edge_check/G/fine.py > data/derived/edge_check/G/fine.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
from sweep import C, sets
S = sets()
for name in ("fit", "rec", "Sep18-21", "Sep22-27"):
    P = [x["r2"] for x in C if x["fire"] and S[name](x)]; Rf = [x["r2"] for x in C if not x["fire"] and S[name](x)]
    print(f"\n=== {name}: {len(P)} fires ({len(Rf)} refused)")
    print(f"{'h':>3s} {'mean':>7s} {'median':>7s} {'win':>4s} {'step':>6s} {'se':>5s} {'drops>5pt':>9s} {'rises>5pt':>9s} {'landed h+2..4':>13s} {'refused':>7s}")
    for h in range(1, 41):
        v = [p[h] for p in P]; d = [p[h] - p[h - 1] for p in P]; land = mean([mean([p[h + j] for j in (2, 3, 4)]) for p in P])
        print(f"{h:3d} {mean(v):+7.1%} {median(v):+7.1%} {sum(a > 0 for a in v)/len(v):4.0%} {mean(d)*100:+6.2f} {se(d)*100:5.2f} {sum(a < -0.05 for a in d):9d} {sum(a > 0.05 for a in d):9d} {land:+13.1%} {mean([p[h] for p in Rf]):+7.1%}")
