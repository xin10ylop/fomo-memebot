"""baseline.py: reproduce the brief's baseline (fleets >= 2 by block k-2, behind1 $15 model, h300, $13 stake, $0.33 gas) per window.
    cd /home/user/fomo-memebot && python3 /tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad/improve/B/baseline.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
W = load()
print("launches per window (joined, with behind1_15_h300):", {n: len(W[n]["rows"]) for n in W})
fitcv = [r["cv"] for n in FIT_NAMES for r in W[n]["rows"]]; valcv = [r["cv"] for n in VAL_NAMES for r in W[n]["rows"]]
print("duplicate cvs inside fit:", len(fitcv) - len(set(fitcv)), " inside val:", len(valcv) - len(set(valcv)), " fit/val overlap:", len(set(fitcv) & set(valcv)))
for label, rule in (("BASELINE fleets>=2 @k-2", BASE), ("borderline fleets>=2 @k-1", lambda r: r["f_k1"] >= 2)):
    print(f"\n=== {label}, behind1 h300")
    for names, tag in ((FIT_NAMES, "FIT pooled"), (VAL_NAMES, "VAL pooled")):
        per, pool = evaluate(W, names, rule)
        for n, m in per.items(): print(fmt(m, n))
        print(fmt(pool, tag))
