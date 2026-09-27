"""check_tapes.py (reviewer D): what I rely on from round 1. (1) B's cached tapes (B/tapes/) against A's independent pull
(A/tapes.json.gz) on the 91 fires: same events, same prices at 15 and 300 blocks. (2) The yardstick reproduces reach_table.txt:
fit 73 fires +26.3%, recent 18 fires +3.5% (model_eff, $13, second place in E1, 300 blocks). (3) coverage of every launch.
    python3 data/derived/edge_check/D/check_tapes.py"""
import sys, os, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
A = json.load(gzip.open("data/derived/edge_check/A/tapes.json.gz", "rt"))
R = c.all_records(); F = [r for r in R if c.fire(r)]
diff_rows = 0; dmax = {15: 0, 300: 0}; res = {"fit": [], "recent": []}
for r in F:
    LA = A[r["cv"]]; LA["ts"] = {int(k): v for k, v in LA["ts"].items()}; LB = c.tape(r["cv"])
    key = lambda x: (x["bn"], x["li"], x["k"], round(x["tk"], 3), round(x["eth"], 12), x["who"])
    ra = sorted(key(x) for x in LA["rows"] if x["bn"] <= r["b0"] + 640); rb = sorted(key(x) for x in LB["rows"])
    if ra != rb: diff_rows += 1
    eA, eB = c.seat_block(LA, r["b0"]), c.seat_block(LB, r["b0"])
    for h in (15, 300):
        a = c.model_eff(LA, 13 / c.E, eA, 1, h)[0]; b = c.model_eff(LB, 13 / c.E, eB, 1, h)[0]; dmax[h] = max(dmax[h], abs(a - b))
    res[r["grp"]].append(c.model_eff(LB, 13 / c.E, eB, 1, 300)[0])
print(f"91 fires: {len(F)}; tapes whose event lists differ between A and B: {diff_rows}; max |A-B| price at h15 {dmax[15]:.4f}, h300 {dmax[300]:.4f}")
for g in ("fit", "recent"): print(f"{g:7s} fires h300 (B tapes): {c.summ(res[g], c.HOURS[g])}")
cov = {g: sum(1 for r in R if r["grp"] == g) for g in ("fit", "recent")}; have = {g: sum(1 for r in R if r["grp"] == g and c.tape(r["cv"])) for g in ("fit", "recent")}
print("launches with a tape:", have, "of", cov)
