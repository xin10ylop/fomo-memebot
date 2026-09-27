"""price.py (edge_check/A): every rule fire priced OFFLINE from tapes.json.gz by an independent re-implementation of the
seat model (second place in the E1 block, tier + 6.18% surcharge on the buy, tier on the sell, 3% supply cap, the buys after
ours folded by their ETH, the sells by their tokens), at $13 and ETH 2570 (reach_table's constants), for holds 15, 30, 60,
150, 300, 600 blocks and a -20% stop (else 300 / else 600). Side by side: reach_table's own model_eff (imported from
src/analysis via stake_scale, on the same tape) and hold_grid's stored behind1_15_h300 for the same launch.
Writes fires.json (one record per fire, with the tape-derived features for test 3).
    python3 data/derived/edge_check/A/price.py"""
import sys, os, json, gzip, math, statistics as st
sys.path.insert(0, "src/analysis"); sys.path.insert(0, "data/derived/edge_check/A")
from common import *
import live_vs_table as lv
sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/stake_scale.py").read().split("\nfor name, cf, hours in W:")[0])   # model_eff, E, GAS (reach_table's pricing)
X0_, Y0_ = 1.68, 1e9; SUR1 = 0.0618; CAPF = 0.03; STAKE = 13.0; ETH = 2570.0; HOLDS = (15, 30, 60, 150, 300, 600)
T = json.load(gzip.open(A + "tapes.json.gz", "rt"))
def tape(L): return [r for r in L["rows"] if r["who"] not in US]
def seat_block(L):
    ts = {int(k): v for k, v in L["ts"].items()}; T0 = L["T0"]
    return next((n for n in range(L["b0"] + 1, L["b0"] + 30) if ts.get(n, 0) == T0 + 1), None), ts
def my_model(L, n_ahead=1, stake_usd=STAKE, stop=None):
    """returns {hold: return}, plus 'stop_300'/'stop_600' when stop is given; independent of lv/stake_scale code"""
    bE1, ts = seat_block(L); tier = L["tier"]; rows = tape(L)
    # clean pass: each buy's net ETH (fixed-ETH buyers)
    X, Y = X0_, Y0_; net_of = {}
    for r in rows:
        if r["k"] == "B":
            if 0 < r["tk"] < Y: n = X * r["tk"] / (Y - r["tk"]); net_of[(r["bn"], r["li"])] = n; X, Y = X + n, Y - r["tk"]
        else: n = X * r["tk"] / (Y + r["tk"]); X, Y = X - n, Y + r["tk"]
    # our entry point: after every event of blocks < bE1 and, in bE1, after the first n_ahead buys (and the sells before them)
    X, Y = X0_, Y0_; i = 0; seen = 0
    while i < len(rows):
        r = rows[i]
        if r["bn"] > bE1: break
        if r["bn"] == bE1 and r["k"] == "B":
            if seen >= n_ahead: break
            seen += 1
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = X + X * r["tk"] / (Y - r["tk"]), Y - r["tk"]
        else: X, Y = X - X * r["tk"] / (Y + r["tk"]), Y + r["tk"]
        i += 1
    # sells of bE1 after the n_ahead buys, before any further buy, come after us (model_eff: post once seen == n_ahead)
    g = stake_usd / ETH; net = g * (1 - tier - SUR1); tk = Y * net / (X + net)
    if tk > CAPF * Y0_: tk = CAPF * Y0_; net = X * tk / (Y - tk); g = net / (1 - tier - SUR1)
    X, Y = X + net, Y - tk; p_in = X / Y; out = {}; stopped = None
    val = lambda X, Y: (X * tk / (Y + tk) * (1 - tier)) / g - 1
    post = rows[i:]; j = 0
    for h in HOLDS:
        while j < len(post) and post[j]["bn"] <= bE1 + h:
            r = post[j]
            if r["k"] == "B":
                n = net_of.get((r["bn"], r["li"]))
                if n is not None: X, Y = X + n, Y - Y * n / (X + n)
            else: X, Y = X - X * r["tk"] / (Y + r["tk"]), Y + r["tk"]
            if stop is not None and stopped is None and X / Y <= p_in * (1 - stop): stopped = (r["bn"] - bE1, val(X, Y))
            j += 1
        out[h] = val(X, Y)
    if stop is not None:
        out["stop_300"] = stopped[1] if stopped and stopped[0] <= 300 else out[300]
        out["stop_600"] = stopped[1] if stopped else out[600]
        out["stop_at"] = stopped[0] if stopped else None
    return out
def fee_audit(L):
    """implied buy fee by second after creation (0,1,2,>=3) and sell fee, from the curve state before each event"""
    ts = {int(k): v for k, v in L["ts"].items()}; T0 = L["T0"]; X, Y = X0_, Y0_; fb = {}; fs = []
    for r in L["rows"]:
        if r["k"] == "B":
            if 0 < r["tk"] < Y:
                n = X * r["tk"] / (Y - r["tk"])
                if r["eth"] > 0: s = ts.get(r["bn"]); fb.setdefault((s - T0) if s is not None else 9, []).append(1 - n / r["eth"])
                X, Y = X + n, Y - r["tk"]
        else:
            n = X * r["tk"] / (Y + r["tk"])
            if n > 0: fs.append(1 - r["eth"] / n)
            X, Y = X - n, Y + r["tk"]
    return fb, fs
LA = {}
for f in ["launches_141_creators.json", "launches_oos_sep2021.json", "launches_175_sep2223.json", "launches_today_sep23.json"] + [f"launches_{w if w != 'sep24paper' else 'sep24_paper'}.json" for w in REC]:
    for l in json.load(open(D + f)): LA.setdefault(l["cv"].lower(), l)
recs = []
for r in all_launches(FIT + REC):
    if not is_fire(r): continue
    L = T.get(r["cv"])
    if L is None: print("no tape", r["cv"]); continue
    bE1, ts = seat_block(L)
    m = my_model(L, stop=0.20); m0 = my_model(L, n_ahead=0)
    Lm = dict(L); Lm["ts"] = ts
    me = model_eff(Lm, 13 / E, bE1, 1, 300)[0]
    Hh = {x["cv"]: x for x in json.load(open(D + HG[r["win"]]))}.get(r["cv"], {})
    la = LA.get(r["cv"], {})
    cf = fleets_by_block(r); cw = fleets_by_block(r, "wallets")
    recs.append({"cv": r["cv"], "win": r["win"], "set": "fit" if r["win"] in FIT else "rec", "T0": r["T0"], "b0": r["b0"], "k": r["k"], "bE1": bE1,
                 "tier": L["tier"], "named_n": L["named"], "creator": r["creator"], "bundle_eth": la.get("bundle_eth"), "hour": la.get("hour"),
                 "fleets": cf, "wallets": cw, "ret": m, "ret_first": m0, "model_eff_h300": me, "hold_grid_h300": Hh.get("behind1_15_h300"),
                 "hg": {k: Hh.get(k) for k in ("behind1_15_h15", "behind1_15_h60", "behind1_15_h300", "behind1_15_h600", "behind1_15_stop20_h600")}})
json.dump(recs, open(A + "fires.json", "w"), indent=0)
fit = [x for x in recs if x["set"] == "fit"]; rec = [x for x in recs if x["set"] == "rec"]
for name, s in (("fit", fit), ("recent", rec)):
    a = [x["ret"][300] for x in s]; b = [x["model_eff_h300"] for x in s]; c = [x["hold_grid_h300"] for x in s]
    print(f"{name:7s} n={len(s):3d}  mine h300 {st.mean(a):+.2%}  reach_table model_eff {st.mean(b):+.2%}  hold_grid behind1_15_h300 {st.mean(c):+.2%}"
          f"  max|mine-model_eff| {max(abs(p-q) for p, q in zip(a, b)):.4f}  max|mine-hold_grid| {max(abs(p-q) for p, q in zip(a, c)):.4f}")
# fee audit, fit vs recent
for name, s in (("fit", fit), ("recent", rec)):
    fb = {}; fs = []; tiers = []
    for x in s:
        L = T[x["cv"]]; b, sl = fee_audit(L)
        for kk, v in b.items(): fb.setdefault(min(kk, 3), []).extend([f - L["tier"] for f in v])
        fs.extend([f - L["tier"] for f in sl])
    print(f"{name}: implied buy fee minus tier by second after creation (median, n):", {kk: (round(st.median(v), 4), len(v)) for kk, v in sorted(fb.items())},
          " sell fee minus tier: median %.5f, 1-99%% [%.4f, %.4f], n %d" % (st.median(fs), sorted(fs)[len(fs)//100], sorted(fs)[-len(fs)//100-1], len(fs)))
