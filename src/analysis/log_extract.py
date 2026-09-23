"""log_extract.py: a compact, shareable copy of the engine's log for the reconciliation.

    sudo python3 src/analysis/log_extract.py [/var/log/sniper/engine.jsonl] [data/live/engine_extract.jsonl.gz]

Keeps the events that describe every decision and every send (start, creation, gates, skips, decisions, bursts, sequencer
answers, landings, scores, trades, alarms, errors, feed events, shooter/relay top-ups) and drops nothing else of substance;
any field whose name mentions key, priv or secret is redacted before writing, though the engine never logs one. Writes
gzip-compressed JSON lines. Commit the file and push, or paste the printed summary."""
import sys, json, gzip, os, collections, datetime, glob
src = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].endswith(".gz") else "/var/log/sniper/engine.jsonl"
dst = next((a for a in sys.argv[1:] if a.endswith(".gz")), "data/live/engine_extract.jsonl.gz")
KEEP = {"start", "creation", "gate_check", "eligible_not_traded", "skip", "trade_decision", "burst_shots", "sent_burst", "send_answers", "burst_landing", "landing",
        "burst_dropped", "buy_reverted", "buy_rejected", "boundary", "slot_shadow", "score", "trade_done", "sell_reverted", "resend", "alarm", "error", "feed_stall",
        "feed_error", "feed_connected", "feed_resolution_ok", "feed_resolution_mismatch", "shooters", "shooter_topup", "relay_topup", "sender_rtt", "sender_addresses",
        "note", "day_start", "state_loaded", "seeded", "landing", "rival", "rival_chain", "reverter_learned", "receipt_timeout", "approve_not_seen", "approve_missing",
        "token_resolved_at_exit", "recovering_open_position", "unsigned_tx", "send_step_loaded", "chain_rivals_connected", "flow"}
def scrub(o):
    if isinstance(o, dict): return {k: ("[redacted]" if any(s in k.lower() for s in ("key", "priv", "secret")) else scrub(v)) for k, v in o.items()}
    if isinstance(o, list): return [scrub(x) for x in o]
    return o
n = collections.Counter(); kept = 0; first = last = None
os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
files = sorted((f for f in glob.glob(src + "*") if not f.endswith(".state.json")), key=os.path.getmtime)   # rotated copies too (.1, .2.gz, ...)
def lines():
    for f in files:
        with (gzip.open if f.endswith(".gz") else open)(f, "rt", errors="replace") as fh:
            yield from fh
with gzip.open(dst, "wt") as g:
    for line in lines():
        try: ev = json.loads(line)
        except ValueError: continue
        n[ev.get("ev")] += 1
        if ev.get("ev") not in KEEP: continue
        t = ev.get("t") or ev.get("ts") or ev.get("time")
        if t: first = first or t; last = t
        g.write(json.dumps(scrub(ev)) + "\n"); kept += 1
print(f"{sum(n.values())} lines read, {kept} kept -> {dst} ({os.path.getsize(dst)/1e6:.1f} MB); first {first} last {last}")
print("kept:", {k: v for k, v in n.most_common() if k in KEEP})
print("dropped:", {k: v for k, v in n.most_common() if k not in KEEP})
