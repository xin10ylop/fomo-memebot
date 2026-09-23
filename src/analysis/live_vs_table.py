"""live_vs_table.py: every one of our real fills against the tables' own model for the SAME launch.

    python3 src/analysis/live_vs_table.py [our_events.json] [--eth-usd 2570]

Pulls (or reads) every Buy/Sell event whose counterparty is our wallet or our relay, groups them by launch, and for
each launch rebuilds exactly what src/analysis/e1_multi.py's score() would have said for that launch at OUR stake:
  first   = our buy as the very first Buy of the E1 block, hold 15 blocks (the tables' +9.3% column)
  last    = after every other Buy of the E1 block (the tables' -5.8% column)
  landed  = in the block and at the position we really got (the buys ahead of us folded first), hold 15
  landed@exit = the same entry, sold at the block our sell really landed in
  actual  = the Sell event's ETH out over the Buy event's ETH in, from the chain, nothing modelled
so the gap between the tables and the wallet splits into: the seat we got (first - landed), the hold we held
(landed - landed@exit) and everything else (landed@exit - actual: fees, curve model, sell slippage). Our own events are
removed from the launch's tape before modelling, so the model does not count our own buy as somebody else's."""
import json, urllib.request, time, sys, os, collections, statistics as st
RPC = os.environ.get("RPC_URL", "https://rpc.mainnet.chain.robinhood.com"); H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 curl/8"}
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
V2F = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"; WALLET = "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01"; RELAY = "0xe8e98c3514d5bd83fdd01360896f2382b861a720"
OURS = {WALLET, RELAY}; X0, Y0 = 1.68, 1e9; SUR = {0: 0.98, 1: 0.0618, 2: 0.0019}; CAP = 0.03
ETH_USD = float(sys.argv[sys.argv.index("--eth-usd") + 1]) if "--eth-usd" in sys.argv else 2570.0
def post(p, tries=6):
    for i in range(tries):
        try:
            r = urllib.request.Request(RPC, data=json.dumps(p).encode(), headers=H); return json.load(urllib.request.urlopen(r, timeout=90))
        except Exception:
            if i == tries - 1: raise
            time.sleep(2 * (i + 1))
def call(m, p):
    r = post({"jsonrpc": "2.0", "id": 1, "method": m, "params": p})
    if "error" in r: raise RuntimeError(r["error"])
    time.sleep(0.25); return r["result"]
def stamps(lo, hi):
    out = {}
    for attempt in range(5):
        need = [n for n in range(lo, hi + 1) if n not in out]
        if not need: break
        for i in range(0, len(need), 5):
            r = post([{"jsonrpc": "2.0", "id": n, "method": "eth_getBlockByNumber", "params": [hex(n), False]} for n in need[i:i + 5]])
            if isinstance(r, list):
                for x in r:
                    if x.get("result"): out[x["id"]] = int(x["result"]["timestamp"], 16)
            time.sleep(0.3)
        if len(out) < hi - lo + 1: time.sleep(1.5 * (attempt + 1))
    return out
def fold_buy(X, Y, tk): return X + X * tk / (Y - tk), Y - tk
def fold_sell(X, Y, tk): return X - X * tk / (Y + tk), Y + tk
def pad(a): return "0x" + "0" * 24 + a[2:]
def load_events(path):
    if path and os.path.exists(path): return json.load(open(path))
    head = int(call("eth_blockNumber", []), 16); lo = head - int(6.5 * 86400 * 9.9); out = []; b = lo
    while b <= head:
        e = min(head, b + 249_999)
        for who in OURS: out += call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "topics": [[BUY, SELL], None, pad(who)]}])
        b = e + 1
    out.sort(key=lambda l: (int(l["blockNumber"], 16), int(l["logIndex"], 16))); return out
def row_of(e):
    d = e["data"][2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]; bn = int(e["blockNumber"], 16)
    who = ("0x" + e["topics"][2][-40:]).lower() if len(e["topics"]) > 2 else None; k = "B" if e["topics"][0] == BUY else "S"
    return {"bn": bn, "k": k, "eth": w[0] if k == "B" else w[1], "tk": w[1] if k == "B" else w[0], "who": who, "li": int(e["logIndex"], 16), "ti": int(e["transactionIndex"], 16), "h": e["transactionHash"]}
def launch(cv, b_first):
    cl = call("eth_getLogs", [{"fromBlock": hex(b_first - 400), "toBlock": hex(b_first), "address": V2F, "topics": [None, None, pad(cv)]}])
    cl = [l for l in cl if len(l["topics"]) > 3]
    if not cl: return None
    b0 = int(cl[0]["blockNumber"], 16); creator = ("0x" + cl[0]["topics"][3][-40:]).lower()
    tx = call("eth_getTransactionByHash", [cl[0]["transactionHash"]]); data = bytes.fromhex(tx["input"][2:]); sel = data[:4].hex()
    words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
    tb = int.from_bytes(words[13], "big") if sel == "f85f8e41" and len(words) > 13 and int.from_bytes(words[13], "big") <= 2000 else None
    named = {"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator}
    ev = call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(b0 + 120), "address": cv, "topics": [[BUY, SELL]]}])
    rows = sorted((row_of(e) for e in ev), key=lambda r: (r["bn"], r["li"])); ts = stamps(b0, b0 + 30)
    return {"cv": cv, "b0": b0, "T0": ts[b0], "ts": ts, "tier": (0.01 + tb / 10000.0) if tb is not None else None, "tb": tb, "named": len(named), "rows": rows, "sel": sel}
def model(L, stake_eth, entry_block, n_ahead, hold=None, exit_block=None, sur=None):
    """e1_multi's score() with the position given as the number of the entry block's buys folded before ours, at a stake in ETH,
    on the launch's tape without our own events; exit at entry+hold or at exit_block, after everything in that block."""
    rows = [r for r in L["rows"] if r["who"] not in OURS]; tier = L["tier"]; ts = L["ts"]; T0 = L["T0"]
    X, Y = X0, Y0; i = 0
    while i < len(rows) and ts.get(rows[i]["bn"], 9e18) == T0:
        r = rows[i]
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
        i += 1
    rest = rows[i:]; seen_in_block = 0; pre = []; post_ = []
    for r in rest:
        if r["bn"] < entry_block: pre.append(r)
        elif r["bn"] == entry_block:
            if r["k"] == "B":
                if seen_in_block < n_ahead: pre.append(r); seen_in_block += 1
                else: post_.append(r)
            else: (pre if seen_in_block < n_ahead else post_).append(r)
        else: post_.append(r)
    for r in pre:
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
    if sur is None: sur = SUR.get(ts.get(entry_block, T0) - T0, 0.0)
    g = stake_eth; net = g * (1 - tier - sur); tk_us = Y * net / (X + net)
    if tk_us > CAP * Y0: tk_us = CAP * Y0; net = X * tk_us / (Y - tk_us); g = net / (1 - tier - sur)
    X, Y = X + net, Y - tk_us; xb = exit_block if exit_block is not None else entry_block + hold
    for r in post_:
        if r["bn"] > xb: break
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
    back = X * tk_us / (Y + tk_us) * (1 - tier)
    return back / g - 1
def main():
    path = next((a for a in sys.argv[1:] if a.endswith(".json")), None); ev = load_events(path)
    ours = [row_of(e) for e in ev]; by_cv = collections.OrderedDict()
    for r, e in zip(ours, ev): by_cv.setdefault(e["address"].lower(), []).append(r)
    print(f"{len(ev)} of our events on {len(by_cv)} curves; ETH/USD {ETH_USD:.0f}\n")
    tot = collections.Counter(); rowsout = []
    for cv, rs in by_cv.items():
        buys = [r for r in rs if r["k"] == "B"]; sells = [r for r in rs if r["k"] == "S"]
        if not buys: continue
        L = launch(cv, buys[0]["bn"])
        if L is None or L["tier"] is None: print(f"{cv}: launch not found or layout unknown ({L and L['sel']})"); continue
        ts = L["ts"]; T0 = L["T0"]; b0 = L["b0"]
        bE1 = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
        eth_in = sum(b["eth"] for b in buys); eth_out = sum(s["eth"] for s in sells); actual = eth_out / eth_in - 1 if sells else None
        b = buys[0]; blk = b["bn"]; sec = ts.get(blk, T0) - T0
        in_block = [r for r in L["rows"] if r["bn"] == blk and r["k"] == "B"]; ahead = [r for r in in_block if r["li"] < b["li"] and r["who"] not in OURS]; behind = [r for r in in_block if r["li"] > b["li"] and r["who"] not in OURS]
        # the fee we really paid on the first fill: from the tape folded up to our event, including everybody's real trades
        X, Y = X0, Y0
        for r in L["rows"]:
            if (r["bn"], r["li"]) >= (b["bn"], b["li"]): break
            if r["k"] == "B":
                if 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
            else: X, Y = fold_sell(X, Y, r["tk"])
        fee_paid = 1 - (X * b["tk"] / (Y - b["tk"])) / b["eth"] if 0 < b["tk"] < Y else None
        sell_blk = sells[-1]["bn"] if sells else None
        m_first = model(L, b["eth"], bE1, 0, hold=15) if bE1 else None; m_last = model(L, b["eth"], bE1, 99, hold=15) if bE1 else None
        m_landed = model(L, b["eth"], blk, len(ahead), hold=15); m_landed_x = model(L, b["eth"], blk, len(ahead), exit_block=sell_blk) if sell_blk else None
        when = time.strftime("%b %d %H:%M:%S", time.gmtime(T0)); via = "relay" if b["who"] == RELAY else "wallet"
        print(f"{when}  {cv}  tier {L['tier']:.0%} named {L['named']}  {via}  fills {len(buys)}  stake {eth_in:.5f} ETH (${eth_in*ETH_USD:.2f})")
        print(f"   landed: block b0+{blk-b0} = second +{sec} ({'E1' if blk == bE1 else 'E1+%d' % (blk-bE1) if bE1 and blk > bE1 else 'CREATION SECOND' if sec == 0 else 'E%d' % sec}), tx index {b['ti']}, {len(ahead)} buy{'s' if len(ahead)!=1 else ''} ahead ({sum(r['eth'] for r in ahead):.3f} ETH), {len(behind)} behind ({sum(r['eth'] for r in behind):.3f} ETH); fee paid {fee_paid:.2%} (tier {L['tier']:.0%} + surcharge {SUR.get(sec,0):.2%} = {L['tier']+SUR.get(sec,0):.2%})")
        print(f"   model at our stake: first {m_first:+.1%}  last {m_last:+.1%}  landed(h15) {m_landed:+.1%}" + (f"  landed@our exit(+{sell_blk-blk} blocks) {m_landed_x:+.1%}" if m_landed_x is not None else "") + (f"   ACTUAL {actual:+.1%}  ({eth_out-eth_in:+.5f} ETH, ${(eth_out-eth_in)*ETH_USD:+.2f})" if actual is not None else "   ACTUAL: no sell found (open or dust)"))
        if actual is not None and m_landed_x is not None:
            print(f"   split: seat {m_landed-m_first:+.1%}  hold {m_landed_x-m_landed:+.1%}  execution/fees/model {actual-m_landed_x:+.1%}")
        rowsout.append({"cv": cv, "T0": T0, "first": m_first, "last": m_last, "landed": m_landed, "landed_x": m_landed_x, "actual": actual, "ahead": len(ahead), "fills": len(buys), "sec": sec, "stake": eth_in, "net": (eth_out - eth_in) if sells else None, "via": via, "fee_paid": fee_paid, "hold": (sell_blk - blk) if sell_blk else None})
        print()
    clean = [r for r in rowsout if r["actual"] is not None and r["fills"] == 1]
    if clean:
        print(f"=== {len(clean)} single-fill trades with a sell: mean actual {st.mean(r['actual'] for r in clean):+.1%} | model first {st.mean(r['first'] for r in clean if r['first'] is not None):+.1%} | landed(h15) {st.mean(r['landed'] for r in clean):+.1%} | landed@exit {st.mean(r['landed_x'] for r in clean):+.1%}")
        print(f"    buys ahead of us: {[r['ahead'] for r in clean]}; seconds landed: {[r['sec'] for r in clean]}; holds (blocks): {[r['hold'] for r in clean]}; fee paid: {[round(r['fee_paid'],4) for r in clean]}")
        print(f"    net ETH {sum(r['net'] for r in clean):+.5f} (${sum(r['net'] for r in clean)*ETH_USD:+.2f}) on stakes {sum(r['stake'] for r in clean):.5f} ETH; multi-fill launches: {[(r['fills'], round(r['net'],5)) for r in rowsout if r['fills'] > 1]}")
    json.dump(rowsout, open("live_vs_table.json", "w"), indent=1)
if __name__ == "__main__":
    main()
