"""pull_tapes.py (edge_check/C): the Buy/Sell tape b0..b0+640 of every launch of the fit and recent crowd files that has no tape
in round 1's caches (B/tapes/, A/tapes*.json.gz): in practice the 85 sep2223 launches B could not pull. Real block stamps
(live_vs_table.launch), the tier from the creation. Public RPC only, 4 threads, 0.15 s between calls (plus live_vs_table.call's
own 0.25 s pause), exponential back-off on any error including 429. Output: C/tapes_extra.json.gz.
    python3 data/derived/edge_check/C/pull_tapes.py"""
import sys, os, json, gzip, time, concurrent.futures as cf
sys.path.insert(0, "src/analysis"); sys.path.insert(0, "data/derived/edge_check/C")
import live_vs_table as lv
from common import load_all, have_tape, C
OUT = C + "tapes_extra.json.gz"; HI = 640
have = json.load(gzip.open(OUT, "rt")) if os.path.exists(OUT) else {}
items = [r for r in load_all() if not have_tape(r["cv"]) and r["cv"] not in have]
print("to pull:", len(items), flush=True)
def one(r):
    cv, b0 = r["cv"], r["b0"]
    for attempt in range(6):
        try:
            L = lv.launch(cv, b0 + 12); time.sleep(0.15)
            if L is None: return cv, None
            more = lv.call("eth_getLogs", [{"fromBlock": hex(b0 + 121), "toBlock": hex(b0 + HI), "address": cv, "topics": [[lv.BUY, lv.SELL]]}]); time.sleep(0.15)
            L["rows"] = sorted(L["rows"] + [lv.row_of(x) for x in more], key=lambda x: (x["bn"], x["li"]))
            L["ts"] = {str(k): v for k, v in L["ts"].items()}; L["hi"] = b0 + HI
            return cv, L
        except Exception as e:
            w = 2 ** attempt; print("retry", cv[:10], str(e)[:80], f"sleep {w}s", flush=True); time.sleep(w)
    return cv, None
t0 = time.time()
with cf.ThreadPoolExecutor(4) as ex:
    for n, (cv, L) in enumerate(ex.map(one, items)):
        if L is not None: have[cv] = L
        else: print("FAILED", cv, flush=True)
        if n % 10 == 0: print(n, "of", len(items), f"{time.time()-t0:.0f} s", flush=True)
json.dump(have, gzip.open(OUT, "wt")); print("tapes:", len(have), f"in {time.time()-t0:.0f} s ->", OUT)
