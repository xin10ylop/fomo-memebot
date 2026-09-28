"""V_0 (data lens): independent re-count of the 6.7 bundle close vs 6.8 (no close) on every replayed launch of the week.
Engine 6.7 = git show 34265b9:src/strategy/sniper_engine.py (R1's engine67.py, byte-checked below), engine 6.8 = the working tree.
For each launch: the feed rows (crowd_raw, chain order) folded by each engine's own watch_curve; three horizons of what the
feed has shown when the gate reads: blocks < k-1 (floor), < k (usual, k-1 read), all captured blocks (R1's horizon).
Outsider value-carrying calls: 'A' every stranger call naming the curve carries value (upper bound), 'B' none does."""
import os, sys, json, importlib.util, collections, hashlib, subprocess
ROOT = "/home/user/fomo-memebot"; HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = {"SEND_MODULE": "", "PRIVATE_KEY": "", "LOG_PATH": os.path.join(HERE, "engine_log.jsonl"), "SEAT": "E1", "ATTACK_MIN": "2", "TIER_MIN_BPS": "100", "TIER_MAX_BPS": "200", "BUNDLE_MIN": "3",
        "BUNDLE_MIN_ETH": "0.3", "BUNDLE_MAX_ETH": "3.0", "MIN_CREATOR_SUPPLY": "0.01", "MAX_CREATOR_BUY_ETH": "2", "HOLD_BLOCKS": "9", "BURST_SLIP": "0.20", "BURST_N": "35",
        "STAKE_MIN": "13", "STAKE_MAX": "13", "WALLET": "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "RELAY": "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
for k, v in LIVE.items(): os.environ[k] = v
os.chdir(ROOT)
src67 = subprocess.check_output(["git", "show", "34265b9:src/strategy/sniper_engine.py"])
open(os.path.join(HERE, "engine67_git.py"), "wb").write(src67)
r1 = open(f"{ROOT}/data/derived/edge_check/N/2026-09-28/R1/engine67.py", "rb").read()
print("R1's engine67.py identical to git 34265b9:", hashlib.sha1(r1).hexdigest() == hashlib.sha1(src67).hexdigest())
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
E7 = load("e67", os.path.join(HERE, "engine67_git.py")); E8 = load("e68", f"{ROOT}/src/strategy/sniper_engine.py")
US = {"0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
import gzip, glob
C = {}
for f in sorted(glob.glob(f"{ROOT}/data/derived/live_vs_table/crowd_raw_*.json.gz")):
    for r in json.load(gzip.open(f, "rt")): C.setdefault(r["cv"].lower(), r)
def bundle(E, r, horizon, outsider_value):
    cv = r["cv"].lower(); named = set(a.lower() for a in r["named"]); creator = r["creator"].lower(); ts0 = 1_700_000_000; blk0 = 1000
    for key in ("valtx", "buys", "sells", "watch"): E.state[key].clear()
    seen = 0.0; closer = None; order = []
    for off, rows in enumerate(r["blocks"][:horizon]):
        for t in sorted(rows, key=lambda t: t["ix"]):
            if t["fr"] in US or t["to"] in US or t["to_token"]: continue
            seen += 0.001; fr = t["fr"]; outsider = not t["named_fr"]
            if t["direct"]:
                if t["sel"][2:] == E.BUY_SEL.hex():
                    E.state["buys"][cv].append((ts0, fr, 0.01, seen, blk0 + off, cv, t["sel"][2:])); order.append((off, t, "direct"))
                continue
            if outsider and not outsider_value: continue
            val = 0.01 if outsider else 0.03
            data = bytes.fromhex(t["sel"][2:]) + b"\0" * 12 + bytes.fromhex(cv[2:]) + (b"".join(b"\0" * 12 + bytes.fromhex(a[2:]) for a in sorted(named)) if t["named_data"] else b"")
            E.state["valtx"].append([seen, ts0, fr, val, data, b"", blk0 + off, t["to"], t["sel"][2:]]); order.append((off, t, "value"))
    w = E.watch_curve(cv, 1e7, ts0, named, creator, blk0=blk0, tax_bps=200)
    # the first outsider row in the creation window (the 6.7 closer)
    for off, t, kind in order:
        if not t["named_fr"] and off <= 9: closer = (off, t["ix"], t["fr"], t["to"], t["sel"], kind); break
    return w["bundle"], bool(w.get("bundle_closed")), closer
if __name__ == "__main__":
    V = {v: {x["cv"]: x for x in json.load(open(f"{ROOT}/data/derived/edge_check/N/2026-09-28/R1/rows_{v}.json"))} for v in ("k2", "k1reg", "kreg")}
    out = []
    for cv, x in V["k1reg"].items():
        r = C.get(cv)
        if r is None: out.append({"cv": cv, "missing": True}); continue
        k = r["k"]; rec = {"cv": cv, "T0": x["T0"], "k": k}
        for hname, hz in (("floor", max(k - 1, 0)), ("usual", k), ("all", len(r["blocks"]))):
            for mode, ov in (("A", True), ("B", False)):
                b7, c7, cl = bundle(E7, r, hz, ov); b8, c8, _ = bundle(E8, r, hz, ov)
                rec[f"{hname}_{mode}"] = [b7, c7, b8, c8]
                if hname == "all" and mode == "A": rec["closer"] = cl
        out.append(rec)
    json.dump(out, open(os.path.join(HERE, "v_bundle_rows.json"), "w"))
    print("launches", len(out), "missing crowd rows", sum(1 for r in out if r.get("missing")))
    print("6.8 ever closes:", sum(1 for r in out if not r.get("missing") and any(r[k][3] for k in r if k.endswith(("_A", "_B")))))
