"""K2/q3_gate.py: the crowd gate. Threshold 1/2/3 fleets at each view; the fires a later view adds, priced at second place and at
the deeper places they would likely land (the crowd is visible only at the tick); other pre-fire signals as an extra condition on
top of the live gate, chosen on one period and read on the other."""
import os, sys, json, gzip, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from sim import *
P = json.load(gzip.open(os.path.join(HERE, "prices.json.gz"), "rt")); PR = P["rows"]; I = P["HS"].index(11)
VIEWS = (("k2", "k-2"), ("k2r", "k-2+reg"), ("k1", "k-1"), ("k1r", "k-1+reg"), ("k0r", "k+reg"))
for slip in (0.07, 0.15):
    print(f"\n==== threshold x view, guard slip {slip:.2f}: fit $ (fires, fills, mean) | read $ ($/day) ====")
    for amin in (1, 2, 3, 4):
        cells = []
        for v, lab in VIEWS:
            res = run(view=v, amin=amin, slip=slip); a, b = summ(res, "fit"), summ(res, "read")
            cells.append(f"{lab}: {a['usd']:+6.1f} ({a['fired']},{a['fills']},{a['mean']:+.0%}) | {b['usd']:+6.1f} ({b['fired']},{b['fills']},{b['mean']:+.0%},{b['usd_day']:+.1f}/d)")
        print(f"  >= {amin}:\n     " + "\n     ".join(cells))
# the fires each later view adds over k-1+reg, priced at several positions
print("\n==== fires the tick's block adds (k+reg fires minus k-1+reg fires), guard ignored, h11 ====")
A = {r["x"]["cv"] for r in run(view="k1r") if r.get("fired")}; B = [r for r in run(view="k0r") if r.get("fired") and r["x"]["cv"] not in A]
for per in ("fit", "read"):
    b = [r for r in B if period(r["x"]) == per]; t = [r for r in b if r["x"]["cv"] in PR]
    print(f"  {per}: {len(b)} added fires; second place (all) {mean([r['x']['behind1_13_h11'] for r in b]):+.1%}; taped {len(t)}: first {mean([PR[r['x']['cv']]['p1'][I] for r in t]):+.1%} second {mean([PR[r['x']['cv']]['p2'][I] for r in t]):+.1%} third {mean([PR[r['x']['cv']]['p3'][I] for r in t]):+.1%} last {mean([PR[r['x']['cv']]['plast'][I] for r in t]):+.1%}")
A2 = {r["x"]["cv"] for r in run(view="k2") if r.get("fired")}; B2 = [r for r in run(view="k1r") if r.get("fired") and r["x"]["cv"] not in A2]
print("==== fires k-1+reg adds over the floor k-2 ====")
for per in ("fit", "read"):
    b = [r for r in B2 if period(r["x"]) == per]; t = [r for r in b if r["x"]["cv"] in PR]
    print(f"  {per}: {len(b)} added fires; second place (all) {mean([r['x']['behind1_13_h11'] for r in b]):+.1%}; taped {len(t)}: first {mean([PR[r['x']['cv']]['p1'][I] for r in t]):+.1%} second {mean([PR[r['x']['cv']]['p2'][I] for r in t]):+.1%} third {mean([PR[r['x']['cv']]['p3'][I] for r in t]):+.1%} last {mean([PR[r['x']['cv']]['plast'][I] for r in t]):+.1%}")
# extra signals on top of the live gate (fleets >= 2 at k-1+reg): every candidate, each period's $ and the other's
print("\n==== extra pre-fire conditions on top of the live gate (slip 0.07 | slip 0.15), $ fit / $ read ====")
def cw(x, off): c = x["cw"]; return c[off] if 0 <= off < len(c) else 0
cands = [("none (live)", lambda x: True),
         ("wallets(k-1) >= 5", lambda x: cw(x, x["k"] - 1) >= 5), ("wallets(k-1) >= 10", lambda x: cw(x, x["k"] - 1) >= 10), ("wallets(k-1) >= 20", lambda x: cw(x, x["k"] - 1) >= 20),
         ("fleets grew k-2 -> k-1 (tables' unit)", lambda x: x["cf"][x["k"] - 1] > (x["cf"][x["k"] - 2] if x["k"] >= 2 else 0) if x["k"] >= 1 else False),
         ("fleets(k-1+reg) >= 3", lambda x: x["f_k1r"] >= 3), ("f_k2 >= 1 (a fleet already at k-2)", lambda x: x["f_k2r"] >= 1),
         ("bundle <= 1.5 ETH", lambda x: x["bundle"] <= 1.5), ("bundle > 1.0 ETH", lambda x: x["bundle"] > 1.0), ("bundle 0.5-2.0", lambda x: 0.5 <= x["bundle"] <= 2.0),
         ("tier 3%", lambda x: x["tb"] == 200), ("tier < 3%", lambda x: x["tb"] < 200), ("k >= 5", lambda x: x["k"] >= 5), ("k <= 6", lambda x: x["k"] <= 6),
         ("named >= 5", lambda x: x["n_named"] >= 5), ("creator supply >= 2%", lambda x: x["tk0"] is None or x["tk0"] >= 0.02 * Y0),
         ("hour 12-23 UTC", lambda x: 12 <= x["hour"] <= 23), ("hour 0-11 UTC", lambda x: x["hour"] < 12)]
for lab, c in cands:
    cells = []
    for slip in (0.07, 0.15):
        res = run(slip=slip, gatefn=(lambda c: (lambda x: x["f_k1r"] >= 2 and c(x)))(c)); a, b = summ(res, "fit"), summ(res, "read")
        cells.append(f"fit {a['fired']:3d}f {a['usd']:+7.2f} | read {b['fired']:3d}f {b['usd']:+7.2f} ({b['usd_day']:+5.2f}/d)")
    print(f"  {lab:38s} " + "  ||  ".join(cells))
