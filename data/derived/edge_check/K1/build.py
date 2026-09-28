"""K1/build.py: one row per launch of the week's engine replay (632 launches, Sep 21 09:40 - Sep 28 09:40 UTC), with every field
the K1 analyses need. The population, the grid/G/tape_bundles merge and the engine's own fleet count come from
src/analysis/engine_replay.py itself (run in-process with runpy, so the population is identical, not a re-implementation);
this script adds the fleet count at every view, each filter flag separately, the guard inputs, the grid returns, G's r2/r3
paths, and (where a tape exists: edge_check A/B/C/D via G's loader) the seat block's buys, first/second/third/last place,
the E2 entry and the seat-block buyers' first sell.  Output: K1/rows.json.gz.   python3 data/derived/edge_check/K1/build.py"""
import os, sys, io, json, gzip, runpy, contextlib, calendar, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
os.chdir(ROOT)
OUT = os.path.join(ROOT, "data/derived/edge_check/K1/rows.json.gz")
sys.argv = ["engine_replay.py", "--view", "k-1", "--reg"]
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    g = runpy.run_path("src/analysis/engine_replay.py", run_name="engine_replay_k1")
print(buf.getvalue().splitlines()[0])
E = g["E"]; fleets = g["fleets"]; FG = fleets.__globals__; bundle_buyers = g["bundle_buyers"]; prior_today = g["prior_today"]
launches = g["launches"]; replay_out = {x["cv"]: x for x in g["out"]}
SPLIT = calendar.timegm((2026, 9, 24, 0, 0, 0))
# tapes: G's loader (A, C, B, D tapes + G's extension to b0+1250)
sys.argv = ["x"]
with contextlib.redirect_stdout(io.StringIO()):
    GC = runpy.run_path("data/derived/edge_check/G/common.py", run_name="gcommon")
tape = GC["tape"]; curve = GC["curve"]; seat_block = GC["seat_block"]; net_eth_of = GC["net_eth_of"]; OURS = GC["OURS"]
X0, Y0 = GC["X0"], GC["Y0"]; fold_buy, fold_sell = GC["fold_buy"], GC["fold_sell"]; Ee = GC["E"]
def fl(r, cv, named, creator, upto, reg):
    FG["REG"] = reg
    return fleets(r, cv, named, creator, r.get("token"), upto)
def per_block(r):
    """raw counts per block offset 0..k+1: curve-aimed txs, fleets (cumulative, crowd_rules unit), wallets (cumulative)"""
    US = {E.WALLET.lower() if hasattr(E, "WALLET") else "", "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
    wal, flt = set(), set(); cw, cf, ntx = [], [], []
    for rows in r["blocks"]:
        n = 0
        for t in rows:
            if t["to"] in US or t["to_token"] or t["fr"] in US: continue
            if t["direct"]:
                if not t["named_fr"]: flt.add(t["fr"]); wal.add(t["fr"]); n += 1
            elif not t["named_data"]:
                flt.add(t["to"]); n += 1
                if not t["named_fr"]: wal.add(t["fr"])
        cw.append(len(wal)); cf.append(len(flt)); ntx.append(n)
    return cw, cf, ntx
def tape_fields(cv):
    L = tape(cv)
    if L is None: return None
    bE1 = seat_block(L)
    if bE1 is None: return {"tape": True, "bE1": None}
    o = {"tape": True}
    rows = [x for x in L["rows"] if x["who"] not in OURS]
    seat = [x for x in rows if x["bn"] == bE1]
    buys = [x for x in seat if x["k"] == "B"]
    o["e1_buys"] = [[round(x["eth"], 6), x["who"]] for x in buys]; o["e1_sells"] = sum(1 for x in seat if x["k"] == "S")
    NET = net_eth_of(L); o["e1_net"] = [round(NET.get((x["bn"], x["li"]), 0.0), 6) for x in buys]
    # the price path of each place at h = 0..60 and a few long exits
    for nm, na in (("p1", 0), ("p2", 1), ("p3", 2), ("p4", 3), ("plast", 10 ** 6)):
        v, gg = curve(L, n_ahead=na, hmax=60)
        o[nm] = [None if x is None else round(x, 5) for x in v] if v else None
    for st_ in (50.0, 100.0, 200.0):
        v, gg = curve(L, n_ahead=1, stake=st_, hmax=13); o[f"p2_{int(st_)}"] = [None if x is None else round(x, 5) for x in v] if v else None
    # E2: the first block of the second after E1's
    bE2 = next((n for n in range(bE1 + 1, bE1 + 30) if L["ts"].get(n, 0) == L["T0"] + 2), None); o["bE2"] = bE2; o["bE1"] = bE1
    if bE2:
        for nm, na in (("e2p1", 0), ("e2p2", 1)):
            v, gg = curve(L, n_ahead=na, hmax=40, entry_block=bE2); o[nm] = [None if x is None else round(x, 5) for x in v] if v else None
        o["e2_buys"] = [round(x["eth"], 6) for x in rows if x["bn"] == bE2 and x["k"] == "B"]
    # later E1+j seats (first place) for j = 1..3: a second seat on the same launch
    for j in (1, 2, 3):
        v, gg = curve(L, n_ahead=0, hmax=20, entry_block=bE1 + j); o[f"e1p{j}"] = [None if x is None else round(x, 5) for x in v] if v else None
        v, gg = curve(L, n_ahead=1, hmax=20, entry_block=bE1 + j); o[f"e1b{j}"] = [None if x is None else round(x, 5) for x in v] if v else None
    # seat-block buyers: the first block (offset from E1) in which any of them sells
    sb = {x["who"] for x in buys}
    fs = next((x["bn"] - bE1 for x in rows if x["bn"] > bE1 and x["k"] == "S" and x["who"] in sb), None); o["seat_first_sell"] = fs
    # sells per block after E1 (count, tokens) for h = 1..30, and buys per block (count, net ETH)
    o["sells_h"] = [sum(1 for x in rows if x["bn"] == bE1 + h and x["k"] == "S") for h in range(0, 31)]
    o["buys_h"] = [round(sum(NET.get((x["bn"], x["li"]), 0.0) for x in rows if x["bn"] == bE1 + h and x["k"] == "B"), 5) for h in range(0, 31)]
    return o
res = []
for r, l, h in launches:
    cv = l["cv"].lower(); t = l["T0"]; named = [a.lower() for a in (l.get("named") or r.get("named") or [])]; creator = (l.get("creator") or r.get("creator") or "").lower()
    tier = l.get("tier", h.get("tier")); tb = round((tier - 0.01) * 10000) if tier is not None else None
    k = r["k"]; tk0 = h.get("tk0")
    row = {"cv": cv, "T0": t, "set": "fit" if t < SPLIT else "read", "day": time.strftime("%b %d", time.gmtime(t)), "hour": time.gmtime(t).tm_hour,
           "k": k, "tier_bps": tb, "bundle": l.get("bundle_eth", h.get("bundle_eth_chain", 0.0)) or 0.0, "n_named": len(named),
           "nb": bundle_buyers(r, named), "repeat": prior_today(creator, t, cv) > 0, "tk0": tk0, "init_buy_eth": h.get("init_buy_eth"),
           "tk_build": h.get("tk_build_13"), "tk_seat1": h.get("tk_seat1_13"), "tk_last": h.get("tk_last_13"), "src": h.get("src", "grid"),
           "replay_why": replay_out[cv]["why"] if cv in replay_out else None}
    for nm, up, reg in (("f_k3", k - 3, False), ("f_k2n", k - 2, False), ("f_k2r", k - 2, True), ("f_k1n", k - 1, False), ("f_k1r", k - 1, True), ("f_k0r", k, True), ("f_kp1r", k + 1, True)):
        row[nm] = fl(r, cv, named, creator, up, reg)
    cw, cf, ntx = per_block(r); row["cw"] = cw; row["cf"] = cf; row["ntx"] = ntx
    for key in list(h.keys()):
        if key.startswith(("behind1_", "first_")): row[key] = h[key]
    res.append(row)
# G's curves (r2, r3 at every h to 1200 at $13) where present
Gc = {x["cv"].lower(): x for x in json.load(gzip.open("data/derived/edge_check/G/curves.json.gz", "rt"))}
nt = 0
for row in res:
    x = Gc.get(row["cv"])
    if x:
        row["g_r2"] = [None if v is None else round(v, 5) for v in x["r2"][:301]]; row["g_r3"] = [None if v is None else round(v, 5) for v in x["r3"][:301]]
        row["g_r2_long"] = {hh: x["r2"][hh] for hh in (400, 600, 900, 1200) if hh < len(x["r2"])}
    tf = tape_fields(row["cv"])
    if tf: row.update(tf); nt += 1
json.dump(res, gzip.open(OUT, "wt"))
print(f"{len(res)} launches written to {OUT}; fit {sum(r['set']=='fit' for r in res)}, read {sum(r['set']=='read' for r in res)}; G curves {sum('g_r2' in r for r in res)}; tapes {nt}")
