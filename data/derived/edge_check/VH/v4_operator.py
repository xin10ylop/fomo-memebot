"""VH verification 4: the operator's launches (bundle at the template's sizes) with the creator's buy, and the named-wallet overlaps;
tries to reproduce H's '17 launches, disjoint except two pairs'."""
import sys, itertools
sys.path.insert(0, "/home/user/fomo-memebot/data/derived/edge_check/VH/rerun"); from common import *; from common import _tapes
TP = _tapes(); P = load()
op = [x for x in P if 4.13 <= x["bundle"] <= 4.31 or abs(x["bundle"] - 2.507) < 0.002 or 1.635 <= x["bundle"] <= 1.655 or abs(x["bundle"] - 1.37) < 0.005]
for x in op:
    d = None
    if x["cv"] in TP:
        rows = sorted(TP[x["cv"]]["rows"], key=lambda r: (r["bn"], r["li"])); d = rows[0]["eth"] if rows[0]["k"] == "B" else 0.0
    x["dev"] = d
    print(f"  {hms(x['T0'])} {x['win']:10s} {x['cv'][:10]} bundle {x['bundle']:.4f} dev {'   n/a' if d is None else '%.4f' % d} sum {'   n/a' if d is None else '%.3f' % (x['bundle'] + d)} named {len(x['named'])} fire_eng {x['fire_eng']} fire_tab {x['fire_tab']}")
pairs = [(a, b, len(set(a["named"]) & set(b["named"]))) for a, b in itertools.combinations(op, 2)]
ov = [p for p in pairs if p[2] > 0]
print(f"{len(op)} launches, {len(pairs)} pairs, {len(ov)} with any shared named wallet, {sum(p[2] >= 3 for p in pairs)} with >= 3 shared")
for a, b, n in ov: print(f"   {hms(a['T0'])} {a['cv'][:10]} ({a['bundle']:.3f}) x {hms(b['T0'])} {b['cv'][:10]} ({b['bundle']:.3f}): {n} shared (named {len(a['named'])}/{len(b['named'])})")
# restricted to fires dropped by the cap (engine or tables)
dr = [x for x in P if (x["fire_eng"] or x["fire_tab"]) and x["bundle"] > 3.0]
print(f"\nfires dropped by the cap (engine or tables): {len(dr)}; overlapping pairs among them:")
for a, b in itertools.combinations(dr, 2):
    n = len(set(a["named"]) & set(b["named"]))
    if n: print(f"   {hms(a['T0'])} {a['cv'][:10]} x {hms(b['T0'])} {b['cv'][:10]}: {n}")
# does any of the dropped fires share >= 3 wallets with ANY earlier launch (causal, the whole population)?
for x in dr:
    prev = [y for y in P if y["T0"] < x["T0"] and len(set(y["named"]) & set(x["named"])) >= 3]
    print(f"   {hms(x['T0'])} {x['cv'][:10]}: earlier launches sharing >= 3 named: {len(prev)} " + ", ".join(f"{hms(y['T0'])} {y['cv'][:10]} b {y['bundle']:.2f}" for y in prev))
