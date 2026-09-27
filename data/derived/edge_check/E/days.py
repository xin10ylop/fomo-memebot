"""days.py (edge_check/E): every statistic of task 1 per group at three holds (h = 9, 15, 300; the sell exactly at E1+h), read
from curves.csv (run curves.py first): n fires / refused, mean, median, win, dead, sd, $ a fire after gas, refused mean, lift.
    python3 data/derived/edge_check/E/days.py > data/derived/edge_check/E/days.txt"""
import csv, os
R = {}
for r in csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "curves.csv"))): R[(r["group"], int(r["h"]))] = r
groups = list(dict.fromkeys(g for g, _ in R))
for h in (9, 11, 15, 300):
    print(f"\n=== h = {h}")
    print(f"{'group':>9s} {'fires':>5s} {'ref':>4s} {'mean':>7s} {'median':>7s} {'win':>4s} {'dead':>4s} {'sd':>5s} {'$/fire':>6s} {'refused':>7s} {'lift':>6s}")
    for g in groups:
        r = R[(g, h)]; f = lambda k: float(r[k])
        print(f"{g:>9s} {r['n']:>5s} {r['n_ref']:>4s} {f('mean'):+7.1%} {f('median'):+7.1%} {f('win'):4.0%} {f('dead'):4.0%} {f('sd'):5.2f} {f('usd'):+6.2f} {f('ref'):+7.1%} {f('lift'):+6.1%}")
