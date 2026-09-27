"""pull_fast.py (reviewer B): the recent population's tapes with one call per launch (the public node throttled the full
pull): every Buy/Sell on the curve b0..b0+640 in one eth_getLogs; the tier from the window's e1_multi file (e1m_*.json);
the block stamps synthesised from the crowd record (blocks b0..b0+k in the creation second T0, then 10 blocks a second,
the cadence measured in world.py: 9.9). Marks the tape ts_synth. Only launches without a full tape.
    python3 data/derived/edge_check/B/pull_fast.py [fit]      (fit: the fit windows' missing launches too, where an e1m file has the tier)"""
import sys, os, json, time, glob, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
import live_vs_table as lv
TIER = {}
for f in glob.glob("data/derived/e1_*/e1m_*.json"):
    for l in json.load(open(f))["launches"]: TIER[l["cv"].lower()] = l["tier"]
def one(r):
    p = c.B + f"tapes/{r['cv']}.json"
    if os.path.exists(p): return "cached"
    if r["cv"] not in TIER: return "no tier"
    for attempt in range(5):
        try:
            ev = lv.call("eth_getLogs", [{"fromBlock": hex(r["b0"]), "toBlock": hex(r["b0"] + 640), "address": r["cv"], "topics": [[lv.BUY, lv.SELL]]}])
            rows = sorted((lv.row_of(x) for x in ev), key=lambda x: (x["bn"], x["li"])); b0, k, T0 = r["b0"], r["k"], r["T0"]
            ts = {str(b0 + i): T0 for i in range(k + 1)}
            for i in range(k + 1, 31): ts[str(b0 + i)] = T0 + 1 + (i - k - 1) // 10
            tier = TIER[r["cv"]]; L = {"cv": r["cv"], "b0": b0, "T0": T0, "ts": ts, "tier": tier, "tb": round((tier - 0.01) * 10000), "named": len(r["named"]), "rows": rows, "sel": "f85f8e41", "to": b0 + 640, "ts_synth": True}
            json.dump(L, open(p, "w")); return "ok"
        except Exception as e:
            err = e; time.sleep(3 * (attempt + 1))
    return f"err {str(err)[:80]}"
items = c.load(c.RECENT) + (c.load(c.FIT) if "fit" in sys.argv else []); t0 = time.time()
with cf.ThreadPoolExecutor(4) as ex: res = list(ex.map(one, items))
print({s: res.count(s) for s in set(res)}, f"{time.time()-t0:.0f}s")
