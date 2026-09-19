"""The send step (runbook section 9), as the file the engine loads when SEND_MODULE points at it.

    sudo cp deploy/send_step.py /etc/sniper/send_step.py
    # in /etc/sniper/engine.env:  SEND_MODULE=/etc/sniper/send_step.py  and  PRIVATE_KEY=0x...
    sudo systemctl restart sniper-engine

Nothing in the repository signs or sends until this file is in place and PRIVATE_KEY is set. The engine builds every
transaction exactly as before (checksummed 'to', hex fields, the next nonce, GAS_HEADROOM on the price); this signs it
with the key from the environment and fires it through the engine's warm sockets, sequencer first and provider second,
and returns the hash. It was run against the engine's own transaction with an unfunded key: the sequencer's only
complaint was the missing funds. Do not improvise on it at the boundary."""
import os, json, time
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


def make_burst(engine):
    """engine 5.6, BURST_N > 1: the buy as BURST_N shots at consecutive nonces. All are signed first; then each is written to
    its own warm socket to the sequencer at its scheduled time (engine.SENDER.fire_slot). Shots that reach the sequencer
    before the second boundary land in the creation second and revert on their minOut for the gas; the first one past it
    fills; the later ones revert on the same minOut once our own fill has moved the price. Returns [(hash, answers)]."""
    key = Account.from_key(os.environ["PRIVATE_KEY"])
    mono = engine.mono; cache = {}

    def signer(k):                                                       # engine 6.0: a shooter's key per shot (keys=), else the wallet's
        if k is None:
            return key
        if k not in cache:
            cache[k] = Account.from_key(k)
        return cache[k]

    def submit_burst(txs, at, label, keys=None):
        bodies = [json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction", "params": ["0x" + bytes(signer(keys[i] if keys else None).sign_transaction(tx).raw_transaction).hex()]}).encode() for i, tx in enumerate(txs)]
        t_signed = mono(); out = []; fired_at = []
        for i, body in enumerate(bodies):
            while mono() < at[i] - 0.004:                               # a prebuilt burst waits for the boundary here: sleep, then spin the last 4 ms
                time.sleep(0.0005)
            while mono() < at[i]:
                pass
            fired_at.append(mono()); out.append(engine.SENDER.fire_slot(body, i))
        engine.log({"ev": "sent_burst", "label": label, "hashes": [h for h, _ in out], "nonces": [tx["nonce"] for tx in txs], "shooters": bool(keys), "sign_ms": round(1000 * (t_signed - (at[0] - 0.0015 * len(txs))), 1),
                    "shot_ms": [round(1000 * (t - at[0]), 1) for t in fired_at], "late_ms": [round(1000 * (t - a), 2) for t, a in zip(fired_at, at)]})
        return out
    return submit_burst
