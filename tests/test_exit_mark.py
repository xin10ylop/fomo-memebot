"""6.25 (runbook 5bj, the runner): the mark-based exit. position_mark = selling every token now, net of the sell fee, over the ETH
paid (the tables' and the simulator's mark); it reads the chain poll's reserves when under a second old, else the feed's fold.
mark_poll folds every Buy and Sell since the creation from the curve's constants. STOP_LOSS sells at or below -it, TAKE_PROFIT at
or above it, both only with EXIT_MARK; ATTACK_MAX refuses a crowd at the build. Nothing changes for the sniper (EXIT_MARK off)."""
import os, sys, tempfile, time
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("SHOOTER_KEYS", ""), ("EXIT_MARK", "1"), ("STOP_LOSS", "0.30"), ("TAKE_PROFIT", "0.30"), ("ATTACK_MAX", "0"), ("MARK_POLL_MS", "5")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
ok(E.EXIT_MARK and E.STOP_LOSS == 0.30 and E.TAKE_PROFIT == 0.30 and E.ATTACK_MAX == 0, "settings: exit_mark on, stop 30%, take-profit 30%, attack_max 0")
X0, Y0 = E.X0, E.Y0
# a position: $10 behind one on a fresh untaxed curve; the mark by the simulator's formula
w = {"X": X0, "Y": Y0, "tax": 0.01}; gross = 0.0037                                    # ETH paid
net = gross * (1 - 0.01 - 0.0618); tk = w["Y"] * net / (w["X"] + net); w["X"] += net; w["Y"] -= tk   # our own buy folded (E1: tier 1% + surcharge)
pos = {"tokens": tk}
m0 = E.position_mark(w, pos, gross)
ok(abs(m0 - (w["X"] * tk / (w["Y"] + tk) * 0.99 / gross - 1)) < 1e-12, "the mark is what selling everything returns net of the 1% fee over the ETH paid")
ok(-0.09 < m0 < -0.06, f"right after an E1 fill the mark is the round trip's fees and impact ({100*m0:+.1f}%)")
# the crowd buys 0.5 ETH: the mark rises; a dump of their tokens: it falls
n2 = 0.5 * 0.99; t2 = w["Y"] * n2 / (w["X"] + n2); w["X"] += n2; w["Y"] -= t2
m1 = E.position_mark(w, pos, gross); ok(m1 > 0.30, f"after a 0.5 ETH buy the mark clears the take-profit ({100*m1:+.0f}%)")
w["X"] -= w["X"] * t2 / (w["Y"] + t2); w["Y"] += t2
w["X"] -= w["X"] * (0.3 * Y0 * 0) / (w["Y"] + 0) if False else 0
ok(abs(E.position_mark(w, pos, gross) - m0) < 1e-9, "the same tokens sold back: the mark returns to where it was")
ok(E.position_mark(w, {"tokens": 0.0}, gross) is None and E.position_mark(w, pos, 0.0) is None, "no tokens or no cost: no mark")
# the chain poll's reserves win while fresh, the feed's fold after a second
w["chain_xy"] = (w["X"] * 1.5, w["Y"], E.mono()); mc = E.position_mark(w, pos, gross)
ok(mc > m0 + 0.3, "a fresh chain reading (reserves 1.5x) is the mark's source")
w["chain_xy"] = (w["X"] * 1.5, w["Y"], E.mono() - 1.5)
ok(abs(E.position_mark(w, pos, gross) - m0) < 1e-9, "a chain reading over a second old is ignored: the feed's fold stands in")
# mark_poll folds the chain's events from the constants (the tables' fold)
BUY, SELL = E.BUY_EV, E.SELL_EV
def word(x): return ("%064x" % int(x * 1e18))
events = [{"blockNumber": "0x10", "logIndex": "0x1", "topics": [BUY], "data": "0x" + word(0.02) + word(1.2e7)},
          {"blockNumber": "0x11", "logIndex": "0x0", "topics": [SELL], "data": "0x" + word(5e6) + word(0.008)},
          {"blockNumber": "0x11", "logIndex": "0x2", "topics": [BUY], "data": "0x" + word(0.05) + word(2.5e7)}]
E.rpc_logs = type("R", (), {"call": staticmethod(lambda m, p: list(reversed(events)))})()
X, Y = X0, Y0
X, Y = X + X * 1.2e7 / (Y - 1.2e7), Y - 1.2e7; X, Y = X - X * 5e6 / (Y + 5e6), Y + 5e6; X, Y = X + X * 2.5e7 / (Y - 2.5e7), Y - 2.5e7
w2 = {"X": X0, "Y": Y0}; pos2 = {"tokens": 1.0}; E.state["open"] = pos2
import threading
t = threading.Thread(target=E.mark_poll, args=(w2, pos2, "0x" + "ab" * 20, 16), daemon=True); t.start(); time.sleep(0.05); E.state["open"] = None; t.join(1.0)
ok("chain_xy" in w2 and abs(w2["chain_xy"][0] - X) < 1e-12 and abs(w2["chain_xy"][1] - Y) < 1e-6, "mark_poll: the events sorted by block and index and folded from X0/Y0 give the chain's reserves")
ok(w2.get("chain_polls", 0) >= 1 and not w2.get("chain_poll_errs"), "the poll counted, no errors")
E.rpc_logs = type("R", (), {"call": staticmethod(lambda m, p: (_ for _ in ()).throw(RuntimeError("node down")))})()
w3 = {"X": X0, "Y": Y0}; pos3 = {"tokens": 1.0}; E.state["open"] = pos3
t = threading.Thread(target=E.mark_poll, args=(w3, pos3, "0x" + "ab" * 20, 16), daemon=True); t.start(); time.sleep(0.03); E.state["open"] = None; t.join(1.0)
ok("chain_xy" not in w3 and w3.get("chain_poll_errs", 0) >= 1 and "node down" in w3.get("chain_poll_err", ""), "a failing node: no reading, the error counted, the feed's fold stands in")
# the engine's use (source checks: the branch sits inside the launch thread)
src = open(E.__file__).read()
ok('if STOP_LOSS > 0 and m <= -STOP_LOSS:' in src and 'if TAKE_PROFIT > 0 and m >= TAKE_PROFIT:' in src and 'elif TAKE_PROFIT > 0 and w["X"] / w["Y"] >= p_in * (1 + TAKE_PROFIT):' in src, "the hold loop: stop and take-profit on the mark with EXIT_MARK, the old price rule without it")
ok('"ev": "mark_exit"' in src and '"mark_hi"' in src and '"chain_polls"' in src and '"blocks_held"' in src, "the exit logs the mark's path (last, high, low), the polls and the blocks held")
ok('if ATTACK_MAX >= 0 and n_att > ATTACK_MAX:' in src and 'attackers {n_att} > ATTACK_MAX {ATTACK_MAX} at the build' in src, "ATTACK_MAX refuses a crowd at the build with its own reason")
ok('b_from = b_create or w.get("blk0") or (buy_block - 30 if buy_block else None)' in src and 'if EXIT_MARK and h and b_from:' in src, "the poll starts from the creation block, never from zero, and only live")
ok('"exit_mark": EXIT_MARK, "stop_loss": STOP_LOSS, "mark_poll_ms": MARK_POLL_MS, "attack_max": ATTACK_MAX' in src and '"release": "6.25"' in src, "the start line carries the switches; release 6.25")
print(f"all {checks} checks passed")
