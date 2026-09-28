"""V_0 mechanism lens, part 2 (after V_0_mechanism_check.py). Joins, per launch, the engine's view of each transaction (crowd_raw rows:
sender, target, selector, named in calldata; D's shots_part for the ETH value) with the chain's Buy events (B/D tapes: buyer, ETH,
tokens; the fee from the curve fold exactly as src/analysis/e1_multi.py: exempt = |fee - tier| <= 0.0008, taxed = fee > 0.5, the
creation's own first buy excluded, creation second = offsets 0..k). Reports:
 Q1  every engine category of fold_buy after 6.8 (named direct, named via helper, creator direct, helper naming buyers, taxed helper,
     outsider), how much of what 6.8 counts the tables call exempt, split before / after 6.7's close; and which table-exempt buys
     the engine does not count.
 Q2  6.7 vs 6.8 gate verdicts (>= 3 buyers, >= 0.3 ETH, <= 3.0 ETH) with each engine's own watch_curve at every read offset
     0..k (not only the block the wait passes); the closest 6.7-partial launch to the 3.0 cap; the contested-launch test (a taxed
     stranger's buy, or a stranger's direct buy, ahead of the team's third exempt buy) on all launches past the pre-gates, model h11.
 Q3  the engine's bundle ETH against the tables' exempt ETH on the launches the cap refuses, by category, and every launch on the
     week where the two sit on different sides of 0.3 or 3.0 at the engine's read."""
import os, sys, json, time, collections, importlib.util, statistics as st
ROOT = "/home/user/fomo-memebot"; N = f"{ROOT}/data/derived/edge_check/N/2026-09-28"; R1 = f"{N}/R1"
SCR = "/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad"
LIVE = {"SEND_MODULE": "", "PRIVATE_KEY": "", "LOG_PATH": f"{SCR}/v0q_engine_log.jsonl", "SEAT": "E1", "ATTACK_MIN": "2", "TIER_MIN_BPS": "100", "TIER_MAX_BPS": "200", "BUNDLE_MIN": "3",
        "BUNDLE_MIN_ETH": "0.3", "BUNDLE_MAX_ETH": "3.0", "MIN_CREATOR_SUPPLY": "0.01", "MAX_CREATOR_BUY_ETH": "2", "HOLD_BLOCKS": "9", "BURST_SLIP": "0.20", "BURST_N": "35",
        "STAKE_MIN": "13", "STAKE_MAX": "13", "WALLET": "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "RELAY": "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
for k, v in LIVE.items(): os.environ[k] = v
os.chdir(ROOT); sys.path.insert(0, R1)
from common import crowd, load_view, usd, period, US
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
E7 = load("e67", f"{R1}/engine67.py"); E8 = load("e68", f"{ROOT}/src/strategy/sniper_engine.py")
C = crowd(); V = load_view("k1reg"); BUY = E8.BUY_SEL.hex(); TAXED = E8.TAXED_HELPER_SELS; X0, Y0 = 1.68, 1e9
VAL = {}
for line in open(f"{ROOT}/data/derived/edge_check/D/shots_part.jsonl"):
    d = json.loads(line); VAL[d["cv"].lower()] = {(off, t["ix"]): t for off, rows in enumerate(d["blocks"]) for t in rows}
def tape(cv):
    for p in (f"{ROOT}/data/derived/edge_check/D/tapes/{cv}.json", f"{ROOT}/data/derived/edge_check/B/tapes/{cv}.json"):
        if os.path.exists(p): return json.load(open(p))
def value(cv, off, t):
    v = VAL.get(cv, {}).get((off, t.get("ix")))
    return (v["value"], True) if v is not None and v["fr"] == t["fr"].lower() else (None, False)
def hhmm(T): return time.strftime("%b %d %H:%M", time.gmtime(T))

def engine_txs(r):
    """the engine's view of every captured transaction in blocks 0..k+1, chain order, with fold_buy's category after 6.8"""
    cv = r["cv"].lower(); named = set(a.lower() for a in r["named"]); creator = r["creator"].lower(); out = []
    for off, rows in enumerate(r["blocks"]):
        for t in sorted(rows, key=lambda t: t.get("ix", 0)):
            fr = t["fr"].lower(); sel = t["sel"][2:]
            if fr in US or t["to"] in US or t["to_token"]: continue
            val, real = value(cv, off, t)
            if t["direct"]:
                if sel != BUY: cat = "direct non-buy (not folded)"
                elif fr in named: cat = "named direct"
                elif fr == creator: cat = "creator direct"
                else: cat = "outsider direct"
            else:
                if real and val <= 0: cat = "value-less call (not folded in s0)"
                elif t["named_data"]: cat = "helper naming buyers"
                elif fr in named: cat = "taxed helper 4d819a2a (named)" if sel in TAXED else "named via helper"
                elif fr == creator: cat = "creator via helper (not counted)"
                else: cat = "outsider value call"
            out.append({"off": off, "ix": t["ix"], "fr": fr, "to": t["to"], "sel": sel, "val": val, "real": real, "cat": cat})
    return out
COUNTED = {"named direct", "creator direct", "helper naming buyers", "named via helper"}
CLOSERS = {"outsider direct", "outsider value call"}

def tape_buys(L, k):
    """(off, ti) -> list of creation-second Buy events with fee class, as e1_multi (the creation's own buy excluded)"""
    X, Y = X0, Y0; out = collections.defaultdict(list); b0 = L["b0"]; tier = L["tier"]
    for i, row in enumerate(sorted(L["rows"], key=lambda x: (x["bn"], x["li"]))):
        off = row["bn"] - b0
        if off > k: break
        if row["k"] == "B":
            tk, eth = row["tk"], row["eth"]
            if 0 < tk < Y:
                net = X * tk / (Y - tk); fee = 1 - net / eth if eth > 0 else 1; X, Y = X + net, Y - tk
                if i > 0:
                    cls = "exempt" if abs(fee - tier) <= 0.0008 else ("taxed" if fee > 0.5 else "other")
                    out[(off, row["ti"])].append({"eth": eth, "cls": cls, "who": row["who"], "fee": fee})
        else:
            tk = row["tk"]; g = X - X * Y / (Y + tk); X, Y = X - g, Y + tk
    return out

pop = [cv for cv, x in V.items() if not x["why"].startswith("PRE") and cv in C]
print(f"launches past the pre-gates with crowd rows: {len(pop)}; with a tape (Buy events, fees): {sum(1 for cv in pop if tape(cv))}")

# ---------------------------------------------------------------- Q1
print("\nQ1. fold_buy's categories after 6.8 against the tables' exempt rule (creation second, blocks 0..min(k,9)); launches with a tape; tx value from D where it has the tx (count shown), else 0")
agg = collections.defaultdict(lambda: collections.Counter()); ex_by_cat = collections.Counter(); ex_total = 0.0; nl = 0; unmatched_ex = []
for cv in pop:
    L = tape(cv); r = C[cv]
    if not L: continue
    nl += 1; k = r["k"]; tb = tape_buys(L, k); txs = engine_txs(r); closed = False; seen_keys = set()
    for t in txs:
        if t["off"] > min(k, 9): continue
        side = "after 6.7's close" if closed else "before"
        buys = tb.get((t["off"], t["ix"]), []); seen_keys.add((t["off"], t["ix"]))
        a = agg[(t["cat"], side)]; a["txs"] += 1; a["txs_real"] += t["real"]; a["val"] += (t["val"] or 0.0)
        a["no_buy"] += (not buys)
        for b in buys: a[b["cls"] + "_eth"] += b["eth"]; a[b["cls"] + "_n"] += 1
        if t["cat"] in CLOSERS: closed = True
    for key, bl in tb.items():
        for b in bl:
            if b["cls"] != "exempt": continue
            ex_total += b["eth"]; cat = next((t["cat"] for t in txs if (t["off"], t["ix"]) == key), "not in crowd rows")
            ex_by_cat[cat] += b["eth"]
            if cat not in COUNTED: unmatched_ex.append((hhmm(V[cv]["T0"]), cv[:10], key, cat, round(b["eth"], 4)))
print(f"  {nl} launches. per category and side: txs (with D value) | tx value (engine ETH) | Buy events: exempt n/ETH, taxed n/ETH, other n | txs with no Buy")
for (cat, side), a in sorted(agg.items(), key=lambda kv: (kv[0][0] not in COUNTED, kv[0][0], kv[0][1])):
    print(f"  {'COUNTED ' if cat in COUNTED else '        '}{cat:36s} {side:18s} {a['txs']:5d} ({a['txs_real']:5d}) | {a['val']:8.3f} | ex {a['exempt_n']:4d} {a['exempt_eth']:7.3f}  tax {a['taxed_n']:3d} {a['taxed_eth']:6.3f}  oth {a['other_n']:3d} | no buy {a['no_buy']:4d}")
print(f"  the tables' exempt ETH, {ex_total:.3f} in all, by the engine category of its transaction: " + ", ".join(f"{c} {e:.3f}" for c, e in ex_by_cat.most_common()))
print(f"  exempt buys the engine does not count: {len(unmatched_ex)}, {sum(u[4] for u in unmatched_ex):.3f} ETH, by launch:")
by = collections.defaultdict(list)
for u in unmatched_ex: by[(u[0], u[1])].append(u)
for (T, c10), us in sorted(by.items()):
    x = next(v for cv, v in V.items() if cv.startswith(c10))
    print(f"    {T} {c10} {len(us)} buys {sum(u[4] for u in us):.3f} ETH, category {collections.Counter(u[3] for u in us).most_common()} | replay {x['why'][:24]}, tables' bundle {x['bundle']:.3f}")

# ---------------------------------------------------------------- Q2
def fold(E, r, upto):
    cv = r["cv"].lower(); named = set(a.lower() for a in r["named"]); creator = r["creator"].lower(); ts0 = 1_700_000_000; blk0 = 1000
    for key in ("valtx", "buys", "sells", "watch"): E.state[key].clear()
    seen = 0.0
    for off, rows in enumerate(r["blocks"][: upto + 1]):
        for t in sorted(rows, key=lambda t: t.get("ix", 0)):
            if t["fr"] in US or t["to"] in US or t["to_token"]: continue
            seen += 0.001; val, ok = value(cv, off, t)
            if val is None: val = 0.03 if (t["named_fr"] or t["named_data"]) else 0.01
            if t["direct"]:
                if t["sel"][2:] == BUY: E.state["buys"][cv].append((ts0, t["fr"], val, seen, blk0 + off, cv, t["sel"][2:]))
                continue
            if val <= 0: continue
            data = bytes.fromhex(t["sel"][2:]) + b"\0" * 12 + bytes.fromhex(cv[2:]) + (b"".join(b"\0" * 12 + bytes.fromhex(a[2:]) for a in named) if t["named_data"] else b"")
            E.state["valtx"].append([seen, ts0, t["fr"], val, data, b"", blk0 + off, t["to"], t["sel"][2:]])
    return E.watch_curve(cv, 1e7, ts0, named, creator, blk0=blk0, tax_bps=200)
def gates(w):
    g = []
    if w["bundle"] < 3: g.append("count")
    if w["bundle_eth"] < 0.3: g.append("floor")
    if w["bundle_eth"] > 3.0: g.append("cap")
    return g
print("\nQ2. 6.7 vs 6.8 at EVERY read offset 0..k (the engine's own watch_curve / fold_buy, D's values, placeholders 0.03 / 0.01 where D has none)")
flips = collections.Counter(); new_ref = []; partial = []; per_launch_add = set()
for cv in pop:
    r = C[cv]; k = r["k"]
    for o in range(0, k + 1):
        w7 = fold(E7, r, o); g7 = gates(w7); b7 = (w7["bundle"], w7["bundle_eth"])
        w8 = fold(E8, r, o); g8 = gates(w8); b8 = (w8["bundle"], w8["bundle_eth"])
        assert b8[0] >= b7[0] and b8[1] >= b7[1] - 1e-12, (cv, o, b7, b8)
        if g7 and not g8: flips["6.8 admits"] += 1; per_launch_add.add(cv)
        if g8 and not g7: flips["6.8 refuses"] += 1; new_ref.append((hhmm(V[cv]["T0"]), cv[:10], o, k, b7, b8, g8))
        if g7 and g8 and set(g7) != set(g8): flips["both refuse, other reason"] += 1
        if not g7 and b8[1] > b7[1] + 1e-9: partial.append((round(3.0 - b8[1], 3), hhmm(V[cv]["T0"]), cv[:10], o, k, (b7[0], round(b7[1], 3)), (b8[0], round(b8[1], 3))))
print(f"  (launch, offset) pairs: {dict(flips)}; launches 6.8 admits at some offset: {len(per_launch_add)}")
print(f"  6.8 refuses where 6.7 admits: {len(new_ref)}", new_ref[:5])
partial.sort()
print(f"  6.7 admits with a partial count (6.8 counts more): {len(partial)} (launch, offset) pairs on {len(set(p[2] for p in partial))} launches; closest to the cap (3.0 - 6.8 ETH):")
for p in partial[:5]: print("   ", p)
seenp = set()
for p in sorted(partial, key=lambda p: p[0]):
    if p[2] in seenp: continue
    seenp.add(p[2]); cvp = next(cv for cv in pop if cv.startswith(p[2])); x = V[cvp]
    print(f"    {p[1]} {p[2]} 6.8 {p[6]} vs 6.7 {p[5]} at offset {p[3]} of k {p[4]} | tables' exempt ETH {x['bundle']:.3f} | values {'real' if all(t['real'] for t in engine_txs(C[cvp]) if t['off'] <= p[3]) else 'placeholder'} | replay {x['why'][:14]}")
mx = max((fold(E8, C[cv], C[cv]["k"])["bundle_eth"], cv) for cv in per_launch_add)
print(f"  the largest 6.8 bundle ETH among the launches 6.8 newly admits (read at k): {mx[0]:.3f} ({mx[1][:10]}, tables {V[mx[1]]['bundle']:.3f})")
print("  a stranger's shot can only ADD to 6.8's count (asserted on every pair): the floor and the count can only newly pass; the cap is the only gate 6.8 can newly fail")

print("\n  one position: replay rows 'GATE position open' at the usual view:", sum(1 for x in V.values() if "position open" in x["why"]))

print("\n  contested launch? launches past the pre-gates, the model's h11 at second place (rows_k1reg 'ret'), by what sits ahead of the team's third exempt buy (tapes):")
grp = collections.defaultdict(list); grpf = collections.defaultdict(list)
for cv in pop:
    L = tape(cv); r = C[cv]; x = V[cv]
    if not L or x["ret"].get("11") is None: continue
    tb = tape_buys(L, r["k"]); order = sorted(((key, b) for key, bl in tb.items() for b in bl), key=lambda kb: kb[0])
    n_ex = 0; taxed_ahead = False
    for key, b in order:
        if b["cls"] == "exempt":
            n_ex += 1
            if n_ex == 3: break
        elif b["cls"] == "taxed": taxed_ahead = True
    txs = engine_txs(r); first_cl = next((t for t in txs if t["cat"] in CLOSERS and t["off"] <= min(r["k"], 9)), None)
    first_team = next((t for t in txs if t["cat"] in COUNTED and t["off"] <= min(r["k"], 9)), None)
    direct_ahead = bool(first_cl and first_cl["cat"] == "outsider direct" and (first_team is None or (first_cl["off"], first_cl["ix"]) < (first_team["off"], first_team["ix"])))
    lab = ("a stranger's direct buy call ahead of the team" if direct_ahead else "a taxed stranger's Buy ahead of the 3rd exempt buy" if taxed_ahead else "neither")
    grp[lab].append(x["ret"]["11"])
    if x.get("fired"): grpf[lab].append(usd(x))
    r1 = any(t["cat"] == "outsider direct" for t in txs[: next((i for i, t in enumerate(txs) if sum(1 for u in txs[: i + 1] if u["cat"] in COUNTED) >= 3), len(txs))] if t["off"] <= min(r["k"], 9))
    if r1: grp["R1's 'closed by a direct buy': any stranger's direct call before the 3rd counted tx"].append(x["ret"]["11"])
    if r1 and x.get("fired"): grpf["R1's 'closed by a direct buy': any stranger's direct call before the 3rd counted tx"].append(usd(x))
for lab in ("neither", "a taxed stranger's Buy ahead of the 3rd exempt buy", "a stranger's direct buy call ahead of the team", "R1's 'closed by a direct buy': any stranger's direct call before the 3rd counted tx"):
    v = grp[lab]; f = [u for u in grpf[lab] if u is not None]
    print(f"    {lab:50s} all: n={len(v):3d} mean h11 {st.mean(v) if v else float('nan'):+6.1%} median {st.median(v) if v else float('nan'):+6.1%} | usual-view fires n={len(f):3d} ${sum(f):+7.2f} (${st.mean(f) if f else float('nan'):+.2f}/fire)")

# ---------------------------------------------------------------- Q3
print("\nQ3. the engine's bundle ETH (6.8, read at k-1) against the tables' exempt ETH, launches with a tape")
diff = []
for cv in pop:
    L = tape(cv); r = C[cv]; x = V[cv]
    if not L: continue
    k = r["k"]; w8 = fold(E8, r, max(0, k - 1)); tb = tape_buys(L, k)
    table = sum(b["eth"] for bl in tb.values() for b in bl if b["cls"] == "exempt"); table_k1 = sum(b["eth"] for key, bl in tb.items() for b in bl if b["cls"] == "exempt" and key[0] <= k - 1)
    diff.append((cv, w8["bundle_eth"], table, table_k1, w8["bundle"], x))
over = [d for d in diff if d[1] > 3.0]
print(f"  engine > 3.0 at k-1: {len(over)} launches; tables' exempt ETH (whole creation second) > 3.0 on {sum(1 for d in over if d[2] > 3.0)}; replay verdicts:", collections.Counter(d[5]['why'][:26] for d in over).most_common())
cats = collections.defaultdict(lambda: collections.Counter())
for cv, e8, table, tk1, nb, x in over:
    r = C[cv]; L = tape(cv); tb = tape_buys(L, r["k"])
    for t in engine_txs(r):
        if t["off"] > min(r["k"] - 1, 9) or t["cat"] not in COUNTED: continue
        bl = tb.get((t["off"], t["ix"]), []); c = cats[t["cat"]]
        c["n"] += 1; c["val"] += t["val"] or 0; c["ex"] += sum(b["eth"] for b in bl if b["cls"] == "exempt"); c["tax"] += sum(b["eth"] for b in bl if b["cls"] == "taxed"); c["buys"] += len(bl); c["nobuy"] += not bl
for cat, c in cats.items():
    print(f"    {cat:24s} txs {c['n']:4d} tx value {c['val']:8.3f} ETH | their Buy events {c['buys']:4d}: exempt {c['ex']:7.3f} taxed {c['tax']:6.3f} | txs without a Buy {c['nobuy']}")
for cv, e8, table, tk1, nb, x in sorted(over, key=lambda d: d[5]["T0"])[:14]:
    print(f"    {hhmm(x['T0'])} {cv[:10]} engine {e8:7.3f} ({nb} buyers) | tables {table:6.3f} (to k-1 {tk1:6.3f}) | replay {x['why'][:28]}")
def allreal(cv, upto): return all(t["real"] for t in engine_txs(C[cv]) if t["off"] <= upto)
real = [d for d in diff if allreal(d[0], C[d[0]]["k"] - 1)]
side = [d for d in real if (d[1] > 3.0) != (d[3] > 3.0) or (d[1] < 0.3) != (d[3] < 0.3)]
print(f"  same horizon (both to block k-1), every value real (D): {len(real)} launches; engine and tables on different sides of 0.3 or 3.0: {len(side)}")
print(f"    engine ETH / tables' exempt ETH to k-1 where both > 0: median {st.median([d[1] / d[3] for d in real if d[3] > 0 and d[1] > 0]):.3f}, above 1.05 on {sum(1 for d in real if d[3] > 0 and d[1] / d[3] > 1.05)}, below 0.95 on {sum(1 for d in real if d[3] > 0 and d[1] / d[3] < 0.95)}")
for lab, S in (("engine > tables x1.05", [d for d in real if d[3] > 0 and d[1] / d[3] > 1.05]), ("engine < tables x0.95", [d for d in real if d[3] > 0 and d[1] / d[3] < 0.95])):
    print(f"    {lab}: " + "; ".join(f"{d[0][:10]} {d[1]:.3f}/{d[3]:.3f} ({d[5]['why'][:12]})" for d in sorted(S, key=lambda d: d[5]['T0'])))
for cv, e8, table, tk1, nb, x in sorted(side, key=lambda d: d[5]["T0"]):
    print(f"    {hhmm(x['T0'])} {cv[:10]} engine {e8:6.3f} tables {table:6.3f} (to k-1 {tk1:6.3f}) | replay {x['why'][:24]:24s} fleets {x.get('fleets')} h11 {x['ret'].get('11') if x['ret'].get('11') is None else round(x['ret']['11'], 3)}" + (f" ${usd(x):+.2f}" if x.get('fired') else ""))
