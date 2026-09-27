"""pull_shots.py (reviewer D): the ETH and gas of every transaction aimed at a launch's curve (to the curve, or naming it in the
calldata, as crowd_raw.py) in the creation second (blocks b0..b0+k) and the seat block (b0+k+1): crowd_raw keeps sender and
target but not the value. Per launch, per block offset: {fr, to, ix, value (ETH), gas, gp (gasPrice gwei), prio (maxPriorityFee
gwei), n_in (calldata bytes)}. Public RPC, 4 threads, batches of 4 blocks per post, 0.25 s after each post, backoff on 429/errors.
    python3 data/derived/edge_check/D/pull_shots.py            -> D/shots.json.gz"""
import sys, os, json, gzip, time, urllib.request, urllib.error, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 curl/8"}
OUT = c.DD + "shots.json.gz"; PART = c.DD + "shots_part.jsonl"
def post(p):
    for i in range(8):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, data=json.dumps(p).encode(), headers=H), timeout=90)); time.sleep(0.25); return r
        except urllib.error.HTTPError as e:
            time.sleep((5 if e.code == 429 else 2) * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    raise RuntimeError("rpc failed")
def one(r):
    cv = r["cv"]; b0, k = r["b0"], r["k"]; offs = list(range(0, k + 2)); blocks = {}
    for i in range(0, len(offs), 4):
        batch = [{"jsonrpc": "2.0", "id": o, "method": "eth_getBlockByNumber", "params": [hex(b0 + o), True]} for o in offs[i:i + 4]]
        for attempt in range(5):
            res = post(batch)
            if isinstance(res, list) and all(x.get("result") for x in res): break
            time.sleep(3 * (attempt + 1))
        else: raise RuntimeError(f"batch failed {cv}")
        for x in res:
            rows = []
            for t in x["result"]["transactions"]:
                to = (t.get("to") or "").lower(); data = t.get("input", "")
                if to == cv or cv[2:] in data:
                    rows.append({"fr": t["from"].lower(), "to": to, "ix": int(t["transactionIndex"], 16), "value": int(t.get("value", "0x0"), 16) / 1e18,
                                 "gas": int(t.get("gas", "0x0"), 16), "gp": int(t.get("gasPrice", "0x0"), 16) / 1e9,
                                 "prio": int(t["maxPriorityFeePerGas"], 16) / 1e9 if t.get("maxPriorityFeePerGas") else None, "n_in": (len(data) - 2) // 2})
            blocks[x["id"]] = rows
    return {"cv": cv, "b0": b0, "k": k, "blocks": [blocks[o] for o in offs]}
done = set()
if os.path.exists(PART):
    for line in open(PART): done.add(json.loads(line)["cv"])
items = [r for r in c.all_records() if r["cv"] not in done]; t0 = time.time(); n = 0
with cf.ThreadPoolExecutor(4) as ex, open(PART, "a") as f:
    for res in ex.map(lambda r: (r, (lambda: one(r))()), items):
        r, x = res; f.write(json.dumps(x) + "\n"); f.flush(); n += 1
        if n % 50 == 0: print(n, "of", len(items), f"{time.time()-t0:.0f}s", flush=True)
allx = [json.loads(l) for l in open(PART)]
json.dump(allx, gzip.open(OUT, "wt")); print("wrote", OUT, len(allx), f"{time.time()-t0:.0f}s")
