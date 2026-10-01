"""6.16: the sequencer-door probe (a signed, always-rejected transaction timed every PROBE_EVERY_S), its summary, the skip rule,
and the send step's probe body."""
import os, sys, json, time, tempfile, collections
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("BANKROLL_USD", "50"), ("STAKE_MIN", "25"), ("STAKE_MAX", "25"), ("SHOOTER_KEYS", ""), ("PROBE_EVERY_S", "10"), ("SEQ_RTT_SKIP_MS", "0")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy")); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deploy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
class Door:
    def __init__(self, delay, answer): self.delay = delay; self.answer = answer; self.calls = []
    def call(self, m, p, tries=1):
        self.calls.append((m, p, tries)); time.sleep(self.delay)
        if isinstance(self.answer, Exception): raise self.answer
        return self.answer
# ---- the probe ------------------------------------------------------------------------------------------------------------
ok(E.seq_probe() is None and not E.state["seq_rtt"], "no send step: no probe, nothing recorded")
E.rpc_seq = Door(0.05, RuntimeError("nonce too low")); ms = E.seq_probe(b"\x01\x02")
ok(45 <= ms <= 400 and E.rpc_seq.calls == [("eth_sendRawTransaction", ["0x0102"], 1)], f"the rejection is timed ({ms} ms) and posted once, as a raw send, where the shots go")
ok(len(E.state["seq_rtt"]) == 1 and E.state["seq_rtt"][0][1] == ms, "recorded")
E.rpc_seq = Door(0.0, "0xdeadbeef"); E.seq_probe(b"\x01")
ok(len(E.state["seq_rtt"]) == 2, "an accepted answer (it cannot happen: nonce 0) is timed all the same")
E.SEND_PROBE = lambda: b"\x09"; E.seq_probe()
ok(E.rpc_seq.calls[-1][1] == ["0x09"], "without an argument the send step's body is posted")
# ---- the summary ----------------------------------------------------------------------------------------------------------
E.state["seq_rtt"] = collections.deque(maxlen=60)
ok(E.seq_rtt() == (None, None, None), "nothing probed yet: three Nones (the gate stays open)")
now = E.mono()
for i, m in enumerate((90.0, 110.0, 100.0, 95.0, 620.0, 1160.0, 640.0)): E.state["seq_rtt"].append((now - (7 - i) * 10, m))
ms, age, med = E.seq_rtt()
ok(ms == 640.0 and 9.5 <= age <= 11 and med == 365.0, f"the latest ({ms} ms, {age} s old) and the median of the last six ({med})")
# ---- the skip rule --------------------------------------------------------------------------------------------------------
ok(E.door_slow(1200.0, 5.0) is False, "SEQ_RTT_SKIP_MS=0: never skips, whatever the probe says")
E.SEQ_RTT_SKIP_MS = 400.0
ok(E.door_slow(1200.0, 5.0) is True, "limit 400: a 1200 ms probe 5 s old skips")
ok(E.door_slow(150.0, 5.0) is False, "a 150 ms probe does not")
ok(E.door_slow(1200.0, 45.0) is False, "a probe older than three cadences (30 s) is not trusted: no skip")
ok(E.door_slow(None, None) is False, "no probe: no skip")
E.SEQ_RTT_SKIP_MS = 0.0
# ---- the send step's body -------------------------------------------------------------------------------------------------
from eth_account import Account
import rlp
k = Account.create(); os.environ["PRIVATE_KEY"] = k.key.hex()
import send_step
probe = send_step.make_probe(E); raw = probe()
ok(isinstance(raw, (bytes, bytearray)) and raw[0] >= 0xc0, "a raw legacy transaction (RLP list)")
fields = rlp.decode(bytes(raw))
ok(fields[0] == b"" and int.from_bytes(fields[2], "big") == 21000 and fields[3] == bytes.fromhex(k.address[2:]) and fields[4] == b"", "nonce 0, 21000 gas, to the wallet itself, value 0")
ok(Account.recover_transaction(bytes(raw)).lower() == k.address.lower(), "signed by the wallet's key")
ok(probe() is raw, "signed once, the same bytes every time")
print(f"\n{checks} checks passed")
