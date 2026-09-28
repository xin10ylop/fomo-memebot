"""K2/build_table.py: one row per qualifying launch of the week (Sep 21 09:40 - Sep 28 09:40 UTC), built exactly the way
src/analysis/engine_replay.py builds its population (same pieces, same merge of grid / tape_bundles / G curves), but keeping
EVERY gate's flag (not only the first) and the engine's fleet count at every view, so that each question can be answered by
re-running the gate chain with one setting changed (K2/sim.py). Offline; run from the repo root:
    python3 data/derived/edge_check/K2/build_table.py      -> data/derived/edge_check/K2/table.json.gz"""
import os, sys, json, gzip, glob, time, calendar, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
os.chdir(ROOT)
LIVE = {"SEND_MODULE": "", "PRIVATE_KEY": "", "LOG_PATH": "/tmp/k2_replay.jsonl", "SEAT": "E1", "ATTACK_MIN": "2", "GATE_CLOSE_MS": "36", "TRADE_HOURS": "",
        "MIN_FOLLOW_ETH_60": "0", "TIER_MIN_BPS": "100", "TIER_MAX_BPS": "200", "BUNDLE_MIN": "3", "BUNDLE_MIN_ETH": "0.3", "BUNDLE_MAX_ETH": "3.0",
        "MIN_CREATOR_SUPPLY": "0.01", "MAX_CREATOR_BUY_ETH": "2", "HOLD_BLOCKS": "9", "BURST_SLIP": "0.07", "BURST_N": "35", "STAKE_MIN": "13", "STAKE_MAX": "13",
        "WALLET": "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "RELAY": "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
for k, v in LIVE.items(): os.environ[k] = v
sys.path.insert(0, "src/strategy"); import sniper_engine as E
T0W = calendar.timegm(time.strptime("2026-09-21 09:40", "%Y-%m-%d %H:%M")); T1W = calendar.timegm(time.strptime("2026-09-28 09:40", "%Y-%m-%d %H:%M"))
D = "data/derived/live_vs_table"; OUT = "data/derived/edge_check/K2/table.json.gz"
US = {"0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
# ---- identical to engine_replay.py -------------------------------------------------------------------------------------------
KNOWN = {"sep2021": ("2026-09-20 13:26", "2026-09-22 01:02"), "sep2223": ("2026-09-22 01:02", "2026-09-23 06:35"), "sep23day": ("2026-09-23 10:22", "2026-09-23 20:20"), "sep24_paper": ("2026-09-24 12:38", "2026-09-24 21:36")}
CROWD_ALIAS = {"sep24_paper": "sep24paper"}
def span_of(n):
    for f in glob.glob(f"data/derived/*/e1m_{n}.json"):
        d = json.load(open(f)); return d["t_lo"], d["t_hi"]
    return KNOWN.get(n) and tuple(calendar.timegm(time.strptime(x, "%Y-%m-%d %H:%M")) for x in KNOWN[n])
GC = {x["cv"].lower(): x for x in json.load(gzip.open("data/derived/edge_check/G/curves.json.gz", "rt"))}
TB = json.load(gzip.open(f"{D}/tape_bundles.json.gz", "rt"))
pieces = []; SKIP = ("141_creators", "175_sep2223", "oos_sep2021", "today_sep23", "sep1819")
for lf in sorted(glob.glob(f"{D}/launches_*.json")):
    n = os.path.basename(lf)[9:-5]; hg = f"{D}/hold_grid_week_{n}.json"
    if n in SKIP: continue
    cf = next((c for c in (f"{D}/crowd_raw_{CROWD_ALIAS.get(n, n)}.json.gz", f"{D}/crowd_raw_{CROWD_ALIAS.get(n, n)}.json") if os.path.exists(c)), None)
    sp = span_of(n)
    if not (cf and sp) or sp[1] < T0W or sp[0] > T1W: continue
    pieces.append((n, lf, cf, hg if os.path.exists(hg) else None, sp))
cre = collections.defaultdict(list)
for c in json.load(gzip.open(f"{D}/creations_week.json.gz", "rt")): cre[c["creator"].lower()].append((c["ts"], c["cv"].lower()))
def prior_today(creator, t, cv):
    d0 = t - (t % 86400); return sum(1 for x, c in cre.get(creator, ()) if c != cv and d0 <= x < t + 120)
def fleets(r, cv, named, creator, token, upto, reg):
    E.state["watch"].clear(); w = E.watch_curve(cv, 1e7, 1_700_000_000, set(named), creator, blk0=r["b0"], tax_bps=200)
    w["tb"] = bytes.fromhex(token[2:]) if token else None
    j = next((i for i, rw in enumerate(r["blocks"]) if any(t.get("named_fr") or t.get("named_data") for t in rw)), -1)
    for off, rows in enumerate(r["blocks"][: upto + 1]):
        if off < j or (off == j and not reg): continue
        for t in rows:
            E.sender_of = (lambda fr: (lambda tx: fr))(t["fr"])
            data = bytes.fromhex(t["sel"][2:]) if t["direct"] else (bytes.fromhex(t["sel"][2:]) + b"\0" * 12 + bytes.fromhex(cv[2:]) + b"".join(b"\0" * 12 + bytes.fromhex(a[2:]) for a in named if t["named_data"]))
            E.note_attack(w, t["to"], b"", data, cv)
    return E.attack_fleets(w)
def bundle_buyers(r, named):
    nm = set(a.lower() for a in named); s = set(); helper = False
    for rows in r["blocks"][: min(len(r["blocks"]), 10)]:
        for t in rows:
            if t.get("named_fr") and t["fr"].lower() in nm: s.add(t["fr"].lower())
            if t.get("named_data"): helper = True
    return len(nm) if helper else len(s)
# ---- crowd_rules.cums (tables' unit, both wallets and fleets, no registration), per block 0..k+1 -----------------------------
def cums_all(r):
    wallets, fl = set(), set(); cw, cf = [], []
    for off, rows in enumerate(r["blocks"]):
        for t in rows:
            if t["to"] in US or t["to_token"] or t["fr"] in US: continue
            if t["direct"]:
                if not t["named_fr"]: fl.add(t["fr"]); wallets.add(t["fr"])
            elif not t["named_data"]:
                fl.add(t["to"])
                if not t["named_fr"]: wallets.add(t["fr"])
        cw.append(len(wallets)); cf.append(len(fl))
    return cw, cf
rows = {}; piece_of = {}
for n, lf, cf, hg, sp in pieces:
    L = {l["cv"].lower(): l for l in json.load(open(lf))}; H = {h["cv"].lower(): h for h in json.load(open(hg))} if hg else {}
    R = json.load(gzip.open(cf, "rt")) if cf.endswith(".gz") else json.load(open(cf))
    for r in R:
        cv = r["cv"].lower(); l = L.get(cv); h = H.get(cv) or {}; g = GC.get(cv)
        if not l or not (T0W <= l["T0"] <= T1W) or cv in rows: continue
        src = "grid" if h.get("behind1_13_h11") is not None else None
        tbv = TB.get(cv)
        if tbv:
            h = dict(h)
            for kk in ("bundle_eth_chain", "tk0", "init_buy_eth", "tier", "tk_build_13", "tk_seat1_13", "tk_last_13"):
                if h.get(kk) is None and (kk if kk != "bundle_eth_chain" else "bundle_eth") in tbv: h[kk] = tbv[kk if kk != "bundle_eth_chain" else "bundle_eth"]
        if g and not h.get("behind1_13_h11"):
            h = dict(h); h.update({f"behind1_13_h{hh}": g["r2"][hh] for hh in (9, 11, 13, 15)}); h["src"] = "G"; src = "G"
        if not h.get("behind1_13_h11"): continue
        rows[cv] = (r, l, h, src, n)
out = []
for cv, (r, l, h, src, piece) in sorted(rows.items(), key=lambda x: x[1][1]["T0"]):
    t = l["T0"]; named = [a.lower() for a in (l.get("named") or r.get("named") or [])]; creator = (l.get("creator") or r.get("creator") or "").lower()
    tier = l.get("tier", h.get("tier")); tb = round((tier - 0.01) * 10000) if tier is not None else 0
    k = r["k"]; cw, cfl = cums_all(r)
    rec = {"cv": cv, "T0": t, "day": time.strftime("%b %d", time.gmtime(t)), "hour": time.gmtime(t).tm_hour, "piece": piece, "src": src, "k": k,
           "tier": tier, "tb": tb, "bundle": l.get("bundle_eth", h.get("bundle_eth_chain", 0.0)) or 0.0, "creator": creator, "n_named": len(named),
           "repeat": prior_today(creator, t, cv), "tk0": h.get("tk0"), "init_buy_eth": h.get("init_buy_eth"), "nb": bundle_buyers(r, named),
           "e1_block_eth": l.get("e1_block_eth"), "e1_block_buyers": l.get("e1_block_buyers"), "e2_block_buyers": l.get("e2_block_buyers"),
           "cw": cw, "cf": cfl, "in_G": cv in GC, "tk_build": h.get("tk_build_13"), "tk_seat1": h.get("tk_seat1_13"), "tk_last": h.get("tk_last_13")}
    for vw, off in (("k3", k - 3), ("k2", k - 2), ("k1", k - 1), ("k0", k)):
        for reg in (False, True):
            rec[f"f_{vw}{'r' if reg else ''}"] = fleets(r, cv, named, creator, r.get("token"), off, reg) if off >= 0 else 0
    rec["f_E1r"] = fleets(r, cv, named, creator, r.get("token"), k + 1, True)          # every fleet that shot through the seat block (ex post)
    for key, v in h.items():
        if key.startswith(("behind1_", "first_")): rec[key] = v
    if "res" in l:
        for key in ("E1_first_h15_10", "E1_last_h15_10", "E2_first_h15_10", "E2_last_h15_10", "E1_first_h30_10", "E2_first_h30_10", "E1_first_h60_10", "E2_first_h60_10"):
            if key in l["res"]: rec["res_" + key] = l["res"][key][0]
    out.append(rec)
json.dump(out, gzip.open(OUT, "wt"))
print(len(out), "launches;", collections.Counter(x["src"] for x in out), "; in G:", sum(x["in_G"] for x in out), "; pieces", len(pieces))
