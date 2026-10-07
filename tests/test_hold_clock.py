"""6.21 (runbook 5bc): the hold is counted from the fill's own chain block (feed_seq < buy_block + HOLD_BLOCKS + 1), not from the
feed block the engine happened to be at when the receipt arrived; the wall-clock cap and the old clock remain as fallbacks."""
import os, sys, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("SHOOTER_KEYS", ""), ("HOLD_BLOCKS", "9")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
ok(E.HOLD_BLOCKS == 9, "HOLD_BLOCKS read")
now = E.mono()
pos = {"buy_block": 1000, "blocks_at_fill": 2003}       # the receipt came in three feed blocks after the fill (6.19's late pollers)
E.state["feed_seq"] = 1005; E.state["blocks"] = 2005
ok(E.still_holding(pos, now), "feed at fill+5: holding")
E.state["feed_seq"] = 1009
ok(E.still_holding(pos, now), "feed at fill+9: still holding (the old clock, started a block after the fill, sold when it had counted 9)")
E.state["feed_seq"] = 1010
ok(not E.still_holding(pos, now), "feed at fill+10 (= buy_block + HOLD_BLOCKS + 1): sell")
E.state["feed_seq"] = 1030
ok(not E.still_holding(pos, now), "well past: sell")
# the old clock would have waited for blocks_at_fill + 9 = 2012 on the feed's own counter: three blocks longer
E.state["feed_seq"] = 1010; E.state["blocks"] = 2009
ok(not E.still_holding(pos, now), "the chain clock decides even though the feed counter has not reached blocks_at_fill + 9")
# fallbacks
pos2 = {"buy_block": None, "blocks_at_fill": 2003}; E.state["feed_seq"] = 1010; E.state["blocks"] = 2011
ok(E.still_holding(pos2, now), "no buy_block (a fill whose block was not read): the feed-counter clock, holding at +8")
E.state["blocks"] = 2012
ok(not E.still_holding(pos2, now), "feed-counter clock: sell at blocks_at_fill + 9")
pos3 = {"buy_block": 1000, "blocks_at_fill": 2003}; E.state["feed_seq"] = None; E.state["blocks"] = 2005
ok(E.still_holding(pos3, now), "feed_seq unknown: the feed-counter clock")
E.state["feed_seq"] = 1002
ok(not E.still_holding(pos3, now - E.HOLD_EFF - 3.1), "the wall-clock cap (HOLD_EFF + 3 s) still ends a hold the feed never finishes counting")
pos4 = {}; ok(E.still_holding(pos4, now) == (now - now < E.HOLD), "no block fields at all: the seconds hold")
print(f"all {checks} checks passed")
