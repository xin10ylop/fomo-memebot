"""gaps.py (reviewer D): round 1 A's two stretches the committed windows skipped (Sep 26 17:38-22:38 'gapA', Sep 27 04:09-09:20
'gapB'; A/crowd_raw_gap*.json.gz, A/launches_gap*.json with the tier), their tapes pulled here (one eth_getLogs each, stamps
synthesised as B/pull_fast.py), priced with features.py, and the recent set re-read with them: 15 and 300 blocks, fires and lift.
    python3 data/derived/edge_check/D/gaps.py > data/derived/edge_check/D/gaps.txt"""
import sys, os, json, gzip, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c, kit as K, features as fe
lv = c.lv; known = {f["cv"] for f in K.FE}; new = []
for g in ("gapA", "gapB"):
    TIER = {l["cv"]: l["tier"] for l in json.load(open(f"data/derived/edge_check/A/launches_{g}.json"))["launches"]}
    for r in json.load(gzip.open(f"data/derived/edge_check/A/crowd_raw_{g}.json.gz", "rt")):
        if r["cv"] in known: continue
        p = c.DD + f"tapes/{r['cv']}.json"
        if not os.path.exists(p):
            ev = lv.call("eth_getLogs", [{"fromBlock": hex(r["b0"]), "toBlock": hex(r["b0"] + 640), "address": r["cv"], "topics": [[lv.BUY, lv.SELL]]}])
            rows = sorted((lv.row_of(x) for x in ev), key=lambda x: (x["bn"], x["li"])); b0, k, T0 = r["b0"], r["k"], r["T0"]
            ts = {str(b0 + i): T0 for i in range(k + 1)}
            for i in range(k + 1, 31): ts[str(b0 + i)] = T0 + 1 + (i - k - 1) // 10
            json.dump({"cv": r["cv"], "b0": b0, "T0": T0, "ts": ts, "tier": TIER[r["cv"]], "named": len(r["named"]), "rows": rows, "to": b0 + 640, "ts_synth": True}, open(p, "w"))
        r["win"] = g; r["grp"] = "recent"; f = fe.feat(r); f["day"] = c.day(f["T0"]); new.append(f)
print(f"{len(new)} new launches, {sum(f['fire'] for f in new)} fires: " + "; ".join(f"{c.hhmm(f['T0'])} {f['cv'][:10]} h15 {f['path'][15]:+.1%} h300 {f['path'][300]:+.1%}" for f in new if f["fire"]))
REC2 = K.REC + new
for h in (15, 300):
    fi = [f["path"][h] for f in REC2 if f["fire"]]; re = [f["path"][h] for f in REC2 if not f["fire"]]
    print(f"recent with the gaps, h{h}: {c.summ(fi)}   refused {c.mean(re):+.1%} ({len(re)})   lift {100*(c.mean(fi)-c.mean(re)):+.1f}")
