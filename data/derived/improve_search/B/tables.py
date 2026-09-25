"""tables.py: the brief's per-window tables (fires, fires/day, mean, median, win %, dead %, $/burst, $/day at $13 after $0.33 gas;
pooled FIT and VAL apart) for the baseline, the nine five-criteria passes (ranked by FIT $/day) and the three closest misses.
    cd /home/user/fomo-memebot && python3 <B>/tables.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from variants import PASSED
W = load()
AIM = lambda rule: (lambda r: r["k"] >= 3 and rule(r))
MISSES = [("MISS wallets>=1@k-2 (fails d)", lambda r: r["w_k2"] >= 1, "behind1_15_h300"),
          ("MISS BASE | (f@k-2==0 & named<4) (fails c)", lambda r: BASE(r) or (r["f_k2"] == 0 and r["named"] < 4), "behind1_15_h300"),
          ("MISS wallets>=1@k-2, stop20 else 600 (fails d)", lambda r: r["w_k2"] >= 1, "behind1_15_stop20_h600")]
def show(label, rule, key):
    print(f"\n### {label}   [{key}]")
    print(f"  {'window':12s} {'fires':>5s} {'/day':>5s} {'mean':>7s} {'median':>7s} {'win':>4s} {'dead':>4s} {'$/burst':>8s} {'$/day':>7s} {'$ total':>8s}")
    for names, tag in ((FIT_NAMES, "FIT pooled"), (VAL_NAMES, "VAL pooled")):
        per, pool = evaluate(W, names, AIM(rule), key)
        for n, m in list(per.items()) + [(tag, pool)]:
            if m["n"] == 0: print(f"  {n:12s} {0:5d}"); continue
            print(f"  {n:12s} {m['n']:5d} {m['per_day']:5.1f} {m['mean']:+7.1%} {m['median']:+7.1%} {m['win']:4.0%} {m['dead']:4.0%} {m['usd_burst']:+8.2f} {m['usd_day']:+7.1f} {m['usd_total']:+8.1f}")
show("BASELINE fleets>=2 @k-2, behind one, 300 blocks", BASE, "behind1_15_h300")
ranked = sorted(PASSED, key=lambda p: -evaluate(W, FIT_NAMES, AIM(p[1]), p[2])[1]["usd_day"])
for i, (label, rule, key) in enumerate(ranked, 1): show(f"PASS #{i} {label}", rule, key)
for label, rule, key in MISSES: show(label, rule, key)
