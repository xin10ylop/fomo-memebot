"""build_dump.py (edge_check/K3): the week's 632 qualifying launches (Sep 21 09:40 - Sep 28 09:40 UTC) through engine_replay.py's own
loaders and the engine's own note_attack / attack_fleets, but with EVERY filter reason recorded (not only the first), the engine's
fleet count at every block offset k-3..k both with and without the registration block, the guard inputs, every hold-grid return
column, and (where the edge review's tapes exist) the seat block's buys. One row per launch -> K3/week_dump.json.gz.
    python3 data/derived/edge_check/K3/build_dump.py
Reproduces engine_replay.py's usual view (k-1 --reg) as a check: printed at the end."""
import os, sys, json, gzip, glob, time, calendar, collections
K3 = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(K3, "..", "..", "..", ".."))
T0 = calendar.timegm(time.strptime("2026-09-21 09:40", "%Y-%m-%d %H:%M")); T1 = calendar.timegm(time.strptime("2026-09-28 09:40", "%Y-%m-%d %H:%M"))
LIVE = {"SEND_MODULE": "", "PRIVATE_KEY": "", "LOG_PATH": os.path.join(K3, "engine_import.jsonl"), "SEAT": "E1", "ATTACK_MIN": "2", "GATE_CLOSE_MS": "36", "TRADE_HOURS": "",
        "MIN_FOLLOW_ETH_60": "0", "TIER_MIN_BPS": "100", "TIER_MAX_BPS": "200", "BUNDLE_MIN": "3", "BUNDLE_MIN_ETH": "0.3", "BUNDLE_MAX_ETH": "3.0",
        "MIN_CREATOR_SUPPLY": "0.01", "MAX_CREATOR_BUY_ETH": "2", "HOLD_BLOCKS": "9", "BURST_SLIP": "0.07", "BURST_N": "35", "STAKE_MIN": "13", "STAKE_MAX": "13",
        "WALLET": "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "RELAY": "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
for k, v in LIVE.items(): os.environ[k] = v
os.chdir(ROOT); sys.path.insert(0, "src/strategy"); sys.path.insert(0, "src/analysis"); import sniper_engine as E
D = "data/derived/live_vs_table"; EC = "data/derived/edge_check"
KNOWN = {"sep2021": ("2026-09-20 13:26", "2026-09-22 01:02"), "sep2223": ("2026-09-22 01:02", "2026-09-23 06:35"), "sep23day": ("2026-09-23 10:22", "2026-09-23 20:20"), "sep24_paper": ("2026-09-24 12:38", "2026-09-24 21:36")}
CROWD_ALIAS = {"sep24_paper": "sep24paper"}
def span_of(n):
    for f in glob.glob(f"data/derived/*/e1m_{n}.json"):
        d = json.load(open(f)); return d["t_lo"], d["t_hi"]
    return KNOWN.get(n) and tuple(calendar.timegm(time.strptime(x, "%Y-%m-%d %H:%M")) for x in KNOWN[n])
GC = {x["cv"].lower(): x for x in json.load(gzip.open(f"{EC}/G/curves.json.gz", "rt"))}
TB = json.load(gzip.open(f"{D}/tape_bundles.json.gz", "rt"))
pieces = []; SKIP = ("141_creators", "175_sep2223", "oos_sep2021", "today_sep23", "sep1819")
for lf in sorted(glob.glob(f"{D}/launches_*.json")):
    n = os.path.basename(lf)[9:-5]; hg = f"{D}/hold_grid_week_{n}.json"
    if n in SKIP: continue
    cf = next((c for c in (f"{D}/crowd_raw_{CROWD_ALIAS.get(n, n)}.json.gz", f"{D}/crowd_raw_{CROWD_ALIAS.get(n, n)}.json") if os.path.exists(c)), None)
    sp = span_of(n)
    if not (cf and sp) or sp[1] < T0 or sp[0] > T1: continue
    pieces.append((n, lf, cf, hg if os.path.exists(hg) else None, sp))
cre = collections.defaultdict(list)
for c in json.load(gzip.open(f"{D}/creations_week.json.gz", "rt")): cre[c["creator"].lower()].append((c["ts"], c["cv"].lower()))
def prior_today(creator, t, cv):
    d0 = t - (t % 86400); return sum(1 for x, c in cre.get(creator, ()) if c != cv and d0 <= x < t + 120)
def fleets_by_block(r, cv, named, creator, token, reg):
    """the engine's cumulative fleet count after each block offset 0..k+1 (registration = the first named block; its shots counted iff reg)"""
    E.state["watch"].clear(); w = E.watch_curve(cv, 1e7, 1_700_000_000, set(named), creator, blk0=r["b0"], tax_bps=200)
    w["tb"] = bytes.fromhex(token[2:]) if token else None
    j = next((i for i, rw in enumerate(r["blocks"]) if any(t.get("named_fr") or t.get("named_data") for t in rw)), -1)
    out = []; shots = []
    for off, rows in enumerate(r["blocks"]):
        n = 0
        if not (off < j or (off == j and not reg)):
            for t in rows:
                E.sender_of = (lambda fr: (lambda tx: fr))(t["fr"])
                data = bytes.fromhex(t["sel"][2:]) if t["direct"] else (bytes.fromhex(t["sel"][2:]) + b"\0" * 12 + bytes.fromhex(cv[2:]) + b"".join(b"\0" * 12 + bytes.fromhex(a[2:]) for a in named if t["named_data"]))
                E.note_attack(w, t["to"], b"", data, cv); n += 1
        out.append(E.attack_fleets(w)); shots.append(n)
    return out, shots, j
def bundle_buyers(r, named):
    nm = set(a.lower() for a in named); s = set(); helper = False
    for rows in r["blocks"][: min(len(r["blocks"]), 10)]:
        for t in rows:
            if t.get("named_fr") and t["fr"].lower() in nm: s.add(t["fr"].lower())
            if t.get("named_data"): helper = True
    return len(nm) if helper else len(s)
# tapes (edge review B, D) for the seat block's buys
TAPES = {}
for d in (f"{EC}/B/tapes", f"{EC}/D/tapes"):
    for f in os.listdir(d): TAPES.setdefault(f[:-5].lower(), os.path.join(d, f))
OURS = {"0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
def seat_info(cv):
    p = TAPES.get(cv)
    if not p: return None
    L = json.load(open(p)); ts = {int(k): v for k, v in L["ts"].items()}; T = L["T0"]
    bE1 = next((n for n in range(L["b0"] + 1, L["b0"] + 30) if ts.get(n, 0) == T + 1), None)
    if bE1 is None: return None
    e1 = [r for r in L["rows"] if r["bn"] == bE1 and r["who"] not in OURS]
    buys = [r for r in e1 if r["k"] == "B"]
    ours_in = any(r["who"] in OURS for r in L["rows"] if r["bn"] <= bE1 + 15)
    bE2 = next((n for n in range(bE1, bE1 + 30) if ts.get(n, 0) == T + 2), None)
    return {"tape": 1, "e1_nbuy": len(buys), "e1_eth": sum(r["eth"] for r in buys), "e1_first_eth": buys[0]["eth"] if buys else 0.0,
            "e1_second_eth": buys[1]["eth"] if len(buys) > 1 else 0.0, "e1_nsell": sum(1 for r in e1 if r["k"] == "S"), "e1_blocks": (bE2 - bE1) if bE2 else None, "ours_in_tape": ours_in}
rows = {}
for n, lf, cf, hg, sp in pieces:
    L = {l["cv"].lower(): l for l in json.load(open(lf))}; H = {h["cv"].lower(): h for h in json.load(open(hg))} if hg else {}
    R = json.load(gzip.open(cf, "rt")) if cf.endswith(".gz") else json.load(open(cf))
    for r in R:
        cv = r["cv"].lower(); l = L.get(cv); h = H.get(cv) or {}; g = GC.get(cv)
        if not l or not (T0 <= l["T0"] <= T1) or cv in rows: continue
        tbv = TB.get(cv); src = "grid" if h.get("behind1_13_h11") is not None else None
        if tbv:
            h = dict(h)
            for kk in ("bundle_eth_chain", "tk0", "init_buy_eth", "tier", "tk_build_13", "tk_seat1_13", "tk_last_13"):
                if h.get(kk) is None and (kk if kk != "bundle_eth_chain" else "bundle_eth") in tbv: h[kk] = tbv[kk if kk != "bundle_eth_chain" else "bundle_eth"]
        if g and not h.get("behind1_13_h11"):
            h = dict(h); h.update({f"behind1_13_h{hh}": g["r2"][hh] for hh in (9, 11, 13, 15)}); src = "G"
        if not h.get("behind1_13_h11"): continue
        rows[cv] = (r, l, h, n, src)
launches = sorted(rows.values(), key=lambda x: x[1]["T0"])
out = []; Y0 = E.Y0
for r, l, h, piece, src in launches:
    cv = l["cv"].lower(); t = l["T0"]; named = [a.lower() for a in (l.get("named") or r.get("named") or [])]; creator = (l.get("creator") or r.get("creator") or "").lower()
    tier = l.get("tier", h.get("tier")); tb = round((tier - 0.01) * 10000) if tier is not None else 0
    k = r["k"]; tk0 = h.get("tk0")
    rec = {"cv": cv, "T0": t, "day": time.strftime("%b %d", time.gmtime(t)), "hour": time.gmtime(t).tm_hour, "piece": piece, "src": src, "k": k,
           "bundle": l.get("bundle_eth", h.get("bundle_eth_chain", 0.0)) or 0.0, "tier_bps": tb, "tk0": tk0, "init_buy_eth": h.get("init_buy_eth"),
           "repeat": prior_today(creator, t, cv), "nb": bundle_buyers(r, named), "named_n": len(named), "creator": creator}
    pre = []
    if rec["repeat"] > 0: pre.append("repeat")
    if tk0 is None: pre.append("tk0 missing")
    elif tk0 <= 0 or tk0 >= Y0: pre.append("no launch-block buy")
    elif tk0 < E.MIN_CREATOR_SUPPLY * Y0: pre.append("supply")
    if (h.get("init_buy_eth") or 0.0) > E.MAX_CREATOR_BUY_ETH: pre.append("creator buy > 2")
    gates = []
    if rec["nb"] < E.BUNDLE_MIN: gates.append("nb")
    if rec["bundle"] < E.BUNDLE_MIN_ETH: gates.append("bundle min")
    if rec["bundle"] > E.BUNDLE_MAX_ETH: gates.append("cap")
    if tb < E.TIER_MIN_BPS or tb > E.TIER_MAX_BPS: gates.append("tier")
    rec["pre"] = pre; rec["gates"] = gates
    for reg in (0, 1):
        fb, shots, j = fleets_by_block(r, cv, named, creator, r.get("token"), reg)
        rec[f"fl_reg{reg}"] = fb
        if reg: rec["shots"] = shots; rec["reg_off"] = j
    rec["tk_build"], rec["tk_seat1"], rec["tk_last"] = h.get("tk_build_13"), h.get("tk_seat1_13"), h.get("tk_last_13")
    rec["ret"] = {kk: v for kk, v in h.items() if kk.startswith(("behind1_", "first_"))}
    g = GC.get(cv)
    if g: rec["g_r2"] = g["r2"][:61]; rec["g_r3"] = g["r3"][:61]; rec["g_win"] = g["win"]
    si = seat_info(cv)
    if si: rec.update(si)
    out.append(rec)
json.dump(out, gzip.open(os.path.join(K3, "week_dump.json.gz"), "wt"))
# check against engine_replay's usual view (k-1 with the registration block)
fired = [x for x in out if not x["pre"] and not x["gates"] and x["fl_reg1"][x["k"] - 1] >= 2]
guard = [x for x in fired if x["tk_build"] and x["tk_seat1"] and x["tk_seat1"] < 0.93 * x["tk_build"]]
fills = [x for x in fired if x not in guard]
usd = sum(x["ret"]["behind1_13_h11"] * 13 - 0.33 for x in fills) - 0.33 * len(guard)
print(f"{len(out)} launches; usual view: fired {len(fired)} guard {len(guard)} fills {len(fills)} mean {sum(x['ret']['behind1_13_h11'] for x in fills)/len(fills):+.1%} $ {usd:+.2f}")
print("tape coverage:", sum(1 for x in out if x.get("tape")), "of", len(out), "; G curve coverage:", sum(1 for x in out if "g_r2" in x))
