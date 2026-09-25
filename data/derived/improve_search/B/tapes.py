"""tapes.py: pull (and cache under <B>/tapes/) the chain tape of every launch that the baseline or one of the nine
five-criteria variants fires on (FIT and VAL), with src/analysis/live_vs_table.launch (public RPC, read-only), for two checks the
tables cannot make: the burst's minOut guard (25% under the build's quote) and the creator-supply filter (MIN_CREATOR_SUPPLY 1%).
    cd /home/user/fomo-memebot && python3 <B>/tapes.py        # ~5 s a launch on a cold cache; re-runs read the cache"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
sys.path.insert(0, os.path.join(REPO, "src/analysis")); import live_vs_table as lv
HERE = os.path.dirname(os.path.abspath(__file__)); TD = os.path.join(HERE, "tapes"); os.makedirs(TD, exist_ok=True)
from variants import PASSED
W = load()
need = {}
for n in FIT_NAMES + VAL_NAMES:
    for r in W[n]["rows"]:
        if BASE(r) or any(rule(r) for _, rule, _ in PASSED): need[r["cv"]] = r
print(len(need), "launches to pull/read", flush=True)
bad = []
for i, (cv, r) in enumerate(sorted(need.items(), key=lambda x: x[1]["T0"])):
    f = os.path.join(TD, cv + ".json")
    if os.path.exists(f): continue
    try:
        L = lv.launch(cv, r["b0"] + r["k"] + 1)
        if L is None: bad.append(cv); continue
        json.dump({k: v for k, v in L.items()}, open(f, "w"))
    except Exception as e:
        print("err", cv[:10], str(e)[:100], flush=True); bad.append(cv)
    if i % 10 == 0: print(i, flush=True)
print("done; failed:", bad)
