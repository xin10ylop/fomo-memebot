"""pull_ext.py (edge_check/G): every Buy/Sell on the curve in blocks b0+641..b0+1250 for all 735 launches (the cached tapes stop at
b0+640), so holds up to 1,200 blocks after E1 (E1 <= b0+10) are priced on the full tape. Public RPC only, 4 threads, 0.15 s between
calls (plus live_vs_table.call's own 0.25 s), exponential back-off on any error including 429. Output G/tapes_ext.json.gz
({cv: rows}); re-running resumes.
    python3 data/derived/edge_check/G/pull_ext.py"""
import sys, os, json, gzip, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
import concurrent.futures as cfu
OUT = G + "tapes_ext.json.gz"
have = json.load(gzip.open(OUT, "rt")) if os.path.exists(OUT) else {}
head = int(lv.call("eth_blockNumber", []), 16)
items = [r for r in load_all() if r["cv"] not in have]
print("to pull:", len(items), "head", head, flush=True)
def one(r):
    cv, b0 = r["cv"], r["b0"]
    if b0 + EXT_HI > head: return cv, None
    for attempt in range(7):
        try:
            ev = lv.call("eth_getLogs", [{"fromBlock": hex(b0 + TAPE_HI + 1), "toBlock": hex(b0 + EXT_HI), "address": cv, "topics": [[lv.BUY, lv.SELL]]}]); time.sleep(0.15)
            return cv, sorted((lv.row_of(x) for x in ev), key=lambda x: (x["bn"], x["li"]))
        except Exception as e:
            w = 2 ** attempt; print("retry", cv[:10], str(e)[:80], f"sleep {w}s", flush=True); time.sleep(w)
    return cv, None
t0 = time.time()
import concurrent.futures as cfu
with cfu.ThreadPoolExecutor(4) as ex:
    for n, (cv, rows) in enumerate(ex.map(one, items)):
        if rows is not None: have[cv] = rows
        else: print("FAILED", cv, flush=True)
        if n % 50 == 0: print(n, "of", len(items), f"{time.time()-t0:.0f} s", flush=True)
json.dump(have, gzip.open(OUT, "wt")); print("extensions:", len(have), f"in {time.time()-t0:.0f} s ->", OUT)
