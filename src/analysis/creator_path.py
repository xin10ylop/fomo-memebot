"""who sends the creation transaction of the launches the rule trades: the factory directly (the engine's feed decoder sees it)
or another contract (invisible to the feed); with the seat's return on each class (cached per curve in creator_path_cache.json)"""
import sys, json, urllib.request, collections, time, glob, os, statistics as st
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl/8"}
FACTORY = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"; SELS = {"0xf85f8e41", "0x3f707e6b"}; PX = RH.PX
def call(m, p, tries=5):
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers=H), timeout=120))["result"]
        except Exception:
            time.sleep(2 * (i + 1))
    return None
txs = {}
for f in glob.glob("rh/creates_v2_*.jsonl"):
    for line in open(f):
        b, tx, topics, data = json.loads(line)
        if len(topics) >= 4: txs["0x" + topics[2][-40:].lower()] = tx
cache = json.load(open("creator_path_cache.json")) if os.path.exists("creator_path_cache.json") else {}
data = RH.load(); data.update(RH.load_new())
rows = []; n = 0
for k in sorted(data):
    for cv, (L, f) in data[k].items():
        kept = f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)
        if not kept or cv not in txs: continue
        if cv not in cache:
            t = call("eth_getTransactionByHash", [txs[cv]])
            if t is None: continue
            cache[cv] = [t["to"].lower(), t["input"][:10]]; n += 1
            if n % 100 == 0: json.dump(cache, open("creator_path_cache.json", "w")); print("fetched", n, file=sys.stderr, flush=True)
        to, sel = cache[cv]; direct = to == FACTORY and sel in SELS
        x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5); roi = (x[0] * PX - 0.10) / (x[1] * PX) if x[1] > 1e-6 else 0.0
        rows.append((k, "factory direct" if direct else f"via {to[:10]} {sel}", roi))
json.dump(cache, open("creator_path_cache.json", "w"))
print(f"{'window':22s} {'kept':>5s} {'factory direct':>15s} {'via other contracts':>20s}")
for k in sorted(set(r[0] for r in rows)):
    xs = [r for r in rows if r[0] == k]; d = [r for r in xs if r[1] == "factory direct"]; o = [r for r in xs if r[1] != "factory direct"]
    print(f"{k[0]} {k[1]:6s}      {len(xs):5d} {len(d):5d} {100*st.mean(r[2] for r in d) if d else 0:+6.1f}% {len(o):6d} {100*st.mean(r[2] for r in o) if o else 0:+6.1f}%")
d = [r[2] for r in rows if r[1] == "factory direct"]; o = [r[2] for r in rows if r[1] != "factory direct"]
print(f"\nall kept launches: {len(rows)}; factory direct {len(d)} ({100*len(d)/len(rows):.0f}%) mean {100*st.mean(d):+.1f}%; via other contracts {len(o)} ({100*len(o)/len(rows):.0f}%) mean {100*st.mean(o):+.1f}%" if o else f"\nall kept launches: {len(rows)}, all factory direct")
print("other contracts:", dict(collections.Counter(r[1] for r in rows if r[1] != "factory direct")))
