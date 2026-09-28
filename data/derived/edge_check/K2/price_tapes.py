"""K2/price_tapes.py: every week launch that has a raw tape (edge_check/B/tapes, D/tapes) re-priced from the tape with the model of
src/analysis/hold_grid.py's model_path (checked equal to model_path below), at every exit block 0..HM after the entry, for
first / second / third / last place in E1, first / second place in E2, and second place at larger stakes; plus what the E1 block
held (the buys ahead of each position) and when the seat block's buyers first sell. Offline. -> K2/prices.json.gz
    python3 data/derived/edge_check/K2/price_tapes.py"""
import os, sys, json, gzip, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
os.chdir(ROOT); sys.path.insert(0, "src/analysis")
import hold_grid as HG
from live_vs_table import fold_buy, fold_sell, X0, Y0, OURS, SUR, CAP
E = 2570.0; HM = 60; LONG = (100, 150, 300, 600)
EC = "data/derived/edge_check/"
T = json.load(gzip.open(HERE + "/table.json.gz", "rt")); want = {x["cv"] for x in T}
TAPES = {}
for d in ("B/tapes/", "D/tapes/"):
    for f in os.listdir(EC + d):
        cv = f[:-5].lower()
        if cv in want and cv not in TAPES:
            L = json.load(open(EC + d + f)); L["ts"] = {int(k): v for k, v in L["ts"].items()}; TAPES[cv] = L
def net_eth_of(L):
    rows = [r for r in L["rows"] if r["who"] not in OURS]; X, Y = X0, Y0; net = {}
    for r in rows:
        if r["k"] == "B":
            if 0 < r["tk"] < Y: net[(r["bn"], r["li"])] = X * r["tk"] / (Y - r["tk"]); X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
    return net
def path(L, stake_usd, entry_block, n_ahead, hs, fold="tk", NET=None):
    """model_path's entry; the exit value (our tokens sold into the curve, tier on the sell) after every block entry+h for h in hs;
    fold='tk' folds later buys by tokens (model_path), 'eth' by their ETH (stake_scale.model_eff, G's curve). Returns (vals, tk, g)"""
    rows = [r for r in L["rows"] if r["who"] not in OURS]; tier = L["tier"]; ts = L["ts"]; T0 = L["T0"]; X, Y = X0, Y0; i = 0
    while i < len(rows) and ts.get(rows[i]["bn"], 9e18) == T0:
        r = rows[i]
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
        i += 1
    rest = rows[i:]; seen = 0; pre = []; post = []
    for r in rest:
        if r["bn"] < entry_block: pre.append(r)
        elif r["bn"] == entry_block:
            if r["k"] == "B" and seen < n_ahead: pre.append(r); seen += 1
            elif r["k"] == "B": post.append(r)
            else: (pre if seen < n_ahead else post).append(r)
        else: post.append(r)
    for r in pre:
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
    sur = SUR.get(ts.get(entry_block, T0) - T0, 0.0); g = stake_usd / E; net = g * (1 - tier - sur); tk = Y * net / (X + net)
    if tk > CAP * Y0: tk = CAP * Y0; net = X * tk / (Y - tk); g = net / (1 - tier - sur)
    X, Y = X + net, Y - tk; vals = {}; j = 0
    for h in sorted(hs):
        while j < len(post) and post[j]["bn"] <= entry_block + h:
            r = post[j]; j += 1
            if r["k"] == "B":
                if fold == "eth":
                    n = NET.get((r["bn"], r["li"]))
                    if n is not None: X, Y = X + n, Y - Y * n / (X + n)
                elif 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
            else: X, Y = fold_sell(X, Y, r["tk"])
        vals[h] = (X * tk / (Y + tk) * (1 - tier)) / g - 1
    return vals, tk, g
HS = list(range(0, HM + 1)) + list(LONG)
out = {}; chk = []
for x in T:
    L = TAPES.get(x["cv"])
    if L is None: continue
    ts = L["ts"]; T0 = L["T0"]; b0 = L["b0"]
    bE1 = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
    bE2 = next((n for n in range(b0 + 1, b0 + 40) if ts.get(n, 0) == T0 + 2), None)
    if bE1 is None: continue
    NET = net_eth_of(L); o = {"bE1": bE1 - b0, "bE2": (bE2 - b0) if bE2 else None, "tier": L["tier"], "synth": bool(L.get("ts_synth"))}
    for pos, na in (("p1", 0), ("p2", 1), ("p3", 2), ("plast", 10 ** 6)):
        v, tk, g = path(L, 13.0, bE1, na, HS); o[pos] = [v[h] for h in HS]; o["tk_" + pos] = tk
    v, tk, g = path(L, 13.0, bE1, 1, HS, fold="eth", NET=NET); o["p2eth"] = [v[h] for h in HS]
    if bE2:
        for pos, na in (("e2p1", 0), ("e2p2", 1), ("e2last", 10 ** 6)):
            v, tk, g = path(L, 13.0, bE2, na, range(0, 31)); o[pos] = [v[h] for h in range(0, 31)]
    for s in (13, 25, 50, 100, 200, 300, 500):
        for fold in ("tk", "eth"):
            v, tk, g = path(L, float(s), bE1, 1, (9, 11, 13), fold=fold, NET=NET); o[f"s{s}_{fold}"] = [v[9], v[11], v[13], g * E]
    # the E1 block: every buy (not ours) in order, ETH and buyer; sells in it
    rows = [r for r in L["rows"] if r["who"] not in OURS]
    e1b = [r for r in rows if r["bn"] == bE1 and r["k"] == "B"]; o["e1_buys"] = [[r["eth"], r["who"]] for r in e1b]
    o["cs_buys_after_build"] = sum(r["eth"] for r in rows if r["k"] == "B" and b0 + x["k"] - 1 <= r["bn"] <= b0 + x["k"])   # creation-second buys the build view (k-2) cannot see
    seat = {r["who"] for r in e1b}
    fs = next((r["bn"] - bE1 for r in rows if r["k"] == "S" and r["bn"] > bE1 and r["who"] in seat), None); o["seat_first_sell"] = fs
    # tokens sold by the seat block's buyers per block after E1 (h 1..60), and the total ETH bought by anyone per block
    o["seat_sold_tk"] = [sum(r["tk"] for r in rows if r["k"] == "S" and r["bn"] == bE1 + h and r["who"] in seat) for h in range(0, HM + 1)]
    o["buy_eth"] = [sum(r["eth"] for r in rows if r["k"] == "B" and r["bn"] == bE1 + h) for h in range(0, HM + 1)]
    o["sell_n"] = [sum(1 for r in rows if r["k"] == "S" and r["bn"] == bE1 + h) for h in range(0, HM + 1)]
    out[x["cv"]] = o
    # checks: this path equals hold_grid.model_path, and the table's behind-one h11 (grid or G)
    mp = HG.model_path(L, 13.0 / E, bE1, 1, (11,)); chk.append((abs(mp[11] - o["p2"][11]), abs((x.get("behind1_13_h11") or 0) - o["p2"][11]), abs((x.get("behind1_13_h11") or 0) - o["p2eth"][11]), x["src"]))
json.dump({"HS": HS, "rows": out}, gzip.open(HERE + "/prices.json.gz", "wt"))
print(f"{len(out)} launches priced from tapes of {len(T)}")
print(f"|path - hold_grid.model_path| at h11: max {max(c[0] for c in chk):.2e}")
for s in ("grid", "G"):
    c = [a for a in chk if a[3] == s]
    if c: print(f"  vs table ({s}, {len(c)}): token fold max {max(a[1] for a in c):.4f} mean {sum(a[1] for a in c)/len(c):.5f}; ETH fold max {max(a[2] for a in c):.4f} mean {sum(a[2] for a in c)/len(c):.5f}")
