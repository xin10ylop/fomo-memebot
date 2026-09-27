"""bundle_view.py (reviewer I): can a bundle cap be applied in time? For every launch with bundle_eth > 1.5 ETH that has a tape,
the bundle ETH (creation-second buys after the first at fee == tier, as e1_multi) already on the chain by block k-5 (about the
burst's build) and by block k-2 (the gate's view), against the full creation-second bundle; and the flatness of every launch
above 3 ETH (all launches, fires and refused): the share whose seat return is the fee floor at h11, h15 and h300.
    python3 data/derived/edge_check/I/bundle_view.py > data/derived/edge_check/I/bundle_view.txt"""
import sys, os, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
X0, Y0 = 1.68, 1e9; SUR1 = 0.0618
def fold_buy(X, Y, tk): return X + X * tk / (Y - tk), Y - tk
def fold_sell(X, Y, tk): return X - X * tk / (Y + tk), Y + tk
T = {}
for f in ("A/tapes.json.gz", "A/tapes_gapA.json.gz", "A/tapes_gapB.json.gz", "A/tapes_chk27.json.gz", "C/tapes_extra.json.gz"):
    for cv, L in json.load(gzip.open(c.EC + f, "rt")).items(): T.setdefault(cv, L)
for d in ("B/tapes/", "D/tapes/"):
    for f in os.listdir(c.EC + d):
        if f[:-5] not in T: T[f[:-5]] = json.load(open(c.EC + d + f))
def by_block(L):
    ts = {int(k): v for k, v in L["ts"].items()}; T0 = L["T0"]; tier = L["tier"]; X, Y = X0, Y0; out = {}; i = 0
    rows = sorted(L["rows"], key=lambda r: (r["bn"], r["li"]))
    while i < len(rows) and ts.get(rows[i]["bn"], 9e18) == T0:
        r = rows[i]
        if r["k"] == "B":
            if 0 < r["tk"] < Y:
                net = X * r["tk"] / (Y - r["tk"]); fee = 1 - net / r["eth"] if r["eth"] > 0 else 1; X, Y = fold_buy(X, Y, r["tk"])
                if i > 0 and abs(fee - tier) <= 0.0008: out[r["bn"] - L["b0"]] = out.get(r["bn"] - L["b0"], 0.0) + r["eth"]
        else: X, Y = fold_sell(X, Y, r["tk"])
        i += 1
    return out
P = c.load()
print("launches with bundle > 1.5 ETH: bundle ETH on the chain by block k-5 / k-2 / whole creation second (tape), fires marked")
for d in P:
    if d["bundle"] <= 1.5: continue
    L = T.get(d["cv"])
    if L is None: print(f"  {c.hms(d['T0'])} {d['cv'][:10]} {d['win']:10s} k {d['k']} bundle {d['bundle']:.3f}  (no tape)  fire {'T' if d['fire_t'] else '.'}{'E' if d['fire_e'] else '.'}"); continue
    bb = by_block(L); k = d["k"]
    s5 = sum(v for o, v in bb.items() if o <= k - 5); s2 = sum(v for o, v in bb.items() if o <= k - 2); tot = sum(bb.values())
    r = lambda h: "  n/a" if d["r"][h] is None else f"{d['r'][h]:+6.1%}"
    print(f"  {c.hms(d['T0'])} {d['cv'][:10]} {d['win']:10s} k {k:2d} bundle {d['bundle']:.3f}: by k-5 {s5:.3f}, by k-2 {s2:.3f}, all {tot:.3f}  fire {'T' if d['fire_t'] else '.'}{'E' if d['fire_e'] else '.'}  h11 {r(11)} h15 {r(15)} h300 {r(300)}")
print("\nflat launches (seat return within 0.2 points of the fee floor (1 - tier - 6.18%)(1 - tier) - 1) by bundle size, all launches:")
for lo, hi in ((0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 99)):
    S = [d for d in P if lo < d["bundle"] <= hi and d["r"][15] is not None]
    tiers = json.load(open(c.LV + "launches_sep27eve.json"))    # tier for launches without a tape comes from the launches files
    def floor(d):
        L = T.get(d["cv"]); t = L["tier"] if L else None
        if t is None:
            for f in os.listdir(c.LV):
                if f.startswith("launches_") and f.endswith(".json"):
                    x = json.load(open(c.LV + f)); x = x.get("launches", []) if isinstance(x, dict) else x
                    for l in x:
                        if isinstance(l, dict) and l.get("cv", "").lower() == d["cv"].lower() and "tier" in l: t = l["tier"]; break
                if t is not None: break
        return (1 - t - SUR1) * (1 - t) - 1
    fl = {h: sum(1 for d in S if d["r"][h] is not None and abs(d["r"][h] - floor(d)) < 0.002) for h in (15, 300)}
    fires = [d for d in S if d["fire_t"]]
    ff = sum(1 for d in fires if abs(d["r"][15] - floor(d)) < 0.002)
    print(f"  bundle ({lo:.1f}, {hi:.1f}] ETH: {len(S):3d} launches, flat at h15 {fl[15]:3d} ({fl[15]/len(S):4.0%}), flat at h300 {fl[300]:3d} ({fl[300]/len(S):4.0%}); tables' fires {len(fires)}, flat at h15 {ff}")
