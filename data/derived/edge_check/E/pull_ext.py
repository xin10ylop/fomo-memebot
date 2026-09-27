"""pull_ext.py (edge_check/E): every Buy/Sell on the curve in blocks b0+641 .. b0+1240 for every launch of the population
(fit 563 + recent 172), so holds up to 1,200 blocks after the seat can be priced. One eth_getLogs per launch on the public
RPC, 4 threads at most, 0.15 s after every call, exponential back-off on 429 or any error. Checkpoints every 50 launches.
    python3 data/derived/edge_check/E/pull_ext.py > data/derived/edge_check/E/pull_ext.log"""
import sys, os, json, gzip, time, threading, urllib.request, urllib.error, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
OUT = c.EE + "tapes_ext.json.gz"; LO, HI = 641, c.EXT_HI
have = json.load(gzip.open(OUT, "rt")) if os.path.exists(OUT) else {}
RPC = "https://rpc.mainnet.chain.robinhood.com"; HDR = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 curl/8"}
lock = threading.Lock(); stats = {"429": 0, "err": 0}
def logs(cv, lo, hi):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [{"fromBlock": hex(lo), "toBlock": hex(hi), "address": cv, "topics": [[c.lv.BUY, c.lv.SELL]]}]}).encode()
    for attempt in range(8):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, data=body, headers=HDR), timeout=60)); time.sleep(0.15)
            if "error" in r: raise RuntimeError(str(r["error"])[:100])
            return r["result"]
        except urllib.error.HTTPError as e:
            with lock: stats["429" if e.code == 429 else "err"] += 1
            time.sleep(min(60, 2 ** attempt))
        except Exception as e:
            with lock: stats["err"] += 1
            time.sleep(min(60, 2 ** attempt))
    raise RuntimeError("gave up " + cv)
def one(r):
    b0 = r["b0"]; ev = logs(r["cv"], b0 + LO, b0 + HI)
    return r["cv"], {"b0": b0, "lo": b0 + LO, "hi": b0 + HI, "rows": sorted((c.lv.row_of(x) for x in ev), key=lambda x: (x["bn"], x["li"]))}
items = [r for r in c.load_all() if r["cv"] not in have]; t0 = time.time(); print("to pull:", len(items), flush=True)
with cf.ThreadPoolExecutor(4) as ex:
    for n, fut in enumerate(cf.as_completed([ex.submit(one, r) for r in items])):
        try: cv, X = fut.result(); have[cv] = X
        except Exception as e: print("FAILED", str(e)[:100], flush=True)
        if n % 50 == 49:
            json.dump(have, gzip.open(OUT, "wt")); print(n + 1, "of", len(items), f"{time.time()-t0:.0f} s", stats, flush=True)
json.dump(have, gzip.open(OUT, "wt")); print("extended tapes:", len(have), f"in {time.time()-t0:.0f} s", stats, "->", OUT, flush=True)
