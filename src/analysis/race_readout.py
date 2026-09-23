"""race_readout.py: were we LATE to the seat, or BEATEN? One line per burst, from the engine's own timing, all rotated logs.

    sudo python3 src/analysis/race_readout.py [/var/log/sniper/engine.jsonl]

flip-first_shot = the seat second's first block (the flip, wall clock) minus our first shot's send time: positive means the
burst straddled the tick (that many ms of shots landed in the tax second and reverted, the next one filled); negative means
every shot left after the tick, we were late by that much. `fill shot` = which shot of the burst filled (1 = the first).
Joined with data/derived/live_vs_table/sep17_20_fills.json (who was ahead of us in the block, the real return) when present."""
import sys, os, json, glob, gzip, time, collections, statistics as st
P = sys.argv[1] if len(sys.argv) > 1 else "/var/log/sniper/engine.jsonl"
ev = []
for f in glob.glob(P + "*"):
    if f.endswith(".state.json"): continue
    op = gzip.open if f.endswith(".gz") else open
    try:
        with op(f, "rt", errors="replace") as fh:
            for line in fh:
                try: ev.append(json.loads(line))
                except ValueError: pass
    except OSError as e: print("cannot read", f, e)
ev.sort(key=lambda e: e.get("t", 0)); print(f"{len(ev)} events from {len(glob.glob(P + '*'))} files, {time.strftime('%b %d %H:%M', time.gmtime(ev[0]['t']))} - {time.strftime('%b %d %H:%M', time.gmtime(ev[-1]['t']))} UTC" if ev else "no events"); 
if not ev: raise SystemExit
side = {}
for cand in ("data/derived/live_vs_table/sep17_20_fills.json", os.path.join(os.path.dirname(__file__), "../../data/derived/live_vs_table/sep17_20_fills.json")):
    if os.path.exists(cand):
        for r in json.load(open(cand)): side[r["cv"].lower()] = r
        break
dec = {}; rows = []
for e in ev:
    if e["ev"] == "trade_decision": dec[e["curve"].lower()] = e
    if e["ev"] == "burst_landing":
        cv = e["curve"].lower(); d = dec.get(cv, {}); shots = e.get("shots", []); inc = [s for s in shots if s.get("status") is not None]; rej = sum(1 for s in shots if s.get("rejected"))
        fill_i = next((i + 1 for i, s in enumerate(shots) if s.get("status") == "0x1"), None); fill = shots[fill_i - 1] if fill_i else None
        blocks = sorted({s["block"] for s in inc if s.get("block") is not None}); s = side.get(cv, {})
        rows.append({"t": e["t"], "cv": cv, "straddle": e.get("flip_minus_first_shot_ms"), "fill_shot": fill_i, "fill_idx": fill["tx_index"] if fill else None, "included": len(inc), "rejected": rej, "n": len(shots),
                     "blocks": (blocks[0], blocks[-1]) if blocks else None, "send_ms": d.get("seat_flip_to_send_ms"), "ahead": s.get("ahead"), "actual": s.get("actual"), "first": s.get("first"), "model": e.get("target_model")})
print(f"{'when (UTC)':15s} {'curve':10s} {'flip-1st shot':>13s} {'fill shot':>9s} {'tx idx':>6s} {'incl/rej/n':>10s} {'ahead':>5s} {'actual':>7s} {'if first':>8s}")
for r in rows:
    print(f"{time.strftime('%b %d %H:%M:%S', time.gmtime(r['t'])):15s} {r['cv'][:10]:10s} {('%+.0f ms' % r['straddle']) if r['straddle'] is not None else '-':>13s} {(str(r['fill_shot']) if r['fill_shot'] else 'none'):>9s} {(str(r['fill_idx']) if r['fill_idx'] is not None else '-'):>6s} {r['included']:>3d}/{r['rejected']:>2d}/{r['n']:<3d} "
          f"{(str(r['ahead']) if r['ahead'] is not None else '-'):>5s} {('%+.0f%%' % (100*r['actual'])) if r['actual'] is not None else '-':>7s} {('%+.0f%%' % (100*r['first'])) if r['first'] is not None else '-':>8s}")
fills = [r for r in rows if r["fill_shot"]]; withs = [r for r in fills if r["straddle"] is not None]
def q(v): return f"n={len(v)} median {st.median(v):+.0f} ms, min {min(v):+.0f}, max {max(v):+.0f}" if v else "n=0"
print(f"\nbursts {len(rows)}, filled {len(fills)}, no fill {len(rows)-len(fills)} (all shots reverted or refused)")
print("flip - first shot, fills with SOMEBODY ahead:", q([r["straddle"] for r in withs if r["ahead"]]))
print("flip - first shot, fills with NOBODY ahead:  ", q([r["straddle"] for r in withs if r["ahead"] == 0]))
print("flip - first shot, bursts with no fill:      ", q([r["straddle"] for r in rows if not r["fill_shot"] and r["straddle"] is not None]))
late = [r for r in withs if r["straddle"] < 0]; print(f"LATE bursts (every shot after the tick): {len(late)} of {len(withs)} fills; fill shot numbers when somebody was ahead: {[r['fill_shot'] for r in fills if r['ahead']]}; when nobody: {[r['fill_shot'] for r in fills if r['ahead'] == 0]}")
print("tx index of our fill when somebody was ahead:", [r["fill_idx"] for r in fills if r["ahead"]], "| nobody ahead:", [r["fill_idx"] for r in fills if r["ahead"] == 0])
rtt = [e for e in ev if e["ev"] == "sender_rtt"]
if rtt: print("sender RTT:", {k: v for k, v in rtt[-1].items() if k not in ("ev", "t")})
