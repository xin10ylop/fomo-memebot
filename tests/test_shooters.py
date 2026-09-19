"""Shooters (engine 6.0): with SHOOTER_KEYS and RELAY, every shot comes from its own shooter wallet at that wallet's nonce,
with no value (the relay buys with its ETH), 250k gas, the shooter's key handed to the send step; the wallet's nonce is
reserved for the approve and the sell only; a refused shot gives its nonce back; the relay's balance and the shooters'
gas gate the launch; the relay is refilled after the exit. Scripted feed, no network.

    python3 tests/test_shooters.py
"""
import os, sys, json, time, threading, tempfile
from eth_account import Account
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
RELAY = "0x00000000000000000000000000000000000beef3"
KEYS = [Account.create() for _ in range(4)]
for k, v in (("SEAT", "E1"), ("SEND_MODE", "predict"), ("MARGIN_MS", "0"), ("BURST_N", "4"), ("BURST_STEP_MS", "4"), ("BURST_LEAD_MS", "8"), ("BURST_SLIP", "0.25"),
             ("BUNDLE_MIN", "3"), ("BUNDLE_MIN_ETH", "0.3"), ("BUNDLE_MAX_ETH", "0"), ("MIN_CREATOR_SUPPLY", "0.01"), ("TIER_MIN_BPS", "100"), ("TIER_MAX_BPS", "200"),
             ("MAX_RESOLVE_MS", "600"), ("HOLD_S", "0.3"), ("TAKE_PROFIT", "0"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("MIN_FOLLOW_ETH_60", "0"),
             ("BANKROLL_USD", "300"), ("STAKE_MIN", "15"), ("STAKE_MAX", "15"), ("RELAY", RELAY), ("WALLET", "0xE0686DC72b04c12CeEFeea75E286E4Ef7C056f01"),
             ("SHOOTER_KEYS", ",".join("0x" + bytes(x.key).hex() for x in KEYS))):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

fails = []
def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail and not ok else ""))
    if not ok: fails.append(name)

captured = []; submitted = []
E.score_launch = lambda *a, **k: None
E.close_position = lambda pos, why: (captured.append(dict(pos)), E.state.update({"open": None}))
E.save_state = lambda: None
E.submit = lambda tx, label: (submitted.append((label, tx)), E.log({"ev": "unsigned_tx", "label": label, "tx": tx}), "0x" + "e" * 64)[2]
E.SENDER.mine = lambda: None
E.SENDER.rejected = lambda ans: False
E.get_logs = lambda filt, tries=3, seat=False: []
E.resolve_receipt = lambda *a, **k: None
E.tune_margin = lambda rec, seat_ts: None
E.refresh_wallet = lambda why="": None
E.refresh_shooters = lambda nonces=True, gas=True: None
E.next_nonce = lambda: E.state["nonce"]
T = 1_800_000_000; ADDR = [x.address.lower() for x in KEYS]
E.state.update({"nonce": 5, "chain_at": E.mono(), "eth_usd": 2500.0, "gas_price": 2 * 10 ** 8, "base_fee": 10 ** 8, "feed_ts": T, "blocks": 1000, "bankroll": 300.0, "day_start": 300.0, "open": None, "stopped": False,
                "wallet_eth": 0.02, "wallet_at": E.mono(), "relay_eth": 0.012, "relay_at": E.mono(), "shooter_nonce": {a: 10 + i for i, a in enumerate(ADDR)}, "shooter_eth": {a: 0.0001 for a in ADDR}, "shooter_at": E.mono()})
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
    time.sleep(1.0); E.state["chain_at"] = E.mono(); E.state["relay_at"] = E.mono()
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
def burst(txs, at, label, keys=None): calls.append((E.mono(), txs, at, label, keys)); return [("0x%064x" % (i + 1), None) for i in range(len(txs))]
E.SEND = object(); E.SEND_BURST = burst
CV = {"v": None}; FILLS = {"idx": (2,)}; NONE = {"idx": (4,)}
def receipt(h, timeout=10.0, ans=None, stop=None):
    i = int(h, 16)
    if i in NONE["idx"]:
        return None
    if i in FILLS["idx"]:
        return {"status": "0x1", "blockNumber": "0x11", "transactionIndex": hex(i), "logs": [{"topics": [E.BUY_EV, "0x" + RELAY[2:].zfill(64), "0x" + E.WALLET[2:].zfill(64)], "address": CV["v"], "data": "0x" + ("%064x" % int(0.006e18)) + ("%064x" % int(1_000_000e18))}]}
    return {"status": "0x0", "blockNumber": "0x10" if i == 1 else "0x11", "transactionIndex": hex(i), "logs": []}
E.wait_receipt = receipt

check("shooters: four addresses derived from the keys", E.SHOOTERS == ADDR)
check("shooters: WALLET_STAKE off", E.WALLET_STAKE is False)

# 1. a burst: shots from the shooters, no value, 250k gas, keys to the send step; the wallet's nonce reserved for two
CV["v"] = "0x" + "c1" * 20
c, curve = launch(1)
d = events("trade_decision", c)
check("shooters: the launch traded", bool(d), str([e.get("gates") for e in events("eligible_not_traded", c, wait=0.2)]))
if d:
    _, txs, at, _, keys = calls[-1]
    check("shooters: one shot per shooter, at each shooter's own nonce (10..13)", [int(t["nonce"], 16) for t in txs] == [10, 11, 12, 13], str([t["nonce"] for t in txs]))
    check("shooters: the keys handed to the send step are the shooters', in order", keys == E.SHOOTER_KEYS, str(keys)[:60])
    check("shooters: no value on the shot (the relay pays), 250k gas, to the relay", all(int(t["value"], 16) == 0 and int(t["gas"], 16) == 250_000 and t["to"].lower() == RELAY for t in txs))
    check("shooters: calldata carries the curve, the stake, the minOut and the deadline", txs[0]["data"][:10] == "0x1622dbe4" and abs(int(txs[0]["data"][74:138], 16) / 1e18 * 2500 - 15) < 0.5 and int(txs[0]["data"][202:266], 16) == T + 1)
    check("shooters: the wallet's nonce is reserved for the approve and the sell only (5 -> 7)", E.state["nonce"] == 7, str(E.state["nonce"]))
    time.sleep(0.6)
    check("shooters: the position's nonce is the wallet's next minus one (4), the approve at 5", captured and captured[-1]["nonce"] == 4 and any(l == "approve" and int(t["nonce"], 16) == 5 for l, t in submitted), str((captured[-1]["nonce"] if captured else None, [(l, t["nonce"]) for l, t in submitted if l == "approve"])))
    check("shooters: nonces advanced for the shots the chain took, the refused shot 4 gave its nonce back", E.state["shooter_nonce"][ADDR[0]] == 11 and E.state["shooter_nonce"][ADDR[3]] == 13, str(E.state["shooter_nonce"]))
    bd = events("burst_dropped", wait=0.3)
    check("shooters: the refused shot is logged as dropped", bd and bd[-1]["lost"] == 1)
    time.sleep(0.5)
    check("shooters: the position gets the tokens from the shooter's receipt", captured and abs(captured[-1]["tokens"] - 1_000_000) < 1)

# 2. the relay holds less than the stake: not traded
E.state.update({"relay_eth": 0.001, "open": None, "busy_until": 0.0}); CV["v"] = "0x" + "c2" * 20; submitted.clear()
c, curve = launch(2)
g = events("eligible_not_traded", c)
check("shooters: the relay below the stake gates the launch", bool(g) and any("the relay holds" in x for x in g[0]["gates"]), str(g[0]["gates"] if g else events("trade_decision", c, wait=0.2)))

# 3. shooters out of gas: not traded
E.state.update({"relay_eth": 0.012, "open": None, "busy_until": 0.0, "shooter_eth": {a: 0.00001 for a in ADDR}}); CV["v"] = "0x" + "c3" * 20
c, curve = launch(3)
g = events("eligible_not_traded", c)
check("shooters: no shooter with gas gates the launch", bool(g) and any("shooters have a nonce and gas" in x for x in g[0]["gates"]), str(g[0]["gates"] if g else None))
E.state["shooter_eth"] = {a: 0.0001 for a in ADDR}

# 4. relay refill after an exit: a plain transfer to the relay for the shortfall to 1.5 stakes
class R:
    def __init__(self): self.calls = []
    def call(self, m, p, **k):
        self.calls.append((m, p))
        if m == "eth_getBalance": return hex(int(0.002e18)) if p[0].lower() == RELAY else hex(int(0.03e18))
        return "0x0"
E.rpc = R(); submitted.clear(); E.SEND = object()
E.relay_topup("test")
tu = events("relay_topup", wait=0.5); tr = [t for l, t in submitted if l == "relay_float"]
target = 1.5 * 15 / 2500.0
check("relay refill: one transfer to the relay for the shortfall to 1.5 stakes", tu and tr and tr[0]["to"].lower() == RELAY and abs(int(tr[0]["value"], 16) / 1e18 - (target - 0.002)) < 1e-6, str((tu[-1] if tu else None, tr[:1])))

# 5. dry run: no keys, no shooter nonces needed
E.SEND = None; E.SEND_BURST = None; E.state.update({"nonce": 9, "chain_at": E.mono(), "open": None, "busy_until": 0.0}); CV["v"] = "0x" + "c4" * 20
c, curve = launch(4)
d = events("trade_decision", c); u = [e for e in events("unsigned_tx", wait=1.0) if e.get("label", "").startswith("buy")]
check("dry run with shooters: unsigned shots at the shooters' nonces, no value", d and u and all(int(e["tx"]["value"], 16) == 0 for e in u) and len(u) == 4, str([(e["tx"]["nonce"], e["tx"]["value"]) for e in u][:4]))

print("\nFAILED: " + str(fails) if fails else "\nall checks passed"); os._exit(1 if fails else 0)
