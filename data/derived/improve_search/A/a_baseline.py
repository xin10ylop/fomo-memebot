"""a_baseline.py (searcher A): the baseline (fleets >= 2 by block k-2, behind1 h300, $13, $0.33 gas) per window, fit and
validation pooled, plus the cross-check against crowd_rules.py's own rows and the k-1 borderline.
    python3 a_baseline.py"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a_common import *

rows = load_all(verbose=True)
n, bad = crosscheck_crowd_rules(rows)
print(f"cross-check against crowd_rules.py's own fit rows: {n} launches, {bad} differences (cv, ret, fleets by block, f_k2)")
base = lambda r: at(r["cf"], r["k"] - 2) >= 2
table("BASELINE: fleets >= 2 by block k-2 (exact), behind1_15_h300", evaluate(rows, base))
table("borderline (NOT executable as a headline): fleets >= 2 by block k-1", evaluate(rows, lambda r: at(r["cf"], r["k"] - 1) >= 2))
print("\nvalidation baseline fires:")
for r in sorted([r for r in rows if r["set"] == "val" and base(r)], key=lambda r: r["T0"]):
    print(f"  {r['win']:10s} {r['cv'][:10]} k={r['k']} fleets {r['cf']} ret {r['ret']:+.1%}")
missing = [r["cv"][:10] for r in rows if not r["has_launch"]]
print("launches without a launches_ record (features missing):", missing)
