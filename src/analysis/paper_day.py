"""paper_day.py: score a paper (dry-run) day of engine 6.1 from its log and the chain, the way the trade will be taken live.

    sudo python3 src/analysis/paper_day.py [/var/log/sniper/engine.jsonl] [--from "YYYY-MM-DD HH:MM"] [--stake 13] [--hold 300] [--min-attackers 2]

Every trade_decision of the window (the launches the engine would have fired at, dry run) and every eligible_not_traded refused
by the attackers gate: for each, the tape from the chain and the model at the positions we can get (behind one, behind two, behind
everybody in the seat block) held HOLD_BLOCKS blocks, at the stake, with the burst's gas. Prints the day's mean, win rate, dead
share and dollars per burst, and the same for the launches the gate refused (what skipping them saved). The go/no-go number
for the runbook: behind one at the hold, after gas, over at least 40 gated launches."""
import sys, os, json, glob, gzip, time, datetime, statistics as st, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import live_vs_table as lv
from hold_grid import model_path
ap = argparse.ArgumentParser(); ap.add_argument("log", nargs="?", default="/var/log/sniper/engine.jsonl"); ap.add_argument("--from", dest="t_from", default=None); ap.add_argument("--to", dest="t_to", default=None)
ap.add_argument("--stake", type=float, default=13.0); ap.add_argument("--hold", type=int, default=300); ap.add_argument("--min-attackers", type=int, default=2); ap.add_argument("--gas", type=float, default=0.33); ap.add_argument("--eth-usd", type=float, default=2570.0)
a = ap.parse_args(); utc = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M").replace(tzinfo=datetime.timezone.utc).timestamp() if x else None
t_from, t_to = utc(a.t_from), utc(a.t_to)
ev = []
for f in sorted((f for f in glob.glob(a.log + "*") if not f.endswith(".state.json")), key=os.path.getmtime):
    with (gzip.open if f.endswith(".gz") else open)(f, "rt", errors="replace") as fh:
        for line in fh:
            try: e = json.loads(line)
            except ValueError: continue
            if e.get("ev") in ("trade_decision", "eligible_not_traded", "start") and (t_from is None or e["t"] >= t_from) and (t_to is None or e["t"] <= t_to): ev.append(e)
ev.sort(key=lambda e: e["t"])
if t_from is None:
    starts = [i for i, e in enumerate(ev) if e["ev"] == "start"]; ev = ev[starts[-1]:] if starts else ev
fired = [e for e in ev if e["ev"] == "trade_decision"]; refused = [e for e in ev if e["ev"] == "eligible_not_traded" and any("attackers" in g for g in e.get("gates", []))]
print(f"{len(ev)} events; fired (or would have) {len(fired)}, refused by the attackers gate {len(refused)}, hold {a.hold} blocks, stake ${a.stake:.0f}, gas ${a.gas:.2f} a burst")
def score(events, label):
    rows = []
    for e in events:
        cv = e["curve"].lower()
        try:
            cl = [x for x in lv.call("eth_getLogs", [{"fromBlock": hex(66_000_000), "toBlock": "latest", "address": lv.V2F, "topics": [None, None, lv.pad(cv)]}]) if len(x["topics"]) > 3]
            if not cl: continue
            b0 = int(cl[0]["blockNumber"], 16); L = lv.launch(cv, b0 + 12)
            if L is None or L["tier"] is None: continue
            more = lv.call("eth_getLogs", [{"fromBlock": hex(b0 + 121), "toBlock": hex(b0 + a.hold + 30), "address": cv, "topics": [[lv.BUY, lv.SELL]]}])
            L["rows"] = sorted(L["rows"] + [lv.row_of(x) for x in more], key=lambda r: (r["bn"], r["li"])); ts = L["ts"]; T0 = L["T0"]
            bE1 = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
            if bE1 is None: continue
            r = {"cv": cv, "when": time.strftime("%b %d %H:%M", time.gmtime(T0)), "attackers": e.get("attackers")}
            for pos, nah in (("behind1", 1), ("behind2", 2), ("last", 99)): r[pos] = model_path(L, a.stake / a.eth_usd, bE1, nah, (a.hold,))[a.hold]
            rows.append(r); print(f"  {r['when']} {cv[:10]} attackers {r['attackers']}: behind one {r['behind1']:+.0%}  behind two {r['behind2']:+.0%}  last {r['last']:+.0%}", flush=True)
        except Exception as ex: print("  err", cv[:10], str(ex)[:80])
    if not rows: print(f"{label}: nothing to score"); return
    for pos in ("behind1", "behind2", "last"):
        v = [r[pos] for r in rows]; usd = [x * a.stake - a.gas for x in v]
        print(f"{label:22s} {pos:8s} n={len(v):3d} mean {st.mean(v):+6.1%} median {st.median(v):+6.1%} win {sum(x>0 for x in v)/len(v):3.0%} dead {sum(x<-0.4 for x in v)/len(v):3.0%}  ${st.mean(usd):+.2f} a burst after gas (SE ${st.pstdev(usd)/len(usd)**0.5:.2f})")
score(fired, "fired"); score(refused, "refused by the gate")
