"""The send step signs each burst shot with its shooter's key when keys= is given (engine 6.0), and with the wallet's key
otherwise; the hashes it returns are the signed transactions' hashes.

    python3 tests/test_send_step_keys.py
"""
import os, sys, json, importlib.util, types
from eth_account import Account
from eth_utils import keccak
W = Account.create(); K = [Account.create() for _ in range(3)]
os.environ["PRIVATE_KEY"] = "0x" + bytes(W.key).hex()
fired = []
class Sender:
    def fire_slot(self, body, slot):
        raw = json.loads(body)["params"][0]; fired.append(raw); return "0x" + keccak(bytes.fromhex(raw[2:])).hex(), []
engine = types.SimpleNamespace(WALLET=W.address, mono=lambda: __import__("time").monotonic(), SENDER=Sender(), log=lambda e: None)
spec = importlib.util.spec_from_file_location("ss", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deploy", "send_step.py")); ss = importlib.util.module_from_spec(spec); spec.loader.exec_module(ss)
burst = ss.make_burst(engine)
tx = {"to": __import__("eth_utils").to_checksum_address("0x" + "ab" * 20), "value": "0x0", "data": "0x1622dbe4" + "00" * 32, "gas": hex(250000), "gasPrice": hex(10 ** 8), "chainId": 4663}
fails = []
def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail and not ok else ""))
    if not ok: fails.append(name)
t0 = engine.mono()
out = burst([dict(tx, nonce=hex(7)), dict(tx, nonce=hex(3)), dict(tx, nonce=hex(0))], [t0 + 0.01, t0 + 0.014, t0 + 0.018], "buy", keys=["0x" + bytes(k.key).hex() for k in K])
senders = [Account.recover_transaction(raw) for raw in fired]
check("with keys: each shot is signed by its shooter, in order", senders == [k.address for k in K], str(senders))
check("with keys: the returned hashes are the signed transactions' hashes", [h for h, _ in out] == ["0x" + keccak(bytes.fromhex(r[2:])).hex() for r in fired])
fired.clear()
out = burst([dict(tx, nonce=hex(1)), dict(tx, nonce=hex(2))], [engine.mono() + 0.01, engine.mono() + 0.014], "buy")
check("without keys: the wallet signs every shot", [Account.recover_transaction(r) for r in fired] == [W.address, W.address])
print("\nFAILED: " + str(fails) if fails else "\nall checks passed"); os._exit(1 if fails else 0)
