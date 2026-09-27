"""pull_ext.py (edge_check/F): extends every launch's tape from b0+640 to b0+1240 (one eth_getLogs per launch: every Buy/Sell on the
curve b0+641..b0+1240), so holds reach 1,200 blocks after the seat; and re-pulls b0..b0+640 on a seeded sample of 40 launches to
check the cached tapes against the chain event by event. Public RPC only, 4 threads, 0.15 s between calls per thread (plus
live_vs_table.call's own 0.25 s), exponential back-off (2, 4, 8 .. 64 s) on any error including 429.
    python3 data/derived/edge_check/F/pull_ext.py > data/derived/edge_check/F/pull_ext.txt"""
import sys, os, json, gzip, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
import concurrent.futures as cfu
OUT = F + "ext.json.gz"; LO, HI = 641, 1240
have = json.load(gzip.open(OUT, "rt")) if os.path.exists(OUT) else {}
R = load_all(); items = [r for r in R if r["cv"] not in have]
def logs(cv, a, b):
    for attempt in range(7):
        try:
            time.sleep(0.15); return lv.call("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(b), "address": cv, "topics": [[lv.BUY, lv.SELL]]}])
        except Exception as e:
            w = 2 ** (attempt + 1); print("retry", cv[:10], str(e)[:80], f"sleep {w}s", flush=True); time.sleep(w)
    raise RuntimeError("gave up " + cv)
def one(r):
    ev = logs(r["cv"], r["b0"] + LO, r["b0"] + HI)
    return r["cv"], {"hi": r["b0"] + HI, "rows": sorted((lv.row_of(x) for x in ev), key=lambda x: (x["bn"], x["li"]))}
t0 = time.time(); print("launches", len(R), "to extend", len(items), flush=True)
with cfu.ThreadPoolExecutor(4) as ex:
    for n, (cv, x) in enumerate(ex.map(one, items)):
        have[cv] = x
        if n % 100 == 0: print(n, "of", len(items), f"{time.time()-t0:.0f} s", flush=True)
json.dump(have, gzip.open(OUT, "wt")); print("extended:", len(have), f"in {time.time()-t0:.0f} s; events b0+641..b0+1240: {sum(len(x['rows']) for x in have.values())}", flush=True)
# the check: the cached b0..b0+640 against a fresh pull
random.seed(11); S = random.sample(R, 40); key = lambda x: (x["bn"], x["li"], x["k"], round(x["tk"], 6), round(x["eth"], 12), x["who"])
def chk(r):
    L = tape(r["cv"], ext=False); ev = logs(r["cv"], r["b0"], r["b0"] + 640)
    return r["cv"], L["src"], sorted(key(x) for x in L["rows"]) == sorted(key(lv.row_of(x)) for x in ev), len(ev)
with cfu.ThreadPoolExecutor(4) as ex: res = list(ex.map(chk, S))
bad = [x for x in res if not x[2]]
print(f"cache check: {len(res)} launches re-pulled b0..b0+640, {sum(x[3] for x in res)} events, identical {len(res)-len(bad)}/{len(res)}; sources {sorted(set(x[1] for x in res))}; mismatches {[(c[:10], s) for c, s, _, _ in bad]}")
