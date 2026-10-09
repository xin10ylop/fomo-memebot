"""6.25 (runbook 5bj, the runner): the mark-based exit. position_mark = selling every token now, net of the sell fee, over the ETH
paid (the tables' and the simulator's mark); it reads the chain poll's reserves when under a second old, else the feed's fold.
mark_poll folds every Buy and Sell since the creation from the curve's constants. STOP_LOSS sells at or below -it, TAKE_PROFIT at
or above it, both only with EXIT_MARK; ATTACK_MAX refuses a crowd at the build. Nothing changes for the sniper (EXIT_MARK off)."""
import os, sys, tempfile, time
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("SHOOTER_KEYS", ""), ("EXIT_MARK", "1"), ("STOP_LOSS", "0.30"), ("TAKE_PROFIT", "0.30"), ("ATTACK_MAX", "0"), ("MARK_POLL_MS", "5"), ("MARK_FRESH_S", "1.5"), ("MARK_FEED_AFTER_S", "1.0"), ("MARK_FEED_STALE_S", "3.0")):
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
pos = {"tokens": tk, "t_mark0": -1e9}                                   # the fill long ago: with no chain reading the feed's fold decides
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
# 6.26: which source decides. A fresh chain reading wins; once a chain reading exists, a stale one decides nothing until the poll has
# been silent MARK_FEED_STALE_S (then the feed's fold); before any chain reading the feed's fold decides after MARK_FEED_AFTER_S
pos["t_mark0"] = 100.0
ok(E.position_mark(w, pos, gross, now=100.2) is None, "no chain reading yet and 0.2 s since the fill: no decision")
ok(abs(E.position_mark(w, pos, gross, now=101.1) - m0) < 1e-9, "no chain reading 1.1 s after the fill: the feed's fold decides")
w["chain_xy"] = (w["X"] * 1.5, w["Y"], 101.0)
ok(E.position_mark(w, pos, gross, now=101.5) > m0 + 0.3, "a fresh chain reading (reserves 1.5x) is the mark's source")
ok(E.position_mark(w, pos, gross, now=102.7) is None, "a chain reading 1.7 s old: no decision (the feed's fold may not stand in yet)")
ok(abs(E.position_mark(w, pos, gross, now=104.1) - m0) < 1e-9, "the poll silent for 3.1 s: the feed's fold decides")
w.pop("chain_xy")
# dry run: our buy is not on the curve; the mark adds it
wd = {"X": X0, "Y": Y0, "tax": 0.01}; td = wd["Y"] * net / (wd["X"] + net)
pd = {"tokens": td, "t_mark0": 0.0, "dry": True}
md = E.position_mark(wd, pd, gross, now=5.0)
ok(abs(md - m0) < 2e-3, f"dry run: the virtual buy added, the mark matches the live one ({100*md:+.2f}% vs {100*m0:+.2f}%)")
# mark_reading: the fold from the constants, and the answers it refuses
BUY, SELL = E.BUY_EV, E.SELL_EV
def word(x): return ("%064x" % int(x * 1e18))
H = "0x" + "77" * 32
events = [{"blockNumber": "0x10", "logIndex": "0x1", "topics": [BUY], "data": "0x" + word(0.02) + word(1.2e7), "transactionHash": "0x" + "11" * 32},
          {"blockNumber": "0x11", "logIndex": "0x0", "topics": [SELL], "data": "0x" + word(5e6) + word(0.008), "transactionHash": "0x" + "22" * 32},
          {"blockNumber": "0x11", "logIndex": "0x2", "topics": [BUY], "data": "0x" + word(0.05) + word(2.5e7), "transactionHash": H}]
X, Y = X0, Y0
X, Y = X + X * 1.2e7 / (Y - 1.2e7), Y - 1.2e7; X, Y = X - X * 5e6 / (Y + 5e6), Y + 5e6; X, Y = X + X * 2.5e7 / (Y - 2.5e7), Y - 2.5e7
r = E.mark_reading(list(reversed(events)), {"buy_hash": H})
ok(r and abs(r[0] - X) < 1e-12 and abs(r[1] - Y) < 1e-6 and r[2] == 0x11, "the events sorted by block and index and folded from X0/Y0 give the chain's reserves and the last block")
ok(E.mark_reading([], {"buy_hash": H}) is None and E.mark_reading(None, {}) is None, "an empty answer is refused (the creator's buy is always there)")
ok(E.mark_reading(events[:2], {"buy_hash": H}) is None, "live, an answer without our buy is refused (a node behind our fill: the -55% stop)")
ok(E.mark_reading(events[:2], {"buy_block": 0x12}) is None and E.mark_reading(events, {"buy_block": 0x11}) is not None, "without the hash, an answer that ends before our fill block is refused")
# mark_poll: one try, back off after an error or an untrusted answer
import threading
calls = []
class R:
    def __init__(self, answers): self.answers = answers
    def call(self, m, p, tries=3):
        calls.append((m, p, tries)); a = self.answers.pop(0) if self.answers else list(events)
        if isinstance(a, Exception): raise a
        return a
E.MARK_BACKOFF_S = 0.05; E.MARK_POLL_MS = 5
E.rpc_logs = R([RuntimeError("node down"), [], list(events)])
w2 = {"X": X0, "Y": Y0}; pos2 = {"tokens": 1.0, "buy_hash": H}; E.state["open"] = pos2
t = threading.Thread(target=E.mark_poll, args=(w2, pos2, "0x" + "ab" * 20, 16), daemon=True); t.start(); time.sleep(0.3); E.state["open"] = None; t.join(1.0)
ok(all(c[2] == 1 for c in calls) and calls[0][1][0]["fromBlock"] == hex(16), "one try per poll, from the block given")
ok(w2.get("chain_poll_errs") == 1 and w2.get("chain_poll_untrusted", 0) == 1 and "chain_xy" in w2 and w2["chain_last_block"] == 0x11, "an error and an empty answer counted, then a trusted reading stored")
# the poll's start block: never the feed's message counter
E.state["flip_block"][1791500000] = 84_000_100
ok(E.mark_from_block(None, 1791500000, 84_000_130) == 84_000_100, "no creation block: the first block of the creation second as the feed numbered it")
ok(E.mark_from_block(84_000_101, 1791500000, 84_000_130) == 84_000_101, "the creation block when known")
ok(E.mark_from_block(None, 1791500999, 84_000_130) == 84_000_090, "neither: 40 blocks before the fill")
ok(E.mark_from_block(412_345, 1791500999, 84_000_130) == 84_000_090, "a number far from the fill (a message counter) is replaced: within 2,000 blocks of the fill")
# the engine's use (source checks: the branch sits inside the launch thread)
src = open(E.__file__).read()
ok('if STOP_LOSS > 0 and m <= -STOP_LOSS:' in src and 'if TAKE_PROFIT > 0 and m >= TAKE_PROFIT:' in src and 'elif TAKE_PROFIT > 0 and w["X"] / w["Y"] >= p_in * (1 + TAKE_PROFIT):' in src, "the hold loop: stop and take-profit on the mark with EXIT_MARK, the old price rule without it")
ok('"ev": "mark_exit"' in src and '"mark_hi"' in src and '"chain_polls"' in src and '"blocks_held"' in src, "the exit logs the mark's path (last, high, low), the polls and the blocks held")
ok('if ATTACK_MAX >= 0 and n_att > ATTACK_MAX:' in src and 'attackers {n_att} > ATTACK_MAX {ATTACK_MAX} at the build' in src, "ATTACK_MAX refuses a crowd at the build with its own reason")
ok('b_from = mark_from_block(b_create, feed_ts, buy_block) if EXIT_MARK else None' in src and 'if EXIT_MARK and b_from:' in src and 'pos["dry"] = h is None' in src, "the poll starts from mark_from_block, in dry run too; a dry position is marked as dry")
ok('if not (EXIT_MARK and (state.get("open") or {}).get("curve") == curve):' in src and 'state["busy_until"] = 0.0; state["watch"].pop(curve, None)' in src, "a held curve keeps its feed fold past 25 s; after a mark exit the busy timer clears and the watch is dropped")
ok('"exit_mark": EXIT_MARK, "stop_loss": STOP_LOSS, "mark_poll_ms": MARK_POLL_MS, "attack_max": ATTACK_MAX' in src, "the start line carries the switches")
print(f"all {checks} checks passed")
