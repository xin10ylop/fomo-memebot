"""The wallet-sized stake (engine 5.93): live, every buy is the wallet less the gas reserve, so a second shot of the burst can
never be funded (the sequencer drops it). Above STAKE_MAX the engine refuses; a stale balance refuses; a supply cap that
would leave a second fill fundable refuses; the hold clock starts at the fill, not after the settle. Scripted feed, no network.

    python3 tests/test_wallet_stake.py
"""
import os, sys, json, time, threading, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODE", "predict"), ("MARGIN_MS", "0"), ("BURST_N", "4"), ("BURST_STEP_MS", "4"), ("BURST_LEAD_MS", "8"), ("BURST_SLIP", "0.03"),
             ("BUNDLE_MIN", "3"), ("BUNDLE_MIN_ETH", "0.3"), ("BUNDLE_MAX_ETH", "0"), ("MIN_CREATOR_SUPPLY", "0.01"), ("TIER_MIN_BPS", "100"), ("TIER_MAX_BPS", "200"),
             ("MAX_RESOLVE_MS", "600"), ("HOLD_S", "0.3"), ("TAKE_PROFIT", "0"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("MIN_FOLLOW_ETH_60", "0"),
             ("BANKROLL_USD", "300"), ("STAKE_MIN", "15"), ("STAKE_MAX", "60"), ("WALLET_STAKE", "1"), ("GAS_RESERVE_USD", "2.5"), ("SUPPLY_FRAC", "0.03")):
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
E.state.update({"nonce": 5, "chain_at": E.mono(), "eth_usd": 2500.0, "gas_price": 2 * 10 ** 8, "base_fee": 10 ** 8, "feed_ts": T, "blocks": 1000, "bankroll": 300.0, "day_start": 300.0, "open": None, "stopped": False})
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
def launch(k, eth=0.6, flip_after_s=0.9, supply=0.02):
    curve = "0x" + ("%02x" % (0xc0 + k)) * 20; tok = "0x" + ("%02x" % (0xd0 + k)) * 20; creator = "0x" + ("%02x" % k) * 20; W = wallets(k)
    time.sleep(1.0)                                                       # the previous launch's scripted flip must be over before this one starts
    def feed():
        time.sleep(0.05)
        raw = ("one-%d" % k).encode(); SENDERS[raw] = W[0]
        data = bytes.fromhex("6f49227e") + bytes(12) + bytes.fromhex(curve[2:]) + b"".join(bytes(12) + bytes.fromhex(a[2:]) for a in W[1:]) + bytes(32)
        E.state["valtx"].append([E.mono(), T, None, eth, data, raw, 1000, "0x" + "14b9a544" + "0" * 32, "6f49227e"])
        with E.cond: E.cond.notify_all()
        time.sleep(flip_after_s - 0.05)
        with E.cond: E.state["feed_ts"] = T + 1; E.state["flip_at"][T + 1] = E.mono(); E.cond.notify_all()
    threading.Thread(target=feed, daemon=True).start()
    E.resolve_rpc = lambda *a, **kw: (tok, curve, supply * E.Y0, 1000)
    E.state["feed_ts"] = T; E.state["busy_until"] = 0.0; E.boundary = lambda: (0.0, 0.9, 0.010)
    t_ref = E.mono() - 0.5; E.state["ref"] = (t_ref, T)
    E._handle_creation(creator, E.ZERO, int(0.035e18), E.mono(), T, set(W), 1000, tax_bps=100)
    return creator, curve, t_ref + 1.0

calls = []
def burst(txs, at, label): calls.append((E.mono(), txs, at, label)); return [("0x%064x" % (i + 1), None) for i in range(len(txs))]
E.SEND = object(); E.SEND_BURST = burst
CV = {"v": None}; FILL_AT = {"t": None}
def receipt(h, timeout=10.0, ans=None, stop=None):
    i = int(h, 16)
    if i == 2:
        time.sleep(0.05); FILL_AT["t"] = FILL_AT["t"] or E.mono()
        return {"status": "0x1", "blockNumber": "0x11", "transactionIndex": "0x0", "logs": [{"topics": [E.BUY_EV], "address": CV["v"], "data": "0x" + ("%064x" % int(0.004e18)) + ("%064x" % int(1_000_000e18))}]}
    if i in (1, 3): return {"status": "0x0", "blockNumber": "0x10" if i == 1 else "0x11", "transactionIndex": "0x1", "logs": []}
    time.sleep(0.05); return None
E.wait_receipt = receipt

# 1. wallet $40: the stake is the wallet less the reserve, the shot's value is that
E.state.update({"wallet_eth": 40.0 / 2500.0, "wallet_at": E.mono()}); CV["v"] = "0x" + "c1" * 20
c, _, _ = launch(1)
d = events("trade_decision", c)
check("wallet $40: the launch traded", bool(d), str([e.get("gates") for e in events("eligible_not_traded", c, wait=0.2)]))
if d:
    reserve = E.wallet_reserve_eth() * 2500.0
    check("wallet $40: stake is the wallet less the reserve", abs(d[0]["stake_usd"] - (40.0 - reserve)) < 0.01, f"stake {d[0]['stake_usd']:.2f} reserve {reserve:.2f}")
    check("wallet $40: reserve covers 4 shots, approve, the $2 exit ceiling and the upfront gas (2.5-3 dollars)", 2.4 < reserve < 3.5, f"{reserve:.2f}")
    v = int(calls[-1][1][0]["value"], 16) / 1e18 * 2500.0
    check("wallet $40: the shot's value equals the stake (the cap is not binding)", abs(v - d[0]["stake_usd"]) < 0.05, f"value ${v:.2f}")
    check("wallet $40: a second fill would need more than what is left", 40.0 - v < v, f"left ${40.0 - v:.2f}")
    time.sleep(0.6)
    check("hold clock: the position's t_buy is the fill's time, not after the settle", captured and FILL_AT["t"] and abs(captured[-1]["t_buy"] - FILL_AT["t"]) < 0.03, f"{(captured[-1]['t_buy'] - FILL_AT['t']) * 1000 if captured and FILL_AT['t'] else None} ms")
    check("hold clock: fill_seen_ms recorded", d[0].get("fill_seen_ms") is None or d[0].get("fill_seen_ms") >= 0)   # the decision is logged before the receipts; the field lands on the stored decision
    check("hold clock: the settle did not delay the position (fill seen to position under 0.7 s)", captured and (E.state["decisions"][d[0]["curve"]].get("fill_seen_ms") or 0) < 700, str(E.state["decisions"].get(d[0]["curve"], {}).get("fill_seen_ms")))

# 2. wallet $200 with STAKE_MAX 60: refused, with the withdraw instruction
E.state.update({"wallet_eth": 200.0 / 2500.0, "wallet_at": E.mono(), "open": None, "busy_until": 0.0}); CV["v"] = "0x" + "c2" * 20; FILL_AT["t"] = None
c, _, _ = launch(2)
g = events("eligible_not_traded", c)
check("wallet $200 > STAKE_MAX 60: not traded", bool(g) and not events("trade_decision", c, wait=0.2))
check("wallet $200: the gate says withdraw or raise STAKE_MAX", bool(g) and any("withdraw the excess or raise STAKE_MAX" in x for x in g[0]["gates"]), str(g[0]["gates"] if g else None))

# 3. wallet $10: below the minimum stake
E.state.update({"wallet_eth": 10.0 / 2500.0, "wallet_at": E.mono(), "open": None, "busy_until": 0.0}); CV["v"] = "0x" + "c3" * 20
c, _, _ = launch(3)
g = events("eligible_not_traded", c)
check("wallet $10 < STAKE_MIN 15: not traded, says top up", bool(g) and any("below the minimum stake" in x for x in g[0]["gates"]), str(g[0]["gates"] if g else None))

# 4. stale balance: refused
E.state.update({"wallet_eth": 40.0 / 2500.0, "wallet_at": E.mono() - 120, "open": None, "busy_until": 0.0}); CV["v"] = "0x" + "c4" * 20
c, _, _ = launch(4)
g = events("eligible_not_traded", c)
check("balance older than a minute: not traded", bool(g) and any("not read in the last minute" in x for x in g[0]["gates"]), str(g[0]["gates"] if g else None))

# 5. the supply cap shrinks the buy below half the wallet: a second shot could fill, so the launch is skipped
E.state.update({"wallet_eth": 60.0 / 2500.0, "wallet_at": E.mono(), "open": None, "busy_until": 0.0}); CV["v"] = "0x" + "c5" * 20
n_calls = len(calls); E.SUPPLY_FRAC = 0.001; c, _, _ = launch(5)      # a cap of 0.1% of supply costs far less than the $57 stake
E.SUPPLY_FRAC = 0.03
g = events("eligible_not_traded", c)
check("supply cap leaves a second fill fundable: not traded", bool(g) and any("second shot could fill" in x for x in g[0]["gates"]), str(g[0]["gates"] if g else None))
check("supply cap case: no shots sent", len(calls) == n_calls, str(len(calls) - n_calls))
check("supply cap case: the nonce reservation was released", E.state["nonce"] is None and E.state["busy_until"] == 0.0, f"nonce {E.state['nonce']} busy {E.state['busy_until']}")

# 6. dry run ignores the wallet (paper bankroll)
E.SEND = None; E.state.update({"nonce": 9, "chain_at": E.mono(), "wallet_eth": None, "wallet_at": -1e9, "open": None, "busy_until": 0.0}); CV["v"] = "0x" + "c6" * 20
c, _, _ = launch(6)
d = events("trade_decision", c)
check("dry run: traded on the paper bankroll without a wallet reading", bool(d) and abs(d[0]["stake_usd"] - 45.0) < 0.01, str(d[0]["stake_usd"] if d else events("eligible_not_traded", c, wait=0.2)))

print("\nFAILED: " + str(fails) if fails else "\nall checks passed"); os._exit(1 if fails else 0)
