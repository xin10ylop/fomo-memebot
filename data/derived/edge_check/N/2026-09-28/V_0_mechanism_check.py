"""V_0 (mechanism lens) on R1's proposal 'deploy engine 6.8's bundle fix'. Replays BOTH engines' own watch_curve / fold_buy
(6.7 = R1/engine67.py = git show 34265b9, 6.8 = src/strategy/sniper_engine.py at aa0f85a) on the chain rows of every launch
of the week (crowd_raw order), with the transactions' REAL ETH values from reviewer D's shots_part.jsonl where it has the
launch (R1 used 0.01 / 0.03 placeholders), and applies the engine's three bundle gates (>= 3 buyers, >= 0.3 ETH, <= 3.0 ETH)
at the moment the engine reads them: the end of the block in which its pre-gate wait (bundle_view: named buyers >= 3 and
ETH >= 0.3, no closing) first passes. Reports: which launches 6.8 adds and removes against 6.7, where the bundle becomes
visible against the tick k, and the usual-view $ of the difference by half (R1's rows_k1reg at slip 0.20)."""
import os, sys, json, time, collections, importlib.util
ROOT = "/home/user/fomo-memebot"; N = f"{ROOT}/data/derived/edge_check/N/2026-09-28"; R1 = f"{N}/R1"
SCR = "/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad"
LIVE = {"SEND_MODULE": "", "PRIVATE_KEY": "", "LOG_PATH": f"{SCR}/v0_engine_log.jsonl", "SEAT": "E1", "ATTACK_MIN": "2", "TIER_MIN_BPS": "100", "TIER_MAX_BPS": "200", "BUNDLE_MIN": "3",
        "BUNDLE_MIN_ETH": "0.3", "BUNDLE_MAX_ETH": "3.0", "MIN_CREATOR_SUPPLY": "0.01", "MAX_CREATOR_BUY_ETH": "2", "HOLD_BLOCKS": "9", "BURST_SLIP": "0.20", "BURST_N": "35",
        "STAKE_MIN": "13", "STAKE_MAX": "13", "WALLET": "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "RELAY": "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
for k, v in LIVE.items(): os.environ[k] = v
os.chdir(ROOT); sys.path.insert(0, R1); sys.path.insert(0, f"{ROOT}/src/strategy")
from common import crowd, load_view, usd, period, days, eligible, US
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
E7 = load("e67", f"{R1}/engine67.py"); E8 = load("e68", f"{ROOT}/src/strategy/sniper_engine.py")
C = crowd(); V = load_view("k1reg"); VK2 = load_view("k2"); VK = load_view("kreg")
VAL = {}
for line in open(f"{ROOT}/data/derived/edge_check/D/shots_part.jsonl"):
    d = json.loads(line); VAL[d["cv"].lower()] = {(off, t["ix"]): t for off, rows in enumerate(d["blocks"]) for t in rows}
def value(cv, off, t, named_row):
    v = VAL.get(cv, {}).get((off, t.get("ix")))
    if v is not None and v["fr"] == t["fr"].lower(): return v["value"], True
    return (0.03 if named_row else 0.01), False
def fold(E, r, upto):
    """the engine's w after folding the chain rows of blocks 0..upto (feed order = chain order); every value from D where known"""
    cv = r["cv"].lower(); named = set(a.lower() for a in r["named"]); creator = r["creator"].lower(); ts0 = 1_700_000_000; blk0 = 1000
    for key in ("valtx", "buys", "sells", "watch"): E.state[key].clear()
    seen = 0.0; real = True
    for off, rows in enumerate(r["blocks"][: upto + 1]):
        for t in sorted(rows, key=lambda t: t.get("ix", 0)):
            if t["fr"] in US or t["to"] in US or t["to_token"]: continue
            seen += 0.001; ts = ts0 if off <= r["k"] - 1 else ts0 + 1
            val, ok = value(cv, off, t, t["named_fr"] or t["named_data"]); real &= ok
            if t["direct"]:
                if t["sel"][2:] == E.BUY_SEL.hex(): E.state["buys"][cv].append((ts, t["fr"], val, seen, blk0 + off, cv, t["sel"][2:]))
                continue
            if val <= 0: continue                                           # the feed records value-less calls in no valtx (and folds them only in seconds 1-2)
            data = bytes.fromhex(t["sel"][2:]) + b"\0" * 12 + bytes.fromhex(cv[2:]) + (b"".join(b"\0" * 12 + bytes.fromhex(a[2:]) for a in named) if t["named_data"] else b"")
            E.state["valtx"].append([seen, ts, t["fr"], val, data, b"", blk0 + off, t["to"], t["sel"][2:]])
    w = E.watch_curve(cv, 1e7, ts0, named, creator, blk0=blk0, tax_bps=200)
    return w, real
def view_passes(r, upto):
    """the pre-gate wait (bundle_view): named buyers (direct or helper, value >= 0.005) and their ETH through block upto, no closing"""
    cv = r["cv"].lower(); named = set(a.lower() for a in r["named"]); b = set(); eth = 0.0
    for off, rows in enumerate(r["blocks"][: upto + 1]):
        for t in rows:
            if t["to_token"] or t["fr"] in US: continue
            val, _ = value(cv, off, t, True)
            if t["named_data"] and val >= 0.005: b |= named; eth += val
            elif t["named_fr"] and t["fr"].lower() in named and val >= 0.005: b.add(t["fr"].lower()); eth += val
    return len(b) >= 3 and eth >= 0.3
def gate(w):
    g = []
    if w["bundle"] < 3: g.append(f"bundle {w['bundle']} < 3")
    if w["bundle_eth"] < 0.3: g.append("ETH < 0.3")
    if w["bundle_eth"] > 3.0: g.append("ETH > 3.0")
    return g
out = []
for cv, x in V.items():
    if cv not in C or x["why"].startswith("PRE"): continue
    r = C[cv]; k = r["k"]
    g = next((o for o in range(0, k) if view_passes(r, o)), None)      # the block whose end lets the engine read its gates (before the tick)
    if g is None: out.append({"cv": cv, "x": x, "g": None}); continue
    w7, real = fold(E7, r, g); w8, _ = fold(E8, r, g)
    out.append({"cv": cv, "x": x, "g": g, "k": k, "real": real, "g7": gate(w7), "g8": gate(w8), "b7": (w7["bundle"], round(w7["bundle_eth"], 3)), "b8": (w8["bundle"], round(w8["bundle_eth"], 3))})
rest_ok = lambda x: x["why"] in ("FILL", "GUARD no fill") or x["why"].startswith("GATE bundle")   # passes the crowd gate at the usual view (or failed only a bundle gate: fleets checked below)
def crowd_ok(x): return (x.get("fleets") or 0) >= 2 and x.get("tier") is not None and 0.02 <= x["tier"] + 1e-9 <= 0.03 or (x.get("fleets") or 0) >= 2 and x["why"] in ("FILL", "GUARD no fill")
print("V_0: 6.7 vs 6.8 bundle gates at the engine's read (the block its bundle wait passes), real values from D where known")
print(f"launches past the pre-gates in the replay: {len(out)}; bundle never visible before the tick (wait fails, both engines skip): {sum(1 for o in out if o['g'] is None)}")
add = [o for o in out if o["g"] is not None and o["g7"] and not o["g8"]]; rem = [o for o in out if o["g"] is not None and not o["g7"] and o["g8"]]
both = [o for o in out if o["g"] is not None and o["g7"] and o["g8"]]
print(f"6.8 admits, 6.7 refused: {len(add)} | 6.8 refuses, 6.7 admitted: {len(rem)} | both refuse: {len(both)}")
print("  6.7's reasons on the added set:", collections.Counter(o["g7"][0].split(" <")[0].split(" >")[0] for o in add).most_common())
print("  6.8's reasons on the removed set:", [(o["cv"][:10], o["g8"], o["b7"], o["b8"]) for o in rem])
print("  both refuse, 6.8's reasons:", collections.Counter(o["g8"][0] for o in both).most_common(6))
print("\nthe added set at the usual view (k-1 + registration), crowd gate as the replay counts it:")
for o in sorted(add, key=lambda o: o["x"]["T0"]):
    x = o["x"]; fired = x.get("fired", False)
    print(f"  {time.strftime('%b %d %H:%M', time.gmtime(x['T0']))} {o['cv'][:10]} k {o['k']} read@blk {o['g']} (k-{o['k'] - o['g']}) 6.7 {o['b7']} {o['g7'][0]:14s} 6.8 {o['b8']} vals {'real' if o['real'] else 'placeholder'} | replay {x['why'][:22]:22s} fleets {x.get('fleets')}" + (f" h11 {x['ret']['11']:+.1%} ${usd(x):+.2f}" if fired and usd(x) is not None else ""))
for vn, VV in (("floor k-2", VK2), ("usual k-1+reg", V), ("ceiling k+reg", VK)):
    s = {}
    for p in ("fit", "read"):
        f = [VV[o["cv"]] for o in add if VV[o["cv"]].get("fired") and period(VV[o["cv"]]["T0"]) == p]; u = [usd(y) for y in f if usd(y) is not None]
        s[p] = f"{len(f)} fires ${sum(u):+.2f} (${sum(u) / days(p):+.2f}/day)"
    print(f"  {vn:14s} fit {s['fit']} | read {s['read']}")
import re; r1_36 = {re.search(r"0x[0-9a-f]{8}", l).group(0) for l in open(f"{R1}/q3_bundle.txt") if l.startswith("  closed by a") and ("FILL" in l or "GUARD" in l)}
mine = {o["cv"][:10] for o in add if o["x"].get("fired")}
print(f"\nR1's 20 usual-view fires vs this replay's added fires: in both {len(r1_36 & mine)}, R1 only {sorted(r1_36 - mine)}, here only {sorted(mine - r1_36)}")
print("\nwhere the bundle becomes readable, block offset before the tick (k - g), fired launches at the usual view:")
for lab, S in (("added by 6.8", [o for o in add if o["x"].get("fired")]), ("admitted by both", [o for o in out if o["g"] is not None and not o["g7"] and not o["g8"] and o["x"].get("fired")])):
    c = collections.Counter(o["k"] - o["g"] for o in S); print(f"  {lab:18s} n={len(S):3d} " + " ".join(f"k-{d}:{c[d]}" for d in sorted(c)))
closers = collections.Counter()
for o in add:
    r = C[o["cv"]]; named = set(a.lower() for a in r["named"])
    for off, rows in enumerate(r["blocks"]):
        hit = next((t for t in sorted(rows, key=lambda t: t.get("ix", 0)) if not t["named_fr"] and not t["named_data"] and not t["to_token"] and t["fr"] not in US), None)
        if hit: closers[(hit["fr"][:10], hit["to"][:10])] += 1; break
print("\nthe first stranger in the added launches (sender, target):", closers.most_common(5))
print("\nR1's usual-view fires not in the added set here:")
for p in sorted(r1_36 - mine):
    o = next(o for o in out if o["cv"].startswith(p)); x = o["x"]
    print(f"  {time.strftime('%b %d %H:%M', time.gmtime(x['T0']))} {p} read@blk {o['g']} k {x['k']} 6.7 {o.get('b7')} {o.get('g7')} 6.8 {o.get('b8')} {o.get('g8')} vals {'real' if o.get('real') else 'ph'} | replay bundle {x['bundle']:.3f} {x['why'][:10]} ${usd(x):+.2f}")
print("\nboth engines refuse at their read while the replay's bundle gates pass (an engine-vs-model gap 6.8 does not touch):")
for o in out:
    if o["g"] is not None and o["g8"] and o["g7"]:
        x = o["x"]; print(f"  {time.strftime('%b %d %H:%M', time.gmtime(x['T0']))} {o['cv'][:10]} 6.7 {o['b7']} 6.8 {o['b8']} {o['g8'][0]:10s} vals {'real' if o['real'] else 'ph'} | replay bundle {x['bundle']:.3f} {x['why'][:24]:24s} fleets {x.get('fleets')}" + (f" ${usd(x):+.2f}" if x.get('fired') and usd(x) is not None else ""))
nv = [o for o in out if o["g"] is None]
f = [o for o in nv if o["x"].get("fired")]
print(f"\nnever readable before the tick by this reconstruction: {len(nv)} launches, {len(f)} of them usual-view replay fires (${sum(usd(o['x']) or 0 for o in f):+.2f}):", collections.Counter(o["x"]["why"][:16] for o in nv).most_common(5))
