"""sprayer_list.py (6.21, runbook 5bc): the relay contracts that spray a launch's creation second and seat block with dozens of
transactions, refit from the crowd tables of the last N days, for the engine's ATTACK_GROUP (they count as one fleet between them).

    python3 src/analysis/sprayer_list.py [--days 7] [--min-tx 30] [--min-launches 5] [--out data/derived/sprayers.json]

A sprayer: one 'to' address with at least --min-tx transactions on a single launch's blocks (creation second + seat block), on at
least --min-launches launches in the window. Ordinary snipers send one shot per wallet (a relay fleet shows 3-35 transactions);
the sprayers of Oct 2+ send 50-180. Prints the list and the per-contract statistics; writes the JSON the deploy line reads."""
import json, gzip, glob, sys, time, collections, os
def arg(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
DAYS = float(arg("--days", "7")); MIN_TX = int(arg("--min-tx", "50")); MIN_L = int(arg("--min-launches", "5")); OUT = arg("--out", "data/derived/sprayers.json")
OURS = {"0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}   # our wallet and relay: a 70-shot burst of ours looks like a spray
now = time.time(); lo = now - DAYS * 86400
per = collections.defaultdict(lambda: collections.defaultdict(int)); days = collections.defaultdict(set); seen = set(); n_l = 0
for f in glob.glob("data/derived/live_vs_table/crowd_raw_*.json*"):
    try: R = json.load(gzip.open(f, "rt")) if f.endswith(".gz") else json.load(open(f))
    except Exception: continue
    for L in R:
        cv = L["cv"].lower()
        if L.get("T0", 0) < lo or cv in seen: continue
        seen.add(cv); n_l += 1
        c = collections.Counter((t.get("to") or "").lower() for rows in L["blocks"] for t in rows if not t.get("direct") and t.get("to") and (t.get("to") or "").lower() not in OURS)
        for a, n in c.items():
            if n >= MIN_TX: per[a][cv] = n; days[a].add(time.strftime("%m-%d", time.gmtime(L["T0"])))
rows = sorted(((a, len(v), sorted(v.values())[len(v) // 2], max(v.values())) for a, v in per.items() if len(v) >= MIN_L), key=lambda x: -x[1])
print(f"{n_l} launches in the last {DAYS:g} days; {len(rows)} contracts with >= {MIN_TX} transactions on >= {MIN_L} launches:")
for a, n, med, mx in rows: print(f"  {a}  launches {n:3d}  median tx {med:3d}  max {mx:3d}  days {','.join(sorted(days[a]))}")
out = {"fitted": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)), "window_days": DAYS, "min_tx": MIN_TX, "min_launches": MIN_L, "launches": n_l,
       "sprayers": [a for a, *_ in rows], "stats": {a: {"launches": n, "median_tx": med, "max_tx": mx} for a, n, med, mx in rows}}
os.makedirs(os.path.dirname(OUT), exist_ok=True); json.dump(out, open(OUT, "w"), indent=1)
print(f"ATTACK_GROUP={','.join(out['sprayers'])}")
