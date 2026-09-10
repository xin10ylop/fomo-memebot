#!/usr/bin/env python3
"""First-block sniper engine v4, dry-run by design (report sections 20-23, docs/SNIPER_RUNBOOK.md).

Live, it listens to the Robinhood Chain sequencer feed, decodes legacy, type-1 and type-2 transactions, detects Pons V2
creations (factory 0xe33e..., selectors 0xf85f8e41 and 0x3f707e6b), reads the creator, the quote asset, the initial buy
and the creator's exempt (named) wallets from the calldata, and resolves the new curve from the feed itself: the named
wallets buy it inside the creation second and the address they buy is the curve. Buys of a curve are recognised whether
they call the curve directly or go through a router (any value-carrying transaction whose calldata names the curve).
Gates (sections 21.6, 23): bundle of >= BUNDLE_MIN named wallets and >= BUNDLE_MIN_ETH, creator's launch buy >=
MIN_CREATOR_SUPPLY of supply, no non-named buyer of the curve during second one, and (OUT2_MAX, SEAT_WAIT_MS) no
non-named buyer of the curve in the seat's second before our send, which in react mode happens SEAT_WAIT_MS after the
feed opened that second: the replay's "0.3 s into second two, alone" entry. Seat: E2 (second whole second after the creation's timestamp,
+0.19%), E1 (+6.18%), E0 only for an exempt wallet. Sizing on the curve as the feed shows it at send time (the curve's
reserves are folded incrementally as the feed delivers each buy and sell, so nothing is rebuilt after the boundary),
minOut at SLIP below the sized tokens (a wrong-second landing reverts for gas). Sends in react mode (woken by the feed
message that opens the seat's second, after that message's transactions are indexed) or predict mode (at the seat's
boundary from the two-sided bracket estimator plus MARGIN_MS). Live: reads the tokens received from the buy's event,
approves at once, sells the balance HOLD s after the buy landed, or earlier when the curve price is up TAKE_PROFIT over
our entry (if > 0) or a dump is seen (STOP_SELL_FRAC > 0); learns MARGIN_MS from where the buy landed. Every
rule-passing launch is scored 25 s after creation with the simulator's exact-curve replay; the dry-run bankroll follows
those scores; the feed's gate readings are checked against the chain's at score time. State (bankroll, day, scores,
open position, margin) is persisted next to the log and recovered on restart.

Latency (section 23): monotonic clock on the critical path, senders recovered with coincurve (router transactions
lazily, only when they name a curve we trade), no resolution at all for launches the calldata already rules out, the
curve resolved the moment the bundle is visible, one Condition wake per feed message instead of polling, sleep-then-spin
for a predicted boundary (interval-vote estimator), log writes on a queue, warm keep-alive sockets to the sequencer and
the provider (SENDER, one shared TLS context), the collector off while anything is in flight, a 2 s feed watchdog.

What it does not do: sign or broadcast. submit(tx, label) logs the transaction and returns None; replace it with a
function that signs with your key (to-addresses are checksummed; eth_account refuses lowercase ones) and posts the raw
transaction through SENDER.fire(body) (the sequencer and the provider, same hash); return the transaction hash. The
runbook says what to verify on the first live trade.
"""
import asyncio, base64, json, os, sys, time, math, threading, queue, http.client, ssl, urllib.parse, urllib.request, collections, statistics as st, datetime, gc
import rlp
from eth_account import Account
from eth_utils import keccak, to_checksum_address

RPC_URL = os.environ.get("RPC_URL", "https://rpc.mainnet.chain.robinhood.com")
SEQ_URL = os.environ.get("SEQ_URL", "https://sequencer.mainnet.chain.robinhood.com")
FEED_URL = os.environ.get("FEED_URL", "wss://feed.mainnet.chain.robinhood.com")
LOG_PATH = os.environ.get("LOG_PATH", "sniper_engine.jsonl"); STATE_PATH = LOG_PATH + ".state.json"
WALLET = os.environ.get("WALLET", "0x0000000000000000000000000000000000000000").lower()
ETH_USD = float(os.environ.get("ETH_USD", "2445")); ETH_USD_URL = os.environ.get("ETH_USD_URL", "https://api.coinbase.com/v2/prices/ETH-USD/spot")
BANKROLL = float(os.environ.get("BANKROLL_USD", "300"))
FRAC = float(os.environ.get("FRAC", "0.15")); STAKE_MIN = float(os.environ.get("STAKE_MIN", "25")); STAKE_MAX = float(os.environ.get("STAKE_MAX", "300"))
HOLD = float(os.environ.get("HOLD_S", "5")); SUPPLY_FRAC = float(os.environ.get("SUPPLY_FRAC", "0.03")); SLIP = float(os.environ.get("SLIP", "0.25"))
TAKE_PROFIT = float(os.environ.get("TAKE_PROFIT", "0.5"))                # sell when the curve price is up this fraction over our entry (0 = off)
SEAT = os.environ.get("SEAT", "E2").upper(); EXEMPT = os.environ.get("EXEMPT", "0") == "1"
BUNDLE_MIN = int(os.environ.get("BUNDLE_MIN", "3" if SEAT in ("E1", "E2") else "0"))
BUNDLE_MIN_ETH = float(os.environ.get("BUNDLE_MIN_ETH", "0.3"))
OUT1_MAX = int(os.environ.get("OUT1_MAX", "0"))
OUT1_MIN_ETH = float(os.environ.get("OUT1_MIN_ETH", "0"))                 # second-one outsider buys below this size do not count (0 = all count; 0.01 makes the gate immune to planted dust)
OUT2_MAX = int(os.environ.get("OUT2_MAX", "0"))                          # non-named buys visible in the seat's second before we send
SEAT_WAIT_MS = float(os.environ.get("SEAT_WAIT_MS", "300"))              # react mode: watch the seat's second this long for an outsider before sending (section 23)
TIER_ASSUMED = float(os.environ.get("TIER_ASSUMED", "0.05"))
STOP_SELL_FRAC = float(os.environ.get("STOP_SELL_FRAC", "0"))
SEND_MODE = os.environ.get("SEND_MODE", "react"); MARGIN_MS = float(os.environ.get("MARGIN_MS", "15"))
MARGIN_MIN_MS = float(os.environ.get("MARGIN_MIN_MS", "5")); MARGIN_MAX_MS = float(os.environ.get("MARGIN_MAX_MS", "60"))
MAX_LATE_S = float(os.environ.get("MAX_LATE_S", "0.5"))                  # do not send more than this far into the seat's second
MIN_CREATOR_SUPPLY = float(os.environ.get("MIN_CREATOR_SUPPLY", "0.01"))
MAX_CREATOR_BUY_ETH = float(os.environ.get("MAX_CREATOR_BUY_ETH", "2"))
SWITCH_N = int(os.environ.get("SWITCH_N", "15")); SWITCH = float(os.environ.get("SWITCH", "-0.10")); DAILY_STOP = float(os.environ.get("DAILY_STOP", "0.50"))
MAX_RESOLVE_MS = int(os.environ.get("MAX_RESOLVE_MS", "1500"))
GAS_MAX_SHARE = float(os.environ.get("GAS_MAX_SHARE", "0.05"))
GAS_HEADROOM = float(os.environ.get("GAS_HEADROOM", "2.0"))                # gasPrice sent = this x eth_gasPrice: the quote equals the base fee, a tick up refuses the tx (23.7)
GAS_EST_BUY, GAS_EST_APPROVE, GAS_EST_SELL = 100_000, 50_000, 80_000        # measured gas used by direct curve calls (receipts, Sep 9): the cost estimate; limits below are higher
REQUIRE_COINCURVE = os.environ.get("REQUIRE_COINCURVE", "0") == "1"
PIN_CPU = os.environ.get("PIN_CPU", "")                                   # e.g. "1": keep the process off core 0 (interrupts) on a 2-vCPU box
GAS_BUY, GAS_APPROVE, GAS_SELL = 500_000, 80_000, 200_000
FACTORY = bytes.fromhex("e33e9e479df8802cb0866d5d05258bec4cf62948"); CREATE_SELS = {bytes.fromhex("f85f8e41"), bytes.fromhex("3f707e6b")}
FACTORY_HEX = "0x" + FACTORY.hex()
BUY_EV = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL_EV = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
BUY_SEL = bytes.fromhex("59a87bc1"); SELL_SEL = bytes.fromhex("d04c6983"); APPROVE_SEL = "095ea7b3"
UA = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/engine"}
X0, Y0 = 1.68, 1e9
SURCHARGE = {"E0": 0.0, "E1": 0.0618, "E2": 0.0019}; SEAT_SECONDS = {"E0": 0, "E1": 1, "E2": 2}
ZERO = "0x" + "0" * 40
mono = time.monotonic


# ----------------------------------------------------------------------------------------------------------------- logging
_logq = queue.SimpleQueue()


def _log_writer():
    while True:
        ev = _logq.get()
        try:
            with open(LOG_PATH, "a") as f:
                f.write(json.dumps(ev) + "\n")
        except Exception:
            pass


def log(ev):
    """never blocks the caller: the record goes on a queue and one thread writes it"""
    ev["t"] = time.time(); _logq.put(ev)


threading.Thread(target=_log_writer, daemon=True).start()


# ------------------------------------------------------------------------------------------------------- sender recovery
def _sender_slow(t):
    return Account.recover_transaction(t).lower()


try:
    from coincurve import PublicKey as _PK

    def _sender_fast(t):
        """sender of a legacy / type-1 / type-2 envelope straight from coincurve (about 0.1 ms; eth_account takes 0.4 ms with
        coincurve and 5.5 ms without)"""
        if t[0] >= 0xc0:
            b = rlp.decode(t); v = int.from_bytes(b[6], "big")
            if v >= 35:
                cid = (v - 35) // 2; rec = (v - 35) % 2
                unsigned = rlp.encode(b[:6] + [cid.to_bytes((cid.bit_length() + 7) // 8 or 1, "big"), b"", b""])
            else:
                rec = v - 27; unsigned = rlp.encode(b[:6])
            h = keccak(unsigned); r, s = b[7], b[8]
        else:
            b = rlp.decode(t[1:]); r, s = b[-2], b[-1]; rec = int.from_bytes(b[-3], "big") if b[-3] else 0
            h = keccak(bytes([t[0]]) + rlp.encode(b[:-3]))
        sig = r.rjust(32, b"\0") + s.rjust(32, b"\0") + bytes([rec])
        return "0x" + keccak(_PK.from_signature_and_message(sig, h, hasher=None).format(compressed=False)[1:])[-20:].hex()

    def _selftest():
        a = Account.create()
        for tx in ({"to": to_checksum_address("0x" + "ab" * 20), "value": 1, "data": b"\x01\x02", "gas": 21000, "gasPrice": 7, "nonce": 3, "chainId": 4663},
                   {"to": to_checksum_address("0x" + "cd" * 20), "value": 5, "data": b"", "gas": 21000, "maxFeePerGas": 9, "maxPriorityFeePerGas": 1, "nonce": 0, "chainId": 4663, "type": 2}):
            raw = bytes(a.sign_transaction(tx).raw_transaction)
            if _sender_fast(raw) != a.address.lower() or _sender_slow(raw) != a.address.lower():
                return False
        return True

    sender_of = _sender_fast if _selftest() else _sender_slow
    SENDER_BACKEND = "coincurve-direct" if sender_of is _sender_fast else "eth_account"
except Exception:
    sender_of = _sender_slow; SENDER_BACKEND = "eth_account"
if REQUIRE_COINCURVE and SENDER_BACKEND != "coincurve-direct":
    raise SystemExit("coincurve is not usable: signature recovery would take 5 ms per transaction. pip install coincurve (deploy/ohio_setup.sh does).")


# ------------------------------------------------------------------------------------------------------------- transport
_CTX = ssl.create_default_context()                    # one TLS context for every connection: building one costs 20-25 ms


class Rpc:
    def __init__(self, url):
        u = urllib.parse.urlparse(url); self.host = u.netloc; self.path = u.path or "/"; self.local = threading.local()

    def call(self, method, params):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        for i in range(3):
            try:
                c = getattr(self.local, "c", None)
                if c is None:
                    c = http.client.HTTPSConnection(self.host, timeout=10, context=_CTX); self.local.c = c
                c.request("POST", self.path, body=body, headers=UA); r = c.getresponse(); d = json.loads(r.read())
                if "error" in d:
                    raise RuntimeError(d["error"])
                return d["result"]
            except Exception:
                self.local.c = None
                if i == 2:
                    raise
                time.sleep(0.03)


class Sender:
    """pre-opened, keep-alive TLS sockets to the send endpoints (the sequencer first: it is the admission point; the provider
    forwards to it). fire(body) posts the same signed transaction to every endpoint and returns the first answer. Live only:
    the dry run keeps the sockets warm and measures them, and sends nothing."""
    PING = b'{"jsonrpc":"2.0","id":0,"method":"eth_chainId","params":[]}'

    def __init__(self, urls):
        self.eps = []
        for u in urls:
            if not u:
                continue
            p = urllib.parse.urlparse(u); self.eps.append({"url": u, "host": p.netloc, "path": p.path or "/", "c": None, "lock": threading.Lock(), "rtt_ms": None, "ok": False})
        threading.Thread(target=self._keepalive, daemon=True).start()

    def _ping(self, e):
        with e["lock"]:
            try:
                if e["c"] is None:
                    e["c"] = http.client.HTTPSConnection(e["host"], timeout=5, context=_CTX)
                t0 = mono(); e["c"].request("POST", e["path"], body=self.PING, headers=UA); e["c"].getresponse().read(); e["rtt_ms"] = round(1000 * (mono() - t0), 1); e["ok"] = True
            except Exception:
                e["c"] = None; e["ok"] = False

    def _keepalive(self):
        n = 0
        while True:
            for e in self.eps:
                self._ping(e)
            if n % 20 == 0:
                log({"ev": "sender_rtt", "endpoints": [{"host": e["host"], "warm_rtt_ms": e["rtt_ms"], "ok": e["ok"]} for e in self.eps]})
            n += 1; time.sleep(5)

    def _one(self, e, body, out):
        with e["lock"]:
            try:
                if e["c"] is None:
                    e["c"] = http.client.HTTPSConnection(e["host"], timeout=5, context=_CTX)
                e["c"].request("POST", e["path"], body=body, headers=UA); d = json.loads(e["c"].getresponse().read()); out.append((e["host"], d))
            except Exception as ex:
                e["c"] = None; out.append((e["host"], {"error": str(ex)[:120]}))

    def fire(self, body, wait_s=2.0):
        """post the same body to every endpoint at once; returns (result, per-endpoint answers)"""
        out = []; ths = [threading.Thread(target=self._one, args=(e, body, out), daemon=True) for e in self.eps]
        for th in ths:
            th.start()
        t0 = mono()
        while mono() - t0 < wait_s:
            for host, d in out:
                if "result" in d:
                    return d["result"], out
            if len(out) == len(ths):
                break
            time.sleep(0.0001)
        return None, out


rpc = Rpc(RPC_URL)
SENDER = Sender([SEQ_URL, RPC_URL if RPC_URL != SEQ_URL else None])
state = {"bankroll": BANKROLL, "day": None, "day_start": BANKROLL, "stopped": False, "busy_until": 0.0, "scores": collections.deque(maxlen=max(SWITCH_N, 60)),
         "launched_today": collections.Counter(), "seeded": False, "feed_ts": 0, "last_seen_ts": 0, "traded": {}, "eth_usd": ETH_USD,
         "buys": collections.defaultdict(list),        # curve -> [(ts, sender, value_eth, seen)] direct buys
         "sells": collections.defaultdict(list),       # curve -> [(seen, tokens)] direct sells
         "valtx": collections.deque(maxlen=4000),      # [seen, ts, sender_or_None, value_eth, data, raw] value-carrying non-direct txs: router buys, sender recovered lazily
         "watch": {},                                  # curve -> incremental reserves and counters, folded by the feed loop for the curves we are trading
         "known_curves": {}, "brackets": collections.deque(maxlen=300), "ref": None, "flip_at": {}, "flip_block": {}, "connected_at": 0.0,
         "blocks": 0, "prev_seen": None, "prev_ts": 0, "nonce": None, "gas_price": None, "chain_at": 0.0, "open": None, "decisions": {},
         "landings": {"since_early": 0, "first": 0}, "schedule": collections.deque(maxlen=20), "rule_passing": collections.deque(maxlen=400), "rules_changed": False, "creations": 0, "timing": collections.deque(maxlen=60), "last_creation_at": 0.0}
lock = threading.Lock()
cond = threading.Condition()                           # notified by the feed loop after every message is fully indexed


def save_state():
    try:
        d = {"bankroll": state["bankroll"], "day": str(state["day"]), "day_start": state["day_start"], "stopped": state["stopped"], "scores": list(state["scores"]),
             "open": state["open"], "margin_ms": MARGIN_MS, "saved_at": time.time()}
        tmp = STATE_PATH + ".tmp"; json.dump(d, open(tmp, "w")); os.replace(tmp, STATE_PATH)
    except Exception as e:
        log({"ev": "error", "stage": "save_state", "err": str(e)[:200]})


def load_state():
    global MARGIN_MS
    try:
        d = json.load(open(STATE_PATH))
        if str(datetime.datetime.utcnow().date()) == d.get("day"):
            state["bankroll"] = d["bankroll"]; state["day"] = datetime.datetime.utcnow().date(); state["day_start"] = d["day_start"]; state["stopped"] = d["stopped"]
        for x in d.get("scores", []):
            state["scores"].append(x)
        state["open"] = d.get("open"); MARGIN_MS = float(d.get("margin_ms", MARGIN_MS))
        log({"ev": "state_loaded", "bankroll": state["bankroll"], "scores": len(state["scores"]), "open": state["open"] is not None, "margin_ms": MARGIN_MS})
    except FileNotFoundError:
        pass
    except Exception as e:
        log({"ev": "error", "stage": "load_state", "err": str(e)[:200]})


def abi_word(x):
    return x.to_bytes(32, "big").hex() if isinstance(x, int) else x[2:].rjust(64, "0")


def submit(tx, label):
    """DRY RUN: logs the exact unsigned transaction and returns None. Live: sign it (Account.sign_transaction(tx) works as
    built: checksummed to, hex fields), then SENDER.fire(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction",
    "params": ["0x" + raw.hex()]}).encode()) and return the hash."""
    log({"ev": "unsigned_tx", "label": label, "tx": tx})
    return None


# ---------------------------------------------------------------------------------------------------------- background
def chain_loop():
    """nonce, gas price and the ETH price, refreshed in the background so the critical path never waits on the RPC"""
    n = 0
    while True:
        try:
            state["nonce"] = int(rpc.call("eth_getTransactionCount", [WALLET, "pending"]), 16); state["gas_price"] = int(int(rpc.call("eth_gasPrice", []), 16) * GAS_HEADROOM); state["chain_at"] = mono()
        except Exception as e:
            if n % 20 == 0:
                log({"ev": "error", "stage": "chain_loop", "err": str(e)[:160]})
        if n % 100 == 0:
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(ETH_USD_URL, headers={"User-Agent": UA["User-Agent"]}), timeout=10)); px = float(d["data"]["amount"])
                if 100 < px < 100000:
                    state["eth_usd"] = px
            except Exception:
                pass
            rp = state["rule_passing"]; now = time.time()
            tm = list(state["timing"]); fs = [a for a, b in tm if a is not None]
            log({"ev": "flow", "rule_passing_last_6h": sum(1 for t in rp if now - t < 21600), "rule_passing_last_1h": sum(1 for t in rp if now - t < 3600),
                 "mean_score_last_60": round(st.mean(list(state["scores"])[-60:]), 4) if state["scores"] else None, "creations_seen": state["creations"],
                 "median_first_sell_s": round(st.median(fs), 2) if fs else None, "share_dumped_inside_hold": round(st.mean(b for a, b in tm), 4) if tm else None,
                 "silent_min": round((mono() - state["last_creation_at"]) / 60, 1) if state["last_creation_at"] else None})
            if state["last_creation_at"] and mono() - state["last_creation_at"] > 1800 and mono() - state["connected_at"] > 1800:
                log({"ev": "alarm", "what": "no creation seen from the factory for 30 minutes while the feed is connected: the launchpad moved, stopped or changed its factory"})
            b = boundary()
            if b:
                log({"ev": "boundary", "theta_ms": round(1000 * b[0], 1), "confidence": round(b[1], 3), "bracket_width_ms": round(1000 * b[2], 1), "samples": len(state["brackets"]), "margin_ms": round(MARGIN_MS, 2)})
        n += 1; time.sleep(3)


_bcache = {"at": -1e9, "v": None}


def boundary():
    """interval-vote estimator of theta, the sequencer's second boundary on the local monotonic clock relative to the
    reference flip (state['ref']): every second gives a bracket (arrival of the last block stamped s-1, arrival of the first
    block stamped s], both minus s; each bracket votes for the 1 ms bins it covers and theta is the centre of the most-voted
    run. One stalled delivery cannot move it (it only votes elsewhere), and 30 brackets are enough. Returns (theta,
    confidence = peak votes / brackets, median bracket width) or None; cached for a second."""
    if mono() - _bcache["at"] < 1.0:
        return _bcache["v"]
    br = [(lo, hi) for lo, hi in state["brackets"] if 0 < hi - lo < 0.35]
    v = None
    if len(br) >= 30:
        base = min(lo for lo, hi in br); span = int((max(hi for lo, hi in br) - base) * 1000) + 2; votes = [0] * span
        for lo, hi in br:
            for k in range(int((lo - base) * 1000) + 1, int((hi - base) * 1000) + 1):
                votes[k] += 1
        m = max(votes); idx = [k for k, x in enumerate(votes) if x == m]
        v = (base + ((idx[0] + idx[-1]) / 2 + 0.5) / 1000.0, m / len(br), st.median(hi - lo for lo, hi in br))
    _bcache["at"] = mono(); _bcache["v"] = v
    return v


def wait_for_second(feed_ts, seconds, seen_at, deadline=3.5, watch=None):
    """block until it is time to send for the seat. react: woken by the feed message that opens the seat's second (its
    transactions are already indexed). predict: at seat_second + theta + MARGIN_MS on the monotonic clock, sleeping until
    4 ms before and spinning the rest. Returns the mode used, or None when the seat's second is already more than MAX_LATE_S
    old or was never seen (do not send on stale data)."""
    target_ts = feed_ts + seconds
    if SEND_MODE == "predict" and seconds >= 1:
        b = boundary(); ref = state["ref"]
        if b is not None and b[1] >= 0.5 and ref is not None:                 # a low-confidence estimate (a stalled or jittery feed) falls back to react
            target = ref[0] + (target_ts - ref[1]) + b[0] + MARGIN_MS / 1000.0
            with cond:
                while state["feed_ts"] < target_ts and mono() - seen_at < deadline:
                    d = target - mono()
                    if d <= 0.0:
                        break
                    if d > 0.004:
                        cond.wait(min(d - 0.004, 0.5))
                    else:
                        cond.release()
                        try:
                            while mono() < target and state["feed_ts"] < target_ts:
                                pass
                        finally:
                            cond.acquire()
                        break
            if state["feed_ts"] > target_ts:
                return None
            if state["feed_ts"] == target_ts and mono() - state["flip_at"].get(target_ts, mono()) > MAX_LATE_S:
                return None
            return "predict" if state["feed_ts"] < target_ts else "predict-late"
    with cond:
        while state["feed_ts"] < target_ts and mono() - seen_at < deadline:
            cond.wait(0.25)
    if state["feed_ts"] != target_ts or mono() - state["flip_at"].get(target_ts, mono()) > MAX_LATE_S:
        return None
    if SEAT_WAIT_MS > 0 and watch is not None:                       # the seat rule: send SEAT_WAIT_MS into the second unless an outsider has already bought
        until = state["flip_at"][target_ts] + SEAT_WAIT_MS / 1000.0
        with cond:
            while mono() < until and watch["out2"] <= OUT2_MAX and state["feed_ts"] == target_ts:
                cond.wait(max(0.0, min(until - mono(), 0.05)))
        if state["feed_ts"] != target_ts:
            return None
    return "react"


def tune_margin(receipt, seat_ts):
    """live only, off the trade path. Early (stamped before the seat's second): +15 ms at E2, where it means second one was paid
    at +6.18%; +5 ms at E1, where it means the creation second and the minOut refused it for gas only. Otherwise
    every 20 landings without an early one: -2 ms if fewer than 80% of them were first-block landings (a later block is a
    noisy signal, the sequencer drains on its own timer). Floor MARGIN_MIN_MS, cap MARGIN_MAX_MS. Logs the landing position
    from the receipt: block, timestamp against the seat's second, transaction index, blocks after the feed's flip."""
    global MARGIN_MS
    try:
        b = int(receipt["blockNumber"], 16); ts = int(rpc.call("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)
        prev = int(rpc.call("eth_getBlockByNumber", [hex(b - 1), False])["timestamp"], 16); L = state["landings"]
        if ts < seat_ts:
            MARGIN_MS = min(MARGIN_MAX_MS, MARGIN_MS + (5.0 if SEAT == "E1" else 15.0)); where = "early"; L["since_early"] = 0; L["first"] = 0
        else:
            where = "first block" if prev < ts else "later block"; L["since_early"] += 1; L["first"] += where == "first block"
            if L["since_early"] >= 20:
                if L["first"] / L["since_early"] < 0.8:
                    MARGIN_MS = max(MARGIN_MIN_MS, MARGIN_MS - 2.0)
                L["since_early"] = 0; L["first"] = 0
        fb = state["flip_block"].get(seat_ts)
        log({"ev": "landing", "block": b, "block_ts": ts, "seat_ts": seat_ts, "where": where, "tx_index": int(receipt.get("transactionIndex", "0x0"), 16),
             "blocks_after_flip": (b - fb) if fb is not None else None, "margin_ms": round(MARGIN_MS, 2), "status": receipt.get("status")}); save_state()
    except Exception as e:
        log({"ev": "error", "stage": "tune_margin", "err": str(e)[:200]})


def gas_cost_usd():
    """the round trip's cost at the price we send with (measured gas used, not the limits)"""
    gp = state["gas_price"]
    return (GAS_EST_BUY + GAS_EST_APPROVE + GAS_EST_SELL) * gp / 1e18 * state["eth_usd"] if gp else None


def new_day_check():
    d = datetime.datetime.utcnow().date()
    if state["day"] != d:
        state["day"] = d; state["day_start"] = state["bankroll"]; state["stopped"] = False; state["launched_today"].clear(); state["seeded"] = False
        threading.Thread(target=seed_launched_today, daemon=True).start(); save_state()


def seed_launched_today():
    """creators that already launched today, in the background, so 'first launch of the day' is exact from the moment the engine starts"""
    for attempt in range(6):
        try:
            head = int(rpc.call("eth_blockNumber", []), 16)
            secs = (datetime.datetime.utcnow() - datetime.datetime.combine(datetime.datetime.utcnow().date(), datetime.time())).total_seconds()
            b = head - int(secs * 9.9); found = collections.Counter()
            while b <= head:
                e = min(head, b + 20000)
                for l in rpc.call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "address": FACTORY_HEX}]):
                    if len(l["topics"]) > 3:
                        found["0x" + l["topics"][3][-40:]] += 1
                b = e + 1; time.sleep(0.2)
            with lock:
                for k, v in found.items():
                    state["launched_today"][k] = max(state["launched_today"][k], v)
                state["seeded"] = True
            log({"ev": "seeded", "creators_today": len(found)}); return
        except Exception as e:
            log({"ev": "error", "stage": "seed", "attempt": attempt, "err": str(e)[:160]}); time.sleep(20 * (attempt + 1))


# ------------------------------------------------------------------------------------------------- curve bookkeeping
def curve_buys(curve, since_ts=None):
    """every buy of the curve seen on the feed so far: direct calls and value-carrying transactions whose calldata names the
    curve (their senders recovered now, only for the few that match). Used once, when a curve is resolved; afterwards the
    feed loop folds new buys into state['watch'][curve] as they arrive."""
    cb = bytes.fromhex(curve[2:]); out = list(state["buys"].get(curve, []))
    for e in state["valtx"]:
        if cb in e[4]:
            if e[2] is None:
                try:
                    e[2] = sender_of(e[5])
                except Exception:
                    e[2] = "?"
            out.append((e[1], e[2], e[3], e[0]))
    if since_ts is not None:
        out = [b for b in out if b[0] >= since_ts]
    return out


def watch_curve(curve, tk0, feed_ts, named, creator):
    """register the curve for incremental folding and build its state from what the feed has shown so far"""
    net0 = X0 * tk0 / (Y0 - tk0); w = {"X": X0 + net0, "Y": Y0 - tk0, "cb": bytes.fromhex(curve[2:]), "ts0": feed_ts, "named": named, "creator": creator,
                                       "bundle": 0, "bundle_eth": 0.0, "out1": 0, "out2": 0, "buys": 0, "sells": 0, "since": mono(), "dump": None, "wallets": set()}
    for ts_, snd, val, seen in curve_buys(curve, feed_ts):
        fold_buy(w, ts_, snd, val)
    for seen, tk in state["sells"].get(curve, []):
        fold_sell(w, tk)
    state["watch"][curve] = w
    return w


def fold_buy(w, ts_, snd, val):
    if val > 0:
        net = val * 0.99; X, Y = w["X"], w["Y"]; tk = Y - X * Y / (X + net); w["X"] = X + net; w["Y"] = Y - tk
    w["buys"] += 1
    if snd in w["named"]:
        if ts_ == w["ts0"]:
            w["bundle"] += 1; w["wallets"].add(snd)                        # buys and distinct wallets: the tables count buys (no sender in the event data)
        if ts_ <= w["ts0"] + 1:
            w["bundle_eth"] += val
    elif snd != w["creator"] and snd != WALLET:
        if ts_ == w["ts0"] + 1 and val >= OUT1_MIN_ETH:
            w["out1"] += 1
        elif ts_ == w["ts0"] + 2:
            w["out2"] += 1


def fold_sell(w, tk):
    w["sells"] += 1
    if 0 < tk < Y0:
        X, Y = w["X"], w["Y"]; g = X - X * Y / (Y + tk); w["X"] = X - g; w["Y"] = Y + tk
    if STOP_SELL_FRAC > 0 and tk >= STOP_SELL_FRAC * Y0:
        w["dump"] = tk


def size_buy(X, Y, stake_eth, seat):
    fee = TIER_ASSUMED + SURCHARGE[seat]; tk = SUPPLY_FRAC * Y0
    net = X * tk / (Y - tk); gross = net / (1 - fee)
    if gross > stake_eth:
        gross = stake_eth; net = gross * (1 - fee); tk = Y * net / (X + net)
    return tk, net, gross, fee


# ------------------------------------------------------------------------------------------------------------ scoring
def exact_score(events, b_create, tk0, stake_eth, seat, tol=0.10, slip=0.3, hold=HOLD, frac=SUPPLY_FRAC, gated=True, stop_sell_frac=None, tp=None):
    """the simulator's replay (sniper_exact.replay plus the take-profit of risk_harness.replay) on the curve's own Buy/Sell
    events. Returns (pnl_usd, cost_usd, t_in, tier, label_bundle, label_bundle_eth, label_out1) or "filtered" or None."""
    rows = []; X, Y = X0, Y0; tier = None
    for i, (b, li, buy, q, tk, fee) in enumerate(events):
        t = (b - b_create) / 9.9
        if buy:
            if tk <= 0 or tk >= Y or q <= 0:
                return None
            net = X * tk / (Y - tk); tax = 1 - net / q
            if i == 0:
                if not (0 <= tax <= 0.2):
                    return None
                tier = tax
            rows.append((t, "B", q, tk, net, tax)); X += net; Y -= tk
        else:
            gross = X - X * Y / (Y + tk); rows.append((t, "S", q, tk, gross, 1 - q / gross if gross > 0 else 0.0)); X -= gross; Y += tk
    if tier is None or rows[0][1] != "B":
        return None
    first_taxed = next((r[0] for r in rows[1:] if r[1] == "B" and r[5] - tier > 0.001), 9e9)
    bundle_rows = [r for r in rows[1:] if r[1] == "B" and r[0] < min(1.0, first_taxed) and r[5] - tier <= 0.0008]
    lab = (len(bundle_rows), sum(r[2] for r in bundle_rows), sum(1 for r in rows[1:] if r[1] == "B" and 0.05 <= r[5] - tier <= 0.075 and r[2] >= OUT1_MIN_ETH))
    # the tax schedule: every surcharged buy in the first three seconds must sit in a known band (creation second 85-99.5%, second one
    # 5-7.5%, second two 0.12-0.35%); a launch where most surcharged buys fall outside them is anomalous, a run of them means the rules changed
    sur = [r[5] - tier for r in rows[1:] if r[1] == "B" and r[0] <= 3.0 and r[5] - tier > 0.001]
    odd = sum(1 for x in sur if not (0.85 <= x <= 0.995 or 0.05 <= x <= 0.075 or 0.0012 <= x <= 0.0035))
    state["schedule"].append(1 if (sur and odd / len(sur) > 0.5) else 0)
    if gated and (lab[0] < BUNDLE_MIN or lab[1] < BUNDLE_MIN_ETH or rows[0][3] < MIN_CREATOR_SUPPLY * Y0 or (seat == "E2" and lab[2] > OUT1_MAX)):
        return ("filtered",) + lab
    X, Y = X0, Y0; X += rows[0][4]; Y -= rows[0][3]
    lo, hi, fb = {"E0": (-1.0, 0.0008, 0.1), "E1": (0.05, 0.075, 1.0), "E2": (0.0012, 0.0035, 2.0)}[seat]
    idx = next((i for i in range(1, len(rows)) if rows[i][1] == "B" and rows[i][0] <= 3.0 and lo <= rows[i][5] - tier <= hi), None)
    if idx is None:
        idx = next((i for i in range(1, len(rows)) if rows[i][0] >= fb), len(rows)); t_in = fb
    else:
        t_in = rows[idx][0]
    t_in += 0.3; idx = next((i for i in range(1, len(rows)) if rows[i][0] >= t_in), len(rows))       # 0.3 s behind the first buyer of the seat, as the tables assume
    for r in rows[1:idx]:
        if r[1] == "B":
            X += r[4]; Y -= r[3]
        else:
            X -= r[4]; Y += r[3]
    fee = tier + SURCHARGE[seat]
    tk_bot = frac * Y0; net = X * tk_bot / (Y - tk_bot); gross = net / (1 - fee)
    if gross > stake_eth:
        gross = stake_eth; net = gross * (1 - fee); tk_bot = Y * net / (X + net)
    X += net; Y -= tk_bot; held = Y0 - Y - tk_bot; phantom = 0.0; t_exit = t_in + hold + slip; p_in = X / Y
    for r in rows[idx:]:
        t, k, q, tk, net_obs, tax = r
        if t >= t_exit:
            break
        if k == "S" and stop_sell_frac is not None and tk >= stop_sell_frac * Y0 and t_exit > t + slip:
            t_exit = t + slip
        if k == "B":
            tokens = Y - X * Y / (X + net_obs)
            if tokens < tk * (1 - tol):
                phantom += tk; continue
            X += net_obs; Y -= tokens; held += tokens
        else:
            share = held / (held + phantom) if held + phantom > 0 else 1.0
            s = min(tk * share, held); g = X - X * Y / (Y + s); X -= g; Y += s; held -= s; phantom = max(0.0, phantom - (tk - s))
        if tp is not None and X / Y >= p_in * (1 + tp) and t_exit > t + slip:
            t_exit = t + slip
    out = (X - X * Y / (Y + tk_bot)) * (1 - tier)
    first_sell = next((r[0] - t_in for r in rows if r[1] == "S" and r[0] >= t_in), None)
    dumped = sum(r[3] for r in rows if r[1] == "S" and t_in <= r[0] < t_in + hold + slip) / Y0
    state["timing"].append((first_sell, dumped))
    return ((out - gross) * state["eth_usd"] - 1.0, gross * state["eth_usd"], t_in, tier) + lab


def resolve_rpc(creator, deadline=3.0, lookback=40):
    """the curve from the factory's event: (token, curve, tk0, b_create) or None"""
    t0 = mono()
    while mono() - t0 < deadline:
        try:
            head = int(rpc.call("eth_blockNumber", []), 16)
            for l in rpc.call("eth_getLogs", [{"fromBlock": hex(head - lookback), "toBlock": hex(head), "address": FACTORY_HEX}]):
                if len(l["topics"]) > 3 and ("0x" + l["topics"][3][-40:]).lower() == creator:
                    d = l["data"][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
                    return "0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:], w[2] / 1e18, int(l["blockNumber"], 16)
        except Exception:
            pass
        time.sleep(0.02)
    return None


def score_launch(curve, tk0, b_create, stake_usd, creator, src, decision):
    """25 s after creation: the regime signal, the dry-run bankroll update, and the check of the feed's gate readings against the chain's"""
    time.sleep(25)
    try:
        if b_create is None:
            r = resolve_rpc(creator, deadline=5.0, lookback=600)
            if not r:
                log({"ev": "score", "curve": curve, "result": "creation event not found"}); return
            if r[1].lower() != curve.lower():
                log({"ev": "feed_resolution_mismatch", "feed_curve": curve, "event_curve": r[1], "creator": creator}); state["traded"].pop(curve, None); return
            tk0, b_create = r[2], r[3]; log({"ev": "feed_resolution_ok", "curve": curve})
        head = int(rpc.call("eth_blockNumber", []), 16)
        ev = rpc.call("eth_getLogs", [{"fromBlock": hex(b_create), "toBlock": hex(head), "address": curve, "topics": [[BUY_EV, SELL_EV]]}])
        events = []
        for e in ev:
            d = e["data"][2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]; buy = e["topics"][0] == BUY_EV
            events.append((int(e["blockNumber"], 16), int(e["logIndex"], 16), buy, w[0] if buy else w[1], w[1] if buy else w[0], w[2] if len(w) > 2 else 0.0))
        events.sort(key=lambda x: (x[0], x[1]))
        r = exact_score(events, b_create, tk0, stake_usd / state["eth_usd"], SEAT, gated=BUNDLE_MIN > 0, stop_sell_frac=STOP_SELL_FRAC if STOP_SELL_FRAC > 0 else None, tp=TAKE_PROFIT if TAKE_PROFIT > 0 else None)
        if r is None:
            log({"ev": "score", "curve": curve, "result": "no usable launch-block buy"}); return
        if decision is not None:                                        # what the feed said at decision time vs what the chain says
            lab = r[-3:]
            log({"ev": "gate_check", "curve": curve, "feed": decision, "chain": {"bundle": lab[0], "bundle_eth": round(lab[1], 4), "out1": lab[2]}, "src": src})
        if len(state["schedule"]) >= 20 and sum(state["schedule"]) >= 10 and not state["rules_changed"]:
            state["rules_changed"] = True; log({"ev": "alarm", "what": "tax schedule changed: half of the last 20 scored launches show surcharges outside the known bands; trading stopped until restarted"})
        if r[0] == "filtered":
            log({"ev": "score", "curve": curve, "result": "outside the rule on the chain's reading"}); state["traded"].pop(curve, None); return
        state["rule_passing"].append(time.time())
        pnl, cost, t_in, tier = r[:4]; roi = pnl / cost
        with lock:
            state["scores"].append(roi); sc = list(state["scores"])[-SWITCH_N:]; on = len(sc) < SWITCH_N or st.mean(sc) >= SWITCH
            traded = state["traded"].pop(curve, None)
            if traded is not None:
                state["bankroll"] += min(traded, cost) * roi
        save_state()
        log({"ev": "score", "curve": curve, "roi": round(roi, 4), "pnl_usd": round(pnl, 2), "cost_usd": round(cost, 2), "tier": round(tier, 4), "t_in_s": round(t_in, 2),
             "n_scores": len(sc), "rolling_mean": round(st.mean(sc), 4), "switch_on": on, "traded_dry_run": traded is not None, "bankroll": round(state["bankroll"], 2)})
    except Exception as e:
        log({"ev": "error", "stage": "score", "err": str(e)[:200]})
    finally:
        state["watch"].pop(curve, None)


# ------------------------------------------------------------------------------------------------------------- trading
def wait_receipt(h, timeout=10.0):
    t0 = mono()
    while mono() - t0 < timeout:
        try:
            r = rpc.call("eth_getTransactionReceipt", [h])
            if r:
                return r
        except Exception:
            pass
        time.sleep(0.05)
    return None


def close_position(pos, why):
    """approve (if not yet) and sell the position's balance; used by the hold and by crash recovery"""
    gp = state["gas_price"] or 0; nonce = pos["nonce"]
    if not pos.get("approved"):
        approve = {"to": to_checksum_address(pos["token"]), "value": "0x0", "data": "0x" + APPROVE_SEL + abi_word(pos["curve"]) + abi_word(2 ** 256 - 1), "gas": hex(GAS_APPROVE), "gasPrice": hex(gp), "nonce": hex(nonce + 1), "chainId": 4663}
        ha = submit(approve, "approve"); pos["approved"] = True; pos["approve_hash"] = ha
    sell = {"to": to_checksum_address(pos["curve"]), "value": "0x0", "data": "0x" + SELL_SEL.hex() + abi_word(int(pos["tokens"] * 1e18)) + abi_word(0) + abi_word(WALLET), "gas": hex(GAS_SELL), "gasPrice": hex(gp), "nonce": hex(nonce + 2), "chainId": 4663}
    hs = submit(sell, "sell")
    log({"ev": "trade_done", "curve": pos["curve"], "tokens_sold": pos["tokens"], "held_s": round(mono() - pos["t_buy"], 2), "exit": why, "dry_run": hs is None and pos.get("buy_hash") is None, "sell_hash": hs})
    state["open"] = None; save_state()


def handle_creation(creator, quote, init_buy_wei, seen_at, feed_ts, named, blk0):
    """resolve the curve, apply the gates, size on the feed-tracked curve, take the seat, build the buy, then approve and sell"""
    curve = token = None; tk0 = None; b_create = None; src = None; named = set(named)
    new_day_check()
    with lock:
        prior = state["launched_today"][creator]; state["launched_today"][creator] += 1
    if SEAT in ("E1", "E2") and BUNDLE_MIN > 0 and (quote != ZERO or len(named) < BUNDLE_MIN):
        log({"ev": "skip", "why": ["cannot pass the rule from the calldata (quote or named wallets): not resolved"], "creator": creator, "named_wallets": len(named), "quote": quote}); return

    def count_cands():
        cands = collections.Counter()
        try:
            for cv, lst in list(state["buys"].items()):
                if cv in state["known_curves"]:
                    continue
                cands[cv] += sum(1 for ts_, snd, val, seen in list(lst) if snd in named and ts_ >= feed_ts)
        except RuntimeError:
            pass
        return cands
    if SEAT in ("E1", "E2") and BUNDLE_MIN > 0:
        cands = count_cands()                                              # the moment BUNDLE_MIN named wallets have bought one curve, that is the curve
        while (not cands or cands.most_common(1)[0][1] < BUNDLE_MIN) and state["feed_ts"] <= feed_ts and mono() - seen_at < 1.5:
            with cond:
                cond.wait(0.25)
            cands = count_cands()
        if cands:
            a, c = cands.most_common(1)[0]
            if c >= BUNDLE_MIN:
                curve = a; src = "feed"
                net0 = init_buy_wei / 1e18 * 0.99; tk0 = Y0 - X0 * Y0 / (X0 + net0) if net0 > 0 else 0.0
    if curve is None:
        r = resolve_rpc(creator)
        if r:
            token, curve, tk0, b_create = r; src = "rpc"
    resolve_ms = round((mono() - seen_at) * 1000)
    if not curve:
        log({"ev": "skip", "why": "curve not resolved in 3 s", "creator": creator, "named_wallets": len(named)}); return
    state["known_curves"][curve] = mono()
    reasons = []
    if prior > 0:
        reasons.append(f"creator launched {prior} times today")
    if quote != ZERO:
        reasons.append("quote not native ETH")
    if tk0 is None or tk0 <= 0 or tk0 >= Y0:
        reasons.append("no usable launch-block buy")
    elif tk0 < MIN_CREATOR_SUPPLY * Y0:
        reasons.append(f"creator buy {100 * tk0 / Y0:.1f}% of supply < {100 * MIN_CREATOR_SUPPLY:.0f}%")
    if init_buy_wei / 1e18 > MAX_CREATOR_BUY_ETH:
        reasons.append("creator buy too large")
    if reasons:
        log({"ev": "skip", "why": reasons, "curve": curve, "creator": creator, "resolve_ms": resolve_ms, "resolve_src": src, "named_wallets": len(named)}); return
    w = watch_curve(curve, tk0, feed_ts, named, creator)                 # from here the feed loop folds every buy and sell of this curve as it arrives
    curve_cs = to_checksum_address(curve)
    # the seat's wait: the bundle and second one must be fully visible before the gates are read
    send_mode = None
    if SEAT in ("E1", "E2"):
        send_mode = wait_for_second(feed_ts, SEAT_SECONDS[SEAT], seen_at, watch=w)
    t_wake = mono()
    decision = {"bundle": w["bundle"], "bundle_wallets": len(w["wallets"]), "bundle_eth": round(w["bundle_eth"], 4), "out1": w["out1"], "out2": w["out2"], "blocks_to_seat": state["blocks"] - blk0}
    with lock:
        sc = list(state["scores"])[-SWITCH_N:]; on = len(sc) < SWITCH_N or st.mean(sc) >= SWITCH
        stake_usd = min(STAKE_MAX, max(STAKE_MIN, state["bankroll"] * FRAC)); gates = []
        if w["bundle"] < BUNDLE_MIN:
            gates.append(f"bundle {w['bundle']} < {BUNDLE_MIN}")
        if w["bundle_eth"] < BUNDLE_MIN_ETH:
            gates.append(f"bundle {w['bundle_eth']:.3f} ETH < {BUNDLE_MIN_ETH}")
        if SEAT == "E2" and w["out1"] > OUT1_MAX:
            gates.append(f"{w['out1']} outsider buys in second one > {OUT1_MAX}")
        if SEAT == "E2" and w["out2"] > OUT2_MAX:
            gates.append(f"{w['out2']} outsider buys in the seat's second before our send > {OUT2_MAX}")
        if not on:
            gates.append(f"safety switch off (rolling {st.mean(sc):+.3f} over {len(sc)} < {SWITCH:+.2f})")
        if state["stopped"] or state["bankroll"] < (1 - DAILY_STOP) * state["day_start"]:
            state["stopped"] = True; gates.append("daily stop")
        if state["rules_changed"]:
            gates.append("tax schedule changed (alarm): not trading")
        if mono() < state["busy_until"] or state["open"] is not None:
            gates.append("position open")
        if resolve_ms > MAX_RESOLVE_MS:
            gates.append(f"resolved in {resolve_ms} ms > {MAX_RESOLVE_MS}")
        if state["bankroll"] < STAKE_MIN:
            gates.append("bankroll below the minimum stake")
        if send_mode is None and SEAT in ("E1", "E2"):
            gates.append("seat's second not seen in time (stale feed): not sending")
        if state["nonce"] is None or mono() - state["chain_at"] > 30:
            gates.append("nonce/gas not fresh (RPC)")
        gc_usd = gas_cost_usd()
        if gc_usd is not None and gc_usd > GAS_MAX_SHARE * stake_usd:
            gates.append(f"gas ${gc_usd:.2f} per round trip > {100 * GAS_MAX_SHARE:.0f}% of stake")
        if not gates:
            state["busy_until"] = mono() + HOLD + 3; nonce = state["nonce"]; state["nonce"] += 3; gas_price = state["gas_price"]
    if gates:
        threading.Thread(target=score_launch, args=(curve, tk0, b_create, stake_usd, creator, src, decision), daemon=True).start()
        log({"ev": "eligible_not_traded", "curve": curve, "creator": creator, "resolve_ms": resolve_ms, "resolve_src": src, "named_wallets": len(named), **decision, "gates": gates, "stake_usd": stake_usd}); return
    X, Y = w["X"], w["Y"]; stake_eth = stake_usd / state["eth_usd"]
    tk, net, gross, fee = size_buy(X, Y, stake_eth, SEAT)
    amount_in = int(gross * 1e18); min_out = int(tk * (1 - SLIP) * 1e18)
    buy = {"to": curve_cs, "value": hex(amount_in), "data": "0x" + BUY_SEL.hex() + abi_word(amount_in) + abi_word(min_out) + abi_word(WALLET), "gas": hex(GAS_BUY), "gasPrice": hex(gas_price), "nonce": hex(nonce), "chainId": 4663}
    h = submit(buy, "buy"); t_buy = mono(); tokens = tk; p_in = (X + net) / (Y - tk)
    state["traded"][curve] = min(stake_usd, gross * state["eth_usd"]); state["decisions"][curve] = decision
    threading.Thread(target=score_launch, args=(curve, tk0, b_create, stake_usd, creator, src, decision), daemon=True).start()
    p_creator = (X0 + X0 * tk0 / (Y0 - tk0)) / (Y0 - tk0)
    log({"ev": "trade_decision", "seat": SEAT, "curve": curve, "token": token, "creator": creator, "resolve_ms": resolve_ms, "resolve_src": src, "named_wallets": len(named), **decision,
         "sent_ms": round((t_buy - seen_at) * 1000), "wake_to_send_ms": round((t_buy - t_wake) * 1000, 2), "send_mode": send_mode, "feed_ts_at_send": state["feed_ts"], "seat_ts": feed_ts + SEAT_SECONDS.get(SEAT, 0),
         "seat_flip_to_send_ms": round((t_buy - state["flip_at"][feed_ts + SEAT_SECONDS[SEAT]]) * 1000, 1) if (feed_ts + SEAT_SECONDS.get(SEAT, 0)) in state["flip_at"] else None,
         "stake_usd": stake_usd, "amount_in_eth": amount_in / 1e18, "tokens_target": tk, "supply_share": tk / Y0, "min_out_tokens": min_out / 1e18, "fee_assumed": fee, "price_vs_creator": round((X / Y) / p_creator, 3),
         "margin_ms": MARGIN_MS if send_mode and send_mode.startswith("predict") else None})
    if h:                                                            # live: the tokens actually received, from the buy's own event
        rec = wait_receipt(h)
        if rec:
            if SEAT in ("E1", "E2"):
                threading.Thread(target=tune_margin, args=(rec, feed_ts + SEAT_SECONDS[SEAT]), daemon=True).start()
            if rec.get("status") != "0x1":
                log({"ev": "buy_reverted", "curve": curve, "hash": h}); state["traded"].pop(curve, None); state["busy_until"] = 0.0; return
            for l in rec.get("logs", []):
                if l["topics"][0] == BUY_EV and l["address"].lower() == curve:
                    tokens = int(l["data"][2 + 64:2 + 128], 16) / 1e18
            t_buy = mono()
        else:
            log({"ev": "receipt_timeout", "curve": curve, "hash": h, "note": "assuming the buy landed: approving and selling the sized amount"})
    if token is None:
        r = resolve_rpc(creator, deadline=HOLD - 1, lookback=120); token = r[0] if r else curve
    pos = {"curve": curve, "token": token, "tokens": tokens, "nonce": nonce, "t_buy": t_buy, "buy_hash": h, "approved": False, "seat_ts": feed_ts + SEAT_SECONDS.get(SEAT, 0)}
    state["open"] = pos; save_state()
    gp = gas_price or 0
    approve = {"to": to_checksum_address(token), "value": "0x0", "data": "0x" + APPROVE_SEL + abi_word(curve) + abi_word(2 ** 256 - 1), "gas": hex(GAS_APPROVE), "gasPrice": hex(gp), "nonce": hex(nonce + 1), "chainId": 4663}
    pos["approve_hash"] = submit(approve, "approve"); pos["approved"] = True; save_state()
    why = "hold"
    with cond:
        while mono() - t_buy < HOLD:
            if STOP_SELL_FRAC > 0 and w["dump"] is not None:
                why = f"dump {100 * w['dump'] / Y0:.1f}% of supply"; break
            if TAKE_PROFIT > 0 and w["X"] / w["Y"] >= p_in * (1 + TAKE_PROFIT):
                why = f"take-profit: curve price {w['X'] / w['Y'] / p_in:.2f}x our entry"; break
            cond.wait(min(0.25, max(0.0, HOLD - (mono() - t_buy))))
    close_position(pos, why)


# ------------------------------------------------------------------------------------------------------------- feed
def parse_tx(t):
    """(type, to, value_wei, data) for legacy, type-1 and type-2 envelopes; None for anything else"""
    try:
        if t[0] >= 0xc0:
            b = rlp.decode(t); return 0, b[3], b[4], b[5]
        if t[0] == 1:
            b = rlp.decode(t[1:]); return 1, b[4], b[5], b[6]
        if t[0] == 2:
            b = rlp.decode(t[1:]); return 2, b[5], b[6], b[7]
    except Exception:
        return None
    return None


def decode_batch(l2msg_b64):
    raw = base64.b64decode(l2msg_b64)
    if not raw or raw[0] != 3:
        return []
    i = 1; out = []
    while i + 8 <= len(raw):
        ln = int.from_bytes(raw[i:i + 8], "big"); seg = raw[i + 8:i + 8 + ln]; i += 8 + ln
        if seg and seg[0] == 4:
            out.append(seg[1:])
    return out


def prune(now):
    for cv, at in list(state["known_curves"].items()):
        if now - at > 900:
            state["known_curves"].pop(cv, None); state["buys"].pop(cv, None); state["sells"].pop(cv, None)
    for cv in list(state["buys"]):
        if cv not in state["known_curves"] and state["buys"][cv] and now - state["buys"][cv][-1][3] > 120:
            state["buys"].pop(cv, None)
    for ts_ in [k for k in state["flip_at"] if k < state["feed_ts"] - 120]:
        state["flip_at"].pop(ts_, None); state["flip_block"].pop(ts_, None)
    if not state["watch"] and state["open"] is None:
        gc.collect()                                                     # the collector is off (main); run it only when nothing is in flight


def index_message(inner, ts, seen):
    """index one L2 message's transactions: direct buys and sells, creations, router buys (sender lazily), and the fold of
    everything that touches a watched curve"""
    watched = state["watch"]
    for t in decode_batch(inner.get("l2Msg", "")):
        p = parse_tx(t)
        if p is None:
            continue
        ty, to, value, data = p
        if len(to) != 20:
            continue
        val = int.from_bytes(value, "big") / 1e18 if value else 0.0; sel = data[:4]; to_hex = "0x" + to.hex()
        try:
            if sel == BUY_SEL:                                                       # direct curve buy
                snd = sender_of(t)
                state["buys"][to_hex].append((ts, snd, val, seen))
                if to_hex in watched:
                    fold_buy(watched[to_hex], ts, snd, val)
                continue
            if sel == SELL_SEL and len(data) >= 36:                                 # direct curve sell
                tk = int.from_bytes(data[4:36], "big") / 1e18; state["sells"][to_hex].append((seen, tk))
                if to_hex in watched:
                    fold_sell(watched[to_hex], tk)
                continue
            if to == FACTORY and sel in CREATE_SELS:                                 # creation
                creator = sender_of(t)
                words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
                quote = "0x" + data[4 + 32 * 2 + 12: 4 + 32 * 3].hex() if len(data) >= 4 + 32 * 4 else ZERO
                init_buy = int.from_bytes(data[4 + 32 * 3: 4 + 32 * 4], "big") if len(data) >= 4 + 32 * 4 else 0
                if quote != ZERO and int(quote, 16) < 2 ** 100:                     # unknown layout: not an address, let the RPC path decide
                    quote = ZERO
                named = {"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator, quote}
                state["creations"] += 1; state["last_creation_at"] = mono()
                log({"ev": "creation", "creator": creator, "quote": quote, "init_buy_eth": init_buy / 1e18, "feed_ts": ts, "named_wallets": len(named), "selector": sel.hex(), "tx_type": ty})
                threading.Thread(target=handle_creation, args=(creator, quote, init_buy, seen, ts, named, state["blocks"]), daemon=True).start(); continue
            if val > 0 and len(data) >= 36:                                         # a router buy of some curve: sender recovered only if it names a curve we trade
                e = [seen, ts, None, val, data, t]; state["valtx"].append(e)
                for cv, w in watched.items():
                    if w["cb"] in data:
                        e[2] = sender_of(t); fold_buy(w, ts, e[2], val)
                continue
            if watched and val == 0 and sel not in (BUY_SEL, SELL_SEL):
                for cv, w in watched.items():
                    if w["cb"] in data:                                             # router sell touching a curve we hold
                        fold_sell(w, float("inf") if STOP_SELL_FRAC > 0 else 0.0)
        except Exception as e:
            log({"ev": "error", "stage": "decode", "err": str(e)[:200]})


async def main():
    import websockets
    if SEAT == "E0" and not EXEMPT:
        raise SystemExit("SEAT=E0 needs an address exempt from the snipe surcharge (EXEMPT=1); anyone else pays 93-98% in the creation second. Use SEAT=E2 (runbook).")
    if PIN_CPU:
        try:
            os.sched_setaffinity(0, {int(c) for c in PIN_CPU.split(",")})
        except Exception as e:
            log({"ev": "error", "stage": "pin_cpu", "err": str(e)[:100]})
    sys.setswitchinterval(0.0005)
    load_state(); new_day_check(); threading.Thread(target=chain_loop, daemon=True).start()
    if state["open"]:
        log({"ev": "recovering_open_position", "position": state["open"]}); threading.Thread(target=close_position, args=(state["open"], "recovered after restart"), daemon=True).start()
    log({"ev": "start", "version": 4.1, "seat": SEAT, "exempt": EXEMPT, "bundle_min": BUNDLE_MIN, "bundle_min_eth": BUNDLE_MIN_ETH, "out1_max": OUT1_MAX, "out2_max": OUT2_MAX, "min_creator_supply": MIN_CREATOR_SUPPLY,
         "stop_sell_frac": STOP_SELL_FRAC, "take_profit": TAKE_PROFIT, "send_mode": SEND_MODE, "seat_wait_ms": SEAT_WAIT_MS, "margin_ms": MARGIN_MS, "bankroll": state["bankroll"], "frac": FRAC, "stake": [STAKE_MIN, STAKE_MAX], "hold": HOLD,
         "supply_frac": SUPPLY_FRAC, "switch": [SWITCH_N, SWITCH], "daily_stop": DAILY_STOP, "sender_backend": SENDER_BACKEND, "dry_run": True})
    gc.collect(); gc.freeze(); gc.disable()                            # a generation-2 pass costs milliseconds; prune() collects when nothing is in flight
    last_prune = mono(); backoff = 0.2
    while True:
        try:
            async with websockets.connect(FEED_URL, open_timeout=10, max_size=None, ping_interval=10, ping_timeout=5, max_queue=4, compression=None) as ws:
                log({"ev": "feed_connected"}); state["connected_at"] = mono(); state["prev_seen"] = None; backoff = 0.2
                state["brackets"].clear(); state["ref"] = None; _bcache["at"] = -1e9              # the route, hence theta, may have changed
                while True:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    except asyncio.TimeoutError:
                        log({"ev": "feed_stall", "note": "no message for 2 s: reconnecting"}); break
                    seen = mono(); wall = time.time(); d = json.loads(raw)
                    if seen - last_prune > 30:
                        prune(seen); last_prune = seen
                    for m in d.get("messages", []):
                        inner = m["message"]["message"]; hdr = inner.get("header", {})
                        ts = int(hdr.get("timestamp", 0) or 0) if int(hdr.get("kind", 0) or 0) == 3 else 0   # L2 messages only: batch reports carry L1 time
                        if not ts:
                            continue
                        warm = wall - ts > 2.0                            # a backlog replay (the feed sends one on connect): index nothing, trade nothing
                        state["blocks"] += 1
                        if not warm:
                            index_message(inner, ts, seen)
                        with cond:
                            if ts > state["last_seen_ts"] and state["last_seen_ts"] and not warm:
                                state["flip_at"].setdefault(ts, seen); state["flip_block"].setdefault(ts, m.get("sequenceNumber"))
                                if state["ref"] is None:
                                    state["ref"] = (seen, ts)
                                if state["prev_seen"] is not None and state["prev_ts"] == ts - 1 and seen - state["prev_seen"] < 0.5:
                                    r0, t0 = state["ref"]; state["brackets"].append(((state["prev_seen"] - r0) - (ts - t0), (seen - r0) - (ts - t0)))
                            state["last_seen_ts"] = max(state["last_seen_ts"], ts); state["feed_ts"] = max(state["feed_ts"], ts)
                            state["prev_seen"] = seen; state["prev_ts"] = ts
                            cond.notify_all()
        except Exception as e:
            log({"ev": "feed_error", "err": str(e)[:200], "retry_s": backoff}); await asyncio.sleep(backoff); backoff = min(5.0, backoff * 2)   # 0.2 s after a drop, slower if the network is gone


if __name__ == "__main__":
    print("sniper engine v4: DRY RUN (submit() logs unsigned transactions and sends nothing); seat", SEAT, "log", LOG_PATH, "sender backend", SENDER_BACKEND)
    asyncio.run(main())
