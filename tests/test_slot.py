"""The slot model (engine 5.7): every block's wall-clock arrival folded on the sequencer's ~101.6 ms slot grid recovers the period
and phase through 20 ms of delivery jitter, predicts the arrival of a second's first block to a few ms, aims the burst with
SLOT_SEND, and scores itself against every flip (slot_shadow). Scripted arrivals, no network.

    python3 tests/test_slot.py
"""
import os, sys, json, time, random, tempfile, statistics as st
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODE", "predict"), ("SLOT_SEND", "1"), ("SLOT_LEAD_MS", "180"), ("FEED_LAG_MS", "85"), ("BURST_N", "5"), ("BURST_STEP_MS", "3"), ("BURST_LEAD_MS", "6"),
             ("MARGIN_MS", "0"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("BUNDLE_MIN", "3")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

fails = []
def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail and not ok else ""))
    if not ok: fails.append(name)

random.seed(7)
P, FL, JIT = 0.10163, 0.085, 0.020                       # the sequencer's period, the feed's lag, the delivery jitter (std)
t0 = time.time() - 95.0; t0 = t0 - (t0 % 1.0) + 0.0371   # slot 0 created 37.1 ms after a whole second, 95 s ago
true_arrival = lambda k: t0 + k * P + FL
for k in range(900):
    E.state["arrivals"].append(true_arrival(k) + random.gauss(0, JIT))
E._scache["at"] = -1e9
m = E.slot_model()
check("slot model fits with 900 jittered blocks", m is not None, str(m))
if m:
    check("period recovered within 0.05 ms", abs(m[0] - P) * 1000 < 0.05, f"{1000*m[0]:.3f} vs {1000*P:.3f}")
    # the phase: any slot's arrival modulo the period
    ph_err = ((m[1] - (true_arrival(450) % m[0])) + m[0] / 2) % m[0] - m[0] / 2   # at the window's centre, where a 0.05 ms period error costs nothing
    check("phase recovered within 3 ms at the window's centre", abs(ph_err) * 1000 < 3, f"{1000*ph_err:.2f} ms")
    check("concentration R above the confidence floor", m[2] >= 0.12, f"R {m[2]:.3f}")
# predict the first block of a second inside the window
S = int(true_arrival(600)) + 1
k_true = next(k for k in range(0, 2000) if t0 + k * P >= S)          # the first slot created at or after the second
pred = E.slot_predict(S)
check("the seat second's first block predicted within 4 ms of its true arrival", pred is not None and abs(pred - true_arrival(k_true)) * 1000 < 4, f"{(pred - true_arrival(k_true))*1000:.1f} ms" if pred else "None")
# seat_target with SLOT_SEND: the send leaves SLOT_LEAD_MS + BURST_LEAD_MS before that arrival
E.state["feed_ts"] = S - 1
tgt = E.seat_target(S - 1, 1)
want = E.mono() + (true_arrival(k_true) - time.time()) - 0.180 - 0.006
check("seat_target aims SLOT_LEAD_MS + BURST_LEAD_MS before the predicted arrival", tgt is not None and abs(tgt - want) * 1000 < 4, f"{(tgt - want)*1000:.1f} ms" if tgt else "None")
# the shadow score: 31 flips scored against the model
E.boundary = lambda: None; E.state["ref"] = None
for i in range(1, 33):
    S_i = int(true_arrival(i * 10)) + 1
    k_i = next(k for k in range(0, 2000) if t0 + k * P >= S_i)
    E.score_flip(S_i, true_arrival(k_i) + random.gauss(0, JIT), E.mono())
    E.state["slot_pred"][S_i + 1] = (E.slot_predict(S_i + 1), None)  # the next flip's prediction, as the feed loop would store it
    S_n = S_i + 1; k_n = next(k for k in range(0, 2000) if t0 + k * P >= S_n)
    E.score_flip(S_n, true_arrival(k_n) + random.gauss(0, JIT), E.mono())
time.sleep(0.3)
ev = [json.loads(l) for l in open(LOG)]; sh = [e for e in ev if e.get("ev") == "slot_shadow"]
check("slot_shadow logged with the model's error against the flips", bool(sh), str([e.get("ev") for e in ev][-5:]))
if sh:
    check("the model's median absolute error on jittered flips is under 25 ms (one flip's own jitter is 20 ms)", sh[-1]["slot_err_ms"]["abs_median"] < 25, str(sh[-1]["slot_err_ms"]))
# no model: too few blocks
E.state["arrivals"].clear(); E._scache["at"] = -1e9
check("no model with too few blocks; seat_target None under SLOT_SEND", E.slot_model() is None and E.seat_target(S - 1, 1) is None)
print("all slot tests pass" if not fails else f"FAILED: {fails}")
sys.exit(1 if fails else 0)
