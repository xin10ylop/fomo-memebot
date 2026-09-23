"""stake_scale.py: the gated seat (2+ fleets visible by block k-3, second place, 300 blocks) re-priced at larger stakes, our own
impact and the 3% supply cap included. python3 src/analysis/stake_scale.py"""
import json, sys, statistics as st
sys.path.insert(0, "src/analysis"); import live_vs_table as lv
from live_vs_table import fold_buy, fold_sell, X0, Y0, OURS, SUR, CAP
E = 2570.0; GAS = 0.33; STAKES = (13, 50, 100, 150, 200, 300, 500)
def net_eth_of(L):
    """each buy's net ETH into the curve, from a clean pass over the tape (the buyers pay fixed ETH; at a bigger stake of ours they get
    fewer tokens, so the counterfactual folds their ETH, not their tokens: the audit's correction, 24.29)"""
    rows = [r for r in L["rows"] if r["who"] not in OURS]; X, Y = X0, Y0; net = {}
    for r in rows:
        if r["k"] == "B":
            if 0 < r["tk"] < Y: net[(r["bn"], r["li"])] = X * r["tk"] / (Y - r["tk"]); X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
    return net
def model_eff(L, stake_eth, entry_block, n_ahead, hold):
    """behind n_ahead buys in the seat block, hold blocks, on the tape without our own events: (return, effective stake in ETH);
    the buys after ours are folded by their ETH (fixed-ETH buyers), the sells by their tokens"""
    NET = net_eth_of(L)
    def fold_buy_eth(X, Y, r):
        n = NET.get((r["bn"], r["li"]))
        if n is None: return X, Y
        return X + n, Y - Y * n / (X + n)
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
    sur = SUR.get(ts.get(entry_block, T0) - T0, 0.0); g = stake_eth; net = g * (1 - tier - sur); tk = Y * net / (X + net)
    if tk > CAP * Y0: tk = CAP * Y0; net = X * tk / (Y - tk); g = net / (1 - tier - sur)
    X, Y = X + net, Y - tk
    for r in post:
        if r["bn"] > entry_block + hold: break
        if r["k"] == "B": X, Y = fold_buy_eth(X, Y, r)
        else: X, Y = fold_sell(X, Y, r["tk"])
    return (X * tk / (Y + tk) * (1 - tier)) / g - 1, g
W = (("Sep 18-19", "crowd_signal.json", 24), ("Sep 20-21 (oos)", "crowd_signal_oos_sep2021.json", 36), ("Sep 22-23", "crowd_signal_sep2223.json", 30))
out = {}
for name, cf, hours in W:
    C = json.load(open("data/derived/live_vs_table/" + cf))
    def vis(r): a = r["attackers_by_block"]; j = max(0, r["k"] - 3); return a[min(j, len(a) - 1)] if a else 0
    gated = [r for r in C if vis(r) >= 2]; rows = []
    for r in gated:
        L = lv.launch(r["cv"], r["b0"] + r["k"] + 1)
        if L is None or L["tier"] is None: continue
        ev = lv.call("eth_getLogs", [{"fromBlock": hex(r["b0"] + 121), "toBlock": hex(r["b0"] + 340), "address": r["cv"], "topics": [[lv.BUY, lv.SELL]]}])
        L["rows"] = sorted(L["rows"] + [lv.row_of(e) for e in ev], key=lambda x: (x["bn"], x["li"])); ts = L["ts"]; T0 = L["T0"]
        bE1 = next((n for n in range(r["b0"] + 1, r["b0"] + 30) if ts.get(n, 0) == T0 + 1), None)
        if bE1 is None: continue
        row = {}
        for s in STAKES: row[s] = model_eff(L, s / E, bE1, 1, 300)
        rows.append(row)
    out[name] = (rows, hours)
    print(f"\n=== {name}: {len(rows)} fired launches, second place, 300 blocks; per day = per burst x fires/day (fills assumed on every burst)")
    print(f"{'stake':>6s} {'eff. stake':>10s} {'return':>8s} {'win':>4s} {'$/burst':>8s} {'$/day':>7s}  capped")
    for s in STAKES:
        v = [x[s][0] for x in rows]; eff = [x[s][1] * E for x in rows]; usd = [x[s][0] * x[s][1] * E - GAS for x in rows]; capped = sum(1 for x in rows if x[s][1] * E < s * 0.99)
        print(f"{s:>6d} {st.mean(eff):>10.0f} {st.mean(v):>+8.1%} {sum(x>0 for x in v)/len(v):>4.0%} {st.mean(usd):>+8.2f} {st.mean(usd)*len(rows)/hours*24:>+7.0f}  {capped}/{len(rows)}")
print("\n=== the three windows pooled (per day at each window's own rate, averaged)")
print(f"{'stake':>6s} {'return':>8s} {'$/burst':>8s} {'$/day':>7s}")
for s in STAKES:
    allr = [x for rows, _ in out.values() for x in rows]; v = [x[s][0] for x in allr]; usd = [x[s][0] * x[s][1] * E - GAS for x in allr]
    days = [st.mean(x[s][0] * x[s][1] * E - GAS for x in rows) * len(rows) / hours * 24 for rows, hours in out.values()]
    print(f"{s:>6d} {st.mean(v):>+8.1%} {st.mean(usd):>+8.2f} {st.mean(days):>+7.0f}")
