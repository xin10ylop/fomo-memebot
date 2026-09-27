"""check_counts.py (edge_check/A): reviewer A's independent fleet/wallet counter (common.fleets_by_block) against
crowd_rules.cums on every launch of the fit and recent crowd files; the fire counts; the duplicated records.
    python3 data/derived/edge_check/A/check_counts.py"""
import sys, json; sys.path.insert(0, "data/derived/edge_check/A"); sys.path.insert(0, "src/analysis")
from common import *
sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])        # cums, at (the tables' own counter)
for name, ws in (("fit", FIT), ("recent", REC)):
    tot = sum(len(load_raw(w)) for w in ws); L = all_launches(ws); mf = sum(fleets_by_block(r) != cums(r)[1] for r in L); mw = sum(fleets_by_block(r, "wallets") != cums(r)[0] for r in L)
    fires = [r for r in L if is_fire(r)]
    print(f"{name}: records {tot}, unique launches {len(L)}; fleet-count mismatches {mf}, wallet-count mismatches {mw}; fires {len(fires)}")
recs = [r for w in REC for r in load_raw(w)]; seen = {}; dup = []
for r in recs:
    if r["cv"] in seen: dup.append(r)
    seen[r["cv"]] = 1
print("duplicated recent records:", len(dup), "of which fires:", sum(is_fire(r) for r in dup))
# e1_multi's silent drops: launches of sep25eve (19:28-20:39) that the overlapping sep25eve2 (19:28-22:13) does not have
H = {x["cv"]: x for x in json.load(open(D + HG["sep25eve"]))}
e2 = {r["cv"] for r in load_raw("sep25eve2")}
for r in load_raw("sep25eve"):
    if r["cv"] not in e2:
        cf = fleets_by_block(r); print(f"in sep25eve, missing from sep25eve2: {hms(r['T0'])} {r['cv'][:10]} k {r['k']} fleets {cf} k-2 {at(cf, r['k']-2)} k-1 {at(cf, r['k']-1)} h300 {H[r['cv']]['behind1_15_h300']:+.1%}")
