"""The burst send (engine 5.6): BURST_N shots at consecutive nonces, BURST_STEP_MS apart, the first BURST_LEAD_MS before the
predicted boundary; the filled shot's receipt is the buy, the rest revert or are refused. Scripted feed, no network.

    python3 tests/test_burst.py
"""
import os, sys, json, time, threading, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODE", "predict"), ("MARGIN_MS", "0"), ("BURST_N", "4"), ("BURST_STEP_MS", "4"), ("BURST_LEAD_MS", "8"), ("BURST_SLIP", "0.07"),
             ("BUNDLE_MIN", "3"), ("BUNDLE_MIN_ETH", "0.3"), ("BUNDLE_MAX_ETH", "0"), ("MIN_CREATOR_SUPPLY", "0.01"), ("TIER_MIN_BPS", "100"), ("TIER_MAX_BPS", "200"),
             ("MAX_RESOLVE_MS", "600"), ("HOLD_S", "0.3"), ("TAKE_PROFIT", "0"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("MIN_FOLLOW_ETH_60", "0"),
             ("BANKROLL_USD", "300"), ("STAKE_MIN", "10"), ("STAKE_MAX", "10")):
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
def launch(k, eth=0.6, flip_after_s=0.9):
    curve = "0x" + ("%02x" % (0xc0 + k)) * 20; tok = "0x" + ("%02x" % (0xd0 + k)) * 20; creator = "0x" + ("%02x" % k) * 20; W = wallets(k)
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
    t_ref = E.mono() - 0.5; E.state["ref"] = (t_ref, T)                     # the boundary of T+1 is 0.5 s away
    E._handle_creation(creator, E.ZERO, int(0.035e18), E.mono(), T, set(W), 1000, tax_bps=100)
    return creator, curve, t_ref + 1.0

# 1. live burst: shot 1 lands early (reverted), shot 2 fills, shot 3 reverts, shot 4 is refused
calls = []
def burst(txs, at, label): calls.append((E.mono(), txs, at, label)); return [("0x%064x" % (i + 1), None) for i in range(len(txs))]
E.SEND = object(); E.SEND_BURST = burst
def receipt(h, timeout=10.0, ans=None):
    i = int(h, 16)
    if i == 2:
        return {"status": "0x1", "blockNumber": "0x11", "transactionIndex": "0x0", "logs": [{"topics": [E.BUY_EV], "address": CV, "data": "0x" + ("%064x" % int(0.004e18)) + ("%064x" % int(1_000_000e18))}]}
    if i in (1, 3): return {"status": "0x0", "blockNumber": "0x10" if i == 1 else "0x11", "transactionIndex": "0x1", "logs": []}
    time.sleep(0.05); return None
E.wait_receipt = receipt
CV = "0x" + "c1" * 20
c, _, t_boundary = launch(1)
d = events("trade_decision", c)
check("burst: the launch traded", bool(d), str([e.get("why") for e in events("skip", c, wait=0.2)]) + str([e.get("gates") for e in d]))
check("burst: one burst call of 4 shots", len(calls) == 1 and len(calls[0][1]) == 4, str(len(calls)))
if calls:
    _, txs, at, _ = calls[0]
    check("burst: consecutive nonces from the reserved one (5..8), state nonce advanced by 6", [int(t["nonce"], 16) for t in txs] == [5, 6, 7, 8] and E.state["nonce"] == 11, f"{[int(t['nonce'],16) for t in txs]} {E.state['nonce']}")
    check("burst: shots 4 ms apart", all(abs((at[i + 1] - at[i]) * 1000 - 4) < 0.01 for i in range(3)), str([round((at[i+1]-at[i])*1000, 2) for i in range(3)]))
    check("burst: the first shot planned 8 ms before the boundary estimate (prebuilt: no signing budget)", -9.5 <= (at[0] - t_boundary) * 1000 <= -6.5, f"{(at[0]-t_boundary)*1000:.1f} ms")
    check("burst: the shots were built and handed to the send step before the boundary (prebuilt_ms > 100)", d[0].get("send_mode") == "predict-prebuilt" and (d[0].get("prebuilt_ms") or 0) > 100, f"{d[0].get('send_mode')} {d[0].get('prebuilt_ms')}")
    mo = int(txs[0]["data"][10 + 64:10 + 128], 16) / 1e18
    check("burst: the minOut is 7% below the sized tokens (BURST_SLIP), same in every shot", abs(mo / d[0]["tokens_target"] - 0.93) < 1e-6 and all(t["data"] == txs[0]["data"] for t in txs), f"{mo / d[0]['tokens_target']:.4f}")
    check("burst: every shot carries the same value and calldata, only the nonce differs", len({t["value"] for t in txs}) == 1 and len({t["nonce"] for t in txs}) == 4)
bl = events("burst_landing", wait=3.0)
check("burst_landing: 4 shots, one filled", bool(bl) and bl[0]["filled"] == 1 and len(bl[0]["shots"]) == 4, str(bl[:1])[:200])
t0 = time.time()
while not captured and time.time() - t0 < 3: time.sleep(0.02)
check("the position holds the filled shot's tokens (1.0M from its Buy event), its hash, nonce = last shot's (8)", bool(captured) and abs(captured[0]["tokens"] - 1_000_000) < 1 and captured[0]["buy_hash"] == "0x%064x" % 2 and captured[0]["nonce"] == 8, str({k: captured[0].get(k) for k in ("tokens", "buy_hash", "nonce")}) if captured else "no position")
check("the decision records burst 4", d and d[0].get("burst") == 4)

# 2. no shot fills: buy_reverted, no position
calls.clear(); captured.clear(); E.state["nonce"] = 5; E.state["chain_at"] = E.mono()
E.wait_receipt = lambda h, timeout=10.0, ans=None: {"status": "0x0", "blockNumber": "0x10", "transactionIndex": "0x1", "logs": []}
c, CV, _ = launch(2)
d = events("trade_decision", c); r = events("buy_reverted", wait=3.0)
check("all shots revert: buy_reverted logged, no position", bool(d) and any(e.get("curve") == CV for e in r) and E.state["open"] is None and not captured)

# 3. dry run: the burst is four unsigned transactions with consecutive nonces
E.SEND = None; E.SEND_BURST = None; calls.clear(); E.state["nonce"] = 5; E.state["chain_at"] = E.mono()
c, CV, _ = launch(3)
d = events("trade_decision", c); u = [e for e in events("unsigned_tx", wait=1.0) if e.get("label", "").startswith("buy#")]
check("dry run: four unsigned buy shots, consecutive nonces", bool(d) and len(u) == 4 and sorted(int(e["tx"]["nonce"], 16) for e in u) == list(range(int(u[0]["tx"]["nonce"], 16), int(u[0]["tx"]["nonce"], 16) + 4)) if u else False, str(len(u)))
print("all burst tests pass" if not fails else f"FAILED: {fails}")
sys.exit(1 if fails else 0)
