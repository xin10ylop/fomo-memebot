"""chain_since.py: an independent read of the chain, no engine involved: since a UTC hour today (default 12), how many launches, how many were team-funded (bundled), and how many of those had a bot in second one. If the engine took nothing and this says every bundled launch had a bot in second one, the machine is right and the seat is crowded.

    python3 src/analysis/chain_since.py [hour_utc]"""
import json, urllib.request, time, sys, collections
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl/8"}
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
V2F = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"; CREATE = "0xdcacba5e347ae7abd91cb519eb877af8fa7774e347b85dd3ddcd24a2ba8cdf37"
X0 = 1.68; Y0 = 1e9
now = time.time(); T0 = now - (now % 86400) + (int(sys.argv[1]) if len(sys.argv) > 1 else 12) * 3600
if T0 > now: T0 -= 86400
def call(method, params, tries=6):
    for i in range(tries):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(), headers=H), timeout=120))
            if "error" in r: raise RuntimeError(r["error"])
            return r["result"]
        except Exception as e:
            time.sleep(2 * (i + 1)); err = e
    raise err
bts = {}
def ts(b):
    if b not in bts: bts[b] = int(call("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)
    return bts[b]
head = int(call("eth_blockNumber", []), 16); lo, hi = head - 60000, head
while lo < hi:
    mid = (lo + hi) // 2
    if ts(mid) < T0: lo = mid + 1
    else: hi = mid
b0 = lo; print(f"head {head} at {time.strftime('%H:%M:%S', time.gmtime(ts(head)))} UTC; first block after the start hour: {b0}", flush=True)
creates = call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(head), "address": V2F, "topics": [CREATE]}])
print(f"{len(creates)} V2 creations since the start hour", flush=True)
rows_out = []; cnt = collections.Counter()
for c in creates:
    cv = "0x" + c["topics"][2][-40:].lower(); bc = int(c["blockNumber"], 16)
    logs = call("eth_getLogs", [{"fromBlock": hex(bc), "toBlock": hex(min(head, bc + 80)), "address": cv, "topics": [[BUY, SELL]]}])
    ev = []
    for l in logs:
        d = l["data"][2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]
        ev.append((int(l["blockNumber"], 16), int(l["logIndex"], 16), "B" if l["topics"][0] == BUY else "S", w[0] if l["topics"][0] == BUY else w[1], w[1] if l["topics"][0] == BUY else w[0]))
    ev.sort()
    if not ev or ev[0][2] != "B" or ev[0][0] != bc: cnt["no launch-block buy / not native"] += 1; continue
    X, Y = X0, Y0; tier = None; rows = []; ok = True
    for i, (b, li, k, q, tk) in enumerate(ev):
        if k == "B":
            if tk <= 0 or tk >= Y or q <= 0: ok = False; break
            net = X * tk / (Y - tk); tax = 1 - net / q
            if i == 0:
                if not (0 <= tax <= 0.2): ok = False; break
                tier = tax
            rows.append((b, q, tk, tax)); X += net; Y -= tk
        else:
            gross = X - X * Y / (Y + tk); X -= gross; Y += tk
    if not ok: cnt["not a native curve"] += 1; continue
    tk0 = rows[0][2] / Y0
    first_taxed = next((r[0] for r in rows[1:] if r[3] - tier > 0.001), None)
    bundle = [r for r in rows[1:] if r[3] - tier <= 0.0008 and r[0] - bc <= 9 and (first_taxed is None or r[0] < first_taxed)]
    out1 = sum(1 for r in rows[1:] if 0.05 <= r[3] - tier <= 0.075); out2 = sum(1 for r in rows[1:] if 0.0012 <= r[3] - tier <= 0.0035)
    bundled = len(bundle) >= 3 and sum(r[1] for r in bundle) >= 0.3 and tk0 >= 0.01
    cnt["bundled launch (team-funded)" if bundled else "not bundled"] += 1
    if bundled:
        cnt["  ... with a bot in second one (skipped)" if out1 > 0 else ("  ... second one empty, someone in second two" if out2 > 0 else "  ... second one empty, second two empty (ours to take)")] += 1
        rows_out.append((time.strftime('%H:%M:%S', time.gmtime(ts(bc))), cv[:10], len(bundle), round(sum(r[1] for r in bundle), 3), out1, out2))
for k, v in cnt.items(): print(f"{v:4d}  {k}")
print("\nbundled launches: time, curve, bundle n, bundle ETH, outsiders in second one, in second two")
for r in rows_out: print("  ", *r)
