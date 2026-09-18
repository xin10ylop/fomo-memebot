"""The next-second seat (SEAT=E1) on today's bundles: one helper transaction carries the whole bundle (engine 5.49), the
curve is resolved, the gates read bundle 3, and the send waits for the second after the creation's, in react mode (the feed
message that opens the second) and in predict mode (the boundary estimate). Scripted feed state, no network.

    python3 tests/test_e1_bundle.py
"""
import os, sys, json, time, threading, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODE", "react"), ("SEAT_WAIT_MS", "0"), ("MARGIN_MS", "15"), ("BUNDLE_MIN", "3"), ("BUNDLE_MIN_ETH", "0.3"), ("BUNDLE_MAX_ETH", "0"),
             ("MIN_CREATOR_SUPPLY", "0.01"), ("TIER_MIN_BPS", "100"), ("TIER_MAX_BPS", "200"), ("MAX_RESOLVE_MS", "600"), ("HOLD_S", "0.3"), ("TAKE_PROFIT", "0"),
             ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("MIN_FOLLOW_ETH_60", "0"), ("BANKROLL_USD", "300"), ("STAKE_MIN", "10"), ("STAKE_MAX", "10")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

fails = []
def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail and not ok else ""))
    if not ok: fails.append(name)

E.score_launch = lambda *a, **k: None
E.close_position = lambda pos, why: E.state.update({"open": None})
E.save_state = lambda: None
E.submit = lambda tx, label: None
E.wait_receipt = lambda *a, **k: None
E.SENDER.mine = lambda: None
E.get_logs = lambda filt, tries=3, seat=False: []
E.resolve_receipt = lambda *a, **k: None                    # no network: the creation receipt is not there, the (mocked) log scan resolves the curve
T = 1_800_000_000
E.state.update({"nonce": 5, "chain_at": E.mono(), "eth_usd": 2500.0, "gas_price": 2 * 10 ** 8, "base_fee": 10 ** 8, "feed_ts": T, "blocks": 1000, "bankroll": 300.0, "day_start": 300.0, "open": None, "stopped": False})
E.state["flip_at"][T] = E.mono()
SENDERS = {}
E.sender_of = lambda raw: SENDERS.get(raw)

def events(creator, kind, wait=2.5):
    t0 = time.time()
    while time.time() - t0 < wait:
        try:
            out = [json.loads(l) for l in open(LOG)]
        except FileNotFoundError:
            out = []
        hits = [e for e in out if e.get("ev") == kind and e.get("creator") == creator]
        if hits:
            return hits
        time.sleep(0.02)
    return []

def wallets(k):
    return ["0x" + ("%040x" % (0x1000 * k + i)) for i in range(3)]

def launch(k, sender, recipients, eth, flip_after_s, bundle_after_s=0.05, sender_named=False):
    """one helper transaction with the bundle (bundle_after_s after the creation), then the feed opens the next second"""
    curve = "0x" + ("%02x" % (0xc0 + k)) * 20; tok = "0x" + ("%02x" % (0xd0 + k)) * 20; creator = "0x" + ("%02x" % k) * 20
    def feed():
        time.sleep(bundle_after_s)
        raw = ("one-%d" % k).encode(); SENDERS[raw] = sender
        data = bytes.fromhex("6f49227e") + bytes(12) + bytes.fromhex(curve[2:]) + b"".join(bytes(12) + bytes.fromhex(a[2:]) for a in recipients) + bytes(32)
        E.state["valtx"].append([E.mono(), T, None, eth, data, raw, 1000, "0x" + "14b9a544" + "0" * 32, "6f49227e"])
        with E.cond:
            E.cond.notify_all()
        time.sleep(max(0.0, flip_after_s - bundle_after_s))
        with E.cond:
            E.state["feed_ts"] = T + 1; E.state["flip_at"][T + 1] = E.mono(); E.cond.notify_all()
    threading.Thread(target=feed, daemon=True).start()
    E.resolve_rpc = lambda *a, **kw: (tok, curve, 0.02 * E.Y0, 1000)
    E.state["feed_ts"] = T; E.state["busy_until"] = 0.0
    t0 = E.mono(); E._handle_creation(creator, E.ZERO, int(0.035e18), E.mono(), T, set(recipients) | ({sender} if sender_named else set()), 1000, tax_bps=100)
    return creator, E.mono() - t0

# 1. react mode: a bundler-service wallet sends one helper call for three named buyers; the feed opens the next second 0.4 s later
W = wallets(1); c, el = launch(1, "0x" + "5e" * 20, W, 0.6, flip_after_s=0.4)
d = events(c, "trade_decision")
check("E1 react: one-transaction bundle from an unnamed bundler wallet, three named buyers: traded", bool(d), str([e.get("why") for e in events(c, "skip", wait=0.2)]) + str([e.get("gates") for e in d]))
if d:
    check("E1 react: the decision reads bundle 3, 0.6 ETH, send_mode react", d[0].get("bundle") == 3 and abs(d[0].get("bundle_eth", 0) - 0.6) < 1e-6 and d[0].get("send_mode") == "react", f"{d[0].get('bundle')} {d[0].get('bundle_eth')} {d[0].get('send_mode')}")
    check("E1 react: the send waited for the next second (>= 0.35 s after the creation)", el >= 0.35, f"{el:.3f}s")
    check("E1 react: seat_ts is the creation's second + 1", d[0].get("seat_ts") == T + 1, str(d[0].get("seat_ts")))

# 2. predict mode: a confident boundary estimate puts the send at the boundary minus MARGIN_MS, before the feed's flip
E.SEND_MODE = "predict"
E.boundary = lambda: (0.0, 0.9, 0.010)
E.state["ref"] = (E.mono() - 0.5, T)                       # second T opened 0.5 s ago on the monotonic clock: the boundary of T+1 is 0.5 s away
W = wallets(2); c, el = launch(2, W[0], W[1:], 0.45, flip_after_s=0.9, sender_named=True)
d = events(c, "trade_decision")
check("E1 predict: sender named with two more buyers in the calldata: traded", bool(d), str([e.get("why") for e in events(c, "skip", wait=0.2)]) + str([e.get("gates") for e in d]))
if not d:
    print("   log tail:", [ (e.get("ev"), str(e)[:160]) for e in [json.loads(l) for l in open(LOG)][-6:]])
if d:
    check("E1 predict: bundle 3, 0.45 ETH, send_mode predict (sent before the feed's flip)", d[0].get("bundle") == 3 and abs(d[0].get("bundle_eth", 0) - 0.45) < 1e-6 and d[0].get("send_mode") == "predict", f"{d[0].get('bundle')} {d[0].get('bundle_eth')} {d[0].get('send_mode')}")
    check("E1 predict: sent within 60 ms of the estimated boundary (0.5 s - 15 ms)", 0.40 <= el <= 0.56, f"{el:.3f}s")

# 3. one named wallet alone in the helper call: not a bundle, skipped
E.SEND_MODE = "react"
W = wallets(3); c, el = launch(3, W[0], [], 1.5, flip_after_s=0.3, sender_named=True)
d = events(c, "trade_decision", wait=1.0)
check("E1: one named buyer with 1.5 ETH is not a bundle: no trade", not d, str([e.get("gates") for e in d]))

print("all E1 bundle tests pass" if not fails else f"FAILED: {fails}")
sys.exit(1 if fails else 0)
