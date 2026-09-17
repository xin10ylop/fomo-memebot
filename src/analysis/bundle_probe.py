"""chain probe: for every V2 creation in the last N minutes, the calldata's named wallets and, for creations naming 3+, the Buy
events on the curve in the next 40 blocks with each buyer's sender/to/selector: do the named wallets buy, directly, and when
(blocks after the creation)?"""
import json, urllib.request, time, sys, concurrent.futures as cf, collections
RPC = "https://robinhood-mainnet.g.alchemy.com/v2/" + __import__("os").environ["ALCHEMY_KEY"] + ""; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl/8"}
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; V2F = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"
MINUTES = float(sys.argv[1]) if len(sys.argv) > 1 else 25
def call(method, params, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(), headers=H)
            r = json.load(urllib.request.urlopen(req, timeout=60))
            if "error" in r: raise RuntimeError(r["error"])
            return r["result"]
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(1.5 * (i + 1))
head = int(call("eth_blockNumber", []), 16)
ts_head = int(call("eth_getBlockByNumber", [hex(head), False])["timestamp"], 16)
lo = head - 200
while True:
    t = int(call("eth_getBlockByNumber", [hex(lo), False])["timestamp"], 16)
    if ts_head - t >= MINUTES * 60 or lo < head - 200000: break
    lo -= max(200, int((MINUTES * 60 - (ts_head - t)) * 8))
print(f"head {head} ts {ts_head}; window from block {lo} ({(ts_head - t)/60:.1f} min, {head - lo} blocks, {(head-lo)/(ts_head-t):.1f} blocks/s)")
logs = []
b = lo
while b <= head:
    e = min(head, b + 9999); logs += call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "address": V2F}]); b = e + 1
creations = collections.OrderedDict()
for l in logs:
    creations.setdefault(l["transactionHash"], int(l["blockNumber"], 16))
print(f"creations in the window: {len(creations)}")
def named_of(tx):
    data = bytes.fromhex(tx["input"][2:]); sel = data[:4].hex(); words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
    creator = tx["from"].lower()
    quote = "0x" + data[4 + 32 * 2 + 12: 4 + 32 * 3].hex() if len(data) >= 4 + 32 * 4 else "0x" + "0" * 40
    named = {"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator, quote}
    return sel, creator, quote, named
def one(txh, b0):
    tx = call("eth_getTransactionByHash", [txh]); sel, creator, quote, named = named_of(tx)
    if len(named) < 3 or int(quote, 16) != 0:
        return {"tx": txh, "b0": b0, "sel": sel, "named": len(named), "pass": False}
    rec = call("eth_getTransactionReceipt", [txh])
    curve = next((l["address"].lower() for l in rec["logs"] if l["topics"][0] == BUY), None)
    if not curve:
        return {"tx": txh, "b0": b0, "sel": sel, "named": len(named), "pass": True, "curve": None}
    buys = call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(b0 + 40), "address": curve, "topics": [BUY]}])
    rows = []
    for l in buys:
        if l["transactionHash"] == txh: continue
        t = call("eth_getTransactionByHash", [l["transactionHash"]])
        rows.append({"blk": int(l["blockNumber"], 16) - b0, "from": t["from"].lower(), "to": (t["to"] or "").lower(), "sel": t["input"][:10], "eth": int(t["value"], 16) / 1e18,
                     "named": t["from"].lower() in named, "direct": (t["to"] or "").lower() == curve})
    blks = sorted({b0} | {b0 + r["blk"] for r in rows})
    tss = {bb: int(call("eth_getBlockByNumber", [hex(bb), False])["timestamp"], 16) for bb in blks[:12]}
    return {"tx": txh, "b0": b0, "sel": sel, "named": len(named), "pass": True, "curve": curve, "creator": creator, "rows": rows, "ts": tss}
out = []
with cf.ThreadPoolExecutor(8) as ex:
    for r in ex.map(lambda kv: one(*kv), list(creations.items())):
        out.append(r)
json.dump(out, open("bundle_probe.json", "w"))
P = [r for r in out if r.get("pass")]
print(f"calldata pre-check (3+ named, ETH quote) passed: {len(P)} of {len(out)}")
print("\nper launch: blocks after the creation of each named-wallet buy (d = direct call to the curve, r = via a contract), and the bundle's completion (3 named buys, 0.3 ETH)")
comp = []; direct_named = 0; total_named = 0; any_named = 0; first_named_blk = []; ts_lag = []
for r in P:
    if not r.get("curve"): print(f"  {r['tx'][:12]} no curve (no Buy in the creation tx)"); continue
    nm = [x for x in r["rows"] if x["named"]]; total_named += len(nm); direct_named += sum(x["direct"] for x in nm); any_named += bool(nm)
    k = 0; e = 0.0; tc = None
    for x in sorted(nm, key=lambda x: x["blk"]):
        k += 1; e += x["eth"]
        if k >= 3 and e >= 0.3 and tc is None: tc = x["blk"]
    comp.append(tc)
    if nm: first_named_blk.append(min(x["blk"] for x in nm))
    seq = " ".join(f"{x['blk']}{'d' if x['direct'] else 'r'}" for x in sorted(nm, key=lambda x: x["blk"])) or "-"
    oth = sum(1 for x in r["rows"] if not x["named"])
    sec = None
    if tc is not None and (r["b0"] + tc) in r["ts"]: sec = r["ts"][r["b0"] + tc] - r["ts"][r["b0"]]
    print(f"  {r['tx'][:12]} sel {r['sel']} named {r['named']:2d} | named buys at blocks: {seq:30s} | complete at block {str(tc):>4s} (+{sec if sec is not None else '?'} s) | other buys in 40 blocks: {oth}")
c = [x for x in comp if x is not None]
print(f"\nsummary: launches passing the calldata check {len(comp)}, with any named-wallet buy in 40 blocks {any_named}, bundle complete (3 buys, 0.3 ETH) {len(c)}")
if total_named: print(f"named-wallet buys: {total_named}, direct calls to the curve {direct_named} ({100*direct_named/total_named:.0f}%)")
if first_named_blk: print("first named buy, blocks after the creation:", collections.Counter(first_named_blk).most_common(12))
if c: print("bundle complete, blocks after the creation:", sorted(collections.Counter(c).items()))
