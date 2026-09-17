"""The creation-second seat (engine 5.3) enters only once the bundle is visible on the feed: the named wallets' buys resolve
the curve and fill the gates; a launch whose bundle never shows within E0_BUNDLE_WAIT_S is skipped without an RPC call and
without a send. Driven on a scripted feed state, no network.

    python3 tests/test_e0_wait.py
"""
import os, sys, json, time, threading, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E0"), ("E0_OUTSIDER", "1"), ("BUNDLE_MIN", "3"), ("BUNDLE_MIN_ETH", "0.3"), ("BUNDLE_MAX_ETH", "0"), ("MIN_CREATOR_SUPPLY", "0.01"),
             ("TIER_MIN_BPS", "100"), ("TIER_MAX_BPS", "200"), ("E0_BUNDLE_WAIT_S", "0.4"), ("MAX_RESOLVE_MS", "300"), ("HOLD_S", "0.3"), ("TAKE_PROFIT", "0"),
             ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("MIN_FOLLOW_ETH_60", "0"), ("BANKROLL_USD", "300"), ("STAKE_MIN", "10"), ("STAKE_MAX", "10")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

fails = []
def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail and not ok else ""))
    if not ok: fails.append(name)

closed = []
E.resolve_rpc = lambda *a, **k: None                       # no network: the E0 path must never need it
E.score_launch = lambda *a, **k: None
E.close_position = lambda pos, why: (closed.append(pos["curve"]), E.state.update({"open": None}))   # the real one clears the position
E.save_state = lambda: None
E.submit = lambda tx, label: None
E.wait_receipt = lambda *a, **k: None
E.SENDER.mine = lambda: None
T = 1_800_000_000
E.state.update({"nonce": 5, "chain_at": E.mono(), "eth_usd": 2500.0, "gas_price": 2 * 10 ** 8, "base_fee": 10 ** 8, "feed_ts": T, "blocks": 1000, "bankroll": 300.0, "day_start": 300.0, "open": None, "busy_until": 0.0})
E.state["flip_at"][T] = E.mono()

def events(creator, kind, wait=2.0):
    t0 = time.time()
    while time.time() - t0 < wait:
        try:
            out = [json.loads(l) for l in open(LOG)]
        except FileNotFoundError:
            out = []
        hits = [e for e in out if e.get("ev") == kind and e.get("creator") == creator]
        if hits:
            return hits
        time.sleep(0.05)
    return []

def run(creator, curve, named, buys, delay_s, tax_bps=100):
    """buys: list of (wallet, eth) appended to the feed state delay_s after the creation; returns the elapsed seconds"""
    def feed():
        time.sleep(delay_s)
        for w, eth in buys:
            E.state["buys"][curve].append((T, w, eth, E.mono(), 1001, curve, "59a87bc1"))
        with E.cond:
            E.cond.notify_all()
    threading.Thread(target=feed, daemon=True).start()
    t0 = E.mono()
    E._handle_creation(creator, E.ZERO, int(0.035e18), E.mono(), T, set(named), 1000, tax_bps=tax_bps)
    return E.mono() - t0

def wallets(k):                                                   # each launch names its own wallets, as on the chain
    return ["0x" + ("%040x" % (0x1000 * k + i)) for i in range(3)]

# 1. the bundle shows 120 ms after the creation: the curve is resolved from the feed, the gates see it, the seat is taken
c1, cv1 = "0x" + "11" * 20, "0x" + "a1" * 20
W = wallets(1); el = run(c1, cv1, W, [(w, 0.15) for w in W], 0.12)
d = events(c1, "trade_decision")
check("bundle visible at 120 ms: traded", bool(d), "no trade_decision")
if d:
    d = d[0]
    check("resolved from the feed, not the RPC", d.get("resolve_src") == "feed", d.get("resolve_src"))
    check("the gates saw the bundle (3 buys, 0.45 ETH)", d.get("bundle") == 3 and abs(d.get("bundle_eth", 0) - 0.45) < 1e-6, f"{d.get('bundle')} {d.get('bundle_eth')}")
    check("the wait for the bundle is recorded (100-400 ms)", 100 <= (d.get("bundle_wait_ms") or 0) <= 400, str(d.get("bundle_wait_ms")))
    check("the token's tax is on the decision", d.get("tax_bps") == 100)
check("the position was closed after the hold", bool(events(c1, "trade_decision")) and any(closed), "close_position not called")

# 2. no bundle ever shows: skipped at the deadline, no send, no RPC
c2, cv2 = "0x" + "22" * 20, "0x" + "a2" * 20
W = wallets(2); el = run(c2, cv2, W, [], 9.0)
s = events(c2, "skip", wait=1.0)
check("no bundle: skipped with the reason", bool(s) and any("bundle not visible" in str(e.get("why")) for e in s), str([e.get("why") for e in s]))
check("no bundle: the deadline held (0.4-0.7 s)", 0.38 <= el <= 0.7, f"{el:.2f} s")
check("no bundle: no trade decision", not events(c2, "trade_decision", wait=0.3))

# 3. three named buys but only 0.15 ETH: the ETH floor holds
c3, cv3 = "0x" + "33" * 20, "0x" + "a3" * 20
W = wallets(3); run(c3, cv3, W, [(w, 0.05) for w in W], 0.05)
s = events(c3, "skip", wait=1.0)
check("bundle under the ETH floor: skipped", bool(s) and any("0.150 ETH" in str(e.get("why")) for e in s), str([e.get("why") for e in s]))

# 4. a full bundle on a 1%-tier token: resolved, then refused by the tier gate (the gate still reads)
c4, cv4 = "0x" + "44" * 20, "0x" + "a4" * 20
W = wallets(4); run(c4, cv4, W, [(w, 0.15) for w in W], 0.05, tax_bps=0)
g = events(c4, "eligible_not_traded", wait=1.0)
check("1%-tier token with a full bundle: refused by the tier gate", bool(g) and any("token tax 0 bps < 100" in x for x in g[0].get("gates", [])), str([e.get("gates") for e in g]))

# 5. the bundle shows at 350 ms: over MAX_RESOLVE_MS=300 but inside the E0 limit (wait + 150 ms), still traded
c5, cv5 = "0x" + "55" * 20, "0x" + "a5" * 20
W = wallets(5); time.sleep(3.5); run(c5, cv5, W, [(w, 0.15) for w in W], 0.35)   # after the first trade's busy window (hold + 3 s)
d = events(c5, "trade_decision")
check("bundle at 350 ms: the resolve limit includes the wait, traded", bool(d) and 330 <= (d[0].get("bundle_wait_ms") or 0) <= 450, str([e.get("bundle_wait_ms") for e in d]) if d else str([e.get("gates") for e in events(c5, "eligible_not_traded", wait=0.5)]))

# 6. the same wallets launch again while their earlier, too-small bundle is still in the feed state: the new curve wins
c6, cv6 = "0x" + "66" * 20, "0x" + "a6" * 20
W = wallets(3); run(c6, cv6, W, [(w, 0.15) for w in W], 0.05)
d = events(c6, "trade_decision")
check("stale buys of the same wallets on another curve are not taken for the bundle", bool(d) and d[0].get("curve") == cv6 and d[0].get("bundle_eth") and abs(d[0]["bundle_eth"] - 0.45) < 1e-6, str([(e.get("curve"), e.get("bundle_eth")) for e in d]) if d else str([e.get("why") for e in events(c6, "skip", wait=0.5)]))
print("all creation-second wait tests pass" if not fails else f"{len(fails)} TESTS FAILED: {fails}")
raise SystemExit(1 if fails else 0)
