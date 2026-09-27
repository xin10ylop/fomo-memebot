"""holds4.py (reviewer B), test 4: the fires at holds 15/30/60/150/300/600 blocks and with a stop (-20%, -30%, -40% of the
position's sale value, sold 3 blocks after the trigger block), stake_scale.model_eff's pricing (buyers after us folded by
their ETH), $13, second place in E1; fit vs recent. Optional arg `all` prices every launch (fires and refused).
    python3 data/derived/edge_check/B/holds4.py"""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
_saved = list(sys.argv); sys.argv = ["x"]
exec(open("src/analysis/stake_scale.py").read().split("\nfor name, cf, hours in W:")[0])   # model_eff, net_eth_of, E, GAS
sys.argv = _saved
from features import load_tape
def path(L, stake_eth, entry_block, n_ahead, holds, stops):
    NET = net_eth_of(L); rows = [r for r in L["rows"] if r["who"] not in OURS]; tier = L["tier"]; ts = L["ts"]; T0 = L["T0"]; X, Y = X0, Y0; i = 0
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
    sur = SUR.get(ts.get(entry_block, T0) - T0, 0.0); g = stake_eth; net = g * (1 - tier - sur); tk = Y * net / (X + net)
    if tk > CAP * Y0: tk = CAP * Y0; net = X * tk / (Y - tk); g = net / (1 - tier - sur)
    X, Y = X + net, Y - tk
    val = lambda X, Y: (X * tk / (Y + tk) * (1 - tier)) / g - 1
    out = {}; trig = {s: None for s in stops}; hmax = max(holds)
    for r in post:
        if r["bn"] > entry_block + hmax: break
        for h in holds:
            if h not in out and r["bn"] > entry_block + h: out[h] = val(X, Y)
        for s in stops:
            if s in out: continue
            if trig[s] is not None and r["bn"] > trig[s] + 3: out[s] = val(X, Y)
        if r["k"] == "B":
            n = NET.get((r["bn"], r["li"]))
            if n is not None: X, Y = X + n, Y - Y * n / (X + n)
        else: X, Y = fold_sell(X, Y, r["tk"])
        for s in stops:
            if trig[s] is None and val(X, Y) <= -s and r["bn"] <= entry_block + 300: trig[s] = r["bn"]
    for h in holds: out.setdefault(h, val(X, Y))
    for s in stops:
        if s not in out: out[s] = val(X, Y) if trig[s] is not None else out[300]
    return out
HOLDS = (15, 30, 60, 150, 300, 600); STOPS = (0.2, 0.3, 0.4)
def price(f):
    L = load_tape(f["cv"]); return path(L, 13 / E, f["bE1"], 1, HOLDS, STOPS)
if __name__ == "__main__":
    F = json.load(open(c.B + "features.json")); ALL = len(sys.argv) > 1 and sys.argv[1] == "all"
    res = {}
    for f in F:
        if not (f["fire"] or ALL): continue
        res[f["cv"]] = price(f)
    json.dump(res, open(c.B + ("holds_all.json" if ALL else "holds_fires.json"), "w"))
    for g in ("fit", "recent"):
        S = [f for f in F if f["grp"] == g and f["fire"]]
        print(f"== {g} fires ({len(S)}); mean / win / dead / $ per fire at $13 after $0.33 gas")
        for key in HOLDS + STOPS:
            v = [res[f["cv"]][key] for f in S]
            lab = f"hold {key}" if key in HOLDS else f"stop -{key:.0%} (else 300)"
            print(f"  {lab:24s} mean {st.mean(v):+6.1%}  median {st.median(v):+6.1%}  win {sum(x>0 for x in v)/len(v):3.0%}  dead {sum(x<-0.4 for x in v)/len(v):3.0%}  ${st.mean(v)*13-0.33:+.2f}")
        chk = [abs(res[f['cv']][300] - f['ret']['300']) for f in S]; print(f"  (check: hold 300 here vs features.json, max abs diff {max(chk):.4f})")
