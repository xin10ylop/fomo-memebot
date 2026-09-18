"""both legal outside seats with real second boundaries, several days: E1 = first block of the second after the creation's
(first / after that block's other buys / one block late), E2 = first block of the second after that; holds 15/30/60 blocks;
who occupies the E1 block (repeat buyer addresses). Output: one JSON per window with every launch's numbers."""
import json, urllib.request, time, sys, collections, statistics as st, concurrent.futures as cf, os
RPC = os.environ.get("RPC_URL", "https://rpc.mainnet.chain.robinhood.com")   # the public endpoint: no provider usage for history reads
H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl/8"}
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"; V2F = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"
X0, Y0 = 1.68, 1e9; ETH_USD = 2500.0; SUR = {1: 0.0618, 2: 0.0019}; CAP = 0.03
HOURS = float(sys.argv[1]); BACK_H = float(sys.argv[2]); OUT = sys.argv[3]; TIER_LO = float(sys.argv[4]) if len(sys.argv) > 4 else 0.02; TIER_HI = float(sys.argv[5]) if len(sys.argv) > 5 else 0.03
if os.path.exists(OUT): print("exists, skipping", OUT); sys.exit(0)
def post(payload, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(payload).encode(), headers=H)
            return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception:
            if i == tries - 1: raise
            time.sleep(2 * (i + 1))
def call(m, p):
    r = post({"jsonrpc": "2.0", "id": 1, "method": m, "params": p})
    if "error" in r: raise RuntimeError(r["error"])
    return r["result"]
def stamps(lo, hi):
    out = {}
    for attempt in range(4):
        need = [n for n in range(lo, hi + 1) if n not in out]
        if not need: break
        r = post([{"jsonrpc": "2.0", "id": n, "method": "eth_getBlockByNumber", "params": [hex(n), False]} for n in need])
        if isinstance(r, list):
            for x in r:
                if x.get("result"): out[x["id"]] = int(x["result"]["timestamp"], 16)
        if len(out) < hi - lo + 1: time.sleep(1.5 * (attempt + 1))
    return out
head = int(call("eth_blockNumber", []), 16) - 60 - int(BACK_H * 3600 * 9.9); lo = head - int(HOURS * 3600 * 9.9)
t_lo = int(call("eth_getBlockByNumber", [hex(lo), False])["timestamp"], 16); t_hi = int(call("eth_getBlockByNumber", [hex(head), False])["timestamp"], 16)
logs = []; b = lo
while b <= head:
    e = min(head, b + 9999); logs += call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "address": V2F}]); b = e + 1
cre = collections.OrderedDict()
for l in logs:
    if len(l["topics"]) > 3: cre.setdefault(l["transactionHash"], (int(l["blockNumber"], 16), "0x" + l["topics"][2][-40:], "0x" + l["topics"][3][-40:]))
def fold_buy(X, Y, tk): return X + X * tk / (Y - tk), Y - tk
def fold_sell(X, Y, tk): return X - X * tk / (Y + tk), Y + tk
def one(item):
    txh, (b0, cv, creator) = item
    tx = call("eth_getTransactionByHash", [txh]); data = bytes.fromhex(tx["input"][2:]); sel = data[:4].hex()
    words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
    if sel != "f85f8e41" or len(words) < 14: return None
    quote = int.from_bytes(words[2], "big"); named = {"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator}
    tb = int.from_bytes(words[13], "big") if int.from_bytes(words[13], "big") <= 2000 else None
    if quote != 0 or tb is None or len(named) < 3: return None
    tier = 0.01 + tb / 10000.0
    if not (TIER_LO <= tier <= TIER_HI): return None
    ev = call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(b0 + 90), "address": cv, "topics": [[BUY, SELL]]}])
    ev.sort(key=lambda e: (int(e["blockNumber"], 16), int(e["logIndex"], 16)))
    ts = stamps(b0, b0 + 24); T0 = ts[b0]                      # the creation second and the next hold at most ten blocks each
    rows = []
    for e in ev:
        d = e["data"][2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]; bn = int(e["blockNumber"], 16); who = "0x" + e["topics"][2][-40:] if len(e["topics"]) > 2 else None
        rows.append((bn, "B" if e["topics"][0] == BUY else "S", w[0] if e["topics"][0] == BUY else w[1], w[1] if e["topics"][0] == BUY else w[0], who))
    if not rows or rows[0][1] != "B" or rows[0][0] != b0: return None
    X, Y = X0, Y0; bundle_eth = 0.0; i = 0
    while i < len(rows) and ts.get(rows[i][0], 9e18) == T0:
        bn, k, eth, tk, who = rows[i]
        if k == "B":
            if 0 < tk < Y:
                net = X * tk / (Y - tk); fee = 1 - net / eth if eth > 0 else 1; X, Y = fold_buy(X, Y, tk)
                if i > 0 and abs(fee - tier) <= 0.0008: bundle_eth += eth
        else: X, Y = fold_sell(X, Y, tk)
        i += 1
    if bundle_eth < 0.3: return None
    X1, Y1 = X, Y; rest = rows[i:]
    bE1 = next((n for n in range(b0 + 1, b0 + 25) if ts.get(n, 0) == T0 + 1), None); bE2 = next((n for n in range(b0 + 1, b0 + 25) if ts.get(n, 0) == T0 + 2), None)
    if bE1 is None or bE2 is None: return None
    out = {"b0": b0, "cv": cv, "T0": T0, "hour": time.gmtime(T0).tm_hour, "tier": tier, "bundle_eth": bundle_eth, "same_second_blocks": bE1 - b0 - 1, "res": {},
           "e1_block_buyers": [r[4] for r in rest if r[0] == bE1 and r[1] == "B"], "e1_block_eth": sum(r[2] for r in rest if r[0] == bE1 and r[1] == "B"),
           "e2_block_buyers": [r[4] for r in rest if r[0] == bE2 and r[1] == "B"]}
    def score(entry_block, pos, sur, hold, stake, tp=None):
        Xs, Ys = X1, Y1; j = 0
        # everything before our entry block, and (pos == last) the buys of our block
        for r in rest:
            bn, k, eth, tk, who = r
            if bn < entry_block or (bn == entry_block and pos == "last"):
                if k == "B":
                    if 0 < tk < Ys: Xs, Ys = fold_buy(Xs, Ys, tk)
                else: Xs, Ys = fold_sell(Xs, Ys, tk)
        g = stake / ETH_USD; net = g * (1 - tier - sur); tk_us = Ys * net / (Xs + net)
        if tk_us > CAP * Y0: tk_us = CAP * Y0; net = Xs * tk_us / (Ys - tk_us); g = net / (1 - tier - sur)
        Xs, Ys = Xs + net, Ys - tk_us; p_in = Xs / Ys; exit_block = entry_block + hold
        for r in rest:
            bn, k, eth, tk, who = r
            if bn < entry_block or (bn == entry_block and pos == "last") or bn > exit_block: continue
            if k == "B":
                if 0 < tk < Ys: Xs, Ys = fold_buy(Xs, Ys, tk)
            else: Xs, Ys = fold_sell(Xs, Ys, tk)
            if tp and Xs / Ys >= p_in * (1 + tp): exit_block = min(exit_block, bn + 3)
        back = Xs * tk_us / (Ys + tk_us) * (1 - tier)
        return back / g - 1, g * ETH_USD
    for stake in (10.0, 250.0):
        for hold in (15, 30, 60):
            out["res"][f"E1_first_h{hold}_{int(stake)}"] = score(bE1, "first", SUR[1], hold, stake)
            out["res"][f"E1_last_h{hold}_{int(stake)}"] = score(bE1, "last", SUR[1], hold, stake)
            out["res"][f"E1_late1_h{hold}_{int(stake)}"] = score(bE1 + 1, "last", SUR[1], hold, stake)
            out["res"][f"E2_first_h{hold}_{int(stake)}"] = score(bE2, "first", SUR[2], hold, stake)
            out["res"][f"E2_last_h{hold}_{int(stake)}"] = score(bE2, "last", SUR[2], hold, stake)
        out["res"][f"E1_first_h60tp50_{int(stake)}"] = score(bE1, "first", SUR[1], 60, stake, tp=0.5)
        out["res"][f"E1_last_h60tp50_{int(stake)}"] = score(bE1, "last", SUR[1], 60, stake, tp=0.5)
    return out
def safe(item):
    try: return one(item)
    except Exception as e:
        errors.append(str(e)[:80]); return None
errors = []
with cf.ThreadPoolExecutor(3) as ex: res = [r for r in ex.map(safe, list(cre.items())) if r]
print("launch errors:", len(errors), errors[:3])
json.dump({"t_lo": t_lo, "t_hi": t_hi, "creations": len(cre), "launches": res}, open(OUT, "w"))
print(f"{time.strftime('%b %d %H:%M', time.gmtime(t_lo))}-{time.strftime('%b %d %H:%M', time.gmtime(t_hi))} UTC: {len(cre)} creations, {len(res)} qualifying -> {OUT}")
