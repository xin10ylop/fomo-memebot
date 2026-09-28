"""engine_vs_chain.py: every launch the prediction listed (the chain's population) against what the engine did with it,
launch by launch, from the engine's log with its rotations (engine.jsonl, .1, .2.gz ...). Closes the evening reading:
a predicted fire that the engine neither fired nor refused at the gate is either one of its pre-gate filters (named
here) or a hole (NO EVENT), and a hole is a defect to chase (Sep 27: the public node's 429s left two-fleet launches
without a block clock).

    sudo python3 src/analysis/engine_vs_chain.py data/derived/live_vs_table/launches_X.json [/var/log/sniper/engine.jsonl] \
        [--crowd data/derived/live_vs_table/crowd_raw_X.json.gz] [--fires-only] [--from "2026-09-28 05:33" --to "2026-09-28 18:00"]
--from/--to bound the reading's window (UTC): without them the launches' own span, which cannot show an engine-only launch
after the population's last one (the reverse check below).
--crowd adds the fleets the rule counts at k-2 (the engine's view) to every line; --fires-only keeps the launches the
rule fires on (fleets >= 2 at k-2): the tables' fires against the engine's disposition of each."""
import json, gzip, glob, os, sys, datetime as dt, collections
args = list(sys.argv[1:]); crowd_f = None; fires_only = False
if "--fires-only" in args: fires_only = True; args.remove("--fires-only")
if "--crowd" in args: i = args.index("--crowd"); crowd_f = args[i + 1]; del args[i:i + 2]
bounds = {}
for k in ("--from", "--to"):                                                    # the reading's window (UTC "YYYY-mm-dd HH:MM"); without it the launches' own span
    if k in args: i = args.index(k); bounds[k] = dt.datetime.strptime(args[i + 1], "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp(); del args[i:i + 2]
la_f = args[0]; log = args[1] if len(args) > 1 else "/var/log/sniper/engine.jsonl"
fleets_k2 = {}
if crowd_f:
    _argv = sys.argv; sys.argv = ["x", "0.76", "0.71"]
    exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "crowd_rules.py")).read().split("rules = [")[0])   # cums, at
    sys.argv = _argv
    for r in (json.load(gzip.open(crowd_f, "rt")) if crowd_f.endswith(".gz") else json.load(open(crowd_f))):
        cw, cf = cums(r); fleets_k2[r["cv"].lower()] = at(cf, r["k"] - 2)
L = json.load(open(la_f)); L = sorted(L, key=lambda l: l["T0"])
t0, t1 = bounds.get("--from", L[0]["T0"] - 600), bounds.get("--to", L[-1]["T0"] + 900)
by_curve = collections.defaultdict(list); by_creator = collections.defaultdict(list); errs = []
for f in sorted((f for f in glob.glob(log + "*") if not f.endswith(".state.json")), key=os.path.getmtime):
    with (gzip.open if f.endswith(".gz") else open)(f, "rt", errors="replace") as fh:
        for line in fh:
            try: e = json.loads(line)
            except ValueError: continue
            t = e.get("t", 0)
            if not (t0 <= t <= t1): continue
            if e.get("ev") in ("error", "alarm", "feed_error", "feed_stall", "feed_connected", "start"): errs.append(e)
            if e.get("curve"): by_curve[e["curve"].lower()].append(e)
            if e.get("creator"): by_creator[e["creator"].lower()].append(e)
fmt = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%H:%M:%S")
def why(e):
    w = e.get("gates") or e.get("why") or e.get("what") or e.get("result") or ""
    return (w[0] if isinstance(w, list) and w else w) if not isinstance(w, dict) else str(w)
DISP = ("trade_decision", "eligible_not_traded", "skip", "creation")
holes = 0
for l in L:
    cv = l["cv"].lower(); cr = (l.get("creator") or "").lower()
    if fires_only and fleets_k2.get(cv, 0) < 2: continue
    evs = [e for e in by_curve.get(cv, []) if e["ev"] in DISP] or [e for e in by_creator.get(cr, []) if e["ev"] in DISP and abs(e["t"] - l["T0"]) < 120]
    evs.sort(key=lambda e: e["t"]); last = next((e for e in reversed(evs) if e["ev"] != "creation"), None)
    tag = ("FIRE " if last["ev"] == "trade_decision" else "GATE " if last["ev"] == "eligible_not_traded" and "attackers" in str(why(last)) else "PRE  ") if last else ("CREATION ONLY (thread ended without a decision)" if evs else "NO EVENT (never seen by the engine)")
    if not last: holes += 1
    near = [e for e in errs if abs(e["t"] - l["T0"]) < 90]
    fk = f" fleets@k-2 {fleets_k2[cv]}" if cv in fleets_k2 else ""
    print(f"{dt.datetime.fromtimestamp(l['T0'], dt.timezone.utc).strftime('%b %d')} {fmt(l['T0'])} {cv[:10]}{' tier %s' % l['tier'] if l.get('tier') is not None else ''} named {len(l.get('named') or [])}{' bundle %.3f' % l['bundle_eth'] if l.get('bundle_eth') is not None else ''}{fk} | {tag}{('' if not last else str(why(last))[:80])}"
          + (f"   [{'; '.join(e['ev'] + ' ' + fmt(e['t']) + ' ' + str(e.get('err') or e.get('what') or '')[:40] for e in near[:3])}]" if near else ""))
n = sum(1 for l in L if not fires_only or fleets_k2.get(l["cv"].lower(), 0) >= 2)
# the reverse direction (Sep 28, report 24.40): launches the engine judged eligible (fired or refused at the gate) that the chain's
# population does not hold. Each is a launch the tables never priced: on Sep 28 02:51 a bundle burned on the creation-second tax
# (named wallets through a helper buying in its own name) that the engine counted as 0.49 ETH. Engine 6.6 refuses those; a line here
# after 6.6 is a new kind of launch to read from the chain before anything else.
pop = {l["cv"].lower() for l in L}; only = []
for cv, evs in by_curve.items():
    if cv in pop: continue
    dec = [e for e in evs if e["ev"] in ("trade_decision", "eligible_not_traded") and t0 <= e["t"] <= t1]
    if dec: only.append((dec[0]["t"], cv, dec[-1]))
for t, cv, e in sorted(only):
    print(f"{dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime('%b %d')} {fmt(t)} {cv[:10]} | ENGINE ONLY (not in the chain's population): {e['ev']} bundle {e.get('bundle_eth')} ETH named {e.get('named_wallets')} tax {e.get('tax_bps')} | {str(why(e))[:80]}")
print(f"\n{n} launches{' (fires at k-2)' if fires_only else ''}, {holes} without a decision in the log, {len(only)} engine-only (eligible on the feed, absent from the chain's population)")
