"""6.24 (runbook 5bg): the burst's late start. burst_start(burst_at): the aim (the estimated tick + MARGIN_MS - BURST_LEAD_MS) still
ahead -> the stream starts on it; the aim passed with the estimated tick at least LATE_SEND_MIN_MS ahead -> it starts now (the
copies it drops would have landed in the creation second and reverted); nearer, or no estimate -> None, the 5.62 refusal. Oct 8
12:45: the creation block the 7th of its second's ten, the engine at the gate 103 ms after it, the aim (tick - 165 ms) just passed,
a +22% seat refused with a confident estimator (0.92 over 300 brackets)."""
import os, sys, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("SHOOTER_KEYS", ""), ("BURST_N", "35"), ("BURST_LEAD_MS", "180"), ("MARGIN_MS", "15"), ("SEND_MODE", "predict"), ("LATE_SEND_MIN_MS", "100")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
ok(E.LATE_SEND_MIN_MS == 100.0 and E.BURST_LEAD_MS == 180.0 and E.MARGIN_MS == 15.0, "settings: lead 180, margin 15, late-start margin 100 ms (the default)")
now = 1000.0
ok(E.burst_start(None, now) is None, "no estimate: None (the 5.62 refusal)")
ok(E.burst_start(now + 0.040, now) == (now + 0.040, 0.0), "the aim 40 ms ahead: the stream starts on the aim, late 0")
# the aim passed: the estimated tick is aim + lead - margin = aim + 165 ms
ok(E.burst_start(now - 0.010, now) == (now, 10.0), "the aim passed 10 ms ago, the tick 155 ms ahead: starts now, late 10 ms")
ok(E.burst_start(now - 0.064, now) == (now, 64.0), "the aim passed 64 ms ago, the tick 101 ms ahead: starts now (just inside the margin)")
ok(E.burst_start(now - 0.067, now) is None, "the aim passed 67 ms ago, the tick 98 ms ahead: refused (under the margin)")
ok(E.burst_start(now - 0.300, now) is None, "the tick already passed: refused")
# Oct 8 12:45 (runbook 5bg): the creation block 83324041, the 7th of ten in its second; the tick about 300 ms after it on the feed,
# the aim 165 ms before the tick, the engine ready 103 ms after the creation with the feed's delivery jitter against it
seen = now; tick = seen + 0.255; aim = tick - 0.165
ok(E.burst_start(aim, seen + 0.103) == (seen + 0.103, 13.0), "12:45 replayed: the aim 13 ms past at the check, the tick 152 ms ahead: 6.24 starts the stream (6.23 refused)")
E.LATE_SEND_MIN_MS = 0.0
ok(E.burst_start(now - 0.010, now) is None and E.burst_start(now + 0.010, now) == (now + 0.010, 0.0), "LATE_SEND_MIN_MS 0: a passed aim is refused as in 6.23; an aim ahead unchanged")
E.LATE_SEND_MIN_MS = 100.0
# the slot model (SLOT_SEND=1, the box's live aim): the tick sits SLOT_LEAD_MS + BURST_LEAD_MS after the aim, not BURST_LEAD_MS - MARGIN_MS
ok(abs(E.tick_after_aim_s() - 0.165) < 1e-9, "vote: the tick 165 ms after the aim (lead 180 - margin 15)")
E.SLOT_SEND = True; E.SLOT_LEAD_MS = 100.0
ok(abs(E.tick_after_aim_s() - 0.280) < 1e-9, "slot: the tick 280 ms after the aim (slot lead 100 + lead 180)")
ok(E.burst_start(now - 0.179, now) == (now, 179.0), "slot: the aim passed 179 ms ago, the tick 101 ms ahead: starts now")
ok(E.burst_start(now - 0.182, now) is None, "slot: the aim passed 182 ms ago, the tick 98 ms ahead: refused")
E.SLOT_SEND = False
# the engine's use of it (source checks, the branch sits inside handle_creation)
src = open(E.__file__).read()
ok('bs = burst_start(burst_at)' in src and '"predict-prebuilt" if late_start_ms == 0 else "predict-late-start"' in src, "handle_creation: the mode is predict-late-start when the stream starts after the aim")
ok('t_first = max(burst_at, mono()) if burst_at is not None' in src, "the first shot: on the aim, or now when the aim passed")
ok('open_by = ((burst_at if burst_at is not None else t_first) + (GATE_CLOSE_MS' in src, "the gate's deadline is measured from the aim, not the (possibly late) first shot")
ok('open_by = max(open_by, burst_at + (BURST_LEAD_MS + GATE_LATE_MS) / 1000.0)' in src, "with GATE_CLOSE_MS set, a late start keeps the gate open to the tick")
ok('"aim_ms": None if burst_at is None else round((burst_at - now) * 1000, 1), "tick_ms": tick_ms, "seat_on_feed": seat_on_feed' in src and 'burst_at + tick_after_aim_s() - now' in src and 'burst_at + tick_after_aim_s() - t_first' in src, "the skip logs aim_ms, tick_ms (model-aware) and seat_on_feed; the decision's tick_ms_at_start too")
ok("the seat's second is already on the feed: not sending" in src and "the aim passed" in src and "no confident boundary estimate" in src, "three distinct skip reasons")
ok('decision["late_start_ms"] = late_start_ms; decision["tick_ms_at_start"]' in src and '"late_send_min_ms": LATE_SEND_MIN_MS' in src and float(__import__("re").search(r'"release": "([\d.]+)"', src).group(1)) >= 6.24, "the decision logs late_start_ms and tick_ms_at_start; the start line the setting; release 6.24 or later")
print(f"all {checks} checks passed")
