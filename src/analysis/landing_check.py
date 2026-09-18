"""landing_check.py: where did each live buy land, against the second rule and the other buys of its block?

    ALCHEMY_KEY=... python3 src/analysis/landing_check.py 0xhash [0xhash ...]
    ALCHEMY_KEY=... python3 src/analysis/landing_check.py --log /var/log/sniper/engine.jsonl

For every buy hash: the receipt (status, block, index), the curve's creation block and the block timestamps, so the buy is
classed as `creation second` (98% tax, reverts on the minOut), `first block of the next second` (the E1 seat), `later block of
the next second`, or `second two or later`; then the other buys of the curve in the same block, before and after ours, with
their surcharge class. "first in the block" is the position the honest E1 table pays +8-20% for (report 24.19)."""
import os, sys, json, urllib.request, time
RPC = os.environ.get("RPC_URL") or ("https://robinhood-mainnet.g.alchemy.com/v2/" + os.environ["ALCHEMY_KEY"])
H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/landing"}
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; V2F = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"; X0, Y0 = 1.68, 1e9
def call(m, p, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers=H)
            r = json.load(urllib.request.urlopen(req, timeout=60))
            if "error" in r: raise RuntimeError(r["error"])
            return r["result"]
        except Exception:
            if i == tries - 1: raise
            time.sleep(1.5 * (i + 1))
def ts_of(n): return int(call("eth_getBlockByNumber", [hex(n), False])["timestamp"], 16)
def check(h):
    tx = call("eth_getTransactionByHash", [h]); rc = call("eth_getTransactionReceipt", [h])
    if not tx or not rc: print(f"{h[:12]}: not found"); return
    cv = tx["to"].lower(); bl = int(rc["blockNumber"], 16); idx = int(rc["transactionIndex"], 16); ok = rc["status"] == "0x1"
    # the creation block: the factory's creation event that names this curve, searched backwards
    b0 = None
    for lo in (bl - 120, bl - 1200, bl - 12000):
        ev = call("eth_getLogs", [{"fromBlock": hex(max(0, lo)), "toBlock": hex(bl), "address": V2F, "topics": [None, None, "0x" + "0" * 24 + cv[2:]]}])
        if ev: b0 = int(ev[0]["blockNumber"], 16); break
    if b0 is None: print(f"{h[:12]}: creation block not found"); return
    T0, Tb = ts_of(b0), ts_of(bl)
    # first block of each second after the creation
    first_next = None; n = b0 + 1
    while n <= bl + 20:
        if ts_of(n) == T0 + 1: first_next = n; break
        n += 1
    if Tb == T0: where = "creation second (98% tax: the minOut reverts it, gas only)"
    elif Tb == T0 + 1: where = "FIRST block of the next second (the E1 seat)" if bl == first_next else f"next second, block {bl - first_next + 1} of it (one or more blocks late)"
    else: where = f"second +{Tb - T0} after the creation (E2 or later, +0.19%)"
    # the other buys of the curve in our block, by log order against our index, with their surcharge class
    ev = call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(bl), "address": cv, "topics": [BUY]}])
    ev.sort(key=lambda e: (int(e["blockNumber"], 16), int(e["logIndex"], 16)))
    X, Y = X0, Y0; tier = None; before = []; after = []
    for e in ev:
        d = e["data"][2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]; eth, tk = w[0], w[1]; ebl = int(e["blockNumber"], 16); eidx = int(e["transactionIndex"], 16)
        if tk <= 0 or tk >= Y or eth <= 0: continue
        net = X * tk / (Y - tk); fee = 1 - net / eth; X += net; Y -= tk
        if tier is None: tier = fee; continue
        if ebl == bl and e["transactionHash"].lower() not in OURS:          # the other shots of our own burst are not "others"
            cls = "exempt" if abs(fee - tier) <= 0.0008 else ("98%" if fee - tier > 0.5 else f"+{100 * (fee - tier):.1f}%")
            (before if eidx < idx else after).append(f"idx {eidx} {eth:.3f} ETH {cls}")
    gas = int(rc["gasUsed"], 16) * int(rc.get("effectiveGasPrice", tx.get("gasPrice", "0x0")), 16) / 1e18
    print(f"{h[:12]}  curve {cv[:10]}  {'OK' if ok else 'REVERTED'}  block +{bl - b0} after the creation, index {idx}, gas {gas:.6f} ETH")
    print(f"    landed in: {where}")
    print(f"    other buys of this curve in our block: {len(before)} before us [{', '.join(before)}], {len(after)} after us [{', '.join(after)}]")
    print(f"    verdict: {'FIRST IN THE BLOCK' if not before and Tb == T0 + 1 and bl == first_next else ('reverted' if not ok else 'not first')}")
OURS = set()
hashes = [a for a in sys.argv[1:] if a.startswith("0x")]
if "--log" in sys.argv:
    for l in open(sys.argv[sys.argv.index("--log") + 1]):
        try: e = json.loads(l)
        except Exception: continue
        if e.get("ev") == "buy_reverted" and e.get("hash"): hashes.append(e["hash"])
        if e.get("ev") == "trade_done" and not e.get("dry_run") and e.get("buy_hash"): hashes.append(e["buy_hash"])
        if e.get("ev") == "burst_landing": hashes += [sh["hash"] for sh in e.get("shots", []) if sh.get("hash") and sh.get("block") is not None]   # every included shot of a burst
OURS.update(x.lower() for x in hashes)
for h in dict.fromkeys(hashes): check(h)
if not hashes: print("no buy hashes (pass them, or --log engine.jsonl)")
