"""The send step (runbook section 9), as the file the engine loads when SEND_MODULE points at it.

    sudo cp deploy/send_step.py /etc/sniper/send_step.py
    # in /etc/sniper/engine.env:  SEND_MODULE=/etc/sniper/send_step.py  and  PRIVATE_KEY=0x...
    sudo systemctl restart sniper-engine

Nothing in the repository signs or sends until this file is in place and PRIVATE_KEY is set. The engine builds every
transaction exactly as before (checksummed 'to', hex fields, the next nonce, GAS_HEADROOM on the price); this signs it
with the key from the environment and fires it through the engine's warm sockets, sequencer first and provider second,
and returns the hash. It was run against the engine's own transaction with an unfunded key: the sequencer's only
complaint was the missing funds. Do not improvise on it at the boundary."""
import os, json
from eth_account import Account


def make(engine):
    key = Account.from_key(os.environ["PRIVATE_KEY"])
    if key.address.lower() != engine.WALLET.lower():
        raise SystemExit(f"send_step: PRIVATE_KEY is for {key.address}, WALLET is {engine.WALLET}: fix engine.env")

    def submit(tx, label):
        signed = key.sign_transaction(tx)
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction", "params": ["0x" + bytes(signed.raw_transaction).hex()]}).encode()
        result, answers = engine.SENDER.fire(body)
        engine.log({"ev": "sent_tx", "label": label, "hash": result, "answers": [(h, str(d)[:120]) for h, d in answers]})
        return result
    return submit
