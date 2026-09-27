"""pull_tapes.py (edge_check/A): the Buy/Sell tape of every rule fire (fleets >= 2 at k-2) of the fit and recent windows,
b0 .. b0+640 (holds to 600 blocks after the seat), block stamps b0..b0+30, the launch's tier; cached to tapes.json.gz so all
pricing is offline. Public RPC only, 4 threads; live_vs_table's call()/post() pace (0.25 s after each call) and retry with
backoff (2, 4, 6 ... s) on any HTTP error including 429.
    python3 data/derived/edge_check/A/pull_tapes.py"""
import sys, os, json, gzip, time, concurrent.futures as cf
sys.path.insert(0, "src/analysis"); sys.path.insert(0, "data/derived/edge_check/A")
import live_vs_table as lv
from common import *
OUT = A + "tapes.json.gz"; HI = 640
have = json.load(gzip.open(OUT, "rt")) if os.path.exists(OUT) else {}
items = [r for r in all_launches(FIT + REC) if is_fire(r)]
extra = sys.argv[1:]            # optional: more curve addresses (b0 looked up from the crowd files)
if extra:
    byc = {r["cv"]: r for r in all_launches(FIT + REC)}; items += [byc[c] for c in extra if c in byc]
items = [r for r in items if r["cv"] not in have]
def one(r):
    cv, b0 = r["cv"], r["b0"]
    for attempt in range(4):
        try:
            L = lv.launch(cv, b0 + 12)
            if L is None: return cv, None
            time.sleep(0.15)
            more = lv.call("eth_getLogs", [{"fromBlock": hex(b0 + 121), "toBlock": hex(b0 + HI), "address": cv, "topics": [[lv.BUY, lv.SELL]]}])
            L["rows"] = sorted(L["rows"] + [lv.row_of(x) for x in more], key=lambda x: (x["bn"], x["li"]))
            L["ts"] = {str(k): v for k, v in L["ts"].items()}; L["hi"] = b0 + HI
            return cv, L
        except Exception as e:
            print("retry", cv[:10], str(e)[:80], flush=True); time.sleep(3 * (attempt + 1))
    return cv, None
t0 = time.time()
with cf.ThreadPoolExecutor(4) as ex:
    for n, (cv, L) in enumerate(ex.map(one, items)):
        if L is not None: have[cv] = L
        else: print("FAILED", cv, flush=True)
        if n % 10 == 0: print(n, "of", len(items), f"{time.time()-t0:.0f} s", flush=True)
json.dump(have, gzip.open(OUT, "wt")); print("tapes:", len(have), f"in {time.time()-t0:.0f} s ->", OUT)
