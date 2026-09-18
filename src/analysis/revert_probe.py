"""why the live buy reverted: decode the custom error, find the first block after the creation where the same call passes,
and check on today's launches vs two days ago whether any surcharged (outsider) buy still lands inside blocks 1-5."""
import json, urllib.request, time, sys, collections, concurrent.futures as cf
import os; RPC = "https://robinhood-mainnet.g.alchemy.com/v2/" + os.environ["ALCHEMY_KEY"]; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl/8"}
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; V2F = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"; X0, Y0 = 1.68, 1e9
def rpc(method, params, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(), headers=H)
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception:
            if i == tries - 1: raise
            time.sleep(1.5 * (i + 1))
def call(m, p):
    r = rpc(m, p)
    if "error" in r: raise RuntimeError(r["error"])
    return r["result"]
def verdict(r):
    if "result" in r: return "OK"
    d = (r["error"] or {}).get("data") or ""; return "REVERT " + (d if isinstance(d, str) else str(d))
# ---- part A: our launch
h = "0x8161cf5b91611aeedb8deca1cd1c0bdcb71381c584535cfdde3be84c60b24ef4"; cv = "0x1372f53992cfde9b53138ed4c20ced94ee7153b3"; b0 = 66126811
tx = call("eth_getTransactionByHash", [h]); bl = int(tx["blockNumber"], 16)
base = {"from": tx["from"], "to": tx["to"], "value": tx["value"], "data": tx["input"], "gas": hex(500000)}
r = rpc("eth_call", [base, hex(bl - 1)]); d = r["error"]["data"]
print("A. custom error selector", d[:10], "| args:", [int(d[10 + 64 * i: 10 + 64 * (i + 1)], 16) for i in range((len(d) - 10) // 64)])
print("   (args / 1e18:", [int(d[10 + 64 * i: 10 + 64 * (i + 1)], 16) / 1e18 for i in range((len(d) - 10) // 64)], ")")
print("   our call, by state-after-block offset from the creation (state used by a tx in block k is the state after block k-1):")
for k in range(0, 9):
    print(f"     state after +{k} -> {verdict(rpc('eth_call', [base, hex(b0 + k)]))[:60]}")
print("   at state after +2 (what our tx saw), other amounts, same wallet:")
for eth in (0.0004, 0.00004, 0.02, 0.1):
    a = int(eth * 1e18); data = tx["input"][:10] + hex(a)[2:].rjust(64, "0") + tx["input"][74:]
    print(f"     {eth} ETH -> {verdict(rpc('eth_call', [dict(base, value=hex(a), data=data), hex(b0 + 2)]))[:60]}")
rnd = "0x" + "a1" * 20
print(f"   at state after +2, a random unrelated address -> {verdict(rpc('eth_call', [dict(base, **{'from': rnd}), hex(b0 + 2)]))[:60]}")
# ---- part B: regime check on two windows
head = int(call("eth_blockNumber", []), 16) - 30
def window(label, hi, hours):
    lo = hi - int(hours * 3600 * 9.9)
    t_lo = int(call("eth_getBlockByNumber", [hex(lo), False])["timestamp"], 16); t_hi = int(call("eth_getBlockByNumber", [hex(hi), False])["timestamp"], 16)
    logs = []; b = lo
    while b <= hi:
        e = min(hi, b + 9999); logs += call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "address": V2F}]); b = e + 1
    cre = collections.OrderedDict()
    for l in logs:
        if len(l["topics"]) > 3: cre.setdefault(l["transactionHash"], (int(l["blockNumber"], 16), "0x" + l["topics"][2][-40:]))
    def one(item):
        txh, (b0_, cv_) = item
        ev = call("eth_getLogs", [{"fromBlock": hex(b0_), "toBlock": hex(b0_ + 12), "address": cv_, "topics": [BUY]}])
        ev.sort(key=lambda e: (int(e["blockNumber"], 16), int(e["logIndex"], 16)))
        X, Y = X0, Y0; tier = None; first_sur = None; sur_early = []; ex_early = 0
        for e in ev:
            dd = e["data"][2:]; w = [int(dd[i:i + 64], 16) / 1e18 for i in range(0, len(dd), 64)]; eth, tk = w[0], w[1]; blk = int(e["blockNumber"], 16) - b0_
            if tk <= 0 or tk >= Y or eth <= 0: continue
            net = X * tk / (Y - tk); X += net; Y -= tk; fee = 1 - net / eth
            if tier is None: tier = fee; continue
            if abs(fee - tier) <= 0.0008:
                if blk <= 5: ex_early += 1
            else:
                if first_sur is None: first_sur = (blk, fee)
                if blk <= 5: sur_early.append((blk, round(fee, 4)))
        return {"b0": b0_, "tier": tier, "first_sur": first_sur, "sur_early": sur_early, "ex_early": ex_early, "n": len(ev)}
    with cf.ThreadPoolExecutor(8) as ex: res = list(ex.map(one, list(cre.items())))
    res = [r for r in res if r["tier"] is not None]
    early = [r for r in res if r["sur_early"]]
    firsts = collections.Counter(min(r["first_sur"][0], 12) for r in res if r["first_sur"])
    print(f"\nB. {label}: {time.strftime('%b %d %H:%M', time.gmtime(t_lo))}-{time.strftime('%H:%M', time.gmtime(t_hi))} UTC, {len(res)} launches with a creation buy")
    print(f"   launches with an outsider (surcharged) buy landing in blocks 1-5: {len(early)} of {len(res)}")
    print(f"   first surcharged buy's block offset, count by offset: {dict(sorted(firsts.items()))}")
    if early:
        fees = collections.Counter(round(f - r['tier'], 3) for r in early for (_, f) in r['sur_early'])
        print(f"   surcharge over the tier on those early outsider buys (count): {dict(fees.most_common(5))}")
    return res
window("today (last 10 h)", head, 10)
window("two days ago (same-length window)", head - int(48 * 3600 * 9.9), 10)
