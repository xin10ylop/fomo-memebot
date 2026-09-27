"""gate_view.py (edge_check/H): can the engine see the bundle in time? bundle_eth (e1_multi's rule) counted only on blocks up to
offset k-2 of the creation second (the gate's view), against the whole second, for every launch with a tape; and the cap priced
on that view.  python3 data/derived/edge_check/H/gate_view.py > data/derived/edge_check/H/gate_view.txt
The 24 tape-less launches (sep27pm/eve) cannot be split by block: their row says 'no tape'."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *; from common import _tapes
TP = _tapes(); P = load()
def bundle_upto(L, last_off):
    rows = sorted(L["rows"], key=lambda r: (r["bn"], r["li"])); ts = {int(k): v for k, v in L["ts"].items()}; T0 = L["T0"]; tier = L["tier"]
    X, Y = X0, Y0; b = 0.0; i = 0
    while i < len(rows) and ts.get(rows[i]["bn"], 9e18) == T0:
        r = rows[i]
        if r["k"] == "B":
            tk, eth = r["tk"], r["eth"]
            if 0 < tk < Y:
                net = X * tk / (Y - tk); fee = 1 - net / eth if eth > 0 else 1; X, Y = fold_buy(X, Y, tk)
                if i > 0 and abs(fee - tier) <= 0.0008 and r["bn"] - L["b0"] <= last_off: b += eth
        else: X, Y = fold_sell(X, Y, r["tk"])
        i += 1
    return b
for x in P:
    x["b_k2"] = bundle_upto(TP[x["cv"]], x["k"] - 2) if x["cv"] in TP else None
print("launches with bundle >= 2.5 ETH (whole second) or >= 2.5 ETH by k-2: whole second vs visible by block k-2 (the gate)")
for x in P:
    if x["bundle"] >= 2.5 or (x["b_k2"] or 0) >= 2.5:
        print(f"  {hms(x['T0'])} {x['set']:3s} {x['cv'][:10]} k {x['k']:2d} bundle {x['bundle']:.3f} by k-2 {'no tape' if x['b_k2'] is None else '%.3f' % x['b_k2']}"
              f"  eng {x['f_eng']} tab {x['f_tab']}{' FIRE-eng' if x['fire_eng'] else ''}  h15 {x['r15']:+6.1%}")
for s in ("fit", "rec"):
    F = [x for x in P if x["set"] == s and x["fire_eng"] and x["b_k2"] is not None]
    for c in (3.0,):
        a = [x for x in F if x["bundle"] > c]; b = [x for x in F if x["b_k2"] > c]
        print(f"{s}: engine fires with a tape {len(F)}; dropped by a {c} ETH cap on the whole second {len(a)}, on the k-2 view {len(b)}; caught by both {len(set(y['cv'] for y in a) & set(y['cv'] for y in b))}")
