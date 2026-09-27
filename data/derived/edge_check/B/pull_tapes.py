"""pull_tapes.py (reviewer B): every Buy/Sell on a launch's curve from b0 to b0+640, the block stamps b0..b0+30, the tier,
cached under tapes/<cv>.json. Public RPC, 4 threads, live_vs_table's call (0.25 s after each call, retries with backoff).
    python3 data/derived/edge_check/B/pull_tapes.py fires|recent|all"""
import sys, os, json, time, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
import live_vs_table as lv
TO = 640
def one(r):
    p = c.B + f"tapes/{r['cv']}.json"
    if os.path.exists(p): return "cached"
    for attempt in range(4):
        try:
            L = lv.launch(r["cv"], r["b0"] + 12)
            if L is None: return "nolaunch"
            more = lv.call("eth_getLogs", [{"fromBlock": hex(r["b0"] + 121), "toBlock": hex(r["b0"] + TO), "address": r["cv"], "topics": [[lv.BUY, lv.SELL]]}])
            L["rows"] = sorted(L["rows"] + [lv.row_of(x) for x in more], key=lambda x: (x["bn"], x["li"]))
            L["ts"] = {str(k): v for k, v in L["ts"].items()}; L["to"] = r["b0"] + TO
            json.dump(L, open(p, "w")); return "ok"
        except Exception as e:
            err = e; time.sleep(3 * (attempt + 1))
    return f"err {str(err)[:80]}"
which = sys.argv[1] if len(sys.argv) > 1 else "fires"
items = {"fires": lambda: c.fires(c.FIT) + c.fires(c.RECENT), "recent": lambda: c.load(c.RECENT), "all": lambda: c.fires(c.FIT) + c.fires(c.RECENT) + c.load(c.RECENT) + c.load(c.FIT)}[which]()
seen = set(); items = [r for r in items if not (r["cv"] in seen or seen.add(r["cv"]))]
t0 = time.time(); n = 0
with cf.ThreadPoolExecutor(4) as ex:
    for r, s in zip(items, ex.map(one, items)):
        n += 1
        if s not in ("ok", "cached") or n % 50 == 0: print(n, r["cv"][:10], s, f"{time.time()-t0:.0f}s", flush=True)
print("done", len(items), f"{time.time()-t0:.0f}s")
