"""check_late.py (reviewer I): how close hold_grid's behind1_15_h15 (the only price of the 24 sep27pm/sep27eve launches) is
to curves.json r2[15] (the yardstick of everything else), on the recent launches that have both; and the late launches'
fires with their h15 price.   python3 data/derived/edge_check/I/check_late.py > data/derived/edge_check/I/check_late.txt"""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
P = c.load(); byc = {d["cv"].lower(): d for d in P}
diffs = []; fd = []
for w in c.REC:
    p = c.LV + f"hold_grid_{w}.json"
    if not os.path.exists(p): continue
    for x in json.load(open(p)):
        d = byc.get(x["cv"].lower())
        if d is None or d["src"] != "curves": continue
        df = x["behind1_15_h15"] - d["r"][15]; diffs.append(df)
        if d["fire_t"]: fd.append(df)
ad = sorted(abs(x) for x in diffs)
print(f"hold_grid behind1_15_h15 minus curves r2[15], recent launches with both: n {len(diffs)}  mean {st.mean(diffs):+.2%}  median |diff| {st.median(ad):.2%}  90th pct |diff| {ad[int(0.9*len(ad))]:.2%}  max |diff| {ad[-1]:.2%}")
print(f"  on the tables' fires among them: n {len(fd)}  mean diff {st.mean(fd):+.2%}  max |diff| {max(abs(x) for x in fd):.2%}")
print("\nthe sep27pm / sep27eve launches that fire (either count), h15 from hold_grid, bundle from launches_*.json:")
for d in P:
    if d["per"] == "late" and (d["fire_t"] or d["fire_e"]):
        print(f"  {c.hms(d['T0'])} {d['cv'][:10]} {d['win']:8s} fleets@k-2 tables {d['fk2_t']} engine {d['fk2_e']}  bundle {d['bundle']:.3f} ETH  named {len(d['named']):2d}  h15 {d['r'][15]:+.1%}")
