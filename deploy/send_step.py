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


def make_probe(engine):
    """engine 6.16: the raw bytes of one signed transaction the sequencer always rejects (the wallet's nonce 0, long used: "nonce too
    low"), signed once; the engine posts it every PROBE_EVERY_S and times the reply (its door's delay, report 24.51). It can
    never land: the nonce is spent, so no gas, no balance, no state is touched."""
    key = Account.from_key(os.environ["PRIVATE_KEY"])
    signed = key.sign_transaction({"to": key.address, "value": 0, "data": b"", "gas": 21000, "gasPrice": 10 ** 9, "nonce": 0, "chainId": 4663})
    raw = bytes(signed.raw_transaction)

    def probe():
        return raw
    return probe


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

    # engine 6.7 (review J): the shots signed straight with coincurve, about 0.1 ms each against 0.65 ms through eth_account (35 shots:
    # 4 ms, not 23). Legacy EIP-155 transactions only (the engine builds every shot with gasPrice). Each key is proved once against
    # eth_account on a probe transaction before it is used; a key whose two signatures differ is signed through eth_account for good.
    fast = {}
    try:
        from coincurve import PrivateKey as _PK
        import rlp
        from eth_utils import keccak, to_checksum_address

        def _int(x):
            return x if isinstance(x, int) else int(x, 16)

        def _fast_sign(pk, tx):
            data = tx.get("data", b""); data = bytes.fromhex(data[2:]) if isinstance(data, str) else bytes(data)
            f = [_int(tx["nonce"]), _int(tx["gasPrice"]), _int(tx["gas"]), bytes.fromhex(tx["to"][2:]), _int(tx["value"]), data]
            cid = int(tx["chainId"]); sig = _PK(pk).sign_recoverable(keccak(rlp.encode(f + [cid, 0, 0])), hasher=None)
            return rlp.encode(f + [sig[64] + 35 + 2 * cid, int.from_bytes(sig[:32], "big"), int.from_bytes(sig[32:64], "big")])

        PROBE = {"to": to_checksum_address("0x" + "ab" * 20), "value": 1, "data": "0x0102", "gas": 21000, "gasPrice": 7, "nonce": 3, "chainId": 4663}

        def fast_key(k):
            """the key's bytes when its direct signature equals eth_account's on the probe, else None (proved once per key)"""
            if k not in fast:
                acct = signer(k); pk = bytes(acct.key)
                try:
                    fast[k] = pk if _fast_sign(pk, PROBE) == bytes(acct.sign_transaction(PROBE).raw_transaction) else None
                except Exception:
                    fast[k] = None
            return fast[k]

        def sign_raw(k, tx):
            pk = fast_key(k) if "gasPrice" in tx and "maxFeePerGas" not in tx else None
            return (_fast_sign(pk, tx) if pk else bytes(signer(k).sign_transaction(tx).raw_transaction)), bool(pk)

        try:                                                              # 6.9: prove every key at load; the first burst after a restart used to sign in 22 ms (the proofs), the rest in 4
            fast_key(None)
            for _k in os.environ.get("SHOOTER_KEYS", "").split(","):
                if _k.strip():
                    fast_key(_k.strip())
        except Exception:
            pass
    except Exception:
        def sign_raw(k, tx):
            return bytes(signer(k).sign_transaction(tx).raw_transaction), False

    def submit_burst(txs, at, label, keys=None, gate=None, open_by=None, alt=None, pick=None):
        """engine 6.2: with gate (a callable), a shot is sent only once gate() is true; shots before that are skipped (they would have
        landed in the tax second and reverted anyway), and if the gate is still shut at the shot scheduled after open_by no later shot
        is sent at all. A skipped shot is (None, None) in the result. 6.13: with alt (a second transaction per shot, the boosted stake
        at the same nonce) and pick (a callable), each shot sends the alt when pick() is true at its time; the alt set is signed after
        the base set and only when that signing cannot delay the first shot."""
        t_sign0 = mono(); raws = [sign_raw(keys[i] if keys else None, tx) for i, tx in enumerate(txs)]; n_fast = sum(1 for _, f in raws if f)
        bodies = [json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction", "params": ["0x" + raw.hex()]}).encode() for raw, _ in raws]
        alt_bodies = None; alt_skipped = None
        if alt is not None and pick is not None:
            per = (mono() - t_sign0) / max(1, len(txs))                     # the base set's cost per signature, measured just now
            if mono() + per * len(alt) * 1.5 < at[0]:
                alt_raws = [sign_raw(keys[i] if keys else None, tx) for i, tx in enumerate(alt)]
                alt_bodies = [json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction", "params": ["0x" + raw.hex()]}).encode() for raw, _ in alt_raws]
            else:
                alt_skipped = f"no time to sign the boosted set ({1000 * per * len(alt):.0f} ms needed)"
        t_signed = mono(); out = []; fired_at = []; opened = gate is None; opened_at = None; shut = False; boosted = []
        for i, body in enumerate(bodies):
            while mono() < at[i] - 0.0015:                              # a prebuilt burst waits for the boundary here: sleep to 1.5 ms before the shot,
                time.sleep(0.0002)                                       # then spin yielding the interpreter lock each turn (engine 6.7, review J: the old
            while mono() < at[i]:                                        # 4 ms spin held the lock for the whole burst and starved the feed loop at the gate)
                time.sleep(0)
            if not opened and not shut:
                opened = bool(gate())
                if opened:
                    opened_at = i
                elif open_by is not None and at[i] >= open_by:
                    shut = True                                          # too late for a shot to straddle the tick: the burst is abandoned
            if not opened:
                fired_at.append(mono()); out.append((None, None)); boosted.append(False); continue
            try:
                use_alt = bool(alt_bodies is not None and pick())        # 6.13: the boosted shot when a smart helper is in at this moment
            except Exception:
                use_alt = False                                          # never let the pick break the burst
            boosted.append(use_alt); fired_at.append(mono()); out.append(engine.SENDER.fire_slot(alt_bodies[i] if use_alt else body, i))
        engine.state["last_boosted"] = boosted
        engine.log({"ev": "sent_burst", "label": label, "hashes": [h for h, _ in out], "nonces": [tx["nonce"] for tx in txs], "shooters": bool(keys), "gated": sum(1 for h, _ in out if h is None), "boosted": sum(boosted), "alt_skipped": alt_skipped, "gate_opened_at_shot": opened_at, "sign_ms": round(1000 * (t_signed - t_sign0), 1), "signed_direct": n_fast,
                    "shot_ms": [round(1000 * (t - at[0]), 1) for t in fired_at], "late_ms": [round(1000 * (t - a), 2) for t, a in zip(fired_at, at)]})
        return out
    submit_burst.alt = True                                               # 6.13: the engine passes alt= and pick= only to a send step that has this
    return submit_burst
