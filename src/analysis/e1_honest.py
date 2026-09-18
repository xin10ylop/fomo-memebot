"""the next-second seat (E1) scored with real block timestamps: for every qualifying launch (>=3 named wallets, bundle >=0.3 ETH
in the creation's clock second, tier 1-2%, ETH quote) enter in the first block of the next second, before or after the other
buys of that block, 6.18% surcharge + tier, hold 1.5 s (15 blocks), sell at the tier fee with our own impact."""
import json, urllib.request, time, sys, collections, statistics as st, concurrent.futures as cf
import os; RPC = "https://robinhood-mainnet.g.alchemy.com/v2/" + os.environ["ALCHEMY_KEY"]; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl/8"}
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"; V2F = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"
X0, Y0 = 1.68, 1e9; ETH_USD = 2482.0; SUR = 0.0618; HOLD_BLOCKS = 15; CAP_SUPPLY = 0.03
HOURS = float(sys.argv[1]) if len(sys.argv) > 1 else 14; BACK_H = float(sys.argv[2]) if len(sys.argv) > 2 else 0; TIER_LO = float(sys.argv[3]) if len(sys.argv) > 3 else 0.02; TIER_HI = float(sys.argv[4]) if len(sys.argv) > 4 else 0.03
def post(payload, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(payload).encode(), headers=H)
            return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception:
            if i == tries - 1: raise
            time.sleep(1.5 * (i + 1))
def call(m, p):
    r = post({"jsonrpc": "2.0", "id": 1, "method": m, "params": p})
    if "error" in r: raise RuntimeError(r["error"])
    return r["result"]
def stamps(lo, hi):
    r = post([{"jsonrpc": "2.0", "id": n, "method": "eth_getBlockByNumber", "params": [hex(n), False]} for n in range(lo, hi + 1)])
    return {x["id"]: int(x["result"]["timestamp"], 16) for x in r if x.get("result")}
head = int(call("eth_blockNumber", []), 16) - 60 - int(BACK_H * 3600 * 9.9); lo = head - int(HOURS * 3600 * 9.9)
t_lo = int(call("eth_getBlockByNumber", [hex(lo), False])["timestamp"], 16); t_hi = int(call("eth_getBlockByNumber", [hex(head), False])["timestamp"], 16)
print(f"window {time.strftime('%b %d %H:%M', time.gmtime(t_lo))}-{time.strftime('%b %d %H:%M', time.gmtime(t_hi))} UTC ({(t_hi-t_lo)/3600:.1f} h)")
logs = []; b = lo
while b <= head:
    e = min(head, b + 9999); logs += call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "address": V2F}]); b = e + 1
cre = collections.OrderedDict()
for l in logs:
    if len(l["topics"]) > 3: cre.setdefault(l["transactionHash"], (int(l["blockNumber"], 16), "0x" + l["topics"][2][-40:], "0x" + l["topics"][3][-40:]))
print("creations:", len(cre))
def one(item):
    txh, (b0, cv, creator) = item
    tx = call("eth_getTransactionByHash", [txh]); data = bytes.fromhex(tx["input"][2:]); sel = data[:4].hex()
    words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
    if sel != "f85f8e41" or len(words) < 14: return None
    quote = int.from_bytes(words[2], "big")
    named = {"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator}
    tb = int.from_bytes(words[13], "big") if int.from_bytes(words[13], "big") <= 2000 else None
    if quote != 0 or tb is None or len(named) < 3: return None
    tier = 0.01 + tb / 10000.0
    if not (TIER_LO <= tier <= TIER_HI): return None
    ev = call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(b0 + 45), "address": cv, "topics": [[BUY, SELL]]}])
    ev.sort(key=lambda e: (int(e["blockNumber"], 16), int(e["logIndex"], 16)))
    ts = stamps(b0, b0 + 45); T0 = ts[b0]
    rows = []  # (block, kind, eth, tk)
    for e in ev:
        d = e["data"][2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]; bn = int(e["blockNumber"], 16)
        if e["topics"][0] == BUY: rows.append((bn, "B", w[0], w[1]))
        else: rows.append((bn, "S", w[1], w[0]))
    if not rows or rows[0][1] != "B" or rows[0][0] != b0: return None
    # the creation second: fold everything with the creation's timestamp; the bundle = exempt buys there (fee == tier)
    X, Y = X0, Y0; bundle_eth = 0.0; n_exempt = 0; i = 0
    while i < len(rows) and ts.get(rows[i][0], 9e18) == T0:
        bn, k, eth, tk = rows[i]
        if k == "B":
            if tk <= 0 or tk >= Y: i += 1; continue
            net = X * tk / (Y - tk); X += net; Y -= tk; fee = 1 - net / eth if eth > 0 else 1
            if i > 0 and abs(fee - tier) <= 0.0008: bundle_eth += eth; n_exempt += 1
        else:
            X -= X * tk / (Y + tk); Y += tk
        i += 1
    if bundle_eth < 0.3: return None
    bE = next((n for n in range(b0 + 1, b0 + 46) if ts.get(n, 0) == T0 + 1), None)
    if bE is None: return None
    same_second_blocks = bE - b0 - 1
    out = {"b0": b0, "cv": cv, "tier": tier, "bundle_eth": bundle_eth, "n_exempt": n_exempt, "same_second_blocks": same_second_blocks, "hour": time.gmtime(T0).tm_hour, "res": {}}
    rest = rows[i:]
    ahead = [r for r in rest if r[0] == bE and r[1] == "B"]  # the other buys in our entry block
    for pos in ("first", "last"):
        for stake in (10.0, 100.0, 250.0):
            Xs, Ys = X, Y
            if pos == "last":
                for bn, k, eth, tk in ahead:
                    if tk <= 0 or tk >= Ys: continue
                    Xs += Xs * tk / (Ys - tk); Ys -= tk
            g = stake / ETH_USD; net = g * (1 - tier - SUR); tk_us = Ys * net / (Xs + net)
            if tk_us > CAP_SUPPLY * Y0:
                tk_us = CAP_SUPPLY * Y0; net = Xs * tk_us / (Ys - tk_us); g = net / (1 - tier - SUR)
            Xs += net; Ys -= tk_us
            for bn, k, eth, tk in rest:
                if bn < bE or (bn == bE and pos == "last") or bn > bE + HOLD_BLOCKS: continue
                if bn == bE and pos == "first" and k == "B":
                    pass
                if k == "B":
                    if tk <= 0 or tk >= Ys: continue
                    Xs += Xs * tk / (Ys - tk); Ys -= tk
                else:
                    Xs -= Xs * tk / (Ys + tk); Ys += tk
            back = Xs * tk_us / (Ys + tk_us) * (1 - tier)
            out["res"][(pos, stake)] = (back / g - 1, g * ETH_USD)
    out["ahead"] = len(ahead); out["ahead_eth"] = sum(r[2] for r in ahead)
    out["follow_eth"] = sum(r[2] for r in rest if r[1] == "B" and bE < r[0] <= bE + HOLD_BLOCKS)
    return out
with cf.ThreadPoolExecutor(6) as ex: res = [r for r in ex.map(one, list(cre.items())) if r]
print(f"qualifying launches (>=3 named, bundle >=0.3 ETH in the creation second, tier {TIER_LO:.0%}-{TIER_HI:.0%}): {len(res)}  -> {len(res)/((t_hi-t_lo)/86400):.0f}/day")
print(f"blocks after the creation block that still share its second: median {st.median(r['same_second_blocks'] for r in res):.0f}, share with >=3 such blocks (a 0.3 s send lands inside): {sum(r['same_second_blocks']>=3 for r in res)/len(res):.0%}")
print(f"other buys in our entry block (the first block of the next second): mean {st.mean(r['ahead'] for r in res):.1f}, launches with none {sum(r['ahead']==0 for r in res)}, mean ETH ahead {st.mean(r['ahead_eth'] for r in res):.3f}")
print(f"\n{'position':8s} {'stake':>6s} {'n':>3s} {'mean':>7s} {'median':>7s} {'win':>5s} {'dead<-20%':>9s} {'$/trade':>8s} {'$/day':>7s}")
for pos in ("first", "last"):
    for stake in (10.0, 100.0, 250.0):
        v = [r["res"][(pos, stake)] for r in res]; roi = [x[0] for x in v]; usd = [x[0] * x[1] for x in v]
        print(f"{pos:8s} {stake:6.0f} {len(v):3d} {st.mean(roi):+7.1%} {st.median(roi):+7.1%} {sum(x>0 for x in roi)/len(roi):5.0%} {sum(x<-0.2 for x in roi)/len(roi):9.0%} {st.mean(usd):+8.2f} {sum(usd)/((t_hi-t_lo)/86400):+7.0f}")
print("\nby hour (UTC), position last, $10: n / mean / dead")
byh = collections.defaultdict(list)
for r in res: byh[r["hour"]].append(r["res"][("last", 10.0)][0])
print("  " + "  ".join(f"{h:02d}h:{len(v)}/{st.mean(v):+.0%}/{sum(x<-0.2 for x in v)/len(v):.0%}" for h, v in sorted(byh.items())))
ours = [r for r in res if r["cv"].lower() == "0x1372f53992cfde9b53138ed4c20ced94ee7153b3"]
if ours:
    r = ours[0]; print(f"\nour live launch 0x1372f539: bundle {r['bundle_eth']:.2f} ETH, {r['same_second_blocks']} more blocks in its second, {r['ahead']} buys ahead in the next-second block; E1 $10 first {r['res'][('first',10.0)][0]:+.1%}, last {r['res'][('last',10.0)][0]:+.1%}")
json.dump([{k: (v if k != "res" else {f"{a}_{int(b)}": c for (a, b), c in v.items()}) for k, v in r.items()} for r in res], open(f"e1_honest_{int(BACK_H)}.json", "w"))
