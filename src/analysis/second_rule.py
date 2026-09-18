"""is the 98% tax a same-second rule? block timestamps around our launch, and across today's early outsider buys:
surcharge vs whether the buy's block shares the creation block's timestamp."""
import json, urllib.request, time, collections, concurrent.futures as cf
import os; RPC = "https://robinhood-mainnet.g.alchemy.com/v2/" + os.environ["ALCHEMY_KEY"]; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl/8"}
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; V2F = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"; X0, Y0 = 1.68, 1e9
def call(m, p, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers=H)
            r = json.load(urllib.request.urlopen(req, timeout=60))
            if "error" in r: raise RuntimeError(r["error"])
            return r["result"]
        except Exception:
            if i == tries - 1: raise
            time.sleep(1.5 * (i + 1))
b0 = 66126811
ts = {k: int(call("eth_getBlockByNumber", [hex(b0 + k), False])["timestamp"], 16) for k in range(0, 9)}
print("our launch, block timestamp by offset:", {k: v - ts[0] for k, v in ts.items()}, "(seconds after the creation block's timestamp)")
head = int(call("eth_blockNumber", []), 16) - 30; lo = head - int(10 * 3600 * 9.9)
logs = []; b = lo
while b <= head:
    e = min(head, b + 9999); logs += call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "address": V2F}]); b = e + 1
cre = collections.OrderedDict()
for l in logs:
    if len(l["topics"]) > 3: cre.setdefault(l["transactionHash"], (int(l["blockNumber"], 16), "0x" + l["topics"][2][-40:]))
tscache = {}
def tstamp(n):
    if n not in tscache: tscache[n] = int(call("eth_getBlockByNumber", [hex(n), False])["timestamp"], 16)
    return tscache[n]
def one(item):
    txh, (b0_, cv_) = item
    ev = call("eth_getLogs", [{"fromBlock": hex(b0_), "toBlock": hex(b0_ + 12), "address": cv_, "topics": [BUY]}])
    ev.sort(key=lambda e: (int(e["blockNumber"], 16), int(e["logIndex"], 16)))
    X, Y = X0, Y0; tier = None; out = []
    for e in ev:
        dd = e["data"][2:]; w = [int(dd[i:i + 64], 16) / 1e18 for i in range(0, len(dd), 64)]; eth, tk = w[0], w[1]; bn = int(e["blockNumber"], 16)
        if tk <= 0 or tk >= Y or eth <= 0: continue
        net = X * tk / (Y - tk); X += net; Y -= tk; fee = 1 - net / eth
        if tier is None: tier = fee; continue
        if abs(fee - tier) > 0.0008 and bn - b0_ <= 9: out.append((bn - b0_, round(fee - tier, 3), bn))
    return b0_, out
with cf.ThreadPoolExecutor(8) as ex: res = list(ex.map(one, list(cre.items())))
rows = [(b0_, k, s, bn) for b0_, out in res for (k, s, bn) in out]
print(f"today: {len(rows)} surcharged buys within 9 blocks of a creation, on {sum(1 for _, o in res if o)} launches; reading their block timestamps...")
need = sorted({n for r in rows for n in (r[0], r[3])})
with cf.ThreadPoolExecutor(8) as ex: list(ex.map(tstamp, need))
tab = collections.Counter()
for b0_, k, s, bn in rows:
    same = tstamp(bn) == tstamp(b0_); cls = "98% tax" if s > 0.5 else ("6.2% surcharge" if abs(s - 0.062) < 0.01 else f"other {s}")
    tab[(cls, "same second as creation" if same else "later second")] += 1
for k, v in sorted(tab.items(), key=lambda x: -x[1]): print(f"   {v:5d}  {k[0]:16s} {k[1]}")
