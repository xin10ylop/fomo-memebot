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
ap.add_argument("--stake", type=float, default=13.0); ap.add_argument("--hold", type=int, default=300); ap.add_argument("--gas", type=float, default=0.33); ap.add_argument("--eth-usd", type=float, default=2570.0)
a = ap.parse_args()
def utc(x):
    if not x: return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try: return datetime.datetime.strptime(x, fmt).replace(tzinfo=datetime.timezone.utc).timestamp()
        except ValueError: pass
    raise SystemExit(f"--from/--to: use 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD', got {x!r}")
t_from, t_to = utc(a.t_from), utc(a.t_to)
ev = []
for f in sorted((f for f in glob.glob(a.log + "*") if not f.endswith(".state.json")), key=os.path.getmtime):
    with (gzip.open if f.endswith(".gz") else open)(f, "rt", errors="replace") as fh:
        for line in fh:
            try: e = json.loads(line)
            except ValueError: continue
            if e.get("ev") in ("trade_decision", "eligible_not_traded", "start", "sent_burst") and (t_from is None or e["t"] >= t_from) and (t_to is None or e["t"] <= t_to): ev.append(e)
ev.sort(key=lambda e: e["t"])
if t_from is None:                                                       # no window: from the FIRST start of today (UTC), so a restart does not drop the earlier events
    day0 = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    starts = [i for i, e in enumerate(ev) if e["ev"] == "start" and e["t"] >= day0] or [i for i, e in enumerate(ev) if e["ev"] == "start"]
    ev = ev[starts[0]:] if starts else ev
n_starts = sum(1 for e in ev if e["ev"] == "start"); t0 = min((e["t"] for e in ev), default=None); t1 = max((e["t"] for e in ev), default=None)
bursts = [e for e in ev if e["ev"] == "sent_burst"]; ev = [e for e in ev if e["ev"] != "sent_burst"]
for e in ev:                                                             # live: gate_opened_at_shot lives in the sender's sent_burst event (the last one before the decision)
    if e["ev"] == "trade_decision" and e.get("gate_opened_at_shot") is None:
        b = [x for x in bursts if x["t"] <= e["t"] and e["t"] - x["t"] < 60]
        if b: e["gate_opened_at_shot"] = b[-1].get("gate_opened_at_shot")
fired = [e for e in ev if e["ev"] == "trade_decision"]; refused = [e for e in ev if e["ev"] == "eligible_not_traded" and any("attackers" in g for g in e.get("gates", []))]
fmt = lambda t: time.strftime("%b %d %H:%M", time.gmtime(t)) if t else "-"
print(f"window {fmt(t0)} - {fmt(t1)} UTC ({n_starts} engine start{'s' if n_starts != 1 else ''} inside it); {len(ev)} events; fired (or would have) {len(fired)}, refused by the attackers gate {len(refused)}, hold {a.hold} blocks, stake ${a.stake:.0f}, gas ${a.gas:.2f} a burst")
def score(events, label):
    rows = []
    for e in events:
        cv = e["curve"].lower()
        try:
            cl = [x for x in lv.call("eth_getLogs", [{"fromBlock": hex(66_000_000), "toBlock": "latest", "address": lv.V2F, "topics": [None, None, lv.pad(cv)]}]) if len(x["topics"]) > 3]
            if not cl: print("  ", cv[:10], "no factory log on the chain: not scored"); continue
            b0 = int(cl[0]["blockNumber"], 16); L = lv.launch(cv, b0 + 12)
            if L is None or L["tier"] is None: print("  ", cv[:10], "no tape or unknown tier: not scored"); continue
            more = lv.call("eth_getLogs", [{"fromBlock": hex(b0 + 121), "toBlock": hex(b0 + a.hold + 30), "address": cv, "topics": [[lv.BUY, lv.SELL]]}])
            L["rows"] = sorted(L["rows"] + [lv.row_of(x) for x in more], key=lambda r: (r["bn"], r["li"])); ts = L["ts"]; T0 = L["T0"]
            bE1 = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
            if bE1 is None: print("  ", cv[:10], "no block in the seat's second: not scored"); continue
            r = {"cv": cv, "when": time.strftime("%b %d %H:%M", time.gmtime(T0)), "attackers": e.get("attackers_at_open", e.get("attackers_at_build", e.get("attackers"))),
                 "at_build": e.get("attackers_at_build"), "gated": e.get("gated_shots"), "opened_at": e.get("gate_opened_at_shot")}
            k = max((n - b0 for n in range(b0, b0 + 30) if ts.get(n) == T0), default=None); r["k"] = k      # the creation second's last block offset
            r["view"] = ""
            if e.get("seq_at_build"):                                                                        # 6.4: chain-numbered feed blocks (feed_seq), exact offsets from b0
                off = lambda key: (e[key] - b0) if e.get(key) else None
                dec = "open" if e.get("gate_opened") else "close"
                r["view"] = (f"; k={k}, feed at watch block {off('seq_watch')}, at the build block {off('seq_at_build')}, at the {dec} block {off('seq_at_open')}, after the burst block {off('seq_after_burst')}"
                             f"; fleets/wallets at the {dec} {e.get('fleets_at_open')}/{e.get('wallets_at_open')}, after the burst {e.get('fleets_after_burst')}/{e.get('wallets_after_burst')} ({e.get('attack_unit', 'fleets')} gate)")
            elif e.get("blk0") is not None and e.get("feed_block_at_build") is not None:                      # 6.3: feed-counted blocks
                fo = e.get("feed_block_at_open"); r["view"] = (f"; k={k}, feed at the build block {e['feed_block_at_build'] - e['blk0']}, at the open " + (f"block {fo - e['blk0']}" if fo is not None else "-")
                                                              + f"; fleets/wallets at the open {e.get('fleets_at_open', e.get('fleets_at_build'))}/{e.get('wallets_at_open', e.get('wallets_at_build'))} ({e.get('attack_unit', 'fleets')} gate)")
            if r["opened_at"] is not None: r["view"] += f"; opened at +{r['opened_at'] * e.get('burst_step_ms', 3):.0f} ms (the tick lands about +36 ms)"
            for pos, nah in (("behind1", 1), ("behind2", 2), ("last", 99)):
                info = {}; r[pos] = model_path(L, a.stake / a.eth_usd, bE1, nah, (a.hold,), info=info)[a.hold]
                if e.get("min_out_tokens") and info.get("tk") is not None and info["tk"] < e["min_out_tokens"]:   # 6.4: the burst's minOut guard (built on the feed's curve state) refuses this fill
                    r[pos] = -a.gas / a.stake; r["view"] += f"; GUARD at {pos}: {info['tk']:.0f} tokens < minOut {e['min_out_tokens']:.0f}: no fill, gas only"
            rows.append(r); print(f"  {r['when']} {cv[:10]} attackers {r['attackers']} (at the build {r['at_build']}, gated shots {r['gated']}, opened at shot {r['opened_at']}{r['view']}): behind one {r['behind1']:+.0%}  behind two {r['behind2']:+.0%}  last {r['last']:+.0%}", flush=True)
        except Exception as ex: print("  err", cv[:10], str(ex)[:80])
    if not rows: print(f"{label}: nothing to score"); return
    for pos in ("behind1", "behind2", "last"):
        v = [r[pos] for r in rows]; usd = [x * a.stake - a.gas for x in v]
        print(f"{label:22s} {pos:8s} n={len(v):3d} mean {st.mean(v):+6.1%} median {st.median(v):+6.1%} win {sum(x>0 for x in v)/len(v):3.0%} dead {sum(x<-0.4 for x in v)/len(v):3.0%}  ${st.mean(usd):+.2f} a burst after gas (SE ${st.pstdev(usd)/len(usd)**0.5:.2f})")
score(fired, "fired"); score(refused, "refused by the gate")
