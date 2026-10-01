"""engine_replay.py: the week through the engine's own decision chain, on the chain alone (report 24.41). One basis, no paper or
live readings mixed in: every qualifying launch of the readings' pipeline (launches / crowd / hold-grid files per piece), taken
through the engine's gates in the engine's order with the engine's live settings (runbook 5q-5u), the crowd gate counted by the
engine's own note_attack / attack_fleets on the feed's k-2 view after the curve's registration (the seam test proves that count
equals the tables' on 563 launches), the minOut guard on the engine's sizing (BURST_SLIP), and the fill priced by the same model
the fills reconcile to (second place in the seat block, sold 11 blocks later, $13, gas $0.33 a burst).

Not replayable from the chain, and only ever removing fires: the aim ("no confident boundary estimate"), the registration race
inside the first named block, the sequencer holding a burst, the resolve limit. The creator-repeat gate counts every creation
of the UTC day (creations_week.json.gz); the engine's own counter restarts with the engine, so a column without it is shown.

    python3 src/analysis/engine_replay.py [--from "2026-09-21 09:40"] [--to "2026-09-28 09:40"] [--hold 11] [--no-cap] [--no-repeat] [--view k-1]"""
import os, sys, json, gzip, glob, time, calendar, statistics as st, collections
args = sys.argv[1:]
def arg(k, d=None):
    if k in args: i = args.index(k); v = args[i + 1]; del args[i:i + 2]; return v
    return d
def flag(k):
    if k in args: args.remove(k); return True
    return False
T0 = calendar.timegm(time.strptime(arg("--from", "2026-09-21 09:40"), "%Y-%m-%d %H:%M")); T1 = calendar.timegm(time.strptime(arg("--to", "2026-09-28 09:40"), "%Y-%m-%d %H:%M"))
HOLD = int(arg("--hold", "11")); NO_CAP = flag("--no-cap"); NO_REPEAT = flag("--no-repeat"); VIEW = arg("--view", "k-2"); REG = flag("--reg"); DUMP = arg("--dump"); SLIP = float(arg("--slip", "0.07"))   # --slip: the minOut guard's tolerance to test (the live BURST_SLIP is 0.07)   # --dump file.json: every launch's row (disposition, fleets at k-2/k-1/k, guard ratio, returns by position and hold)   # --reg: count the registration block's shots (the engine does when its launch thread wins the race: 3 of 4 live cases)
LIVE = {"SEND_MODULE": "", "PRIVATE_KEY": "", "LOG_PATH": "/tmp/engine_replay.jsonl", "SEAT": "E1", "ATTACK_MIN": os.environ.get("REPLAY_ATTACK_MIN", "3"), "GATE_CLOSE_MS": "36", "TRADE_HOURS": "",
        "MIN_FOLLOW_ETH_60": "0", "TIER_MIN_BPS": "100", "TIER_MAX_BPS": os.environ.get("REPLAY_TIER_MAX", "300"), "BUNDLE_MIN": "3", "NAMED_MAX": os.environ.get("REPLAY_NAMED_MAX", "12"), "BUNDLE_MIN_ETH": "0.3", "BUNDLE_MAX_ETH": "0" if NO_CAP else "3.0",
        "MIN_CREATOR_SUPPLY": "0.01", "MAX_CREATOR_BUY_ETH": "2", "HOLD_BLOCKS": "9", "BURST_SLIP": "0.07", "BURST_N": "35", "STAKE_MIN": "13", "STAKE_MAX": "13",
        "WALLET": "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "RELAY": "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
for k, v in LIVE.items(): os.environ[k] = v
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."); os.chdir(ROOT); sys.path.insert(0, "src/strategy"); import sniper_engine as E
_argv = sys.argv; sys.argv = ["x", "0.76", "0.71"]; exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0]); sys.argv = _argv   # cums, at (the tables' count per block, for the dump)
STAKE, GAS = 13.0, 0.33; BUSY_S = 6.0
try: SMART = {a.lower() for a in (json.load(open(arg("--smart", "data/derived/smart_helpers.json"))).get("helpers") or {})}   # 6.13: the helpers the engine boosts to $50 on
except Exception: SMART = set()
D = "data/derived/live_vs_table"
KNOWN = {"sep2021": ("2026-09-20 13:26", "2026-09-22 01:02"), "sep2223": ("2026-09-22 01:02", "2026-09-23 06:35"), "sep23day": ("2026-09-23 10:22", "2026-09-23 20:20"), "sep24_paper": ("2026-09-24 12:38", "2026-09-24 21:36")}
CROWD_ALIAS = {"sep24_paper": "sep24paper"}
def span_of(n):
    for f in glob.glob(f"data/derived/*/e1m_{n}.json"):
        d = json.load(open(f)); return d["t_lo"], d["t_hi"]
    return KNOWN.get(n) and tuple(calendar.timegm(time.strptime(x, "%Y-%m-%d %H:%M")) for x in KNOWN[n])
GC = {x["cv"].lower(): x for x in json.load(gzip.open("data/derived/edge_check/G/curves.json.gz", "rt"))} if os.path.exists("data/derived/edge_check/G/curves.json.gz") else {}
TB = json.load(gzip.open(f"{D}/tape_bundles.json.gz", "rt")) if os.path.exists(f"{D}/tape_bundles.json.gz") else {}   # the exempt bundle, the creator's buy and the tier from the edge review's tapes (B, D), for the older launch files   # reviewer G's second-place return at every exit block ($13): the same model, agrees with the grid to 0.4% at worst on 51 shared launches
pieces = []; SKIP = ("141_creators", "175_sep2223", "oos_sep2021", "today_sep23", "sep1819")
for lf in sorted(glob.glob(f"{D}/launches_*.json")):
    n = os.path.basename(lf)[9:-5]; hg = f"{D}/hold_grid_week_{n}.json"
    if n in SKIP: continue
    cf = next((c for c in (f"{D}/crowd_raw_{CROWD_ALIAS.get(n, n)}.json.gz", f"{D}/crowd_raw_{CROWD_ALIAS.get(n, n)}.json") if os.path.exists(c)), None)
    sp = span_of(n)
    if not (cf and sp) or sp[1] < T0 or sp[0] > T1: continue
    pieces.append((n, lf, cf, hg if os.path.exists(hg) else None, sp))
cre = collections.defaultdict(list)
if os.path.exists(f"{D}/creations_week.json.gz"):
    for c in json.load(gzip.open(f"{D}/creations_week.json.gz", "rt")): cre[c["creator"].lower()].append((c["ts"], c["cv"].lower()))
else: NO_REPEAT = True; print("creations_week.json.gz missing: the creator-repeat gate is not applied", file=sys.stderr)
def prior_today(creator, t, cv):
    """the creator's other creations earlier in the UTC day (the file's timestamps are interpolated between hourly anchors, so the launch
    itself is excluded by its curve, not by its time, and a creation within two minutes after is not counted as earlier)"""
    d0 = t - (t % 86400); return sum(1 for x, c in cre.get(creator, ()) if c != cv and d0 <= x < t + 120)
def fleets(r, cv, named, creator, token, upto):
    """the engine's count on the feed's view through block offset `upto`, after the curve's registration (the first named block)"""
    E.state["watch"].clear(); w = E.watch_curve(cv, 1e7, 1_700_000_000, set(named), creator, blk0=r["b0"], tax_bps=200)
    w["tb"] = bytes.fromhex(token[2:]) if token else None
    j = next((i for i, rw in enumerate(r["blocks"]) if any(t.get("named_fr") or t.get("named_data") for t in rw)), -1)
    for off, rows in enumerate(r["blocks"][: upto + 1]):
        if off < j or (off == j and not REG): continue
        for t in rows:
            E.sender_of = (lambda fr: (lambda tx: fr))(t["fr"])
            data = bytes.fromhex(t["sel"][2:]) if t["direct"] else (bytes.fromhex(t["sel"][2:]) + b"\0" * 12 + bytes.fromhex(cv[2:]) + b"".join(b"\0" * 12 + bytes.fromhex(a[2:]) for a in named if t["named_data"]))
            E.note_attack(w, t["to"], b"", data, cv)
    return E.attack_fleets(w), {a.lower() for a in w.get("attack_targets", ())}
def bundle_buyers(r, named):
    nm = set(a.lower() for a in named); s = set(); helper = False
    for rows in r["blocks"][: min(len(r["blocks"]), 10)]:
        for t in rows:
            if t.get("named_fr") and t["fr"].lower() in nm: s.add(t["fr"].lower())
            if t.get("named_data"): helper = True
    return len(nm) if helper else len(s)
rows = {}; cover = []; pending = set(); no_tk0 = 0; no_guard = 0
for n, lf, cf, hg, sp in pieces:
    L = {l["cv"].lower(): l for l in json.load(open(lf))}; H = {h["cv"].lower(): h for h in json.load(open(hg))} if hg else {}
    R = json.load(gzip.open(cf, "rt")) if cf.endswith(".gz") else json.load(open(cf)); cover.append((max(sp[0], T0), min(sp[1], T1)))
    for r in R:
        cv = r["cv"].lower(); l = L.get(cv); h = H.get(cv) or {}; g = GC.get(cv)
        if not l or not (T0 <= l["T0"] <= T1) or cv in rows: continue
        tbv = TB.get(cv)
        if tbv:
            h = dict(h)
            for kk in ("bundle_eth_chain", "tk0", "init_buy_eth", "tier", "tk_build_13", "tk_seat1_13", "tk_last_13"):
                if h.get(kk) is None and (kk if kk != "bundle_eth_chain" else "bundle_eth") in tbv: h[kk] = tbv[kk if kk != "bundle_eth_chain" else "bundle_eth"]
        if g and not h.get("behind1_13_h11"):
            h = dict(h); h.update({f"behind1_13_h{hh}": g["r2"][hh] for hh in (9, 11, 13, 15)}); h["src"] = "G"
        if not h.get("behind1_13_h11"): pending.add(cv); continue
        rows[cv] = (r, l, h)
launches = sorted(rows.values(), key=lambda x: x[1]["T0"])
cover.sort(); merged = []
for lo, hi in cover:
    if merged and lo <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], hi)
    else: merged.append([lo, hi])
hours = collections.Counter(); day = lambda t: time.strftime("%b %d", time.gmtime(t))
for lo, hi in merged:
    t = lo
    while t < hi:
        nxt = min(hi, (t // 86400 + 1) * 86400); hours[day(t)] += (nxt - t) / 3600; t = nxt
out = []; busy_until = 0.0; Y0 = E.Y0
for r, l, h in launches:
    cv = l["cv"].lower(); t = l["T0"]; named = [a.lower() for a in (l.get("named") or r.get("named") or [])]; creator = (l.get("creator") or r.get("creator") or "").lower()
    tier = l.get("tier", h.get("tier")); tb = round((tier - 0.01) * 10000) if tier is not None else 0
    rec = {"cv": cv, "T0": t, "day": day(t), "bundle": l.get("bundle_eth", h.get("bundle_eth_chain", 0.0)) or 0.0, "why": None}   # the older launch files: the bundle from the grid's tape
    reasons = []
    if not NO_REPEAT and prior_today(creator, t, cv) > 0: reasons.append("creator repeat")
    tk0 = h.get("tk0")
    if tk0 is None: no_tk0 += 1                                            # the older pieces' grids are not in yet: the creator-supply gate cannot be applied there (counted)
    elif tk0 <= 0 or tk0 >= Y0: reasons.append("no launch-block buy")
    elif tk0 < E.MIN_CREATOR_SUPPLY * Y0: reasons.append("creator supply < 1%")
    if (h.get("init_buy_eth") or 0.0) > E.MAX_CREATOR_BUY_ETH: reasons.append("creator buy > 2 ETH")
    if E.team_bundle(named): reasons.append(f"team bundle ({len(named)} named > {E.NAMED_MAX})")
    if reasons: rec["why"] = "PRE " + reasons[0]; out.append(rec); continue
    gates = []
    nb = bundle_buyers(r, named)
    if nb < E.BUNDLE_MIN: gates.append(f"bundle {nb} < {E.BUNDLE_MIN}")
    if rec["bundle"] < E.BUNDLE_MIN_ETH: gates.append("bundle ETH < 0.3")
    if E.BUNDLE_MAX_ETH > 0 and rec["bundle"] > E.BUNDLE_MAX_ETH: gates.append("bundle ETH > 3.0 (cap)")
    if tb < E.TIER_MIN_BPS or tb > E.TIER_MAX_BPS: gates.append("tier")
    if t < busy_until: gates.append("position open")
    k = r["k"]; upto = {"k-2": k - 2, "k-1": k - 1, "k": k}[VIEW]
    fl, tg = fleets(r, cv, named, creator, r.get("token"), upto); rec["fleets"] = fl; rec["smart"] = bool(tg & SMART)   # 6.13: a boosted helper is attacking
    if fl < E.ATTACK_MIN: gates.append(f"attackers {fl} < {E.ATTACK_MIN}")
    if gates: rec["why"] = "GATE " + gates[0]; out.append(rec); continue
    rec["fired"] = True
    tb_, ts1 = h.get("tk_build_13"), h.get("tk_seat1_13")
    rec["guard_ratio"] = (ts1 / tb_) if (tb_ and ts1) else None
    if not (tb_ and ts1): no_guard += 1
    if tb_ and ts1 and ts1 < (1 - SLIP) * tb_:
        rec["why"] = "GUARD no fill"; rec["usd"] = -GAS; out.append(rec); continue
    ret = h.get(f"behind1_13_h{HOLD}")
    if ret is None: rec["why"] = "no return column"; out.append(rec); continue
    rec["why"] = "FILL"; rec["ret"] = ret; rec["usd"] = ret * STAKE - GAS; rec["rets"] = {hh: h.get(f"behind1_13_h{hh}") for hh in (9, 11, 13, 15)}; busy_until = t + BUSY_S; out.append(rec)
print(f"engine replay, week {time.strftime('%b %d %H:%M', time.gmtime(T0))} - {time.strftime('%b %d %H:%M', time.gmtime(T1))} UTC: {len(out)} qualifying launches, {sum(hours.values()):.0f} covered hours of {(T1 - T0) / 3600:.0f}; view {VIEW}{' with the registration block' if REG else ' after the registration block'}, hold {HOLD}, cap {'off' if NO_CAP else '3.0'}, creator-repeat gate {'off' if NO_REPEAT else 'on'}; pieces {len(pieces)}")
print("the engine's gate view on the ten live bursts of Sep 26-28 sat at k-2 five times, k-1 twice, k once (two fired on any view); the registration block counted in three of four races: k-2 without it is the floor, k with it the ceiling")
if pending or no_tk0 or no_guard: print(f"NOT COMPLETE: {len(pending)} launches without a return yet (grids still running); creator-supply gate not applicable on {no_tk0} launches, minOut guard on {no_guard} fired launches (no grid fields for the older pieces yet)")
days = sorted(set(x["day"] for x in out) | set(hours), key=lambda d: time.strptime(d + " 2026", "%b %d %Y"))
print(f"\n{'day':7s} {'hours':>5s} {'launch':>6s} {'PRE':>4s} {'GATE':>4s} {'fired':>5s} {'guard':>5s} {'fills':>5s}  {'mean h%d' % HOLD:>9s} {'median':>7s} {'win':>4s} {'dead':>4s}  {'$ total':>8s}  {'fires/24h':>9s} {'$/24h':>7s}")
def summarize(rs, label, hrs=None):
    fired = [x for x in rs if x.get("fired")]; fills = [x for x in fired if x["why"] == "FILL"]; v = [x["ret"] for x in fills]; usd = sum(x.get("usd", 0.0) for x in fired)
    pre = sum(1 for x in rs if x["why"].startswith("PRE")); gate = sum(1 for x in rs if x["why"].startswith("GATE")); guard = sum(1 for x in fired if x["why"].startswith("GUARD"))
    m = st.mean(v) if v else float("nan"); md = st.median(v) if v else float("nan"); win = sum(x > 0 for x in v) / len(v) if v else float("nan"); dead = sum(x < -0.4 for x in v) / len(v) if v else float("nan")
    rate = f"{len(fired) / hrs * 24:9.1f} {usd / hrs * 24:+7.2f}" if hrs else f"{'':9s} {'':7s}"
    print(f"{label:7s} {hrs if hrs else 0:5.1f} {len(rs):6d} {pre:4d} {gate:4d} {len(fired):5d} {guard:5d} {len(fills):5d}  {m:+9.1%} {md:+7.1%} {win:4.0%} {dead:4.0%}  {usd:+8.2f}  {rate}")
for d in days: summarize([x for x in out if x["day"] == d], d, hours.get(d, 0.0))
summarize(out, "week", sum(hours.values()))
fills = [x for x in out if x["why"] == "FILL"]
print("\nby hold, the same fills:")
for hh in (9, 11, 13, 15):
    v = [x["rets"][hh] for x in fills if x["rets"].get(hh) is not None]
    if v: print(f"  h{hh:<3d} {len(v):3d} fills  mean {st.mean(v):+6.1%}  median {st.median(v):+6.1%}  win {sum(x > 0 for x in v) / len(v):3.0%}  ${sum(x * STAKE - GAS for x in v):+8.2f}")
why = collections.Counter(x["why"] for x in out); print("\ndispositions:", ", ".join(f"{k} {v}" for k, v in why.most_common()))
big = sorted(fills, key=lambda x: -x["ret"])[:6]
print("largest fills: " + ", ".join(f"{time.strftime('%b %d %H:%M', time.gmtime(x['T0']))} {x['cv'][:10]} {x['ret']:+.0%}" for x in big))
if len(fills) > 1:
    rest = [x["ret"] for x in fills if x is not big[0]]; print(f"without the largest: mean {st.mean(rest):+.1%} on {len(rest)} fills, ${sum(x * STAKE - GAS for x in rest):+.2f}")
sm = [x for x in fills if x.get("smart")]
if SMART: print(f"boosted (a smart helper attacking, $50 live since Oct 1, 5am): {len(sm)} of {len(fills)} fills" + (f", mean {st.mean(x['ret'] for x in sm):+.1%}, {sum(x['ret'] > 0 for x in sm)} positive; at $25/$50 the fills net ${sum(x['ret'] * (50 if x.get('smart') else 25) - GAS for x in fills):+.2f} against ${sum(x['ret'] * 25 - GAS for x in fills):+.2f} flat" if sm else ""))
if DUMP:
    for x in out:
        r, l, h = rows[x["cv"]]; cw, cf = cums(r); k = r["k"]
        x.update({"k": k, "cf": cf, "f_k2": at(cf, k - 2), "f_k1": at(cf, k - 1), "f_k": at(cf, k), "tier": l.get("tier", h.get("tier")), "tk0": h.get("tk0"), "init_buy_eth": h.get("init_buy_eth"), "named": len(l.get("named") or r.get("named") or []),
                  "guard_ratio": x.get("guard_ratio") if x.get("guard_ratio") is not None else ((h.get("tk_seat1_13") / h.get("tk_build_13")) if (h.get("tk_build_13") and h.get("tk_seat1_13")) else None),
                  "ret": {hh: h.get(f"behind1_13_h{hh}") for hh in (9, 11, 13, 15, 30, 60)}, "ret_first": {hh: h.get(f"first_13_h{hh}") for hh in (9, 11, 13, 15)},
                  "tp50_h600": h.get("behind1_13_tp50_h600"), "stop20_h600": h.get("behind1_13_stop20_h600"), "src": h.get("src")})
    json.dump(out, open(DUMP, "w")); print(f"dumped {len(out)} rows to {DUMP}", file=sys.stderr)
if flag("--list"):
    for x in out: print(f"  {time.strftime('%b %d %H:%M', time.gmtime(x['T0']))} {x['cv'][:10]} bundle {x['bundle']:.3f} fleets {x.get('fleets', '-')}{' BOOST' if x.get('smart') else ''} | {x['why']}" + (f" {x['ret']:+.1%}" if "ret" in x else ""))
