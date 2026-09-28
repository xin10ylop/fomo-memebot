"""Q3a: engine 6.7's bundle-closing rule (a stranger's buy in the creation window closed the bundle count) replayed on the chain's
crowd files for the whole population, and what the launches it skipped pay at the engine's gate (engine_replay dumps, slip 0.20).
The feed's 'buy' is a direct call or a value-carrying call naming the curve; crowd_raw has no value, so two bounds: every stranger
call naming the curve closes (A, upper), only direct calls to the curve close (B, lower). The count is read at the gate's view."""
import json, gzip, glob, os, time, statistics as st
H = os.path.dirname(os.path.abspath(__file__)); D = "/home/user/fomo-memebot/data/derived/live_vs_table"
RELAY = "0xe8e98c3514d5bd83fdd01360896f2382b861a720"
CROWD_ALIAS = {"sep24_paper": "sep24paper"}
CR = {}
for lf in glob.glob(f"{D}/launches_*.json"):
    n = os.path.basename(lf)[9:-5]
    cf = next((c for c in (f"{D}/crowd_raw_{CROWD_ALIAS.get(n, n)}.json.gz", f"{D}/crowd_raw_{CROWD_ALIAS.get(n, n)}.json") if os.path.exists(c)), None)
    if not cf: continue
    for r in (json.load(gzip.open(cf, "rt")) if cf.endswith(".gz") else json.load(open(cf))): CR.setdefault(r["cv"].lower(), r)
def old_count(r, upto, direct_only):
    named = set(a.lower() for a in r.get("named") or []); creator = (r.get("creator") or "").lower(); c = 0; helper = False
    for j, b in enumerate(r["blocks"][: min(upto, 9) + 1]):
        for t in sorted(b, key=lambda t: t["ix"]):
            fr = t["fr"].lower()
            if t.get("to_token") or t["to"].lower() == RELAY: continue
            if t.get("named_data"):                                   # a helper buying for the wallets its calldata lists: the replay counts all named
                c += len(named); continue
            if t.get("named_fr") or fr in named or fr == creator:
                c += 1; continue
            if direct_only and not t["direct"]: continue
            return c, helper, True
    return c, helper, False
FIT_END = 1790208000; TODAY = 1790588400
for view, up in (("k2", -2), ("k1reg", -1), ("kreg", 0)):
    R = json.load(open(f"{H}/rows_{view}.json"))
    for variant, donly in (("A every stranger call", False), ("B direct calls only", True)):
        hit = []
        for x in R:
            if x["why"].startswith("PRE") or "bundle" in x["why"] and "cap" not in x["why"]: continue   # already out before this gate, or a chain bundle under 3
            r = CR.get(x["cv"]); 
            if not r: continue
            c, helper, closed = old_count(r, r["k"] + up, donly)
            if closed and c < 3: hit.append(x)
        fired = [x for x in hit if x.get("fired")]; fills = [x for x in fired if x["why"] == "FILL"]
        usd = sum(x.get("usd", 0) for x in fired)
        def per(lo, hi):
            f = [x for x in fired if lo <= x["T0"] < hi]; fl = [x["ret"]["11"] for x in f if x["why"] == "FILL"]
            return f"fires {len(f):2d} fills {len(fl):2d} mean {st.mean(fl) if fl else float('nan'):+6.1%} ${sum(x.get('usd', 0) for x in f):+7.2f}"
        print(f"{view:6s} {variant:22s}: population launches skipped by the old rule {len(hit):3d}; of them fired at this view {len(fired)}, fills {len(fills)}, mean {st.mean(x['ret']['11'] for x in fills) if fills else float('nan'):+.1%}, ${usd:+.2f}")
        print(f"         fit Sep 21-23 {per(0, FIT_END)} | read Sep 24-28 09:40 {per(FIT_END, TODAY)} | today {per(TODAY, 2e9)}")
        if view == "k1reg" and donly is False:
            for x in fired: print(f"           {time.strftime('%b %d %H:%M', time.gmtime(x['T0']))} {x['cv'][:10]} fleets {x.get('fleets')} {x['why']} {x['ret']['11']:+.1%}")
