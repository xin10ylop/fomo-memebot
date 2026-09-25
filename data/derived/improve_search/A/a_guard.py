"""a_guard.py (searcher A): the two things the hold_grid files cannot say, from the launch's tape (public RPC, cached):
  1. the burst's minOut guard (BURST_SLIP 25%): the engine quotes at the build on the feed's curve state
     (src/strategy/sniper_engine.py size_buy lines 1029-1034, minOut line 1921: TIER_ASSUMED 0.05 + E1 surcharge 0.0618, $13);
     the fill is hold_grid.model_path's behind-one entry (info["tk"]). Refused -> scored -gas ($-0.33, return 0).
     The build's view is not logged in the tables: two assumptions, the creation second's blocks through view(k, 0.71)
     (crowd_rules.py BUILD_F) and through k-2 (the latest the build can have seen); at least the creation block.
  2. the creator's supply (MIN_CREATOR_SUPPLY, sniper_engine.py line 1765: the first buy's tokens / 1e9 < 1%): the engine
     already runs 1%; other cuts are AND-filters on the baseline, so only the fired launches' tapes are needed.
Launches pulled: every fire of the baseline and of each distinct variant that clears (a)-(e) in a_search.py, fit and val.
The pull is checked against hold_grid: model_path(behind one, $15, 300 blocks) must equal behind1_15_h300.
    python3 a_guard.py          (first run pulls ~1 launch/3 s into a_tapes_cache.json; later runs are offline)"""
import os, sys, json; sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # never write .pyc into the repo
import a_search as S
from a_common import *
sys.path.insert(0, os.path.join(REPO, "src/analysis"))
_cwd = os.getcwd(); os.chdir(REPO)
import live_vs_table as lv
from hold_grid import model_path
os.chdir(_cwd)
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "a_tapes_cache.json")
E = 2570.0; SLIP = 0.25; FEE_Q = 0.05 + 0.0618
rows, BASE, RET = S.rows, S.BASE, S.RET
passes = sorted([r for r in S.CAND if r["pass"] and not r["dup_of"]], key=lambda r: -r["res"]["fit"]["usd_day"])
need = {}
for fire in [BASE] + [r["_c"][2] for r in passes]:
    for x in rows:
        if fire(x): need[x["cv"]] = x
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
b0s = {}
for f in os.listdir(D):
    if f.startswith("crowd_raw") and f.endswith(".gz"):
        for r in json.load(gzip.open(D + f, "rt")): b0s[r["cv"]] = r["b0"]
todo = [cv for cv in need if cv not in cache]
print(f"{len(need)} launches needed, {len(todo)} to pull", flush=True)
for i, cv in enumerate(todo):
    x = need[cv]; b0 = b0s[cv]
    try:
        L = lv.launch(cv, b0 + x["k"] + 1)
        ev = lv.call("eth_getLogs", [{"fromBlock": hex(b0 + 121), "toBlock": hex(b0 + 620), "address": cv, "topics": [[lv.BUY, lv.SELL]]}])
        L["rows"] = sorted(L["rows"] + [lv.row_of(e) for e in ev], key=lambda r: (r["bn"], r["li"]))
        cache[cv] = {"b0": L["b0"], "T0": L["T0"], "tier": L["tier"], "ts": {str(k): v for k, v in L["ts"].items()},
                     "rows": [{k: r[k] for k in ("bn", "k", "tk", "eth", "who", "li")} for r in L["rows"]]}
    except Exception as e: print("  err", cv[:10], str(e)[:80], flush=True); continue
    if (i + 1) % 10 == 0: json.dump(cache, open(CACHE, "w")); print(f"  {i + 1} pulled", flush=True)
json.dump(cache, open(CACHE, "w"))

def tapeL(cv):
    c = cache[cv]; return {"b0": c["b0"], "T0": c["T0"], "tier": c["tier"], "ts": {int(k): v for k, v in c["ts"].items()}, "rows": c["rows"]}
info_by = {}; bad = []
for cv, x in need.items():
    if cv not in cache: continue
    L = tapeL(cv); ts, T0, b0 = L["ts"], L["T0"], L["b0"]
    bE1 = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
    if bE1 is None: bad.append(cv[:10]); continue
    chk = model_path(L, 15.0 / E, bE1, 1, (300,))[300]
    if abs(chk - x["behind1_15_h300"]) > 1e-9: bad.append(cv[:10])
    inf = {}; model_path(L, STAKE / E, bE1, 1, (300,), info=inf); tk_fill = inf["tk"]
    tape = [r for r in L["rows"] if r["who"] not in lv.OURS]
    buys0 = [r for r in tape if r["bn"] == b0 and r["k"] == "B"]; tk0 = buys0[0]["tk"] if buys0 else 0.0
    g = {}
    for tag, j in (("v071", view(x["k"], 0.71)), ("k2", x["k"] - 2)):
        j = max(j, 0); X, Y = lv.X0, lv.Y0
        for r in tape:
            if ts.get(r["bn"], 9e18) != T0 or r["bn"] > b0 + j: continue
            if r["k"] == "B":
                if 0 < r["tk"] < Y: X, Y = lv.fold_buy(X, Y, r["tk"])
            else: X, Y = lv.fold_sell(X, Y, r["tk"])
        net = STAKE / E * (1 - FEE_Q); tk_q = Y * net / (X + net)
        g[tag] = tk_fill < (1 - SLIP) * tk_q
    i100 = {}; model_path(L, 100.0 / E, bE1, 1, (300,), info=i100)
    info_by[cv] = {"guard_v071": g["v071"], "guard_k2": g["k2"], "creator_share": tk0 / lv.Y0, "tk100_share": i100["tk"] / lv.Y0}
print(f"tape check against hold_grid behind1_15_h300: {len(info_by)} launches scored, mismatches/unscorable: {bad or 'none'}")

def gret(tag):
    return lambda x: (0.0 if info_by[x["cv"]][tag] else x["behind1_15_h300"]) if x["cv"] in info_by else None
out = []
def P(s=""): print(s); out.append(s)
for tag, lab in (("guard_v071", "build view = view(k, 0.71)"), ("guard_k2", "build view = block k-2")):
    P(f"\n=== minOut guard, {lab}: refused fills scored -gas (return 0, $-0.33)")
    bres = evaluate(rows, BASE, gret(tag)); nb = sum(info_by[x['cv']][tag] for x in rows if BASE(x) and x["cv"] in info_by)
    P(f"  baseline: {nb} of {bres['fit']['n'] + bres['val']['n']} fires guarded. {S.short(bres)}")
    for r in passes:
        fam, name, fire, ret, stake = r["_c"]
        res = evaluate(rows, fire, gret(tag)); f, v = res["fit"], res["val"]
        ok = (f["usd_day"] > bres["fit"]["usd_day"], all(res[w]["usd"] > 0 for w in FIT_NAMES), v["usd"] >= bres["val"]["usd"] - 1e-9 and v["mean"] >= bres["val"]["mean"] - 1e-12,
              f["win"] >= bres["fit"]["win"] - 0.10 and f["dead"] <= bres["fit"]["dead"] + 0.05, f["n"] >= 30)
        ng = sum(info_by[x['cv']][tag] for x in rows if fire(x) and x["cv"] in info_by)
        P(f"  {name}: {ng} guarded. {S.short(res)}  fails vs guarded baseline: {''.join('abcde'[i] for i, o in enumerate(ok) if not o) or 'none'}")
P("\n=== creator's supply share (first buy / 1e9) as an AND-filter on the baseline (the engine already runs >= 1%)")
for cut in (0.0, 0.005, 0.01, 0.02, 0.03, 0.05):
    fire = lambda x, cut=cut: BASE(x) and x["cv"] in info_by and info_by[x["cv"]]["creator_share"] >= cut
    res = evaluate(rows, fire); cr = S.criteria(res)
    P(f"  creator share >= {cut:.1%}: {S.short(res)}  fails (vs the brief's baseline): {''.join(k for k, v in cr.items() if not v) or 'none'}")
P("\n=== the engine's MIN_CREATOR_SUPPLY 1% applied to BOTH sides (every fire of the baseline and of the passes has a tape)")
cs = lambda x: x["cv"] in info_by and info_by[x["cv"]]["creator_share"] >= 0.01
bres = evaluate(rows, lambda x: BASE(x) and cs(x)); P(f"  baseline & creator >= 1%: {S.short(bres)}")
for r in passes:
    fam, name, fire, ret, stake = r["_c"]
    res = evaluate(rows, lambda x, fire=fire: fire(x) and cs(x), ret); f, v = res["fit"], res["val"]
    ok = (f["usd_day"] > bres["fit"]["usd_day"], all(res[w]["usd"] > 0 for w in FIT_NAMES), v["usd"] >= bres["val"]["usd"] - 1e-9 and v["mean"] >= bres["val"]["mean"] - 1e-12,
          f["win"] >= bres["fit"]["win"] - 0.10 and f["dead"] <= bres["fit"]["dead"] + 0.05, f["n"] >= 30)
    P(f"  {name} & creator >= 1%: {S.short(res)}  fails vs that baseline: {''.join('abcde'[i] for i, o in enumerate(ok) if not o) or 'none'}")
P("\n=== the stake: the $100 entry's share of supply against the model's 3% cap (live_vs_table.py CAP), baseline fires")
sh = sorted(info_by[x["cv"]]["tk100_share"] for x in rows if BASE(x) and x["cv"] in info_by)
P(f"  {len(sh)} fires: median {st.median(sh):.2%} of supply, max {sh[-1]:.2%}; at the 3% cap: {sum(v >= lv.CAP * 0.9999 for v in sh)}")
open(os.path.join(HERE, "a_guard_output.txt"), "w").write("\n".join(out) + "\n")
