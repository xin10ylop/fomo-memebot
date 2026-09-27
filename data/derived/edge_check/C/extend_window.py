"""extend_window.py (edge_check/C, a copy of round 1 A's script writing into C/): score a stretch the committed windows do not cover, with the tables' own population and
crowd definitions: e1_multi.py's qualifying test (selector f85f8e41, quote 0, tier 2-3%, >= 3 named, bundle >= 0.3 ETH of
tier-fee buys in the creation second, E1 and E2 found) copied verbatim in logic, but every failed launch is RETRIED (e1_multi
drops a launch silently on any RPC error: sep25eve2 lost 2 of sep25eve's 7), then crowd_raw.py's pull (blocks 0..k+1, every
transaction aimed at the curve) and the tape to b0+640 for every launch. Public RPC, 3 threads, 0.15 s after each call.
    python3 data/derived/edge_check/C/extend_window.py "2026-09-27 09:20" "2026-09-27 11:00" extra27"""
import sys, os, json, gzip, time, calendar, urllib.request, concurrent.futures as cf, collections
sys.path.insert(0, "src/analysis"); pass
import live_vs_table as lv
A = "data/derived/edge_check/C/"
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 curl/8"}
V2F = lv.V2F; BUY, SELL = lv.BUY, lv.SELL; X0, Y0 = 1.68, 1e9
def call(m, p):
    for i in range(8):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers=H), timeout=60)); time.sleep(0.15)
            if "error" in r: raise RuntimeError(r["error"])
            return r["result"]
        except Exception as e:
            if i == 7: raise
            time.sleep(min(30, 2 * (i + 1)))
def ts_of(b): return int(call("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)
def block_at(t):
    hi = int(call("eth_blockNumber", []), 16); lo = hi - 2_000_000
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ts_of(mid) < t: lo = mid
        else: hi = mid
    return hi
def stamps(lo, hi):
    out = {}
    for attempt in range(6):
        need = [n for n in range(lo, hi + 1) if n not in out]
        if not need: break
        for i in range(0, len(need), 5):
            try:
                r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, data=json.dumps([{"jsonrpc": "2.0", "id": n, "method": "eth_getBlockByNumber", "params": [hex(n), False]} for n in need[i:i + 5]]).encode(), headers=H), timeout=60))
                if isinstance(r, list):
                    for x in r:
                        if x.get("result"): out[x["id"]] = int(x["result"]["timestamp"], 16)
            except Exception: time.sleep(2)
            time.sleep(0.3)
        if len(out) < hi - lo + 1: time.sleep(1.5 * (attempt + 1))
    return out
def one(item):
    txh, (b0, cv, creator) = item
    tx = call("eth_getTransactionByHash", [txh]); data = bytes.fromhex(tx["input"][2:]); sel = data[:4].hex()
    words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
    if sel != "f85f8e41" or len(words) < 14: return None
    quote = int.from_bytes(words[2], "big"); named = {"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator}
    tb = int.from_bytes(words[13], "big") if int.from_bytes(words[13], "big") <= 2000 else None
    if quote != 0 or tb is None or len(named) < 3: return None
    tier = 0.01 + tb / 10000.0
    if not (0.02 <= tier <= 0.03): return None
    ev = call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(b0 + 90), "address": cv, "topics": [[BUY, SELL]]}])
    ev.sort(key=lambda e: (int(e["blockNumber"], 16), int(e["logIndex"], 16)))
    ts = stamps(b0, b0 + 24)
    if b0 not in ts: raise RuntimeError("no stamp for b0")
    T0 = ts[b0]; rows = []
    for e in ev:
        d = e["data"][2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]; bn = int(e["blockNumber"], 16)
        rows.append((bn, "B" if e["topics"][0] == BUY else "S", w[0] if e["topics"][0] == BUY else w[1], w[1] if e["topics"][0] == BUY else w[0]))
    if not rows or rows[0][1] != "B" or rows[0][0] != b0: return None
    X, Y = X0, Y0; bundle = 0.0; i = 0
    while i < len(rows) and ts.get(rows[i][0], 9e18) == T0:
        bn, k, eth, tk = rows[i]
        if k == "B":
            if 0 < tk < Y:
                net = X * tk / (Y - tk); fee = 1 - net / eth if eth > 0 else 1; X, Y = X + X * tk / (Y - tk), Y - tk
                if i > 0 and abs(fee - tier) <= 0.0008: bundle += eth
        else: X, Y = X - X * tk / (Y + tk), Y + tk
        i += 1
    if bundle < 0.3: return None
    bE1 = next((n for n in range(b0 + 1, b0 + 25) if ts.get(n, 0) == T0 + 1), None); bE2 = next((n for n in range(b0 + 1, b0 + 25) if ts.get(n, 0) == T0 + 2), None)
    if bE1 is None or bE2 is None: return None
    return {"b0": b0, "cv": cv, "T0": T0, "hour": time.gmtime(T0).tm_hour, "tier": tier, "bundle_eth": bundle, "same_second_blocks": bE1 - b0 - 1, "creator": creator, "named": sorted(named)}
def crowd(l):
    cv = l["cv"]; b0 = l["b0"]; k = l["same_second_blocks"]; creator = l["creator"]; named = set(l["named"]); token = None
    for lg in call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(b0), "address": V2F}]):
        if len(lg["topics"]) > 3 and lg["topics"][2][-40:] == cv[2:]: token = "0x" + lg["topics"][1][-40:]
    blocks = []
    for off in range(0, k + 2):
        blk = call("eth_getBlockByNumber", [hex(b0 + off), True]); rows = []
        for t in blk["transactions"]:
            fr = t["from"].lower(); to = (t.get("to") or "").lower(); data = t.get("input", "")
            if to == cv or cv[2:] in data:
                rows.append({"fr": fr, "to": to, "ix": int(t["transactionIndex"], 16), "direct": to == cv, "named_fr": fr in named or fr == creator, "named_data": any(w[2:] in data for w in named), "to_token": to == token, "sel": data[:10]})
        blocks.append(rows)
    return {"cv": cv, "b0": b0, "k": k, "T0": l["T0"], "token": token, "creator": creator, "named": sorted(named), "blocks": blocks}
def tape(l):
    L = lv.launch(l["cv"], l["b0"] + 12); time.sleep(0.15)
    more = lv.call("eth_getLogs", [{"fromBlock": hex(l["b0"] + 121), "toBlock": hex(l["b0"] + 640), "address": l["cv"], "topics": [[BUY, SELL]]}])
    L["rows"] = sorted(L["rows"] + [lv.row_of(x) for x in more], key=lambda x: (x["bn"], x["li"])); L["ts"] = {str(k): v for k, v in L["ts"].items()}; L["hi"] = l["b0"] + 640
    return L
def retrying(f, items, label):
    out = {}; todo = list(items)
    for p in range(4):
        fails = []
        def g(it):
            try: return it, f(it), None
            except Exception as e: return it, None, str(e)[:80]
        with cf.ThreadPoolExecutor(3) as ex:
            for it, res, err in ex.map(g, todo):
                if err: fails.append(it)
                else: out[it[0] if isinstance(it, tuple) else it["cv"]] = res
        print(f"  {label}: pass {p+1}: {len(todo) - len(fails)} ok, {len(fails)} failed", flush=True)
        if not fails: break
        todo = fails; time.sleep(10)
    return out, len(todo) if fails else 0
if __name__ == "__main__":
    t_lo = calendar.timegm(time.strptime(sys.argv[1], "%Y-%m-%d %H:%M")); t_hi = calendar.timegm(time.strptime(sys.argv[2], "%Y-%m-%d %H:%M")); tag = sys.argv[3]
    lo, hi = block_at(t_lo), block_at(t_hi); print(f"{sys.argv[1]} - {sys.argv[2]}: blocks {lo}-{hi}", flush=True)
    logs = []; b = lo
    while b <= hi:
        e = min(hi, b + 9999); logs += call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "address": V2F}]); b = e + 1
    cre = collections.OrderedDict()
    for l in logs:
        if len(l["topics"]) > 3: cre.setdefault(l["transactionHash"], (int(l["blockNumber"], 16), "0x" + l["topics"][2][-40:], "0x" + l["topics"][3][-40:]))
    print(f"  {len(cre)} creations", flush=True)
    res, unresolved = retrying(one, list(cre.items()), "qualify")
    L = sorted([v for v in res.values() if v], key=lambda x: x["T0"]); print(f"  {len(L)} qualifying launches ({unresolved} creations unresolved after 4 passes)", flush=True)
    C, _ = retrying(crowd, L, "crowd"); TP, _ = retrying(tape, L, "tape")
    json.dump({"t_lo": t_lo, "t_hi": t_hi, "creations": len(cre), "unresolved": unresolved, "launches": L}, open(A + f"launches_{tag}.json", "w"))
    json.dump([C[l["cv"]] for l in L if l["cv"] in C], gzip.open(A + f"crowd_raw_{tag}.json.gz", "wt"))
    json.dump(TP, gzip.open(A + f"tapes_{tag}.json.gz", "wt")); print("wrote", tag, len(L), "launches", len(C), "crowds", len(TP), "tapes")
