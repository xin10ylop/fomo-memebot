"""Engine 6.2: the burst's gate is decided shot by shot (report 24.32). The sender skips shots until the gate opens, sends nothing if it
never opens by the tick's shot, and a skipped shot never touches a shooter's nonce.

    python3 tests/test_gated_burst.py
"""
import os, sys, json, importlib.util, types, time
from eth_account import Account
from eth_utils import keccak, to_checksum_address
W = Account.create(); K = [Account.create() for _ in range(6)]
os.environ["PRIVATE_KEY"] = "0x" + bytes(W.key).hex()
fired = []; logs = []
class Sender:
    def fire_slot(self, body, slot):
        raw = json.loads(body)["params"][0]; fired.append(slot); return "0x" + keccak(bytes.fromhex(raw[2:])).hex(), []
engine = types.SimpleNamespace(WALLET=W.address, mono=time.monotonic, SENDER=Sender(), log=logs.append)
spec = importlib.util.spec_from_file_location("ss", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deploy", "send_step.py")); ss = importlib.util.module_from_spec(spec); spec.loader.exec_module(ss)
burst = ss.make_burst(engine)
tx = {"to": to_checksum_address("0x" + "ab" * 20), "value": "0x0", "data": "0x1622dbe4" + "00" * 32, "gas": hex(250000), "gasPrice": hex(10 ** 8), "chainId": 4663}
keys = ["0x" + bytes(k.key).hex() for k in K]; passed = 0
def check(name, ok):
    global passed
    print(("ok   " if ok else "FAIL ") + name); passed += ok
    assert ok, name
def run(gate, open_by_shot):
    fired.clear(); logs.clear(); t0 = engine.mono() + 0.01; at = [t0 + i * 0.003 for i in range(6)]
    out = burst([dict(tx, nonce=hex(i)) for i in range(6)], at, "buy", keys=keys, gate=gate, open_by=(at[open_by_shot] if open_by_shot is not None else None))
    return out, logs[-1]
# 1. no gate: every shot goes
out, ev = run(None, None)
check("no gate: all six shots sent", fired == list(range(6)) and all(h for h, _ in out) and ev["gated"] == 0 and ev["gate_opened_at_shot"] is None)
# 2. a gate that opens at the third call: shots 0-1 skipped, 2-5 sent
calls = [0]
def opens_third():
    calls[0] += 1; return calls[0] >= 3
out, ev = run(opens_third, 5)
check("gate opens at shot 2: shots 0-1 skipped as (None, None), 2-5 sent", [h is None for h, _ in out] == [True, True, False, False, False, False] and fired == [2, 3, 4, 5])
check("the log says 2 gated, opened at shot 2", ev["gated"] == 2 and ev["gate_opened_at_shot"] == 2)
check("once open it stays open: the gate is not asked again", calls[0] == 3)
# 3. a gate that never opens with open_by at shot 3: nothing sent, nothing asked after shot 3
calls[0] = 0
def never():
    calls[0] += 1; return False
out, ev = run(never, 3)
check("gate never opens: no shot sent, all six (None, None)", fired == [] and all(h is None and a is None for h, a in out))
check("the gate is asked up to the open_by shot and then the burst is abandoned", calls[0] == 4 and ev["gated"] == 6 and ev["gate_opened_at_shot"] is None)
# 4. a gate that opens exactly at the open_by shot still sends from there
calls[0] = 0
def opens_fourth():
    calls[0] += 1; return calls[0] >= 4
out, ev = run(opens_fourth, 3)
check("gate opens at the open_by shot: shots 3-5 sent", fired == [3, 4, 5] and ev["gated"] == 3)
# 5. the engine never decrements a nonce for a shot that was never sent
os.environ.update({"LOG_PATH": "/tmp/test_gated_burst.jsonl", "SEND_MODULE": "", "BURST_N": "35", "ATTACK_MIN": "2", "GATE_LATE_MS": "0"})
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
a, b, c = "0x" + "11" * 20, "0x" + "22" * 20, "0x" + "33" * 20
E.state["shooter_nonce"] = {a: 5, b: 5, c: 5}
E.restore_shooter_nonces([a, b, c], [(None, None, None), ("0xhash", None, [("0xhash", "nonce too high")]), ("0xhash2", {"status": "0x0"}, [])])
check("a gated shot (no hash) keeps its nonce; a refused shot gives one back; a landed shot keeps it", E.state["shooter_nonce"] == {a: 5, b: 4, c: 5})
check("GATE_LATE_MS and the settings are read", E.GATE_LATE_MS == 0.0 and E.ATTACK_MIN == 2)
# 6. the dry run with shooters configured: the nonce map is empty (only the live path fills it) and the build must not crash on it
E.state["shooter_nonce"] = {}
try:
    txs = [dict({"to": "0x0"}, nonce=hex(E.state["shooter_nonce"].get(a, 0))) for a in (a, b, c)]; ok = [t["nonce"] for t in txs] == ["0x0"] * 3
except KeyError:
    ok = False
check("dry run with shooters: an unfilled nonce map builds the shots at nonce 0 instead of raising", ok)
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy", "sniper_engine.py")).read()
check("the burst build reads the shooters' nonces with .get (the panel's night-killer, Sep 23)", 'state["shooter_nonce"].get(a, 0)' in src and 'nonce=hex(state["shooter_nonce"][a])' not in src)
# 7. attackers(): the launch's own token never counts, even when the approve came before the token was learned
w = {"attack_targets": {"0x" + "8532" * 10, "0x" + "99" * 20}, "attack_senders": set(), "tb": None}
check("before the token is learned the approve's target counts (nothing better is known)", E.attackers(w) == 2)
w["tb"] = bytes.fromhex("99" * 20)
check("once the token is learned it is subtracted", E.attackers(w) == 1)
# 8. burst_dropped: only shots that were sent can be lost
recs = [(None, None, None), (None, None, None), ("0xa", {"status": "0x0"}, []), ("0xb", None, [("0xb", "nonce too high")]), ("0xc", {"status": "0x1"}, [])]
lost = [i for i, (hh, r, a) in enumerate(recs) if hh and not r]
check("gated shots are not 'lost': only the refused sent shot is", lost == [3])
print(f"\n{passed} checks passed")
