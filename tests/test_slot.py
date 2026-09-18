"""The ramp model (engine 5.9): a line through the last thirty block arrivals (wall time on block number) predicts the next
second's first block, ten blocks after the last flip, to about the delivery jitter over the square root of thirty; SLOT_SEND aims
the burst FEED_LAG_MS + SLOT_LEAD_MS + BURST_LEAD_MS before that arrival; the model scores itself on every flip. No network.

    python3 tests/test_slot.py
"""
import os, sys, json, time, math, random, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODE", "predict"), ("SLOT_SEND", "1"), ("SLOT_LEAD_MS", "100"), ("FEED_LAG_MS", "85"), ("BURST_N", "5"), ("BURST_STEP_MS", "3"), ("BURST_LEAD_MS", "9"),
             ("MARGIN_MS", "0"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("BUNDLE_MIN", "3"), ("RAMP_BLOCKS", "30")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

fails = []
def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail and not ok else ""))
    if not ok: fails.append(name)

random.seed(11)
P, FL, JIT = 0.1016, 0.085, 0.025
now = time.time(); n0 = 66_000_000; c0 = now - 8.0                  # block n0 created 8 s ago; ten blocks a second, one flip per ten blocks
creation = lambda n: c0 + (n - n0) * P
# 80 blocks with jittered arrivals; flips every ten blocks with the block number recorded
S_first = int(creation(n0)) + 1
for n in range(n0, n0 + 80):
    E.state["arrivals"].append((creation(n) + FL + random.gauss(0, JIT), n))
flips = {}
for j in range(0, 8):
    S = S_first + j; n_flip = n0 + 3 + 10 * j                         # the first block stamped S
    E.state["flip_block"][S] = n_flip; flips[S] = n_flip
E._scache["at"] = -1e9
m = E.slot_model()
check("ramp model fits the last 30 arrivals", m is not None and m[3] == 30, str(m))
if m:
    check("slope within 1 ms of the block period", abs(m[0] - P) * 1000 < 1.0, f"{1000*m[0]:.2f} vs {1000*P:.2f}")
    check("residual near the delivery jitter", 10 < m[2] * 1000 < 45, f"{1000*m[2]:.1f} ms")
S_next = S_first + 8
sp = E.slot_predict(S_next)
true_arr = creation(flips[S_first + 7] + 10) + FL
check("the next flip predicted ten blocks after the last, arrival within 20 ms (about 7 ms std)", sp is not None and sp[1] == flips[S_first + 7] + 10 and abs(sp[0] - true_arr) * 1000 < 20, f"{(sp[0]-true_arr)*1000:.1f} ms" if sp else "None")
E.state["feed_ts"] = S_next - 1
tgt = E.seat_target(S_next - 1, 1)
want = E.mono() + (sp[0] - time.time()) - 0.085 - 0.100 - 0.009 if sp else None
check("seat_target aims FEED_LAG + SLOT_LEAD + BURST_LEAD before the predicted arrival", tgt is not None and abs(tgt - want) * 1000 < 2, f"{(tgt-want)*1000:.1f} ms" if (tgt and want) else "None")
# shadow scoring over 30 flips
E.boundary = lambda: None; E.state["ref"] = None
for j in range(8, 40):
    S = S_first + j; n_flip = flips[S - 1] + 10; flips[S] = n_flip
    for n in range(n_flip - 9, n_flip + 1):
        E.state["arrivals"].append((creation(n) + FL + random.gauss(0, JIT), n))
    E.state["flip_block"][S] = n_flip
    E.score_flip(S, creation(n_flip) + FL + random.gauss(0, JIT), E.mono())
time.sleep(0.3)
sh = [json.loads(l) for l in open(LOG) if '"slot_shadow"' in l]
check("slot_shadow logged", bool(sh))
if sh:
    check("the ramp names the ten-block flip every time and its timing error is within the jitter", sh[-1]["nine_block_misses"] == 0 and sh[-1]["ramp_err_ms"]["abs_median"] < 30, str({k: sh[-1][k] for k in ("ten_block_hits", "nine_block_misses", "ramp_err_ms")}))
# stale flip: no prediction
E.state["flip_block"].clear()
check("no flip seen: no prediction, seat_target None", E.slot_predict(S_first + 41) is None and E.seat_target(S_first + 40, 1) is None)
print("all ramp-model tests pass" if not fails else f"FAILED: {fails}")
sys.exit(1 if fails else 0)
