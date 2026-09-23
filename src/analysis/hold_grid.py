"""hold_grid.py: the seat's return by hold length, first and behind one, on the tables' launches, with the tape to +620 blocks.

    python3 src/analysis/hold_grid.py data/derived/live_vs_table/launches_141_creators.json data/derived/live_vs_table/launches_175_sep2223.json

Holds 15, 30, 60, 150, 300, 600 blocks; a take-profit variant (sell when the curve is +50% over our entry, else at the hold);
a stop variant (sell at -20%, else at the hold). Our stake $15 and $100. Skipped launches: none (every qualifying launch)."""
import json, sys, statistics as st, time
sys.path.insert(0, "src/analysis"); import live_vs_table as lv
from live_vs_table import fold_buy, fold_sell, X0, Y0, OURS, SUR, CAP
E = 2570.0
def model_path(L, stake_eth, entry_block, n_ahead, holds, tp=None, stop=None):
    rows = [r for r in L["rows"] if r["who"] not in OURS]; tier = L["tier"]; ts = L["ts"]; T0 = L["T0"]
    X, Y = X0, Y0; i = 0
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
    X, Y = X + net, Y - tk; p_in = X / Y; out = {}; done = set(); j = 0
    for h in sorted(holds):
        while j < len(post) and post[j]["bn"] <= entry_block + h:
            r = post[j]
            if r["k"] == "B":
                if 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
            else: X, Y = fold_sell(X, Y, r["tk"])
            p = X / Y
            if tp and "tp" not in done and p >= p_in * (1 + tp): out["tp"] = (X * tk / (Y + tk) * (1 - tier)) / g - 1; done.add("tp")
            if stop and "stop" not in done and p <= p_in * (1 - stop): out["stop"] = (X * tk / (Y + tk) * (1 - tier)) / g - 1; done.add("stop")
            j += 1
        out[h] = (X * tk / (Y + tk) * (1 - tier)) / g - 1
    return out
HOLDS = (15, 30, 60, 150, 300, 600); res = []
for f in sys.argv[1:]:
    for l in json.load(open(f)):
        try:
            cv = l["cv"].lower(); b0 = l["b0"]
            L = lv.launch(cv, b0 + l["same_second_blocks"] + 1)
            if L is None or L["tier"] is None: continue
            ev = lv.call("eth_getLogs", [{"fromBlock": hex(b0 + 121), "toBlock": hex(b0 + 620), "address": cv, "topics": [[lv.BUY, lv.SELL]]}])
            L["rows"] = sorted(L["rows"] + [lv.row_of(e) for e in ev], key=lambda r: (r["bn"], r["li"]))
            ts = L["ts"]; T0 = L["T0"]; bE1 = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
            if bE1 is None: continue
            row = {"cv": cv, "T0": T0, "day": time.strftime("%b %d", time.gmtime(T0))}
            for stake in (15.0, 100.0):
                for pos, nah in (("first", 0), ("behind1", 1)):
                    o = model_path(L, stake / E, bE1, nah, HOLDS, tp=0.5, stop=0.2)
                    for h in HOLDS: row[f"{pos}_{int(stake)}_h{h}"] = o[h]
                    row[f"{pos}_{int(stake)}_tp50_h600"] = o.get("tp", o[600]); row[f"{pos}_{int(stake)}_stop20_h600"] = o.get("stop", o[600]); row[f"{pos}_{int(stake)}_tp50_stop20_h600"] = o.get("tp", o.get("stop", o[600])) if ("tp" not in o or "stop" not in o) else (o["tp"] if L else o["stop"])
            res.append(row)
            if len(res) % 25 == 0: print(len(res), "launches", flush=True)
        except Exception as e: print("err", l.get("cv", "")[:10], str(e)[:80], flush=True)
json.dump(res, open("data/derived/live_vs_table/hold_grid.json", "w"), indent=0)
def col(rows, k):
    v = [r[k] for r in rows]; return f"{st.mean(v):+7.1%} med {st.median(v):+7.1%} win {sum(x>0 for x in v)/len(v):3.0%} dead {sum(x<-0.4 for x in v)/len(v):3.0%}"
for day in sorted({r["day"] for r in res}) + ["all"]:
    rows = [r for r in res if day == "all" or r["day"] == day]
    print(f"\n=== {day}: {len(rows)} launches, $15 stake, before gas")
    for pos in ("first", "behind1"):
        for h in HOLDS: print(f"  {pos:8s} hold {h:4d} blocks: {col(rows, f'{pos}_15_h{h}')}")
        print(f"  {pos:8s} tp +50% else 600:  {col(rows, f'{pos}_15_tp50_h600')}")
        print(f"  {pos:8s} stop -20% else 600: {col(rows, f'{pos}_15_stop20_h600')}")
