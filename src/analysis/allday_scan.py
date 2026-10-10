"""(Oct 9, the owner's question "is the profile hiding launches?"; imports the exit study's simulator from the session scratchpad.)
Every launch the factory created in a window (not only the readings' qualifying profile), priced the way the sniper trades:
first in the seat block (E1), $75, hold 11 blocks, 2-block execution (the exit study's simulator); and as the runner trades (behind
one, tp30/stop30/300). Each launch tagged with why the profile would refuse it. Usage: allday.py FROM_UTC TO_UTC OUT.json"""
import sys, os, json, time, calendar, collections, concurrent.futures as cf, urllib.request
sys.path.insert(0, "/home/user/fomo-memebot/src/analysis"); sys.path.insert(0, "/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad/growth/exit")
import sim, rules as R
URL = os.environ["ALCHEMY_READ_URL"]; PUB = "https://rpc.mainnet.chain.robinhood.com"
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
V2F = None
for line in open("/home/user/fomo-memebot/src/analysis/e1_multi.py"):
    if 'V2F = "' in line: V2F = line.split('V2F = "')[1].split('"')[0]; break
def post(payload, url=URL, tries=6):
    for i in range(tries):
        try:
            r = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"content-type": "application/json", "User-Agent": "Mozilla/5.0"})
            return json.load(urllib.request.urlopen(r, timeout=30))
        except Exception as e:
            err = e; time.sleep(1.0 * (i + 1))
    raise err
def call(m, p, url=URL):
    d = post({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}, url)
    if "error" in d: raise RuntimeError(str(d["error"])[:120])
    return d["result"]
FROM, TO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
BLO = int(FROM[2:]) if FROM.startswith("b:") else None; BHI = int(TO[2:]) if TO.startswith("b:") else None   # 5bm: "b:84446548" "b:84446554" prices the creations of a block range (the time estimate drifts by minutes over a day)
if BLO is None: t_from = calendar.timegm(time.strptime(FROM, "%Y-%m-%d %H:%M")); t_to = calendar.timegm(time.strptime(TO, "%Y-%m-%d %H:%M"))
head = int(call("eth_blockNumber", []), 16); th = int(call("eth_getBlockByNumber", [hex(head), False])["timestamp"], 16)
lo = BLO if BLO is not None else head - int((th - t_from) * 9.9) - 200; hi = BHI if BHI is not None else head - int(max(0, th - t_to) * 9.9) - 650   # leave 650 blocks after the window for the tapes
logs = []; b = lo
while b <= hi:
    e = min(hi, b + 9999); logs += call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "address": V2F}], PUB); b = e + 1
cre = collections.OrderedDict()
for l in logs:
    if len(l["topics"]) > 3: cre.setdefault(l["transactionHash"], (int(l["blockNumber"], 16), "0x" + l["topics"][2][-40:], "0x" + l["topics"][3][-40:]))
print(f"{len(cre)} creations in blocks {lo}..{hi}", flush=True)
def one(item):
    txh, (b0, cv, creator) = item
    try:
        tx = call("eth_getTransactionByHash", [txh]); data = bytes.fromhex(tx["input"][2:]); sel = data[:4].hex()
        words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
        rec = {"cv": cv, "b0": b0, "creator": creator, "sel": sel}
        if sel != "f85f8e41" or len(words) < 14: rec["why"] = "other creation call"; return rec
        quote = int.from_bytes(words[2], "big"); named = {"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator}
        tbw = int.from_bytes(words[13], "big"); tb = tbw if tbw <= 2000 else None
        rec.update({"named": len(named), "tax_bps": tb, "quote_eth": quote == 0})
        ev = call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(b0 + 640), "address": cv, "topics": [[BUY, SELL]]}], PUB)
        ev.sort(key=lambda e: (int(e["blockNumber"], 16), int(e["logIndex"], 16)))
        rows = []
        for e in ev:
            d = e["data"][2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]; isb = e["topics"][0] == BUY
            rows.append({"bn": int(e["blockNumber"], 16), "k": "B" if isb else "S", "eth": w[0] if isb else w[1], "tk": w[1] if isb else w[0],
                         "who": ("0x" + e["topics"][2][-40:]) if len(e["topics"]) > 2 else None, "li": int(e["logIndex"], 16), "ti": int(e["transactionIndex"], 16)})
        rec["buys"] = sum(1 for r in rows if r["k"] == "B"); rec["buy_eth_12s"] = round(sum(r["eth"] for r in rows if r["k"] == "B" and r["bn"] <= b0 + 120), 4)
        rec["buyers_12s"] = len({r["who"] for r in rows if r["k"] == "B" and r["bn"] <= b0 + 120})
        if not rows or rows[0]["k"] != "B" or rows[0]["bn"] != b0: rec["why"] = rec.get("why") or "no creator buy in the creation block"
        if quote != 0: rec["why"] = rec.get("why") or "quote not ETH"
        if tb is None: rec["why"] = rec.get("why") or "tax word unreadable"
        if not rows: return rec
        st = post([{"jsonrpc": "2.0", "id": n, "method": "eth_getBlockByNumber", "params": [hex(n), False]} for n in range(b0, b0 + 25)])
        ts = {x["id"]: int(x["result"]["timestamp"], 16) for x in st if x.get("result")}
        T0 = ts.get(b0); bE1 = next((n for n in range(b0 + 1, b0 + 25) if ts.get(n, 0) == T0 + 1), None)
        if bE1 is None: rec["why"] = rec.get("why") or "no seat block found"; return rec
        k = bE1 - b0 - 1; tier = 0.01 + (tb or 0) / 10000.0
        # the team's exempt (bundle) ETH in the creation second, as e1_multi measures it
        X, Y = sim.X0, sim.Y0; bundle = 0.0
        for i, r in enumerate(rows):
            if ts.get(r["bn"], 9e18) != T0: break
            if r["k"] == "B" and 0 < r["tk"] < Y:
                net = X * r["tk"] / (Y - r["tk"]); fee = 1 - net / r["eth"] if r["eth"] else 1
                if i > 0 and abs(fee - tier) <= 0.0008: bundle += r["eth"]
                X, Y = X + net, Y - r["tk"]
            elif r["k"] == "S": X, Y = X - X * r["tk"] / (Y + r["tk"]), Y + r["tk"]
        rec.update({"k": k, "tier": tier, "bundle_eth": round(bundle, 4), "T0": T0})
        prof = []
        if len(named) < 3: prof.append("fewer than 3 team wallets")
        if bundle < 0.3: prof.append("team bundle under 0.3 ETH")
        rec["profile_fail"] = prof
        rec["tier_class"] = "untaxed" if (tb or 0) < 100 else ("sniper 1-3%" if tb <= 300 else "over 3%")
        L = {"rows": rows, "ts": ts, "tier": tier, "T0": T0, "b0": b0}
        for nah, rule, key in ((0, R.hold(11), "first_h11"), (1, None, "runner_b1")):
            E = sim.entry(L, 75 / 2700.0, bE1, nah)
            if rule is None:
                def p(s, _t=0.3, _s=0.3, _c=300):
                    if s["mark"] <= -_s: return (1.0, "stop")
                    if s["mark"] >= _t: return (1.0, "tp")
                    if s["rel"] >= _c - s["dl"]: return (1.0, "cap")
                rule = p
            rec[key] = round(sim.run(E, rule, bE1 + 630, 2)[0], 4)
        return rec
    except Exception as e:
        return {"cv": cv, "b0": b0, "err": str(e)[:100]}
out = []
with cf.ThreadPoolExecutor(5) as ex:
    for i, r in enumerate(ex.map(one, list(cre.items()))):
        out.append(r)
        if i % 100 == 0: print(i, flush=True)
json.dump(out, open(OUT, "w")); print("saved", len(out), flush=True)
