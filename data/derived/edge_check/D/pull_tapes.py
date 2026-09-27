"""pull_tapes.py (reviewer D): the 85 fit launches (sep2223) that round 1 had no tape for. One eth_getLogs per launch (every
Buy/Sell on the curve b0..b0+640), the tier from launches_175_sep2223.json (the e1_multi scan of that window), the block
stamps synthesised from the crowd record exactly as B/pull_fast.py (blocks b0..b0+k in T0, then 10 a second; B/synth_check.py
found the h300 identical to real stamps on 472 launches). Public RPC, 4 threads, 0.25 s after each call, backoff on errors/429.
    python3 data/derived/edge_check/D/pull_tapes.py"""
import sys, os, json, time, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
lv = c.lv
TIER = {l["cv"].lower(): l["tier"] for l in json.load(open(c.LV + "launches_175_sep2223.json"))}
def one(r):
    p = c.DD + f"tapes/{r['cv']}.json"
    if os.path.exists(p) or os.path.exists(c.BB + f"tapes/{r['cv']}.json"): return "cached"
    if r["cv"] not in TIER: return "no tier"
    for attempt in range(6):
        try:
            ev = lv.call("eth_getLogs", [{"fromBlock": hex(r["b0"]), "toBlock": hex(r["b0"] + 640), "address": r["cv"], "topics": [[lv.BUY, lv.SELL]]}])
            rows = sorted((lv.row_of(x) for x in ev), key=lambda x: (x["bn"], x["li"])); b0, k, T0 = r["b0"], r["k"], r["T0"]
            ts = {str(b0 + i): T0 for i in range(k + 1)}
            for i in range(k + 1, 31): ts[str(b0 + i)] = T0 + 1 + (i - k - 1) // 10
            tier = TIER[r["cv"]]
            L = {"cv": r["cv"], "b0": b0, "T0": T0, "ts": ts, "tier": tier, "tb": round((tier - 0.01) * 10000), "named": len(r["named"]), "rows": rows, "sel": "f85f8e41", "to": b0 + 640, "ts_synth": True}
            json.dump(L, open(p, "w")); return "ok"
        except Exception as e:
            err = e; time.sleep(3 * (attempt + 1))
    return f"err {str(err)[:80]}"
items = [r for r in c.all_records() if c.tape(r["cv"]) is None]; t0 = time.time()
with cf.ThreadPoolExecutor(4) as ex: res = list(ex.map(one, items))
print(len(items), "missing;", {s: res.count(s) for s in set(res)}, f"{time.time()-t0:.0f}s")
