"""6.13: the boosted stake. Two signed sets per burst, the send step picks the boosted shot when pick() is true at the shot's time;
the smart-helper list loads from a file and reloads when it changes; the relay float covers the boosted stake."""
import os, sys, json, time, tempfile, types
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("BANKROLL_USD", "50"), ("STAKE_MIN", "25"), ("STAKE_MAX", "25"), ("STAKE_BOOST_USD", "50"), ("SHOOTER_KEYS", "")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy")); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deploy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
# ---- the list ---------------------------------------------------------------------------------------------------------
E.state["eth_usd"] = 2700.0; logged = []; E.log = lambda d: logged.append(d)
f = tempfile.mkdtemp() + "/smart.json"; json.dump({"fitted": "t", "window_days": 7, "helpers": {"0xAAAA": {"n": 9}, "0xbbbb": {"n": 5}}}, open(f, "w")); E.SMART_HELPERS_PATH = f
E.smart_helpers_load(force=True)
ok(E.state["smart_helpers"] == {"0xaaaa", "0xbbbb"}, "the smart helpers load from the file, lower-cased")
w = {"attack_targets": {"0xcccc"}}
ok(E.smart_present(w) is False, "no smart helper among the attackers: not present")
w["attack_targets"].add("0xaaaa")
ok(E.smart_present(w) is True, "a smart helper among the attackers: present")
mt = E.state["smart_mtime"]; E.smart_helpers_load()
ok(E.state["smart_mtime"] == mt and E.state["smart_helpers"] == {"0xaaaa", "0xbbbb"}, "an unchanged file is not reloaded")
time.sleep(0.02); json.dump({"helpers": {"0xdddd": {}}}, open(f, "w")); os.utime(f, (time.time() + 5, time.time() + 5)); E.smart_helpers_load()
ok(E.state["smart_helpers"] == {"0xdddd"}, "a changed file reloads the list")
E.SMART_HELPERS_PATH = "/nonexistent/x.json"; E.smart_helpers_load(force=True)
ok(E.state["smart_helpers"] == {"0xdddd"}, "a missing file leaves the list as it was")
ok(abs(E.relay_float_eth() - 60 / 2700.0) < 1e-12, "the relay float is 1.2 x the boosted stake ($60)")
# ---- the send step: two signed sets, the pick at fire time ------------------------------------------------------------
from eth_account import Account
acct = Account.create(); os.environ["PRIVATE_KEY"] = acct.key.hex(); os.environ["SHOOTER_KEYS"] = ""
sent = []
class Sender:
    def fire_slot(self, body, i): sent.append((i, json.loads(body)["params"][0])); return (f"0xh{i}", None)
eng = types.SimpleNamespace(WALLET=acct.address, SENDER=Sender(), state={}, log=lambda d: logged.append(d), mono=time.monotonic)
import send_step
submit_burst = send_step.make_burst(eng)
ok(getattr(submit_burst, "alt", False) is True, "the send step advertises the alt/pick support")
def tx(amount): return {"to": "0x" + "ab" * 20, "value": "0x0", "data": "0x" + "%064x" % amount, "gas": hex(250000), "gasPrice": hex(10 ** 8), "nonce": hex(1), "chainId": 4663}
base = [tx(25)] * 4; alt = [tx(50)] * 4; t0 = time.monotonic() + 0.25; at = [t0 + i * 0.002 for i in range(4)]
calls = {"n": 0}
def pick():
    calls["n"] += 1; return calls["n"] >= 3                              # the smart helper shows up at the third shot
sent.clear(); logged.clear(); out = submit_burst(base, at, "buy", keys=None, gate=None, open_by=None, alt=alt, pick=pick)
ok(len(out) == 4 and all(h for h, _ in out), "four shots sent")
def amount_of(raw):
    import rlp
    return int.from_bytes(rlp.decode(bytes.fromhex(raw[2:]))[5][-32:], "big")
ok([amount_of(r) for _, r in sent] == [25, 25, 50, 50], "shots 1-2 carry the base stake, shots 3-4 the boosted one (the pick turned true at shot 3)")
ok(eng.state["last_boosted"] == [False, False, True, True], "the engine learns which shots were boosted")
sb = next(d for d in logged if d.get("ev") == "sent_burst"); ok(sb["boosted"] == 2 and sb["alt_skipped"] is None, "sent_burst logs two boosted shots and no skip")
# no time to sign the alt set: the first shot is due now
sent.clear(); logged.clear(); calls["n"] = 10; t1 = time.monotonic() + 0.0005
out = submit_burst(base, [t1 + i * 0.002 for i in range(4)], "buy", alt=alt, pick=pick)
ok([amount_of(r) for _, r in sent] == [25, 25, 25, 25] and next(d for d in logged if d.get("ev") == "sent_burst")["alt_skipped"], "no time to sign the boosted set: every shot is the base stake and the skip is logged")
# no alt at all: the old path
sent.clear(); logged.clear(); out = submit_burst(base, [time.monotonic() + 0.05 + i * 0.002 for i in range(4)], "buy")
ok([amount_of(r) for _, r in sent] == [25] * 4 and eng.state["last_boosted"] == [False] * 4, "without alt the burst is unchanged")
# the gate: shots before the gate opens are skipped, boosted shots only after
sent.clear(); logged.clear(); g = {"n": 0}
def gate(): g["n"] += 1; return g["n"] >= 2
calls["n"] = 10; out = submit_burst(base, [time.monotonic() + 0.05 + i * 0.002 for i in range(4)], "buy", gate=gate, open_by=None, alt=alt, pick=pick)
ok(out[0] == (None, None) and [amount_of(r) for _, r in sent] == [50, 50, 50] and eng.state["last_boosted"] == [False, True, True, True], "a gated first shot is skipped and marked unboosted; the rest go boosted")


# ---- 6.14: two shots per shooter -------------------------------------------------------------------------------------------
# the receipts: the second wave's pollers wait 0.3 s and poll at half the cadence; a fill in the first wave stops everything after the settle
calls = []
class R:
    def __init__(self, have): self.have = have
    def call(self, method, params, tries=3):
        calls.append((time.monotonic(), params[0])); return {"status": "0x1", "blockNumber": "0x10", "transactionIndex": "0x2"} if params[0] in self.have else None
E.rpc = R({"0xw1b"}); E.rpc_logs = R(set()); E.SENDER = type("S", (), {"rejected": lambda self, a: False})()
t0 = time.monotonic(); recs = E.burst_receipts([("0xw1a", None), ("0xw1b", None), ("0xw2a", None), ("0xw2b", None)], timeout=3.0, settle_s=0.2, first_wave=2)
ok(recs[1][1] and recs[1][1]["status"] == "0x1" and time.monotonic() - t0 < 1.0, "the first wave's fill is found and the read ends after the settle")
w2_first = min((t for t, h in calls if h in ("0xw2a", "0xw2b")), default=None)
ok(w2_first is None or w2_first - t0 >= 0.29, "the second wave's pollers did not start before 0.3 s")
n1 = sum(1 for _, h in calls if h == "0xw1a"); n2 = sum(1 for _, h in calls if h == "0xw2a")
ok(n2 <= max(1, n1 // 2) + 1, f"the second wave polled at most half as often ({n2} against {n1})")
# the nonce bookkeeping: two shots per shooter, the refused ones give the nonce back once each
E.state["shooter_nonce"] = {"a": 10, "b": 20}
seq = ["a", "b", "a", "b"]; recs2 = [("0x1", {"status": "0x0"}, None), ("0x2", None, None), ("0x3", {"status": "0x0"}, None), ("0x4", None, None)]
for a, (hh, _, _) in zip(seq, recs2): E.state["shooter_nonce"][a] += 1                                 # the provisional +1 per sent shot
E.restore_shooter_nonces(seq, recs2)
ok(E.state["shooter_nonce"] == {"a": 12, "b": 20}, "a's two shots landed (+2), b's two were refused (given back): the chain's count")
# the hardened pick: a set that raises during the copy never breaks the burst
class Bad:
    def __iter__(self): raise RuntimeError("Set changed size during iteration")
E.state["smart_helpers"] = {"0xaaaa"}
ok(E.smart_present({"attack_targets": Bad()}) is False, "a container that raises while copied answers False, not an exception")
ok(E.smart_present({"attack_targets": {"0xaaaa", "0x1"}}) is True, "and a normal set still answers")
print(f"\n{checks} checks passed")
