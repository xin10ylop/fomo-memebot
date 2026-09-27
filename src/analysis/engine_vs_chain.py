"""engine_vs_chain.py: every launch the prediction listed (the chain's population) against what the engine did with it,
launch by launch, from the engine's log with its rotations (engine.jsonl, .1, .2.gz ...). Closes the evening reading:
a predicted fire that the engine neither fired nor refused at the gate is either one of its pre-gate filters (named
here) or a hole (NO EVENT), and a hole is a defect to chase (Sep 27: the public node's 429s left two-fleet launches
without a block clock).

    sudo python3 src/analysis/engine_vs_chain.py data/derived/live_vs_table/launches_X.json [/var/log/sniper/engine.jsonl]"""
import json, gzip, glob, os, sys, datetime as dt, collections
la_f = sys.argv[1]; log = sys.argv[2] if len(sys.argv) > 2 else "/var/log/sniper/engine.jsonl"
L = json.load(open(la_f)); L = sorted(L, key=lambda l: l["T0"])
t0, t1 = L[0]["T0"] - 600, L[-1]["T0"] + 900
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
    evs = [e for e in by_curve.get(cv, []) if e["ev"] in DISP] or [e for e in by_creator.get(cr, []) if e["ev"] in DISP and abs(e["t"] - l["T0"]) < 120]
    evs.sort(key=lambda e: e["t"]); last = next((e for e in reversed(evs) if e["ev"] != "creation"), None)
    tag = ("FIRE " if last["ev"] == "trade_decision" else "GATE " if last["ev"] == "eligible_not_traded" and "attackers" in str(why(last)) else "PRE  ") if last else ("CREATION ONLY (thread ended without a decision)" if evs else "NO EVENT (never seen by the engine)")
    if not last: holes += 1
    near = [e for e in errs if abs(e["t"] - l["T0"]) < 90]
    print(f"{fmt(l['T0'])} {cv[:10]} tier {l.get('tier')} named {len(l.get('named') or [])} bundle {l.get('bundle_eth', 0):.3f} | {tag}{('' if not last else str(why(last))[:80])}"
          + (f"   [{'; '.join(e['ev'] + ' ' + fmt(e['t']) + ' ' + str(e.get('err') or e.get('what') or '')[:40] for e in near[:3])}]" if near else ""))
print(f"\n{len(L)} launches, {holes} without a decision in the log")
