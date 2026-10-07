"""6.22 (review 5bc F1, growth review): in a multi-wave burst a shot sends its key's lowest UNSENT body, so a shooter whose first
shot the gate skipped sends that first body (its current nonce) at its second slot instead of a nonce + 1 body the sequencer
would refuse ("nonce too high": Oct 5 20:21, 32 of 38 sent shots dead). Without a gate, or with the gate open from the start,
every slot sends its own body as before."""
import os, sys, json, time, types
from eth_account import Account
from eth_utils import to_checksum_address
os.environ["PRIVATE_KEY"] = "0x" + "11" * 32
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deploy"))
import send_step
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
KEYS = ["0x" + ("a%d" % i) * 32 for i in (1, 2, 3)]                     # three shooters
def tx(nonce, i):
    return {"nonce": hex(nonce), "gasPrice": hex(100 + i), "gas": hex(250_000), "to": to_checksum_address("0xe8e98c3514d5bd83fdd01360896f2382b861a720"), "value": hex(10 ** 15), "data": "0x" + "ab" * 36, "chainId": 4663}
fired = []; logged = []
engine = types.SimpleNamespace(mono=time.monotonic, state={}, log=lambda d: logged.append(d),
                               SENDER=types.SimpleNamespace(fire_slot=lambda body, i: fired.append((i, body)) or ("0xh%d" % i, [])))
burst = send_step.make_burst(engine)
def expected(txs, keys):
    return [json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction", "params": ["0x" + bytes(Account.from_key(k).sign_transaction(t).raw_transaction).hex()]}).encode() for t, k in zip(txs, keys)]
def run(waves, gate_open_at=None):
    keys = KEYS * waves; txs = [tx(10 + i // 3, i) for i in range(3 * waves)]   # per shooter: nonce 10, 11, 12 across the waves
    fired.clear(); logged.clear(); t0 = time.monotonic() - 1.0; at = [t0 + 0.001 * i for i in range(len(txs))]
    n = [0]
    def gate():
        n[0] += 1; return n[0] > gate_open_at                             # opens at the shot whose index equals gate_open_at
    out = burst(txs, at, "test", keys=keys, gate=(gate if gate_open_at is not None else None))
    exp = expected(txs, keys); sent = {i: exp.index(b) for i, b in fired}
    return out, sent, exp
# ---- no gate: each slot its own body ------------------------------------------------------------------------------------------
out, sent, exp = run(3)
ok(sent == {i: i for i in range(9)}, "no gate: every slot sends its own body")
ok(all(h == "0xh%d" % i for i, (h, _) in enumerate(out)), "one hash per slot, in slot order")
ok(logged[-1]["partner_substituted"] == 0, "no substitution logged")
# ---- the gate opens at shot 2: shooters 1 and 2 had their first shots skipped --------------------------------------------------
out, sent, exp = run(3, gate_open_at=2)
ok(out[0] == (None, None) and out[1] == (None, None), "slots 0 and 1 skipped (None, None)")
ok(sent[2] == 2, "slot 2 (shooter 3, first shot): its own body, nonce 10")
ok(sent[3] == 0 and sent[4] == 1, "slots 3 and 4 (shooters 1 and 2, second wave): their UNSENT first bodies (nonce 10), not nonce 11")
ok(sent[5] == 5, "slot 5 (shooter 3, second wave): its own second body (nonce 11), its first was sent")
ok(sent[6] == 3 and sent[7] == 4, "third wave for shooters 1 and 2: their second bodies (nonce 11): the chain stays unbroken")
ok(sent[8] == 8, "shooter 3's third body (nonce 12)")
ok(logged[-1]["partner_substituted"] == 4 and logged[-1]["gated"] == 2, "log: 2 gated, 4 substituted")
# ---- the gate opens at shot 4 of a two-wave burst (first wave of shooters 1..3 all skipped, shooter 2's second slot too) ----
out, sent, exp = run(2, gate_open_at=4)
ok([out[i] for i in range(4)] == [(None, None)] * 4, "slots 0-3 skipped")
ok(sent[4] == 1 and sent[5] == 2, "slots 4 and 5 (shooters 2 and 3, second wave) send their first bodies (nonce 10)")
ok(len(fired) == 2, "shooter 1 never fires: both of its slots were gated")
# ---- the gate open from the first shot: as before -----------------------------------------------------------------------------
out, sent, exp = run(2, gate_open_at=0)
ok(sent == {i: i for i in range(6)}, "gate open at shot 0: every slot its own body")
print(f"all {checks} checks passed")
