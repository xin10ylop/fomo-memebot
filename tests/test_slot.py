"""The timer model (engine 5.8): the sequencer's blocks are created on a strict ~101.58 ms timer, so from the block NUMBER of each
second's first block the model recovers the timer and its origin to a millisecond, names the block that opens the seat second
and its creation time, aims the burst at it under SLOT_SEND, and scores itself by block-number hits (slot_shadow). No network.

    python3 tests/test_slot.py
"""
import os, sys, json, time, math, random, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODE", "predict"), ("SLOT_SEND", "1"), ("SLOT_LEAD_MS", "100"), ("BURST_N", "5"), ("BURST_STEP_MS", "2"), ("BURST_LEAD_MS", "4"),
             ("MARGIN_MS", "0"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("BUNDLE_MIN", "3")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

fails = []
def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail and not ok else ""))
    if not ok: fails.append(name)

P = 0.10158; now = time.time(); c0 = now - 200.0 - 0.0437          # block 0 created 200 s ago, 43.7 ms after a whole second
first_block = lambda S: math.ceil((S - c0) / P)                     # the first block created at or after the second
S0 = int(now) - 150
for S in range(S0, S0 + 120):                                       # 120 flips: the second and the number of its first block
    E.state["flip_block"][S] = first_block(S)
E._scache["at"] = -1e9
m = E.slot_model()
check("timer model fits from 120 flip block numbers", m is not None, str(m))
if m:
    check("period recovered within 0.02 ms", abs(m[0] - P) * 1000 < 0.02, f"{1000*m[0]:.3f} vs {1000*P:.3f}")
    check("origin recovered within 2 ms (the admissible interval is narrow)", abs(m[1] - c0) * 1000 < 2 and m[2] * 1000 < 15, f"c0 err {(m[1]-c0)*1000:.2f} ms, width {m[2]*1000:.1f} ms")
S = S0 + 120 + 3
sp = E.slot_predict(S)
check("the seat second's first block: right number and creation time within 2 ms", sp is not None and sp[1] == first_block(S) and abs(sp[0] - (c0 + first_block(S) * P)) * 1000 < 2, str(sp))
E.state["feed_ts"] = S - 1
tgt = E.seat_target(S - 1, 1)
want = E.mono() + ((c0 + first_block(S) * P) - time.time()) - 0.100 - 0.004
check("seat_target aims SLOT_LEAD_MS + BURST_LEAD_MS before the predicted creation", tgt is not None and abs(tgt - want) * 1000 < 3, f"{(tgt - want)*1000:.1f} ms" if tgt else "None")
# the shadow score: 30 more flips, each predicted then confirmed by its block number
E.boundary = lambda: None; E.state["ref"] = None
for S in range(S0 + 120, S0 + 152):
    E.state["flip_block"][S] = first_block(S)
    E.score_flip(S, time.time(), E.mono())
time.sleep(0.3)
sh = [json.loads(l) for l in open(LOG) if '"slot_shadow"' in l]
check("slot_shadow logged", bool(sh), "")
if sh:
    check("every predicted flip block number was a hit", sh[-1]["block_hits"] >= 25 and sh[-1]["block_misses"] == 0, str({k: sh[-1][k] for k in ("block_hits", "block_misses", "miss_slots")}))
# a wrong timer: flips off the grid give a narrow or empty admissible interval -> no confident model
E.state["flip_block"].clear(); E._scache["at"] = -1e9
random.seed(3)
for S in range(S0, S0 + 120):
    E.state["flip_block"][S] = first_block(S) + random.choice([-1, 0, 0, 1])
check("flips off the grid: no confident model, seat_target None", E.slot_predict(S0 + 130) is None and E.seat_target(S0 + 129, 1) is None, str(E.slot_model()))
print("all timer-model tests pass" if not fails else f"FAILED: {fails}")
sys.exit(1 if fails else 0)
