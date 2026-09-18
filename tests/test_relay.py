"""The BuyOnce relay in the engine (5.94): with RELAY set, every shot goes to the relay with (curve, amountIn, minOut) and
the stake as value; the fill is read from the curve's own Buy event in the shot's receipt; the stake is a setting again
(WALLET_STAKE off by default); a double fill is reported as a relay failure. Scripted feed, no network.

    python3 tests/test_relay.py
"""
import os, sys, json, time, threading, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
RELAY = "0x00000000000000000000000000000000000beef1"
for k, v in (("SEAT", "E1"), ("SEND_MODE", "predict"), ("MARGIN_MS", "0"), ("BURST_N", "4"), ("BURST_STEP_MS", "4"), ("BURST_LEAD_MS", "8"), ("BURST_SLIP", "0.25"),
             ("BUNDLE_MIN", "3"), ("BUNDLE_MIN_ETH", "0.3"), ("BUNDLE_MAX_ETH", "0"), ("MIN_CREATOR_SUPPLY", "0.01"), ("TIER_MIN_BPS", "100"), ("TIER_MAX_BPS", "200"),
             ("MAX_RESOLVE_MS", "600"), ("HOLD_S", "0.3"), ("TAKE_PROFIT", "0"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("MIN_FOLLOW_ETH_60", "0"),
             ("BANKROLL_USD", "300"), ("STAKE_MIN", "15"), ("STAKE_MAX", "15"), ("RELAY", RELAY), ("WALLET", "0xE0686DC72b04c12CeEFeea75E286E4Ef7C056f01")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

fails = []
def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail and not ok else ""))
    if not ok: fails.append(name)

captured = []
E.score_launch = lambda *a, **k: None
E.close_position = lambda pos, why: (captured.append(dict(pos)), E.state.update({"open": None}))
E.save_state = lambda: None
E.submit = lambda tx, label: (E.log({"ev": "unsigned_tx", "label": label, "tx": tx}), None)[1]
E.SENDER.mine = lambda: None
E.SENDER.rejected = lambda ans: False
E.get_logs = lambda filt, tries=3, seat=False: []
E.resolve_receipt = lambda *a, **k: None
E.tune_margin = lambda rec, seat_ts: None
E.refresh_wallet = lambda why="": None
T = 1_800_000_000
E.state.update({"nonce": 5, "chain_at": E.mono(), "eth_usd": 2500.0, "gas_price": 2 * 10 ** 8, "base_fee": 10 ** 8, "feed_ts": T, "blocks": 1000, "bankroll": 300.0, "day_start": 300.0, "open": None, "stopped": False,
                "wallet_eth": 0.2, "wallet_at": E.mono()})
E.state["flip_at"][T] = E.mono()
SENDERS = {}
E.sender_of = lambda raw: SENDERS.get(raw)
def events(kind, creator=None, wait=2.5):
    t0 = time.time()
    while time.time() - t0 < wait:
        try: out = [json.loads(l) for l in open(LOG)]
        except FileNotFoundError: out = []
        hits = [e for e in out if e.get("ev") == kind and (creator is None or e.get("creator") == creator)]
        if hits: return hits
        time.sleep(0.02)
    return []
def wallets(k): return ["0x" + ("%040x" % (0x1000 * k + i)) for i in range(3)]
def launch(k, eth=0.6, flip_after_s=0.9):
    curve = "0x" + ("%02x" % (0xc0 + k)) * 20; tok = "0x" + ("%02x" % (0xd0 + k)) * 20; creator = "0x" + ("%02x" % k) * 20; W = wallets(k)
    time.sleep(1.0)
    def feed():
        time.sleep(0.05)
        raw = ("one-%d" % k).encode(); SENDERS[raw] = W[0]
        data = bytes.fromhex("6f49227e") + bytes(12) + bytes.fromhex(curve[2:]) + b"".join(bytes(12) + bytes.fromhex(a[2:]) for a in W[1:]) + bytes(32)
        E.state["valtx"].append([E.mono(), T, None, eth, data, raw, 1000, "0x" + "14b9a544" + "0" * 32, "6f49227e"])
        with E.cond: E.cond.notify_all()
        time.sleep(flip_after_s - 0.05)
        with E.cond: E.state["feed_ts"] = T + 1; E.state["flip_at"][T + 1] = E.mono(); E.cond.notify_all()
    threading.Thread(target=feed, daemon=True).start()
    E.resolve_rpc = lambda *a, **kw: (tok, curve, 0.02 * E.Y0, 1000)
    E.state["feed_ts"] = T; E.state["busy_until"] = 0.0; E.boundary = lambda: (0.0, 0.9, 0.010)
    t_ref = E.mono() - 0.5; E.state["ref"] = (t_ref, T)
    E._handle_creation(creator, E.ZERO, int(0.035e18), E.mono(), T, set(W), 1000, tax_bps=100)
    return creator, curve

calls = []
def burst(txs, at, label): calls.append((E.mono(), txs, at, label)); return [("0x%064x" % (i + 1), None) for i in range(len(txs))]
E.SEND = object(); E.SEND_BURST = burst
CV = {"v": None}; FILLS = {"idx": (2,)}
def receipt(h, timeout=10.0, ans=None, stop=None):
    i = int(h, 16)
    if i in FILLS["idx"]:
        return {"status": "0x1", "blockNumber": "0x11", "transactionIndex": hex(i), "logs": [{"topics": [E.BUY_EV, "0x" + RELAY[2:].zfill(64), "0x" + E.WALLET[2:].zfill(64)], "address": CV["v"], "data": "0x" + ("%064x" % int(0.006e18)) + ("%064x" % int(1_000_000e18))}]}
    if i <= 4: return {"status": "0x0", "blockNumber": "0x10" if i == 1 else "0x11", "transactionIndex": hex(i), "logs": []}
    time.sleep(0.05); return None
E.wait_receipt = receipt

check("relay: WALLET_STAKE is off by default when RELAY is set", E.WALLET_STAKE is False)
check("relay: the address is kept lower-case", E.RELAY == RELAY)

# 1. shots go to the relay with the curve, the stake and the minOut; the value is the stake
CV["v"] = "0x" + "c1" * 20
c, curve = launch(1)
d = events("trade_decision", c)
check("relay: the launch traded", bool(d), str([e.get("gates") for e in events("eligible_not_traded", c, wait=0.2)]))
if d:
    _, txs, at, _ = calls[-1]
    check("relay: every shot's 'to' is the relay", all(tx["to"].lower() == RELAY for tx in txs), str([tx["to"] for tx in txs]))
    data = txs[0]["data"]
    check("relay: selector buy(address,uint256,uint256)", data[:10] == "0xa59ac6dd", data[:10])
    check("relay: word 1 is the curve", data[10:74] == curve[2:].zfill(64), data[10:74])
    amount = int(txs[0]["value"], 16)
    check("relay: word 2 is amountIn and equals the value", int(data[74:138], 16) == amount and abs(amount / 1e18 * 2500 - 15) < 0.5, f"amount {amount / 1e18 * 2500:.2f}")
    min_out = int(data[138:202], 16)
    check("relay: word 3 is minOut at 25% under the target", abs(min_out / 1e18 / d[0]["tokens_target"] - 0.75) < 0.001, f"{min_out / 1e18 / d[0]['tokens_target']:.4f}")
    check("relay: gas limit is the curve's plus the relay's", int(txs[0]["gas"], 16) == E.GAS_BUY + E.RELAY_GAS_EXTRA)
    check("relay: nonces consecutive from the reserved one", [int(tx["nonce"], 16) for tx in txs] == [5, 6, 7, 8], str([tx["nonce"] for tx in txs]))
    time.sleep(0.6)
    check("relay: the fill is read from the curve's Buy event in the relay shot's receipt (1,000,000 tokens)", captured and abs(captured[-1]["tokens"] - 1_000_000) < 1, str(captured[-1]["tokens"] if captured else None))
    check("relay: the position's nonce is the last shot's", captured and captured[-1]["nonce"] == 8, str(captured[-1]["nonce"] if captured else None))
    check("relay: no double-fill alarm", not any("double fill" in e.get("what", "") for e in events("alarm", wait=0.2)))

# 2. a double fill through the relay is reported as a relay failure
CV["v"] = "0x" + "c2" * 20; FILLS["idx"] = (2, 3); E.state.update({"open": None, "busy_until": 0.0})
c, curve = launch(2)
d = events("trade_decision", c); time.sleep(0.8)
al = [e for e in events("alarm", wait=0.5) if "THROUGH THE RELAY" in e.get("what", "")]
check("relay: a double fill is reported as a relay failure", bool(al), str([e.get("what") for e in events("alarm", wait=0.2)]))

# 3. dry run: the unsigned shots show the relay as the destination
E.SEND = None; E.SEND_BURST = None; E.state.update({"nonce": 9, "chain_at": E.mono(), "open": None, "busy_until": 0.0}); CV["v"] = "0x" + "c3" * 20; FILLS["idx"] = ()
c, curve = launch(3)
d = events("trade_decision", c); u = [e for e in events("unsigned_tx", wait=1.0) if e.get("label", "").startswith("buy")]
check("relay: dry run unsigned shots go to the relay", d and u and all(e["tx"]["to"].lower() == RELAY for e in u), str([e["tx"]["to"] for e in u][:2]))

print("\nFAILED: " + str(fails) if fails else "\nall checks passed"); os._exit(1 if fails else 0)
