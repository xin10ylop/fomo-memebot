"""bundle_check.py (reviewer I): bundle_eth as used here (the launches_*.json files, the e1m pull's own number) against a
recomputation from the cached tape rows exactly as src/analysis/e1_multi.py does it (creation-second buys after the first,
whose fee equals the tier within 0.0008), on every launch with a tape; then the population by bundle size, fires by count.
    python3 data/derived/edge_check/I/bundle_check.py > data/derived/edge_check/I/bundle_check.txt"""
import sys, os, json, gzip, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
X0, Y0 = 1.68, 1e9                                   # live_vs_table.X0, Y0
def fold_buy(X, Y, tk): return X + X * tk / (Y - tk), Y - tk
def fold_sell(X, Y, tk): return X - X * tk / (Y + tk), Y + tk
T = {}
for f in ("A/tapes.json.gz", "A/tapes_gapA.json.gz", "A/tapes_gapB.json.gz", "A/tapes_chk27.json.gz", "C/tapes_extra.json.gz"):
    for cv, L in json.load(gzip.open(c.EC + f, "rt")).items(): T.setdefault(cv, L)
for d in ("B/tapes/", "D/tapes/"):
    for f in os.listdir(c.EC + d):
        if f[:-5] not in T: T[f[:-5]] = json.load(open(c.EC + d + f))
def bundle_from_tape(L):
    ts = {int(k): v for k, v in L["ts"].items()}; T0 = L["T0"]; tier = L["tier"]; X, Y = X0, Y0; b = 0.0; i = 0
    rows = sorted(L["rows"], key=lambda r: (r["bn"], r["li"]))
    while i < len(rows) and ts.get(rows[i]["bn"], 9e18) == T0:
        r = rows[i]
        if r["k"] == "B":
            if 0 < r["tk"] < Y:
                net = X * r["tk"] / (Y - r["tk"]); fee = 1 - net / r["eth"] if r["eth"] > 0 else 1; X, Y = fold_buy(X, Y, r["tk"])
                if i > 0 and abs(fee - tier) <= 0.0008: b += r["eth"]
        else: X, Y = fold_sell(X, Y, r["tk"])
        i += 1
    return b
P = c.load(); df = []; big = []
for d in P:
    L = T.get(d["cv"])
    if L is None or L.get("tier") is None: continue
    b = bundle_from_tape(L); df.append(b - d["bundle"])
    if abs(b - d["bundle"]) > 0.01: big.append((d, b))
ad = sorted(abs(x) for x in df)
print(f"launches with a tape: {len(df)} of {len(P)}; |file - tape| median {st.median(ad):.4f} ETH, 95th pct {ad[int(0.95*len(ad))]:.4f}, max {ad[-1]:.4f}; differ by > 0.01 ETH: {len(big)}")
for d, b in big[:15]: print(f"   {c.hms(d['T0'])} {d['cv'][:10]} file {d['bundle']:.3f} tape {b:.3f}")
print("\nlaunches and fires by bundle (file value); caps are applied as bundle_eth <= cap:")
for per in ("fit", "rec", "late"):
    S = [d for d in P if d["per"] == per]
    for lo, hi in ((0, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 99)):
        x = [d for d in S if lo < d["bundle"] <= hi]
        print(f"  {per:4s} bundle ({lo:.1f}, {hi:.1f}] ETH: {len(x):3d} launches, tables fires {sum(d['fire_t'] for d in x):2d}, engine fires {sum(d['fire_e'] for d in x):2d}")
