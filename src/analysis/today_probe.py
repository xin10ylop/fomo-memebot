"""today's launches in the cache's row format, from the chain: for every V2 creation in the last N minutes, the tier and named
wallets from the calldata, every Buy/Sell on the curve for 40 blocks, the bundle (exempt buys within a second) with its block
offset and whether each bundle buy went through a helper contract; then the creation-second seat scored on them."""
import json, urllib.request, time, sys, concurrent.futures as cf, collections, statistics as st
RPC = "https://robinhood-mainnet.g.alchemy.com/v2/" + __import__("os").environ["ALCHEMY_KEY"] + ""; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl/8"}
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"; V2F = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"
X0, Y0 = 1.68, 1e9
MINUTES = float(sys.argv[1]) if len(sys.argv) > 1 else 120
def call(method, params, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(), headers=H)
            r = json.load(urllib.request.urlopen(req, timeout=60))
            if "error" in r: raise RuntimeError(r["error"])
            return r["result"]
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(1.5 * (i + 1))
head = int(call("eth_blockNumber", []), 16) - 60
ts_head = int(call("eth_getBlockByNumber", [hex(head), False])["timestamp"], 16)
lo = head - int(MINUTES * 60 * 9.9)
t_lo = int(call("eth_getBlockByNumber", [hex(lo), False])["timestamp"], 16)
print(f"window: blocks {lo}-{head}, {(ts_head - t_lo)/60:.0f} min, {time.strftime('%H:%M', time.gmtime(t_lo))}-{time.strftime('%H:%M', time.gmtime(ts_head))} UTC")
logs = []; b = lo
while b <= head:
    e = min(head, b + 9999); logs += call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "address": V2F}]); b = e + 1
cre = collections.OrderedDict()
for l in logs:
    if len(l["topics"]) > 3: cre.setdefault(l["transactionHash"], (int(l["blockNumber"], 16), "0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:], "0x" + l["topics"][3][-40:]))
print("creations:", len(cre))
def one(txh, b0, tok, cv, creator):
    tx = call("eth_getTransactionByHash", [txh]); data = bytes.fromhex(tx["input"][2:]); sel = data[:4].hex()
    words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
    quote = "0x" + data[4 + 32 * 2 + 12: 4 + 32 * 3].hex() if len(data) >= 4 + 32 * 4 else "0x" + "0" * 40
    named = {"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator, quote}
    tb = int.from_bytes(words[13], "big") if sel == "f85f8e41" and len(words) > 13 and int.from_bytes(words[13], "big") <= 2000 else None
    tier = 0.01 + (tb or 0) / 10000.0
    ev = call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(b0 + 40), "address": cv, "topics": [[BUY, SELL]]}])
    ev.sort(key=lambda e: (int(e["blockNumber"], 16), int(e["logIndex"], 16)))
    X, Y = X0, Y0; rows = []; meta = []
    for e in ev:
        d = e["data"][2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]; buy = e["topics"][0] == BUY; blk = int(e["blockNumber"], 16) - b0
        if buy:
            eth, tk = w[0], w[1]
            if tk <= 0 or tk >= Y: continue
            net = X * tk / (Y - tk); X += net; Y -= tk; fee = 1 - net / eth if eth > 0 else 0.0
            rows.append((0.1 * blk, "B", eth, tk, net, fee)); meta.append((e["transactionHash"], blk, "0x" + e["topics"][2][-40:].lower() if len(e["topics"]) > 2 else None))
        else:
            tk, eth = w[0], w[1]
            g = X * tk / (Y + tk); X -= g; Y += tk
            rows.append((0.1 * blk, "S", eth, tk, g, 0.0)); meta.append((e["transactionHash"], blk, None))
    if not rows or rows[0][1] != "B" or meta[0][0] != txh:
        return {"tx": txh, "b0": b0, "ok": False, "why": "no creation buy first"}
    # the bundle: exempt buys (fee within 8 bps of the tier) within the first second after the creator's buy; helper or direct per tx
    bundle = []
    for (r, m) in list(zip(rows, meta))[1:]:
        if r[1] == "B" and r[0] < 1.0 and abs(r[5] - tier) <= 0.0008:
            t = call("eth_getTransactionByHash", [m[0]]); bundle.append({"blk": m[1], "eth": r[2], "from": t["from"].lower(), "to": (t["to"] or "").lower(), "direct": (t["to"] or "").lower() == cv, "named": t["from"].lower() in named, "buyer_topic": m[2]})
    return {"tx": txh, "b0": b0, "ok": True, "tier": tier, "tax_bps": tb, "named": len(named), "quote_eth": int(quote, 16) == 0, "tk0": rows[0][3], "rows": rows, "bundle": bundle, "creator": creator, "curve": cv, "ts": t_lo + (b0 - lo) / 9.9}
out = []
with cf.ThreadPoolExecutor(8) as ex:
    for r in ex.map(lambda kv: one(kv[0], *kv[1]), list(cre.items())):
        out.append(r)
json.dump(out, open("today_probe.json", "w"))
ok = [r for r in out if r["ok"]]
print(f"scored launches: {len(ok)} of {len(out)}")
def complete(b, n=3, eth=0.3):
    k = 0; e = 0.0
    for x in sorted(b, key=lambda x: x["blk"]):
        k += 1; e += x["eth"]
        if k >= n and e >= eth: return x["blk"]
    return None
B = [r for r in ok if complete(r["bundle"]) is not None and r["tk0"] >= 0.01 * Y0 and r["quote_eth"]]
print(f"bundled (3 exempt buys, 0.3 ETH, within 1 s; creator >= 1%; ETH quote): {len(B)} = {60*len(B)/MINUTES:.1f}/h; of them 2-3% tier: {sum(1 for r in B if r['tax_bps'] in (100, 200) or (r['tax_bps'] or 0) in range(100, 201))}")
print("bundle complete at block offset:", sorted(collections.Counter(complete(r["bundle"]) for r in B).items()))
hb = [r for r in B if any(not x["direct"] for x in r["bundle"])]; nb = [r for r in B if all(x["named"] for x in r["bundle"])]
print(f"bundles with at least one buy through a helper contract: {len(hb)}; bundles where every buy's sender is a calldata-named wallet: {len(nb)}; calldata named 3+: {sum(1 for r in B if r['named'] >= 3)}")
print("named wallets on the bundled launches:", sorted(collections.Counter(r["named"] for r in B).items()))
print("bundle ETH median:", round(st.median(sum(x["eth"] for x in r["bundle"]) for r in B), 3) if B else None)
sys.path.insert(0, "."); 
exec(open("e0_optimize.py").read().split('periods = [')[0].replace('exec(open("e0_seat.py").read().split(\'print("=== the creation second\')[0])', 'import datetime\nPX = 2430.0\ndata = {}'))
for tier_only in (False, True):
    Ls = [{"tier": r["tier"], "rows": r["rows"], "ts": r["ts"]} for r in B if (not tier_only) or 100 <= (r["tax_bps"] or 0) <= 200]
    if not Ls: print("no launches" if tier_only else ""); continue
    line = f"  {'2-3% tier' if tier_only else 'all tiers':10s} n {len(Ls):3d}:"
    for ta in (0.2, 0.3, 0.4, 0.5):
        rs = [e0x(L, t_after=ta, hold=1.5, tp=None, stake=10)[0] for L in Ls]
        line += f"  entry {ta} s mean {100*st.mean(rs):+6.1f}% median {100*st.median(rs):+6.1f}% win {100*sum(v>0 for v in rs)/len(rs):3.0f}% |"
    print(line)
print("\nper bundled launch: tax_bps, named, bundle buys (block:d/r), ETH, e0 at 0.3 s")
for r in B:
    seq = " ".join(f"{x['blk']}{'d' if x['direct'] else 'r'}" for x in sorted(r["bundle"], key=lambda x: x["blk"]))
    print(f"  {r['tx'][:12]} {time.strftime('%H:%M', time.gmtime(r['ts']))} tax {str(r['tax_bps']):>4s} named {r['named']:2d} | {seq:40s} | {sum(x['eth'] for x in r['bundle']):.3f} ETH | e0@0.3 {100*e0x({'tier': r['tier'], 'rows': r['rows'], 'ts': r['ts']}, t_after=0.3, hold=1.5, tp=None, stake=10)[0]:+6.1f}%")
