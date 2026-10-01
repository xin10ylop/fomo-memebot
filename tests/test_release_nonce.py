"""6.15: a released reservation re-reads the wallet's nonce from the chain instead of only invalidating it (the launch 3 s after a
gated burst was refused "nonce/gas not fresh" on Sep 30 21:26); the landing log's offset from the seat block and the feed's load."""
import os, sys, json, time, tempfile, types, collections
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("BANKROLL_USD", "50"), ("STAKE_MIN", "25"), ("STAKE_MAX", "25"), ("ATTACK_MIN", "3"), ("SHOOTER_KEYS", "")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
class Node:
    def __init__(self, answer): self.answer = answer
    def call(self, m, p, tries=1):
        if isinstance(self.answer, Exception): raise self.answer
        return self.answer
# ---- release_reservation ------------------------------------------------------------------------------------------------
E.rpc = Node(hex(16)); E.rpc_logs = Node(hex(18)); E.state["nonce"] = 20; E.state["chain_at"] = -1e9; E.state["busy_until"] = 1e9
E.release_reservation()
ok(E.state["nonce"] == 18, "the release reads the nonce from the chain: the higher of the two nodes (16, 18) -> 18, not the reserved 20")
ok(E.mono() - E.state["chain_at"] < 1.0, "and the reading is fresh: the next launch is not refused 'nonce/gas not fresh'")
ok(E.state["busy_until"] == 0.0, "the busy window is cleared")
E.rpc = Node(RuntimeError("down")); E.rpc_logs = Node(RuntimeError("down")); E.state["nonce"] = 20; E.state["chain_at"] = E.mono()
E.release_reservation()
ok(E.state["nonce"] is None and E.state["chain_at"] == 0.0, "both nodes down: the old rule (None, the next launch waits for the poll)")
E.rpc = Node(hex(16)); E.rpc_logs = Node(RuntimeError("down")); E.state["nonce"] = 20
E.release_reservation()
ok(E.state["nonce"] == 16, "one node down: the other's answer")
real = E.next_nonce
def poll_wins():
    E.state["nonce"] = 99; E.state["chain_at"] = E.mono()                  # the background poll lands while the release is reading
    return 16
E.next_nonce = poll_wins; E.state["nonce"] = 20; E.release_reservation()
ok(E.state["nonce"] == 99, "the poll's value, written during the read, is kept over the release's own")
E.next_nonce = real
def boom(): raise RuntimeError("x")
E.next_nonce = boom; E.state["nonce"] = 20; E.release_reservation()
ok(E.state["nonce"] is None and E.state["chain_at"] == 0.0, "a raising read is the old rule, never an exception out of the launch thread")
E.next_nonce = real
# ---- landing_offset ------------------------------------------------------------------------------------------------------
E.state["flip_block"] = {1000: 500}
recs = [("h1", None, None), ("h2", {"blockNumber": hex(499), "status": "0x0"}, None), ("h3", {"blockNumber": hex(500), "status": "0x1"}, None), ("h4", {"blockNumber": hex(503), "status": "0x0"}, None)]
ok(E.landing_offset(recs, 1000) == -1, "the first shot landed in the creation second's last block: offset -1")
ok(E.landing_offset(recs[2:], 1000) == 0, "the seat block: offset 0")
ok(E.landing_offset(recs[3:], 1000) == 3, "three blocks late: offset +3")
ok(E.landing_offset(recs, 1001) is None, "no flip block for that second: None")
ok(E.landing_offset([("h", None, None)], 1000) is None, "no receipt: None")
# ---- feed_load -------------------------------------------------------------------------------------------------------------
E.state["block_ntx"] = collections.deque(maxlen=40)
ok(E.feed_load() is None, "no block seen: None")
for n in (5, 8, 6, 7, 5, 30, 31, 29, 30, 32, 28, 30, 31, 29, 30): E.state["block_ntx"].append(n)
ok(E.feed_load() == 30.0, "the mean of the last ten blocks (the steady 28-32 regime), not the earlier quiet ones")
ok(E.feed_load(15) == round(sum((5, 8, 6, 7, 5, 30, 31, 29, 30, 32, 28, 30, 31, 29, 30)) / 15, 1), "a wider window")
print(f"\n{checks} checks passed")
