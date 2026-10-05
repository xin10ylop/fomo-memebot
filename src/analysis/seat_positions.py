"""seat_positions.py (Oct 5, runbook 5az): every fired launch (any view, guard 0.50) re-priced at the positions we get live: the seat block behind 1/3/5/all buys,
and late landings behind everything in the block +2..+33; the guard ratio (tokens vs the build's sizing) and the 11-block return"""
import json, glob, gzip, sys, concurrent.futures as cf
sys.path.insert(0, "src/analysis"); import live_vs_table as lv, hold_grid as hg
S = sys.argv[1]; E = 2570.0   # S: the folder holding engine_replay --dump files d_{k-2,k-1,k}_0.50.json; writes S/positions.json
fired = {}
for v in ("k-2", "k-1", "k"):
    for x in json.load(open(f"{S}/d_{v}_0.50.json")):
        if x.get("fired"):
            y = fired.setdefault(x["cv"].lower(), {"cv": x["cv"].lower(), "T0": x["T0"], "day": x["day"], "views": [], "stake": None, "smart": x.get("smart")})
            y["views"].append(v)
            if x.get("ret", {}).get("11") and x.get("usd") is not None and x["ret"]["11"] != 0: y["stake"] = x["usd"] / x["ret"]["11"]
b0 = {}
for f in glob.glob("data/derived/*/e1m_*.json*"):
    R = json.load(gzip.open(f, "rt")) if f.endswith(".gz") else json.load(open(f))
    for l in R.get("launches", []): b0[l["cv"].lower()] = (l["b0"], l.get("same_second_blocks", l.get("k")))
POS = [("s1", 0, 1), ("s3", 0, 3), ("s5", 0, 5), ("sL", 0, 10**6)] + [(f"L{d}", d, 10**6) for d in (2, 5, 9, 13, 24, 33)]
def one(cv):
    if cv not in b0: return None
    b, k = b0[cv]
    try:
        L = lv.launch(cv, b + (k or 0) + 1, b + 160)
        if L is None or L["tier"] is None: return None
        L["ts"].update(lv.stamps(L["b0"] + 31, L["b0"] + 90))
        ts = L["ts"]; T0 = L["T0"]; bE1 = next((n for n in range(L["b0"] + 1, L["b0"] + 60) if ts.get(n, 0) == T0 + 1), None)
        if bE1 is None: return None
        st = 13.0 / E; Lb = dict(L); Lb["rows"] = [r for r in L["rows"] if r["bn"] <= bE1 - 3]
        info = {}; hg.model_path(Lb, st, bE1, 0, (11,), info=info); tb = info["tk"]
        out = {"bE1": bE1, "bps": None}
        for name, d, n in POS:
            info = {}; r = hg.model_path(L, st, bE1 + d, n, (11,), info=info); out[name] = (info["tk"] / tb, r[11])
        out["ahead_seat"] = sum(1 for r in L["rows"] if r["bn"] == bE1 and r["k"] == "B")
        return out
    except Exception as e:
        return {"err": str(e)[:80]}
with cf.ThreadPoolExecutor(6) as ex:
    for cv, res in zip(list(fired), ex.map(one, list(fired))): fired[cv]["pos"] = res
json.dump(list(fired.values()), open(f"{S}/positions.json", "w")); print("done", len(fired), sum(1 for y in fired.values() if y.get("pos") and "err" not in y["pos"]))
