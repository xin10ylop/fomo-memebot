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
print(f"\n{checks} checks passed")
