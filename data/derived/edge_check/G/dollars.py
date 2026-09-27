"""dollars.py (edge_check/G): task 5. $ a day at $13 at the recent supply, 0.32 fires an hour (7.68 a day), for h = 15, the fit's optimum
(337), the recent optimum (11), the recommendation (setting 9), and 300 (as run to Sep 27). Per-fire returns from the fit's fires and from
the recent fires, each at the table's exit (E1+h) and landed (the average of E1+h+2..h+4). Full fill: every burst fills in second place,
$ = return x effective stake - $0.33 gas. Live mix: half the bursts fill; a fill lands second two times in three and third one time in
three (third place priced with n_ahead=2); gas $0.33 on every burst, filled or not.
    python3 data/derived/edge_check/G/dollars.py > data/derived/edge_check/G/dollars.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
from sweep import C
FPD = 0.32 * 24
F = {per: [x for x in C if x["fire"] and x["set"] == per] for per in ("fit", "rec")}
def ret(x, key, h, landed): return mean([x[key][h + j] for j in (2, 3, 4)]) if landed else x[key][h]
print(f"fires a day at the recent supply: {FPD:.2f}; $13 stake at 2570 $/ETH; gas $0.33 a burst")
print(f"{'h':>10s} {'returns from':>12s} {'exit':>7s} {'2nd place':>9s} {'3rd place':>9s} {'$/day full fill':>15s} {'$/day live mix':>14s}")
for label, h in (("15 (now)", 15), ("9 (rec.)", 9), ("11 (rec opt)", 11), ("337 (fit opt)", 337), ("300 (old)", 300)):
    for per in ("fit", "rec"):
        for landed in (False, True):
            r2 = [ret(x, "r2", h, landed) for x in F[per]]; r3 = [ret(x, "r3", h, landed) for x in F[per]]
            u2 = mean([a * x["g"] * E for a, x in zip(r2, F[per])]); u3 = mean([a * x["g3"] * E for a, x in zip(r3, F[per])])
            full = FPD * (u2 - GAS); live = FPD * (0.5 * (2 / 3 * u2 + 1 / 3 * u3) - GAS)
            print(f"{label:>13s} {per:>9s} {'landed' if landed else 'at h':>7s} {mean(r2):+9.1%} {mean(r3):+9.1%} {full:+15.2f} {live:+14.2f}")
