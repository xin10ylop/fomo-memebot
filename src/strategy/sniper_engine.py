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
import asyncio, base64, json, os, sys, time, math, threading, queue, http.client, ssl, socket, urllib.parse, urllib.request, collections, statistics as st, datetime, gc
import rlp
import traceback
sys.setswitchinterval(0.001)                                                # one-core boxes: the send path must not wait 5 ms slices behind the feed decoder
from eth_account import Account
from eth_utils import keccak, to_checksum_address

for _k, _v in list(os.environ.items()):                 # systemd's EnvironmentFile keeps an inline "# comment" as part of the value: drop it
    if " #" in _v:
        os.environ[_k] = _v.split(" #", 1)[0].rstrip()
RPC_URL = os.environ.get("RPC_URL", "https://rpc.mainnet.chain.robinhood.com")
LOGS_RPC_URL = os.environ.get("LOGS_RPC_URL", "https://rpc.mainnet.chain.robinhood.com")   # log queries span hundreds of blocks; Alchemy's free tier allows 10, the public node allows any
SEQ_URL = os.environ.get("SEQ_URL", "https://sequencer.mainnet.chain.robinhood.com")
FEED_URL = os.environ.get("FEED_URL", "wss://feed.mainnet.chain.robinhood.com")
FEED_COMPRESSION = os.environ.get("FEED_COMPRESSION", "deflate") or None   # 5.48: since Sep 17 ~19:30 UTC the feed refuses a connection that does not offer permessage-deflate ("Compression is required")
FEED_SOURCE = os.environ.get("FEED_SOURCE", "sequencer")                  # "sequencer": Robinhood's feed; "provider": a third-party node's WebSocket (PROVIDER_WS), no Robinhood endpoint at all
PROVIDER_WS = os.environ.get("PROVIDER_WS", "")                            # e.g. wss://robinhood-mainnet.g.alchemy.com/v2/KEY (section 23.10)
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
BUNDLE_MAX_ETH = float(os.environ.get("BUNDLE_MAX_ETH", "0"))     # 0 = no cap. A team that puts in more than this has already taken the move: Sep 12-16 those launches paid -0.7%, the rest +8.5% (audit_combo)
OUT1_MAX = int(os.environ.get("OUT1_MAX", "0"))
OUT1_MIN_ETH = float(os.environ.get("OUT1_MIN_ETH", "0"))                 # second-one outsider buys below this size do not count (0 = all count; 0.01 makes the gate immune to planted dust)
OUT2_MAX = int(os.environ.get("OUT2_MAX", "0"))                          # non-named buys visible in the seat's second before we send
SEAT_WAIT_MS = float(os.environ.get("SEAT_WAIT_MS", "300"))              # react mode: watch the seat's second this long for an outsider before sending (section 23)
TIER_ASSUMED = float(os.environ.get("TIER_ASSUMED", "0.05"))
STOP_SELL_FRAC = float(os.environ.get("STOP_SELL_FRAC", "0"))
TRADE_HOURS = os.environ.get("TRADE_HOURS", "12-05")                 # UTC hours the tables cover and that pay (start-end, wraps midnight); "" = always. 06-12 never measured, 05-06 +0.4% on 33 launches
MIN_RULE_PASSING_1H = int(os.environ.get("MIN_RULE_PASSING_1H", "0"))
MIN_FOLLOW_ETH_60 = float(os.environ.get("MIN_FOLLOW_ETH_60", "0.10")); DEMAND_ARM_N = int(os.environ.get("DEMAND_ARM_N", "10"))  # the floor arms after this many scored clean launches (tables: arming at 10 removes 28 trades worth -$5)  # demand floor: no new trade while the mean follow-on ETH of the last 60 scored launches is below this. The tables never read below 0.15 except Sep 10 12-18 (0.06, those trades lost); costs nothing there, and Sep 11 read 0.01-0.03 all morning  # optional dead-stretch guard; off: the tables' n=7 at -7.8% and yesterday's n=3 at +19.9% pool to nothing


def hours_ok(now=None):
    if not TRADE_HOURS:
        return True
    a, b = (int(x) for x in TRADE_HOURS.split("-")); h = datetime.datetime.utcfromtimestamp(now or time.time()).hour
    return (a <= h < b) if a < b else (h >= a or h < b)
SEND_MODE = os.environ.get("SEND_MODE", "react"); MARGIN_MS = float(os.environ.get("MARGIN_MS", "15"))
MARGIN_MIN_MS = float(os.environ.get("MARGIN_MIN_MS", "5")); MARGIN_MAX_MS = float(os.environ.get("MARGIN_MAX_MS", "60"))
MAX_LATE_S = float(os.environ.get("MAX_LATE_S", "0.5"))                  # do not send more than this far into the seat's second
MIN_CREATOR_SUPPLY = float(os.environ.get("MIN_CREATOR_SUPPLY", "0.01"))
MAX_CREATOR_BUY_ETH = float(os.environ.get("MAX_CREATOR_BUY_ETH", "2"))
SWITCH_N = int(os.environ.get("SWITCH_N", "15")); SWITCH = float(os.environ.get("SWITCH", "-0.10")); DAILY_STOP = float(os.environ.get("DAILY_STOP", "0.50"))
MAX_RESOLVE_MS = int(os.environ.get("MAX_RESOLVE_MS", "1500"))
GAS_MAX_SHARE = float(os.environ.get("GAS_MAX_SHARE", "0.05"))
GAS_HEADROOM = float(os.environ.get("GAS_HEADROOM", "2.0"))
SELL_GAS_HEADROOM = float(os.environ.get("SELL_GAS_HEADROOM", "8.0"))   # cap on the approve and the sell: receipts show only the base fee is charged, so a high cap is free and a fee spike cannot refuse the exit
SELL_CONFIRM_S = float(os.environ.get("SELL_CONFIRM_S", "1.5")); SELL_MAX_S = float(os.environ.get("SELL_MAX_S", "20"))
SELL_FEE_MAX_USD = float(os.environ.get("SELL_FEE_MAX_USD", "2.00"))  # the exit's fee ceiling: the doubling cap stops here. Receipts pay about $0.02; an unbounded cap could spend multiples of the position (audit, Sep 16)                # gasPrice sent = this x eth_gasPrice: the quote equals the base fee, a tick up refuses the tx (23.7)
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
E0_OUTSIDER = os.environ.get("E0_OUTSIDER", "0") == "1"                # explicit opt-in: take the creation second as a wallet that is NOT exempt from the surcharge
TIER_MIN_BPS = int(os.environ.get("TIER_MIN_BPS", "0")); TIER_MAX_BPS = int(os.environ.get("TIER_MAX_BPS", "0"))   # the token's own tax (creation calldata word 13, bps on top of the 1% protocol fee): 0 = no gate. 24.14: 100-200 bps tokens pay +34/+43/+36/+27%
SKIP_TIER1_TEAM_SHARE = float(os.environ.get("SKIP_TIER1_TEAM_SHARE", "0"))
E0_BUNDLE_WAIT_S = float(os.environ.get("E0_BUNDLE_WAIT_S", "0.45"))
E0_BUNDLE_MAX_BLOCKS = int(os.environ.get("E0_BUNDLE_MAX_BLOCKS", "9"))
MAX_LIVE_TRADES = int(os.environ.get("MAX_LIVE_TRADES", "0"))     # live: stop taking seats after this many real buys have been sent since the start (0 = no cap); a controlled first trade
PROVIDER_FALLBACK_S = float(os.environ.get("PROVIDER_FALLBACK_S", "120"))
PROVIDER_HEADS = os.environ.get("PROVIDER_HEADS", "0") == "1"           # also subscribe to newHeads on the provider path (a message every 100 ms; the E1/E2 seats need it, the E0 seat does not)
E0_ALLOW_PROVIDER = os.environ.get("E0_ALLOW_PROVIDER", "0") == "1"   # take the creation-second seat on the provider path too (after deploy/provider_lag_probe.py shows the lag is small)
try:
    PROVIDER_LAG_MS = float(os.environ.get("PROVIDER_LAG_MS", "0") or 0)   # the measured lag of the provider path behind the sequencer: added to the paper landing of seats taken on it
except ValueError:
    PROVIDER_LAG_MS = 0.0; E0_ALLOW_PROVIDER = False                   # a placeholder left in the env file: the seat stays off the provider path until a number is set   # after the sequencer feed refuses us, run on the provider this long, then try the feed again (24.17: the fallback was a one-way door)   # the creation-second seat counts the bundle inside this many blocks of the creation; 3 = the honest table's "complete by 0.3 s" (24.15), the 5.41 paper run lost on later ones   # the creation-second seat waits this long after the creation for the bundle to be visible on the feed (24.15: the tables' edge past the bundle was look-ahead)   # skip a 1%-tier token whose team holds at least this share of supply (0 = off): the worst class in 24.14


def tax_bps_of(sel, words):
    """the token's own tax in basis points, from the creation calldata: word 13 of selector f85f8e41 (0 = the 1% tier, 100 = 2%,
    200 = 3%, 300 = 4%; matched the chain on 117 of 120 launches, Sep 17). None for another layout: the gates then fail closed."""
    if sel.hex() != "f85f8e41" or len(words) <= 13:
        return None
    v = int.from_bytes(words[13], "big")
    return v if v <= 2000 else None
SURCHARGE = {"E0": 0.0 if EXEMPT else 0.0618, "E1": 0.0618, "E2": 0.0019}; SEAT_SECONDS = {"E0": 0, "E1": 1, "E2": 2}
# E0 for a wallet that is not exempt does not exist (report 24.19, correcting 24.13): the snipe tax is keyed to the block's
# clock second, so a buy in any block that carries the creation block's timestamp pays ~98%, whatever its block offset
# (the live trade of Sep 18 landed 3 blocks after the creation and reverted on its minOut). 24.13 measured time in block
# offsets and mistook next-second buys at small offsets for creation-second buys. The 6.18% surcharge starts with the
# first block of the next second: that is SEAT=E1. SEAT=E0 is refused at start-up unless EXEMPT=1.
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
    def __init__(self, url, timeout=10):
        u = urllib.parse.urlparse(url); self.host = u.netloc; self.path = u.path or "/"; self.local = threading.local(); self.timeout = timeout

    def call(self, method, params, tries=3):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        for i in range(tries):
            try:
                c = getattr(self.local, "c", None)
                if c is None:
                    c = http.client.HTTPSConnection(self.host, timeout=self.timeout, context=_CTX); self.local.c = c
                c.request("POST", self.path, body=body, headers=UA); r = c.getresponse(); d = json.loads(r.read())
                if "error" in d:
                    raise RuntimeError(d["error"])
                return d["result"]
            except Exception:
                self.local.c = None
                if i == tries - 1:
                    raise
                time.sleep(0.03)


class _Answers(list):
    """a list of (host, answer) that also carries the state of the send that produced it"""
    meta = None


class Sender:
    """pre-opened, keep-alive TLS sockets to the send endpoints (the sequencer first: it is the admission point; the provider
    forwards to it). The sequencer name resolves to one address per availability zone; each is measured and the socket is
    kept to the fastest (re-measured every 20 minutes), so a box in the sequencer's own zone talks to its own zone.
    fire(body) posts the same signed transaction to every endpoint and returns the first answer. Live only: the dry run
    keeps the sockets warm and measures them, and sends nothing."""
    PING = b'{"jsonrpc":"2.0","id":0,"method":"eth_chainId","params":[]}'

    def __init__(self, urls):
        self.eps = []
        for u in urls:
            if not u:
                continue
            p = urllib.parse.urlparse(u); self.eps.append({"url": u, "host": p.netloc, "path": p.path or "/", "c": None, "lock": threading.Lock(), "rtt_ms": None, "ok": False, "ip": None, "ips": {}})
        self._local = threading.local(); self.last = []
        threading.Thread(target=self._keepalive, daemon=True).start()

    def _connect(self, e):
        """a TLS connection to the pinned address (SNI and Host stay the hostname), or by name when nothing is pinned"""
        c = http.client.HTTPSConnection(e["host"], timeout=5, context=_CTX)
        if e["ip"]:
            raw = socket.create_connection((e["ip"], 443), timeout=5); raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            c.sock = _CTX.wrap_socket(raw, server_hostname=e["host"])
        return c

    def _measure(self, e):
        """round trip to every address the name resolves to (5 pings each, the median), then pin the fastest"""
        try:
            ips = sorted({ai[4][0] for ai in socket.getaddrinfo(e["host"], 443, socket.AF_INET)})
        except Exception:
            return
        res = {}
        for ip in ips:
            try:
                raw = socket.create_connection((ip, 443), timeout=5); raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                c = http.client.HTTPSConnection(e["host"], timeout=5, context=_CTX); c.sock = _CTX.wrap_socket(raw, server_hostname=e["host"]); t = []
                for _ in range(5):
                    t0 = mono(); c.request("POST", e["path"], body=self.PING, headers=UA); c.getresponse().read(); t.append(1000 * (mono() - t0))
                c.close(); res[ip] = round(sorted(t)[2], 2)
            except Exception:
                res[ip] = None
        e["ips"] = res; good = {ip: v for ip, v in res.items() if v is not None}
        if good:
            best = min(good, key=good.get)
            if best != e["ip"]:
                with e["lock"]:
                    e["ip"] = best; e["c"] = None
        log({"ev": "sender_addresses", "host": e["host"], "rtt_ms_by_address": res, "pinned": e["ip"]})

    def _ping(self, e):
        with e["lock"]:
            try:
                if e["c"] is None:
                    e["c"] = self._connect(e)
                t0 = mono(); e["c"].request("POST", e["path"], body=self.PING, headers=UA); e["c"].getresponse().read(); e["rtt_ms"] = round(1000 * (mono() - t0), 1); e["ok"] = True
            except Exception:
                e["c"] = None; e["ok"] = False

    def _keepalive(self):
        n = 0
        while True:
            if n % 240 == 0:                                            # at start and every 20 minutes: which address is nearest
                for e in self.eps:
                    self._measure(e)
            for e in self.eps:
                self._ping(e)
            if n % 20 == 0:
                log({"ev": "sender_rtt", "endpoints": [{"host": e["host"], "address": e["ip"], "warm_rtt_ms": e["rtt_ms"], "ok": e["ok"]} for e in self.eps]})
            n += 1; time.sleep(5)

    def _read(self, e, out, meta):
        """background: the endpoint's reply to a fired transaction; releases the endpoint's lock taken by fire()"""
        try:
            d = json.loads(e["c"].getresponse().read())
        except Exception as ex:
            e["c"] = None; d = {"error": str(ex)[:120]}
        finally:
            e["lock"].release()
        out.append((e["host"], d)); meta["replies"].append((e["host"], round(1000 * (mono() - meta["t0"]), 1)))
        if len(out) >= meta["pending"]:
            meta["done"].set(); meta["complete"] = True
            log({"ev": "send_answers", "hash": meta["hash"], "write_ms": meta["write_ms"], "reply_ms": meta["replies"], "answers": [(h, str(d)[:120]) for h, d in out]})

    def fire(self, body, wait_s=2.0):
        """post the same signed transaction to every endpoint, sequencer first, from the calling thread: the request is written
        and the call returns; the replies are read by background threads (send_answers event). The hash is computed locally
        from the raw transaction, so the critical path ends at the socket write (Sep 11: waiting for the reply on a one-core
        box put the buy 170 ms late). Returns (hash, answers); answers fills in as the endpoints reply (answers(), rejected())."""
        out = _Answers(); self.last = out; self._local.last = out; t0 = mono()
        try:
            h = "0x" + keccak(bytes.fromhex(json.loads(body)["params"][0][2:])).hex()
        except Exception:
            h = None
        meta = {"pending": 0, "done": threading.Event(), "t0": t0, "hash": h, "replies": [], "write_ms": None}; out.meta = meta; fired = []
        for e in self.eps:
            if not e["lock"].acquire(timeout=0.1):                        # a keep-alive ping holds the socket for one round trip; a hung one must not hold the buy
                out.append((e["host"], {"error": "endpoint busy: skipped"})); continue
            try:
                if e["c"] is None:
                    e["c"] = self._connect(e)
                e["c"].request("POST", e["path"], body=body, headers=UA)
            except Exception as ex:
                e["c"] = None; e["lock"].release(); out.append((e["host"], {"error": str(ex)[:120]})); continue
            meta["pending"] += 1; fired.append(e)
        meta["write_ms"] = round(1000 * (mono() - t0), 2)
        for e in fired:
            threading.Thread(target=self._read, args=(e, out, meta), daemon=True).start()
        if meta["pending"] == 0:
            meta["done"].set(); meta["complete"] = True
            log({"ev": "send_answers", "hash": h, "write_ms": meta["write_ms"], "reply_ms": [], "answers": [(hh, str(d)[:120]) for hh, d in out]})
            return None, out
        return h, out

    def mine(self):
        """the answers of the last transaction this thread fired (never another thread's: self.last is shared)"""
        return getattr(self._local, "last", None)

    def answers(self, out, timeout=0.5):
        """wait up to timeout for every endpoint's reply to the fire() that returned out; returns out"""
        meta = getattr(out, "meta", None) if out is not None else None
        ev = meta.get("done") if isinstance(meta, dict) else None        # never raise on the exit path
        if ev is not None:
            ev.wait(timeout)
        return out if out is not None else []

    def rejected(self, out):
        """True only when every endpoint has answered and every answer is a real refusal. 'already known' and 'nonce too
        low' mean the transaction is in the pool or already mined, which is the opposite of refused: reading those as a
        refusal would abandon a buy whose tokens we own (audit, Sep 16)."""
        meta = getattr(out, "meta", None)
        if not out or meta is None or not meta.get("complete"):
            return False
        for _, d in out:
            if "result" in d:
                return False
            err = d.get("error")
            if not isinstance(err, dict):                                 # a timeout or a dropped socket is not a verdict: the sequencer may well have taken it
                return False
            t = str(err).lower()
            if "already known" in t or "nonce too low" in t or "already imported" in t or "known transaction" in t:
                return False
        return True


rpc = Rpc(RPC_URL); rpc_logs = Rpc(LOGS_RPC_URL); rpc_seat = Rpc(RPC_URL, timeout=2.0)   # rpc_seat: the resolver's node on the seat path, nothing may hang there


def get_logs(filt, tries=3, seat=False):
    """eth_getLogs: the provider first, over the whole range in one call (a paid plan takes 10,000 blocks in 200-500 ms; a free
    tier refuses more than ten, and then the same range is fetched in ten-block chunks), and the public node last. On the seat
    path (seat=True) every call is a single try on a 2 s timeout, because the resolver's own loop is the retry: the public node
    hung for 3-7 s on getLogs on Sep 16 and cost 13 seats in 90 minutes as "stale feed" refusals."""
    node = rpc_seat if seat else rpc; t = 1 if seat else tries; errs = []
    try:
        return node.call("eth_getLogs", [filt], tries=t)
    except Exception as e:
        errs.append("provider " + str(e)[:80])
        try:
            a = int(filt["fromBlock"], 16); b = int(node.call("eth_blockNumber", [], tries=t), 16) if filt["toBlock"] == "latest" else int(filt["toBlock"], 16)
            if b - a >= 10:
                out = []
                for x in range(a, b + 1, 10):
                    out += node.call("eth_getLogs", [dict(filt, fromBlock=hex(x), toBlock=hex(min(b, x + 9)))], tries=t)
                return out
        except Exception as e2:
            errs.append("provider chunks " + str(e2)[:80])
    for i in range(t):
        try:
            return rpc_logs.call("eth_getLogs", [filt], tries=t)
        except Exception as e:
            errs.append("public " + str(e)[:80])
            if i < t - 1:
                time.sleep(0.5 * (i + 1))
    raise RuntimeError("logs: " + "; ".join(errs))
SENDER = Sender([SEQ_URL, RPC_URL if RPC_URL != SEQ_URL else None])
state = {"bankroll": BANKROLL, "day": None, "day_start": BANKROLL, "stopped": False, "busy_until": 0.0, "scores": collections.deque(maxlen=max(SWITCH_N, 60)),
         "launched_today": collections.Counter(), "seeded": False, "feed_ts": 0, "last_seen_ts": 0, "traded": {}, "eth_usd": ETH_USD,
         "buys": collections.defaultdict(list),        # curve -> [(ts, sender, value_eth, seen)] direct buys
         "sells": collections.defaultdict(list),       # curve -> [(seen, tokens)] direct sells
         "valtx": collections.deque(maxlen=4000),      # [seen, ts, sender_or_None, value_eth, data, raw] value-carrying non-direct txs: router buys, sender recovered lazily
         "watch": {},                                  # curve -> incremental reserves and counters, folded by the feed loop for the curves we are trading
         "known_curves": {}, "brackets": collections.deque(maxlen=300), "ref": None, "flip_at": {}, "flip_block": {}, "feed_seq": 0, "connected_at": 0.0,
         "blocks": 0, "prev_seen": None, "prev_ts": 0, "nonce": None, "gas_price": None, "chain_at": 0.0, "open": None, "decisions": {},
         "landings": {"since_early": 0, "first": 0}, "schedule": collections.deque(maxlen=20), "rule_passing": collections.deque(maxlen=400), "rules_changed": False, "day_start_real": False, "creations": 0, "timing": collections.deque(maxlen=60), "timing_all": collections.deque(maxlen=60), "scores_e1": collections.deque(maxlen=60), "race_lags": collections.deque(maxlen=60), "out1_flags": collections.deque(maxlen=60), "last_creation_at": 0.0, "reverters": collections.Counter()}
lock = threading.Lock()
cond = threading.Condition()                           # notified by the feed loop after every message is fully indexed


def save_state():
    try:
        d = {"bankroll": state["bankroll"], "day": str(state["day"]), "day_start": state["day_start"], "stopped": state["stopped"], "scores": list(state["scores"]),
             "open": {k: v for k, v in state["open"].items() if k != "closing"} if isinstance(state["open"], dict) else state["open"],
             "margin_ms": MARGIN_MS, "saved_at": time.time(), "timing": list(state["timing"])}
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
        if isinstance(state["open"], dict):
            state["open"].pop("closing", None)                          # a position saved mid-sell must be sellable again after a restart (audit, Sep 16)
        if time.time() - d.get("saved_at", 0) < 3600:                          # the demand readout survives a restart (it gates the first trades); stale after an hour
            for x in d.get("timing", []):
                state["timing"].append(tuple(x))
        log({"ev": "state_loaded", "bankroll": state["bankroll"], "scores": len(state["scores"]), "open": state["open"] is not None, "margin_ms": MARGIN_MS, "timing": len(state["timing"]), "saved_s_ago": round(time.time() - d.get("saved_at", 0))})
    except FileNotFoundError:
        pass
    except Exception as e:
        log({"ev": "error", "stage": "load_state", "err": str(e)[:200]})


def abi_word(x):
    return x.to_bytes(32, "big").hex() if isinstance(x, int) else x[2:].rjust(64, "0")


SEND = None                                                # the operator's send step, loaded from SEND_MODULE (deploy/send_step.py); None = dry run


def load_send_step():
    """SEND_MODULE=/etc/sniper/send_step.py: a file the operator writes (the reference is deploy/send_step.py) whose make(engine)
    returns a function submit(tx, label) -> hash. Nothing in the repository signs or sends; without the file the engine
    stays in dry run. The file is read once at start; an error in it stops the engine before the feed is opened."""
    global SEND
    path = os.environ.get("SEND_MODULE", "")
    if not path:
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location("sniper_send_step", path); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    SEND = mod.make(sys.modules[__name__])
    log({"ev": "send_step_loaded", "path": path, "wallet": WALLET})


def submit(tx, label):
    """DRY RUN (SEND is None): logs the exact unsigned transaction and returns None. Live: the operator's send step signs it
    (Account.sign_transaction(tx) works as built: checksummed to, hex fields), fires it through SENDER (sequencer first,
    provider second) and returns the hash."""
    if SEND is not None:
        return SEND(tx, label)
    log({"ev": "unsigned_tx", "label": label, "tx": tx})
    return None


# ---------------------------------------------------------------------------------------------------------- background
def chain_loop():
    """nonce, gas price and the ETH price, refreshed in the background so the critical path never waits on the RPC"""
    n = 0
    while True:
        try:
            state["nonce"] = int(rpc.call("eth_getTransactionCount", [WALLET, "pending"]), 16); state["base_fee"] = int(rpc.call("eth_gasPrice", []), 16); state["gas_price"] = int(state["base_fee"] * GAS_HEADROOM); state["chain_at"] = mono()
            if SEND is not None and state["open"] is None and (n % 10 == 0 or not state["day_start_real"]):   # live: the bankroll is the wallet's ETH; it changes only on trades, so every 30 s is enough
                bal = int(rpc.call("eth_getBalance", [WALLET, "latest"]), 16) / 1e18; state["wallet_eth"] = bal
                with lock:
                    state["bankroll"] = bal * state["eth_usd"]
                    if not state["day_start_real"]:                       # until the wallet is read, day_start is BANKROLL_USD from the env; a wallet under half of it would latch the daily stop on the first launch (audit, Sep 16)
                        state["day_start"] = state["bankroll"]; state["day_start_real"] = True
                        log({"ev": "day_start", "bankroll_usd": round(state["bankroll"], 2), "stop_at_usd": round((1 - DAILY_STOP) * state["bankroll"], 2)})
        except Exception as e:
            if n % 20 == 0:
                log({"ev": "error", "stage": "chain_loop", "err": str(e)[:160]})
        if n % 100 == 0:
            try:
                try:
                    d = json.load(urllib.request.urlopen(urllib.request.Request(ETH_USD_URL, headers={"User-Agent": UA["User-Agent"]}), timeout=10)); px = float(d["data"]["amount"])
                    if 100 < px < 100000:
                        state["eth_usd"] = px
                except Exception:
                    pass
                rp = list(state["rule_passing"]); now = time.time()          # snapshots: these deques are appended by the score threads while this reduces them (audit, Sep 16)
                tm = list(state["timing"]); fs = [a for a, b, c in tm if a is not None]
                o1 = list(state["out1_flags"]); ta = list(state["timing_all"]); se1 = list(state["scores_e1"]); rl = list(state["race_lags"]); sc = list(state["scores"])
                log({"ev": "flow", "rule_passing_last_6h": sum(1 for t in rp if now - t < 21600), "rule_passing_last_1h": sum(1 for t in rp if now - t < 3600),
                     "mean_score_last_60": round(st.mean(sc[-60:]), 4) if sc else None, "creations_seen": state["creations"],
                     "median_first_sell_s": round(st.median(fs), 2) if fs else None, "share_dumped_inside_hold": round(st.mean(b for a, b, c in tm), 4) if tm else None,
                     "follow_eth_last_20": round(st.mean([c for a, b, c in tm][-20:]), 3) if tm else None, "follow_eth_last_60": round(st.mean(c for a, b, c in tm), 3) if tm else None, "follow_eth_all_60": round(st.mean(ta), 3) if ta else None,
                     "out1_share_last_60": round(st.mean(o1), 2) if o1 else None, "mean_score_e1_last_60": round(st.mean(se1), 4) if se1 else None, "race_first_rival_ms_median": round(st.median(rl), 1) if rl else None, "race_first_block_share": round(sum(1 for x in rl if x < 15) / len(rl), 2) if rl else None,
                     "bankroll_usd": round(state["bankroll"], 2), "wallet_eth": round(state["wallet_eth"], 5) if state.get("wallet_eth") is not None else None,
                     "silent_min": round((mono() - state["last_creation_at"]) / 60, 1) if state["last_creation_at"] else None})
                if state["last_creation_at"] and mono() - state["last_creation_at"] > 1800 and mono() - state["connected_at"] > 1800:
                    log({"ev": "alarm", "what": "no creation seen from the factory for 30 minutes while the feed is connected: the launchpad moved, stopped or changed its factory"})
                b = boundary()
                if b:
                    log({"ev": "boundary", "theta_ms": round(1000 * b[0], 1), "confidence": round(b[1], 3), "bracket_width_ms": round(1000 * b[2], 1), "samples": len(state["brackets"]), "margin_ms": round(MARGIN_MS, 2)})
            except Exception as e:
                if n % 20 == 0:                                              # the readout block used to sit outside every try: one raise stopped the nonce refresh for good and every launch was gated "nonce/gas not fresh" (audit, Sep 16)
                    log({"ev": "error", "stage": "chain_loop_readouts", "err": str(e)[:200]})
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
    flip = state["flip_at"].get(target_ts)
    if state["feed_ts"] != target_ts or flip is None or mono() - flip > MAX_LATE_S:
        return None                                                  # no recorded flip for this second (a reconnect replaying a backlog): send nothing rather than raise
    if SEAT_WAIT_MS > 0 and watch is not None:                       # the seat rule: send SEAT_WAIT_MS into the second unless an outsider has already bought
        until = flip + SEAT_WAIT_MS / 1000.0
        with cond:
            while mono() < until and watch["out2"] + watch["out2_chain"] <= OUT2_MAX and state["feed_ts"] == target_ts:
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
        state["day"] = d; state["day_start"] = state["bankroll"]; state["day_start_real"] = SEND is None; state["stopped"] = False; state["launched_today"].clear(); state["seeded"] = False
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
                for l in get_logs({"fromBlock": hex(b), "toBlock": hex(e), "address": FACTORY_HEX}):
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
    for e in list(state["valtx"]):                                    # a snapshot: the feed appends (and evicts) while this scans (audit, Sep 16)
        if cb in e[4]:
            if e[2] is None:
                try:
                    e[2] = sender_of(e[5])
                except Exception:
                    e[2] = "?"
            out.append((e[1], e[2], e[3], e[0], e[6] if len(e) > 6 else None, e[7] if len(e) > 7 else None, e[8] if len(e) > 8 else None, e[4]))
    if since_ts is not None:
        out = [b for b in out if b[0] >= since_ts]
    return out


def watch_curve(curve, tk0, feed_ts, named, creator, blk0=None, tax_bps=None):
    """register the curve for incremental folding and build its state from what the feed has shown so far"""
    net0 = X0 * tk0 / (Y0 - tk0); w = {"X": X0 + net0, "Y": Y0 - tk0, "cb": bytes.fromhex(curve[2:]), "ts0": feed_ts, "blk0": blk0, "named": named, "creator": creator, "curve": curve,
                                       "tax_bps": tax_bps, "tax": 0.01 + (tax_bps or 0) / 10000.0,             # the buyers' tax on this token: the 1% protocol fee plus the token's own (calldata word 13)
                                       "bundle": 0, "bundle_eth": 0.0, "out1": 0, "out2": 0, "out1_chain": 0, "out2_chain": 0, "tb": None, "buys": 0, "sells": 0, "since": mono(), "dump": None, "wallets": set(), "rivals": []}
    for b in curve_buys(curve, feed_ts):
        ts_, snd, val, seen = b[:4]; blk = b[4] if len(b) > 4 else None
        buyers = named_in(b[7], named) if len(b) > 7 else None                 # a helper call: its recipients are the bundle
        if buyers and snd in named:
            buyers = buyers | {snd}
        fold_buy(w, ts_, snd, val, blk, b[5] if len(b) > 5 else None, b[6] if len(b) > 6 else None, buyers=buyers or None)
    for seen, tk in state["sells"].get(curve, []):
        fold_sell(w, tk)
    state["watch"][curve] = w
    return w


def named_in(data, named):
    """the named wallets whose address appears in a transaction's calldata: a helper contract buying for several wallets in one
    transaction lists its recipients there (Sep 18: one call, one value, thirteen buyers; report 24.18)"""
    if not data or not named:
        return set()
    return {a for a in named if bytes.fromhex(a[2:]) in data}


def fold_buy(w, ts_, snd, val, blk=None, to=None, sel=None, buyers=None):
    """the tables' definitions (section 23.11 dry-run findings): the bundle is the named wallets' buys within nine blocks of the
    creation (block-count time under 1.0 s, as the replay measures it), not the creation's whole timestamp second; its ETH is
    those buys only (named wallets buying again in second one are the team's second round, not the bundle). A rival is any
    non-named sender whose transaction names the curve in second one or two: a direct buy, a value-carrying router buy, or a
    value-less router call (a router buy paid in tokens). A sender whose counted attempts never land (a bot whose second-one buys
    revert on the surcharge) is learned from the chain at scoring time and ignored after three misses."""
    if val > 0:
        net = val * (1 - w.get("tax", 0.01)); X, Y = w["X"], w["Y"]; tk = Y - X * Y / (X + net); w["X"] = X + net; w["Y"] = Y - tk   # the token's own tax from the calldata, not a flat 1%
    w["buys"] += 1
    in_creation = (blk - w["blk0"] <= 9) if (blk is not None and w.get("blk0") is not None) else (ts_ == w["ts0"])
    if buyers:                                                            # one helper transaction buying for several named wallets: the bundle is its buyers, its ETH the value (24.18)
        if in_creation and not w.get("bundle_closed"):
            w["bundle"] += len(buyers); w["wallets"] |= set(buyers); w["bundle_eth"] += val
        return
    if snd in w["named"] or snd == w["creator"]:
        if in_creation and not w.get("bundle_closed"):
            w["bundle"] += 1; w["wallets"].add(snd); w["bundle_eth"] += val   # buys and distinct wallets: the tables count buys (no sender in the event data)
    elif snd != WALLET:
        if in_creation and not w.get("bundle_closed"):                          # the tables end the bundle at the first taxed buy (an outsider paying 93-98% in the creation second)
            w["bundle_closed"] = True
        sec = ts_ - w["ts0"]
        if sec in (1, 2):
            ignored = state["reverters"].get(snd, 0) >= 3
            log({"ev": "rival", "curve": w.get("curve"), "second": sec, "sender": snd, "to": to, "selector": sel, "value": round(val, 5), "ignored": ignored})
            w["rivals"].append([sec, snd])                            # recorded even when ignored, so scoring can un-learn a sender that starts landing again (audit, Sep 16)
            if ignored:
                return
            if sec == 1 and w.get("race_ms") is None:
                fa = state["flip_at"].get(ts_); w["race_ms"] = round((mono() - fa) * 1000, 1) if fa else None
            if sec == 1 and val >= OUT1_MIN_ETH:
                w["out1"] += 1
            elif sec == 2:
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
def gas_usd():
    """a round trip's gas (buy, approve, sell) at the chain's current price: 230,000 gas used at 0.1-0.2 gwei is $0.06-0.14
    (four Sep 11 receipts: $0.021-0.054 a transaction). The scorer used to charge a flat $1.00, which put every paper score
    4 points low at $25 and 10 points low at $10 and fed that bias into the switch and the readouts (found Sep 17)."""
    try:
        return min(1.0, max(0.05, (state.get("base_fee") or 2e8) * 230_000 / 1e18 * state["eth_usd"]))
    except Exception:
        return 0.15


def exact_score(events, b_create, tk0, stake_eth, seat, tol=0.10, slip=0.3, hold=HOLD, frac=SUPPLY_FRAC, gated=True, stop_sell_frac=None, tp=None, front=False, readouts=True, t_entry=None, min_out=None, amount_in=None, info=None):
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
    # the tables end the bundle at the first taxed buy; the creation-second seat is gated on the named wallets' transactions inside nine
    # blocks whatever bought first (a bot through a helper the feed cannot attribute), so its label uses the same window and the
    # paper result of every seat taken is recorded (24.16: a bot at block 1, the team at block 4, the seat +245% in the replay, unscored)
    cut = 1.0 if seat == "E0" else min(1.0, first_taxed)
    bundle_rows = [r for r in rows[1:] if r[1] == "B" and r[0] < cut and r[5] - tier <= 0.0008]
    if info is not None:
        info["bot_first"] = bool(bundle_rows) and first_taxed < bundle_rows[-1][0]      # a taxed outsider landed before the bundle was complete
    if readouts and seat == "E0" and bundle_rows and first_taxed < bundle_rows[-1][0]:
        state["bot_before_bundle"] = state.get("bot_before_bundle", 0) + 1
    lab = (len(bundle_rows), sum(r[2] for r in bundle_rows), sum(1 for r in rows[1:] if r[1] == "B" and 0.05 <= r[5] - tier <= 0.075 and r[2] >= OUT1_MIN_ETH))
    # the tax schedule: every surcharged buy in the first three seconds must sit in a known band (creation second 85-99.5%, second one
    # 5-7.5%, second two 0.12-0.35%); a launch where most surcharged buys fall outside them is anomalous, a run of them means the rules changed
    sur = [r[5] - tier for r in rows[1:] if r[1] == "B" and r[0] <= 3.0 and r[5] - tier > 0.001]
    odd = sum(1 for x in sur if not (0.85 <= x <= 0.995 or 0.05 <= x <= 0.075 or 0.0012 <= x <= 0.0035))
    if readouts:
        state["schedule"].append(1 if (sur and odd / len(sur) > 0.5) else 0)
    if readouts and lab[0] >= BUNDLE_MIN and lab[1] >= BUNDLE_MIN_ETH:
        state["out1_flags"].append(1 if lab[2] > 0 else 0)                              # crowding readout: share of bundled launches with an outsider in second one
        state["timing_all"].append(sum(r[2] for r in rows[1:] if r[1] == "B" and 2.3 <= r[0] < 7.6))   # demand over every bundled launch, crowded or not (the tables' gauge); the floor reads the clean ones only
    if gated and (lab[0] < BUNDLE_MIN or lab[1] < BUNDLE_MIN_ETH or (BUNDLE_MAX_ETH > 0 and lab[1] > BUNDLE_MAX_ETH) or rows[0][3] < MIN_CREATOR_SUPPLY * Y0 or (seat == "E2" and lab[2] > OUT1_MAX)):
        return ("filtered",) + lab
    X, Y = X0, Y0; X += rows[0][4]; Y -= rows[0][3]
    lo, hi, fb = {"E0": (-1.0, 0.0008, 0.1), "E1": (0.05, 0.075, 1.0), "E2": (0.0012, 0.0035, 2.0)}[seat]
    idx = next((i for i in range(1, len(rows)) if rows[i][1] == "B" and rows[i][0] <= 3.0 and lo <= rows[i][5] - tier <= hi), None)
    if idx is None:
        idx = next((i for i in range(1, len(rows)) if rows[i][0] >= fb), len(rows)); t_in = fb
    else:
        t_in = rows[idx][0]
    if front:                                                                                      # the front of the seat's second: ahead of every buyer in it (the E1 plan's assumption)
        t_in = fb; idx = next((i for i in range(1, len(rows)) if rows[i][0] >= fb), len(rows))
    else:
        t_in += 0.3; idx = next((i for i in range(1, len(rows)) if rows[i][0] >= t_in), len(rows))   # 0.3 s behind the first buyer of the seat, as the tables assume
    if t_entry is not None:                                                                        # 5.44: our own estimated landing instead of the tables' assumption
        t_in = t_entry; idx = next((i for i in range(1, len(rows)) if rows[i][0] >= t_in), len(rows))
    for r in rows[1:idx]:
        if r[1] == "B":
            X += r[4]; Y -= r[3]
        else:
            X -= r[4]; Y += r[3]
    fee = tier + SURCHARGE[seat]
    tk_bot = frac * Y0; net = X * tk_bot / (Y - tk_bot); gross = net / (1 - fee)
    if gross > stake_eth:
        gross = stake_eth; net = gross * (1 - fee); tk_bot = Y * net / (X + net)
    if amount_in is not None:                                                                      # the exact transaction the engine built: its amount and its minimum output
        gross = amount_in; net = gross * (1 - fee); tk_bot = Y * net / (X + net)
        if min_out is not None and tk_bot < min_out:                                               # the curve moved past our tolerance before we landed: the buy reverts, gas is the loss
            if info is not None:
                info["reverted"] = True; info["got_vs_min"] = round(tk_bot / min_out, 3)
            return (-gas_usd(), gross * state["eth_usd"], t_in, tier) + lab
    if info is not None:
        info["t_in"] = t_in
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
    follow_eth = sum(r[2] for r in rows if r[1] == "B" and t_in <= r[0] < t_exit)       # demand readout: ETH later buyers brought while we held (section 23.11)
    if readouts:
        state["timing"].append((first_sell, dumped, follow_eth))
    return ((out - gross) * state["eth_usd"] - gas_usd(), gross * state["eth_usd"], t_in, tier) + lab


def resolve_rpc(creator, deadline=3.0, lookback=40):
    """the curve from the factory's event: (token, curve, tk0, b_create) or None"""
    t0 = mono(); head = None; head_at = -1.0
    while mono() - t0 < deadline:
        try:
            if head is None or mono() - head_at > 0.15:                  # blocks are 100 ms apart: asking every 20 ms was fifty calls a launch (Sep 16 bill)
                try:
                    head = int(rpc_seat.call("eth_blockNumber", [], tries=1), 16)
                except Exception:
                    head = int(rpc_logs.call("eth_blockNumber", [], tries=1), 16)   # the provider down: the public node's head, and get_logs falls through to it too
                head_at = mono()
            for l in get_logs({"fromBlock": hex(head - lookback), "toBlock": "latest", "address": FACTORY_HEX}, seat=True):   # one try per node, 2 s timeout: this loop is the retry
                if len(l["topics"]) > 3 and ("0x" + l["topics"][3][-40:]).lower() == creator:
                    d = l["data"][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
                    return "0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:], w[2] / 1e18, int(l["blockNumber"], 16)
        except Exception:
            pass
        time.sleep(0.1)
    return None


def resolve_receipt(txh, creator, deadline=0.35):
    """5.43: the curve from the creation transaction's own receipt, a direct lookup by hash instead of a log scan (the 5.41 paper run
    spent 58-177 ms in the scan on the seats that matter, the same-block bundles). Polls the provider every 15 ms until the block is
    indexed; (token, curve, tk0, b_create) or None, and the caller falls back to resolve_rpc."""
    t0 = mono()
    while mono() - t0 < deadline:
        try:
            rec = rpc_seat.call("eth_getTransactionReceipt", [txh], tries=1)
        except Exception:
            rec = None
        if rec:
            for l in rec.get("logs", []):
                if l.get("address", "").lower() == FACTORY_HEX and len(l["topics"]) > 3 and ("0x" + l["topics"][3][-40:]).lower() == creator:
                    d = l["data"][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
                    return "0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:], w[2] / 1e18, int(rec["blockNumber"], 16)
            return None                                                    # the receipt exists but carries no creation by this creator: not ours
        time.sleep(0.015)
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
        ev = get_logs({"fromBlock": hex(b_create), "toBlock": hex(head), "address": curve, "topics": [[BUY_EV, SELL_EV]]})
        events = []; buyers = set()
        for e in ev:
            d = e["data"][2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]; buy = e["topics"][0] == BUY_EV
            events.append((int(e["blockNumber"], 16), int(e["logIndex"], 16), buy, w[0] if buy else w[1], w[1] if buy else w[0], w[2] if len(w) > 2 else 0.0))
            if buy and len(e["topics"]) > 2:
                buyers.add("0x" + e["topics"][2][-40:].lower())
        events.sort(key=lambda x: (x[0], x[1]))
        for sec, snd in (decision or {}).get("rivals", []):                # a counted rival that never bought is a reverted attempt: learn the sender
            if snd in buyers:
                state["reverters"].pop(snd, None)
            else:
                state["reverters"][snd] += 1
                if state["reverters"][snd] == 3:
                    log({"ev": "reverter_learned", "sender": snd, "note": "three counted attempts that never landed: this sender's attempts are no longer rivals"})
        info = {}
        r = exact_score(events, b_create, tk0, stake_usd / state["eth_usd"], SEAT, gated=BUNDLE_MIN > 0, stop_sell_frac=STOP_SELL_FRAC if STOP_SELL_FRAC > 0 else None, tp=TAKE_PROFIT if TAKE_PROFIT > 0 else None, info=info)
        if r is None:
            log({"ev": "score", "curve": curve, "result": "no usable launch-block buy"}); return
        roi_e1 = None                                                   # paper score of the E1 seat (the front of second one, every bundled launch), for the E1 plan
        try:
            r1 = exact_score(events, b_create, tk0, stake_usd / state["eth_usd"], "E1", gated=True, front=True, readouts=False, tp=TAKE_PROFIT if TAKE_PROFIT > 0 else None)
            if r1 is not None and r1[0] != "filtered" and r1[1] > 0:
                roi_e1 = round(r1[0] / r1[1], 4); state["scores_e1"].append(roi_e1)
        except Exception:
            pass
        if decision is not None and decision.get("race_ms") is not None:
            state["race_lags"].append(decision["race_ms"])
        if decision is not None:                                        # what the feed said at decision time vs what the chain says
            lab = r[-3:]
            log({"ev": "gate_check", "curve": curve, "feed": decision, "chain": {"bundle": lab[0], "bundle_eth": round(lab[1], 4), "out1": lab[2]}, "src": src})
        if len(state["schedule"]) >= 20 and sum(state["schedule"]) >= 10 and not state["rules_changed"]:
            state["rules_changed"] = True; log({"ev": "alarm", "what": "tax schedule changed: half of the last 20 scored launches show surcharges outside the known bands; trading stopped until restarted"})
        if r[0] == "filtered":
            log({"ev": "score", "curve": curve, "result": "outside the rule on the chain's reading", "roi_e1": roi_e1}); state["traded"].pop(curve, None); return
        state["rule_passing"].append(time.time())
        pnl, cost, t_in, tier = r[:4]; roi = pnl / cost
        landing = {}
        if SEAT == "E0" and decision is not None and decision.get("blocks_to_seat") is not None and decision.get("amount_in_eth"):
            # 5.44: the same launch scored at OUR estimated landing: the feed had shown blocks_to_seat blocks after the creation when we sent,
            # the feed trails the sequencer by about one block and the sequencer includes us in the block after the one it is building, so
            # two blocks past the last one seen; with the transaction's own amount and minimum output, so a buy the curve outran is a revert
            li = {}; t_land = (decision["blocks_to_seat"] + 2) / 9.9 + (PROVIDER_LAG_MS / 1000.0 if decision.get("detect") == "provider" else 0.0)
            r2 = exact_score(events, b_create, tk0, stake_usd / state["eth_usd"], SEAT, gated=False, tp=TAKE_PROFIT if TAKE_PROFIT > 0 else None, readouts=False,
                             t_entry=t_land, min_out=decision.get("min_out_tokens"), amount_in=decision["amount_in_eth"], info=li)
            if r2 is not None and r2[0] != "filtered":
                landing = {"roi_landing": round(r2[0] / r2[1], 4), "pnl_landing_usd": round(r2[0], 2), "t_landing": round(t_land, 2), "would_revert": bool(li.get("reverted")), "got_vs_min": li.get("got_vs_min")}
                roi = r2[0] / r2[1]; pnl = r2[0]; cost = r2[1]                        # the paper bankroll and the switch follow the landing score
        with lock:
            state["scores"].append(roi); sc = list(state["scores"])[-SWITCH_N:]; on = len(sc) < SWITCH_N or st.mean(sc) >= SWITCH
            traded = state["traded"].pop(curve, None)
            if traded is not None and SEND is None:                     # dry run: the paper bankroll follows the scores; live: the wallet balance (chain_loop)
                state["bankroll"] += min(traded, cost) * roi
        save_state()
        log({"ev": "score", "curve": curve, "roi": round(roi, 4), "roi_table": round(r[0] / r[1], 4), "roi_e1": roi_e1, "pnl_usd": round(pnl, 2), "cost_usd": round(cost, 2), "tier": round(tier, 4), "t_in_s": round(t_in, 2),
             "bot_first": bool(info.get("bot_first")), **landing,
             "n_scores": len(sc), "rolling_mean": round(st.mean(sc), 4), "switch_on": on, "traded_dry_run": traded is not None, "bankroll": round(state["bankroll"], 2)})
    except Exception as e:
        log({"ev": "error", "stage": "score", "err": str(e)[:200]})
    finally:
        state["watch"].pop(curve, None)


# ------------------------------------------------------------------------------------------------------------- trading
def wait_receipt(h, timeout=10.0, ans=None):
    """the receipt of h within timeout; None sooner when ans (the fire() answers) shows every endpoint refused the transaction"""
    t0 = mono()
    while mono() - t0 < timeout:
        if ans is not None and SENDER.rejected(ans):
            return None
        try:
            r = rpc.call("eth_getTransactionReceipt", [h])
            if r:
                return r
        except Exception:
            pass
        time.sleep(0.05)
    return None


def next_nonce():
    try:
        return int(rpc.call("eth_getTransactionCount", [WALLET, "pending"]), 16)
    except Exception:
        return state["nonce"]


def token_balance(token):
    try:
        return int(rpc.call("eth_call", [{"to": to_checksum_address(token), "data": "0x70a08231" + abi_word(WALLET)}, "latest"]), 16)
    except Exception:
        return None


def token_allowance(token, spender):
    try:
        return int(rpc.call("eth_call", [{"to": to_checksum_address(token), "data": "0xdd62ed3e" + abi_word(WALLET) + abi_word(spender)}, "latest"]), 16)
    except Exception:
        return None


def tx_approve(pos, nonce, cap):
    return {"to": to_checksum_address(pos["token"]), "value": "0x0", "data": "0x" + APPROVE_SEL + abi_word(pos["curve"]) + abi_word(2 ** 256 - 1), "gas": hex(GAS_APPROVE), "gasPrice": hex(int(cap)), "nonce": hex(nonce), "chainId": 4663}


def tx_sell(pos, amount_wei, nonce, cap):
    return {"to": to_checksum_address(pos["curve"]), "value": "0x0", "data": "0x" + SELL_SEL.hex() + abi_word(amount_wei) + abi_word(0) + abi_word(WALLET), "gas": hex(GAS_SELL), "gasPrice": hex(int(cap)), "nonce": hex(nonce), "chainId": 4663}


def send_confirmed(build, label, max_s):
    """live only: send build(cap, nonce) and wait for its receipt; no receipt within SELL_CONFIRM_S, or a refusal, means send again
    with a doubled cap at the next free nonce. 'nonce too low' from the sequencer means an earlier attempt landed: its receipt is
    fetched. Returns (receipt, hash), (None, last hash) after max_s."""
    t0 = mono(); cap = (state.get("base_fee") or state["gas_price"] or 10 ** 8) * SELL_GAS_HEADROOM; hashes = []; attempt = 0
    nonce = next_nonce()                                                 # the SAME nonce every attempt: a fee bump replaces the stuck transaction; a new nonce would queue behind it and both would land (audit, Sep 16)
    cap_max = max(cap, int(SELL_FEE_MAX_USD / max(state["eth_usd"], 1.0) * 1e18 / max(GAS_SELL, 1)))
    while mono() - t0 < max_s:
        attempt += 1; h = submit(build(min(cap, cap_max), nonce), label); ans = SENDER.mine() or []
        if h:
            hashes.append(h); rec = wait_receipt(h, SELL_CONFIRM_S, ans)
            if rec:
                return rec, h
        txt = " ".join(str(d) for _, d in SENDER.answers(ans, 0.2))
        if "nonce too low" in txt:                                       # an earlier attempt is already mined: find its receipt, and move on if it was not ours
            for hh in hashes:
                rec = wait_receipt(hh, 1.0)
                if rec:
                    return rec, hh
            nonce = next_nonce()
        elif "already known" in txt:                                     # the same transaction is still in the pool: raise the fee and re-send at the same nonce
            pass
        if not h:
            time.sleep(0.2)
        cap = min(cap * 2, cap_max)
        log({"ev": "resend", "label": label, "attempt": attempt + 1, "nonce": nonce, "cap_gwei": round(cap / 1e9, 4), "max_fee_usd": round(cap * GAS_SELL / 1e18 * state["eth_usd"], 3), "hashes": len(hashes)})
    return None, (hashes[-1] if hashes else None)


def ensure_approved(pos, amount_wei, max_s):
    """the curve pulls the tokens with transferFrom (a sell without an allowance reverts with ERC20InsufficientAllowance, checked on
    the chain), so the approve must have landed before the sell: its receipt, else the allowance itself, else a fresh approve"""
    h = pos.get("approve_hash"); rec = wait_receipt(h, 1.0) if h else None
    if rec and rec.get("status") == "0x1":
        return True
    al = token_allowance(pos["token"], pos["curve"])
    if al is not None and al >= amount_wei:
        return True
    log({"ev": "approve_missing", "curve": pos["curve"], "approve_hash": h, "allowance": al, "note": "sending the approve again with a high cap"})
    rec, h2 = send_confirmed(lambda cap, nonce: tx_approve(pos, nonce, cap), "approve", max_s)
    if h2:
        pos["approve_hash"] = h2
    if rec and rec.get("status") == "0x1":
        return True
    al = token_allowance(pos["token"], pos["curve"])
    return al is not None and al >= amount_wei


def watch_approve(pos):
    """live: says in the log whether the approve landed inside the hold; close_position re-sends it if not"""
    rec = wait_receipt(pos["approve_hash"], max(1.0, HOLD - 1.0)); pos["approve_ok"] = bool(rec and rec.get("status") == "0x1")
    if not pos["approve_ok"]:
        log({"ev": "approve_not_seen", "curve": pos["curve"], "hash": pos["approve_hash"], "status": rec.get("status") if rec else None})


def close_position(pos, why):
    """sell the position; used by the hold and by crash recovery. Dry run: logs the approve and sell it would send. Live: the
    approve is confirmed first (receipt, allowance, or a fresh approve), the amount is the wallet's real token balance, the sell
    is sent and re-sent with rising caps until its receipt is in, a reverted sell is diagnosed (allowance, balance) and retried,
    and a position whose sell cannot be confirmed within SELL_MAX_S stays open (no new trade is taken) while a background
    retry keeps trying every 5 s and an alarm is logged. The engine never forgets a position."""
    if SEND is None or pos.get("buy_hash") is None:                 # dry run: the transactions as they would be sent
        gp = state["gas_price"] or 0; nonce = pos["nonce"]
        if not pos.get("approved"):
            pos["approve_hash"] = submit(tx_approve(pos, nonce + 1, gp), "approve"); pos["approved"] = True
        hs = submit(tx_sell(pos, int(pos["tokens"] * 1e18), nonce + 2, gp), "sell")
        log({"ev": "trade_done", "curve": pos["curve"], "tokens_sold": pos["tokens"], "held_s": round(mono() - pos["t_buy"], 2), "exit": why, "dry_run": True,
             "buy_hash": pos.get("buy_hash"), "approve_hash": pos.get("approve_hash"), "sell_hash": hs, "seat_ts": pos.get("seat_ts")})
        state["open"] = None; save_state(); return
    with lock:
        if pos.get("closing"):
            return
        pos["closing"] = True
    try:
        if pos["token"] == pos["curve"]:                                  # the token was unknown at the buy: find it now, an approve on the curve reverts
            r = resolve_rpc(pos.get("creator", ""), deadline=2.0, lookback=400)
            if r:
                pos["token"] = r[0]; log({"ev": "token_resolved_at_exit", "curve": pos["curve"], "token": r[0]})
            else:
                log({"ev": "alarm", "what": "token still unknown at the exit: the sell will revert until it is found (every retry re-resolves)", "curve": pos["curve"]})
        t0 = mono(); bal = token_balance(pos["token"]); amount = bal if bal else int(pos["tokens"] * 1e18)
        if bal == 0 and pos.get("sell_hash"):
            log({"ev": "trade_done", "curve": pos["curve"], "tokens_sold": pos["tokens"], "held_s": round(mono() - pos["t_buy"], 2), "exit": why, "dry_run": False, "note": "balance already zero: an earlier sell landed",
                 "buy_hash": pos.get("buy_hash"), "approve_hash": pos.get("approve_hash"), "sell_hash": pos.get("sell_hash"), "seat_ts": pos.get("seat_ts")})
            state["open"] = None; save_state(); return
        if not ensure_approved(pos, amount, SELL_MAX_S / 2):
            log({"ev": "alarm", "what": "approve not confirmed: the sell would revert; retrying in the background", "curve": pos["curve"]})
            threading.Timer(5.0, close_position, args=(pos, "retry after approve")).start(); return
        for _ in range(3):
            rec, hs = send_confirmed(lambda cap, nonce: tx_sell(pos, amount, nonce, cap), "sell", max(2.0, SELL_MAX_S - (mono() - t0)))
            if hs:
                pos["sell_hash"] = hs; save_state()
            if rec and rec.get("status") == "0x1":
                log({"ev": "trade_done", "curve": pos["curve"], "tokens_sold": amount / 1e18, "held_s": round(mono() - pos["t_buy"], 2), "exit": why, "dry_run": False, "sell_confirm_s": round(mono() - t0, 2),
                     "buy_hash": pos.get("buy_hash"), "approve_hash": pos.get("approve_hash"), "sell_hash": hs, "seat_ts": pos.get("seat_ts")})
                state["open"] = None; save_state(); return
            if rec:                                                  # landed and reverted: find out why and fix it
                bal = token_balance(pos["token"]); al = token_allowance(pos["token"], pos["curve"])
                log({"ev": "sell_reverted", "curve": pos["curve"], "hash": hs, "balance": bal, "allowance": al})
                if bal == 0:
                    log({"ev": "trade_done", "curve": pos["curve"], "tokens_sold": amount / 1e18, "held_s": round(mono() - pos["t_buy"], 2), "exit": why, "dry_run": False, "note": "reverted sell but the balance is zero",
                         "buy_hash": pos.get("buy_hash"), "approve_hash": pos.get("approve_hash"), "sell_hash": hs, "seat_ts": pos.get("seat_ts")})
                    state["open"] = None; save_state(); return
                if bal:
                    amount = bal
                if al is not None and al < amount and not ensure_approved(pos, amount, 5.0):
                    break
            if mono() - t0 > SELL_MAX_S:
                break
        log({"ev": "alarm", "what": f"sell not confirmed after {round(mono() - t0, 1)} s: position stays open, retrying every 5 s; check the wallet and the endpoints", "curve": pos["curve"], "sell_hash": pos.get("sell_hash")})
        threading.Timer(5.0, close_position, args=(pos, "retry")).start()
    finally:
        pos["closing"] = False


def handle_creation(creator, quote, init_buy_wei, seen_at, feed_ts, named, blk0, tax_bps=None, txh=None, known=None):
    """the launch thread, guarded: an exception here used to kill the thread silently, and if it happened after the buy the
    tokens were never sold and the 'position open' gate blocked every later trade for good (audit, Sep 16)."""
    try:
        _handle_creation(creator, quote, init_buy_wei, seen_at, feed_ts, named, blk0, tax_bps, txh, known)
    except Exception as e:
        pos = state["open"]
        log({"ev": "alarm", "what": "the launch thread crashed", "err": str(e)[:200], "where": traceback.format_exc().strip().splitlines()[-2][:160],
             "creator": creator, "position_open": pos is not None})
        if pos is not None and not pos.get("closing"):
            threading.Thread(target=close_position, args=(pos, "the launch thread crashed after the buy"), daemon=True).start()
        else:
            release_reservation()


def release_reservation():
    """give the nonce back and make the next launch wait for a fresh one from the chain, so a reserved-but-unused nonce
    cannot leave a gap that strands every later transaction in the pool (audit, Sep 16)."""
    with lock:
        state["nonce"] = None; state["chain_at"] = 0.0; state["busy_until"] = 0.0


def _handle_creation(creator, quote, init_buy_wei, seen_at, feed_ts, named, blk0, tax_bps=None, txh=None, known=None):
    """resolve the curve, apply the gates, size on the feed-tracked curve, take the seat, build the buy, then approve and sell"""
    curve = token = None; tk0 = None; b_create = None; src = None; named = set(named)
    new_day_check()
    with lock:
        prior = state["launched_today"][creator]; state["launched_today"][creator] += 1
    if SEAT in ("E0", "E1", "E2") and BUNDLE_MIN > 0 and (quote != ZERO or len(named) < BUNDLE_MIN):
        log({"ev": "skip", "why": ["cannot pass the rule from the calldata (quote or named wallets): not resolved"], "creator": creator, "named_wallets": len(named), "quote": quote}); return

    def count_cands():
        cands = collections.Counter()
        try:
            for cv, lst in list(state["buys"].items()):
                if cv in state["known_curves"]:
                    continue
                cands[cv] += sum(1 for b in list(lst) if b[1] in named and b[0] >= feed_ts)      # (ts, sender, value, seen, block, to, selector)
        except RuntimeError:
            pass
        return cands
    if SEAT in ("E1", "E2") and BUNDLE_MIN > 0:
        cands = count_cands()                                              # direct named buys already on the feed name the curve at once; a bundle through a
        if cands:                                                          # helper call (every bundle since Sep 17) is read by the shared wait below (5.52)
            a, c = cands.most_common(1)[0]
            if c >= BUNDLE_MIN:
                curve = a; src = "feed"
                net0 = init_buy_wei / 1e18 * 0.99; tk0 = Y0 - X0 * Y0 / (X0 + net0) if net0 > 0 else 0.0
    bundle_wait_ms = None; helper_folded = 0

    def named_txs(within=9):
        """the named wallets' transactions from the creation block on, whatever contract they call: direct curve buys (state['buys'])
        and value-carrying calls to helper contracts (state['valtx'], sender recovered here and cached). On Sep 17 every bundle went
        through a helper contract, invisible to a count of direct curve buys (report 24.16). [(ts, sender, val, blk, to, sel, data, helper)]"""
        out = []
        try:
            for cv, lst in list(state["buys"].items()):
                for x in list(lst):
                    if x[1] in named and x[0] >= feed_ts and (blk0 is None or len(x) < 5 or x[4] is None or blk0 <= x[4] <= blk0 + within):
                        out.append((x[0], x[1], x[2], x[4] if len(x) > 4 else None, x[5] if len(x) > 5 else None, x[6] if len(x) > 6 else None, None, False, frozenset([x[1]])))
            for e in list(state["valtx"]):
                blk = e[6] if len(e) > 6 else None
                if e[1] < feed_ts or e[3] < 0.005 or (blk0 is not None and blk is not None and not blk0 <= blk <= blk0 + within):
                    continue
                buyers = named_in(e[4], named)                                 # the recipients a helper call names (24.18)
                if e[2] is None:
                    try:
                        e[2] = sender_of(e[5])
                    except Exception:
                        e[2] = "?"
                if e[2] in named:
                    buyers = buyers | {e[2]}
                if buyers:
                    out.append((e[1], e[2], e[3], blk, e[7] if len(e) > 7 else None, e[8] if len(e) > 8 else None, e[4], True, frozenset(buyers)))
        except RuntimeError:
            pass
        return out

    chain_rows = None

    def chain_bundle(cv, b0):
        """the lean provider path (5.47): the curve's Buy events since the creation, one log read; exempt buys inside the block window are
        the bundle (the tables' definition), the rest are outsiders. (count, eth, exempt rows, taxed rows, tier, last block); rows are
        (ts, sender, val, blk, fee)"""
        ev = get_logs({"fromBlock": hex(b0), "toBlock": "latest", "address": cv, "topics": [[BUY_EV]]}, seat=True)
        ev = sorted(ev, key=lambda e: (int(e["blockNumber"], 16), int(e.get("logIndex", "0x0"), 16)))
        X, Y = X0, Y0; tier = None; ex = []; tx = []; last = b0
        for i, e in enumerate(ev):
            d = e["data"][2:]; w = [int(d[k:k + 64], 16) / 1e18 for k in range(0, len(d), 64)]; blk = int(e["blockNumber"], 16); last = max(last, blk)
            q, tk = w[0], w[1]
            if tk <= 0 or tk >= Y or q <= 0:
                continue
            net = X * tk / (Y - tk); fee = 1 - net / q; X += net; Y -= tk
            if i == 0:
                tier = fee; continue                                       # the creator's own buy: the token's tier
            snd = ("0x" + e["topics"][2][-40:].lower()) if len(e["topics"]) > 2 else creator
            (ex if (abs(fee - tier) <= 0.0008 and blk - b0 <= E0_BUNDLE_MAX_BLOCKS) else tx).append((feed_ts, snd, q, blk, fee))
        return len(ex), sum(r[2] for r in ex), ex, tx, tier, last

    if SEAT == "E0" and BUNDLE_MIN > 0 and known is not None:
        # 5.47: the lean provider path. The factory event already names the curve; the bundle is read from the curve's own Buy events,
        # polled until it is complete or the wait runs out. No raw transactions here, so the named wallets are not the test: the tables'
        # exempt-buy definition is, the same one the scorer applies.
        token, curve, tk0, b_create = known; src = "log"; c = 0; eth = 0.0
        while mono() - seen_at < E0_BUNDLE_WAIT_S + (PROVIDER_LAG_MS / 1000.0):
            try:
                c, eth, ex, tx, tier_seen, last = chain_bundle(curve, b_create); chain_rows = (ex, tx, last)
            except Exception as e:
                c, eth = 0, 0.0
            if c >= BUNDLE_MIN and eth >= BUNDLE_MIN_ETH:
                break
            time.sleep(0.08)
        if c < BUNDLE_MIN or eth < BUNDLE_MIN_ETH:
            log({"ev": "skip", "why": [f"bundle not on the chain within {1000 * E0_BUNDLE_WAIT_S:.0f} ms and {E0_BUNDLE_MAX_BLOCKS} blocks (provider path: {c} exempt buys, {eth:.3f} ETH)"], "creator": creator,
                 "named_wallets": len(named), "tax_bps": tax_bps, "wait_ms": round((mono() - seen_at) * 1000), "detect": "provider"}); return
        bundle_wait_ms = round((mono() - seen_at) * 1000)
        with cond:
            state["blocks"] = max(state["blocks"], chain_rows[2])           # the chain's progress as the log read saw it: blocks_to_seat is real
    elif SEAT in ("E0", "E1", "E2") and BUNDLE_MIN > 0 and curve is None and known is None:
        # 5.52: every seat on the feed path resolves the curve the same way: the creation receipt (or the log scan) in a thread from the
        # first millisecond, the bundle counted in buyers from direct buys and helper calls (24.18). Before 5.52 the E1/E2 path waited
        # for direct named buys that today's single-transaction bundles never make, so it resolved the curve only when the next second
        # opened on the feed: after the moment an E1 send has to leave.
        # 5.3-5.4: the creation-second seat enters only once the bundle is VISIBLE on the feed, never ahead of it (report 24.15); the bundle
        # is the named wallets' transactions in the creation block and the next nine, direct or through a helper contract (24.16). The chain
        # resolve of the curve starts in the first millisecond and runs while the bundle is awaited; the send goes out when both are in hand.
        box = {}

        def resolve_bg():
            try:
                r = resolve_receipt(txh, creator) if txh else None
                box["src"] = "receipt" if r else "rpc"
                box["r"] = r or resolve_rpc(creator)
            except Exception as e:
                box["r"] = None; log({"ev": "error", "stage": "e0_resolve", "err": str(e)[:200]})
            with cond:
                cond.notify_all()
        threading.Thread(target=resolve_bg, daemon=True).start()
        def bundle_view():
            """(count, ETH, the curve the direct buys name or None): the helper calls plus the direct buys of ONE curve, the first meeting
            both floors, else the best by (buys, ETH); stale buys of the same wallets on an earlier, unresolved curve are not mixed in"""
            tx = named_txs(E0_BUNDLE_MAX_BLOCKS); helpers = [t for t in tx if t[7]]; by = collections.defaultdict(lambda: [0, 0.0])
            for t in tx:
                if not t[7] and t[4] is not None and t[4] not in state["known_curves"]:
                    by[t[4]][0] += 1; by[t[4]][1] += t[2]
            best = None
            for cv_, (n_, e_) in by.items():
                if n_ >= BUNDLE_MIN and e_ >= BUNDLE_MIN_ETH:
                    best = (cv_, n_, e_); break
                if best is None or (n_, e_) > (best[1], best[2]):
                    best = (cv_, n_, e_)
            hb = set().union(*[t[8] for t in helpers]) if helpers else set()   # distinct buyers across the helper calls (one call, thirteen buyers: 24.18)
            return len(hb) + (best[1] if best else 0), sum(t[2] for t in helpers) + (best[2] if best else 0.0), best
        c, eth, best = bundle_view()
        while (c < BUNDLE_MIN or eth < BUNDLE_MIN_ETH) and mono() - seen_at < E0_BUNDLE_WAIT_S:
            with cond:
                cond.wait(0.02)
            c, eth, best = bundle_view()
        if c < BUNDLE_MIN or eth < BUNDLE_MIN_ETH:
            log({"ev": "skip", "why": [f"bundle not visible on the feed within {1000 * E0_BUNDLE_WAIT_S:.0f} ms and {E0_BUNDLE_MAX_BLOCKS} blocks ({c} named buyers, {eth:.3f} ETH)"], "creator": creator,
                 "named_wallets": len(named), "tax_bps": tax_bps, "wait_ms": round((mono() - seen_at) * 1000)}); return
        bundle_wait_ms = round((mono() - seen_at) * 1000)
        if best is not None and best[1] >= BUNDLE_MIN:
            curve = best[0]; src = "feed"                                     # a direct bundle names the curve: no need to wait for the chain
            net0 = init_buy_wei / 1e18 * 0.99; tk0 = Y0 - X0 * Y0 / (X0 + net0) if net0 > 0 else 0.0
        else:
            while "r" not in box and mono() - seen_at < E0_BUNDLE_WAIT_S + 1.5:
                with cond:
                    cond.wait(0.02)
            r = box.get("r")
            if r:
                token, curve, tk0, b_create = r; src = box.get("src", "rpc")
    elif curve is None and known is not None:
        token, curve, tk0, b_create = known; src = "log"
        if SEAT in ("E1", "E2"):
            log({"ev": "skip", "why": "provider path: only the creation-second seat runs on it (no block clock for the seat's second)", "creator": creator}); return
    elif curve is None:
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
    w = watch_curve(curve, tk0, feed_ts, named, creator, blk0, tax_bps)  # from here the feed loop folds every buy and sell of this curve as it arrives
    for t in named_txs():                                                # the named wallets' helper-contract calls: the bundle a direct-buy count cannot see (24.16)
        if t[7] and not (t[6] is not None and w["cb"] in t[6]):              # a helper that names the curve was already seeded by curve_buys
            fold_buy(w, t[0], t[1], t[2], t[3], t[4], t[5], buyers=t[8]); helper_folded += len(t[8])
    if chain_rows is not None:                                            # the lean provider path: the chain's exempt buys are the bundle, the taxed ones outsiders
        for ts_, snd, val, blk, fee in chain_rows[0]:
            fold_buy(w, ts_, creator, val, blk, curve, None); helper_folded += 1
        for ts_, snd, val, blk, fee in chain_rows[1]:
            fold_buy(w, ts_, snd, val, blk, curve, None)
    if token:
        w["tb"] = bytes.fromhex(token[2:])
    else:
        def learn_token():
            r = resolve_rpc(creator, deadline=1.5, lookback=40)
            if r and r[1].lower() == curve:
                w["tb"] = bytes.fromhex(r[0][2:])
        threading.Thread(target=learn_token, daemon=True).start()
    curve_cs = to_checksum_address(curve)
    # the seat's wait: the bundle and second one must be fully visible before the gates are read
    send_mode = None
    if SEAT in ("E1", "E2"):
        send_mode = wait_for_second(feed_ts, SEAT_SECONDS[SEAT], seen_at, watch=w)
    elif SEAT == "E0":
        send_mode = "e0"                                                  # the creation second: no wait, every 100 ms costs 3-5 points
    t_wake = mono()
    decision = {"bundle": w["bundle"], "bundle_wallets": len(w["wallets"]), "bundle_eth": round(w["bundle_eth"], 4), "out1": w["out1"], "out2": w["out2"], "out1_chain": w["out1_chain"], "out2_chain": w["out2_chain"], "race_ms": w.get("race_ms"), "blocks_to_seat": state["blocks"] - blk0, "rivals": list(w["rivals"]),
                "tax_bps": w.get("tax_bps"), "team_share": round((Y0 - w["Y"]) / Y0, 4), "bundle_wait_ms": bundle_wait_ms, "bundle_helper": helper_folded, "detect": state.get("detect", "sequencer")}
    with lock:
        sc = list(state["scores"])[-SWITCH_N:]; on = len(sc) < SWITCH_N or st.mean(sc) >= SWITCH
        stake_usd = min(STAKE_MAX, max(STAKE_MIN, state["bankroll"] * FRAC)); gates = []
        if w["bundle"] < BUNDLE_MIN:
            gates.append(f"bundle {w['bundle']} < {BUNDLE_MIN}")
        if w["bundle_eth"] < BUNDLE_MIN_ETH:
            gates.append(f"bundle {w['bundle_eth']:.3f} ETH < {BUNDLE_MIN_ETH}")
        if BUNDLE_MAX_ETH > 0 and w["bundle_eth"] > BUNDLE_MAX_ETH:
            gates.append(f"bundle {w['bundle_eth']:.3f} ETH > {BUNDLE_MAX_ETH}")
        team_share = (Y0 - w["Y"]) / Y0; tb = w.get("tax_bps")           # the team's share of supply after its launch-block buys; the token's own tax (24.14)
        if TIER_MIN_BPS > 0 and (tb is None or tb < TIER_MIN_BPS):
            gates.append(f"token tax {tb} bps < {TIER_MIN_BPS}" if tb is not None else "token tax unknown (calldata layout)")
        if TIER_MAX_BPS > 0 and (tb is None or tb > TIER_MAX_BPS):
            gates.append(f"token tax {tb} bps > {TIER_MAX_BPS}" if tb is not None else "token tax unknown (calldata layout)")
        if SKIP_TIER1_TEAM_SHARE > 0 and (tb or 0) == 0 and team_share >= SKIP_TIER1_TEAM_SHARE:
            gates.append(f"1%-tier token with the team holding {100*team_share:.0f}% >= {100*SKIP_TIER1_TEAM_SHARE:.0f}% (the worst class, 24.14)")
        if SEAT == "E2" and w["out1"] + w["out1_chain"] > OUT1_MAX:
            gates.append(f"{w['out1']} outsider buys in second one > {OUT1_MAX}" + (f" (+{w['out1_chain']} seen on the chain)" if w["out1_chain"] else ""))
        if SEAT == "E2" and w["out2"] + w["out2_chain"] > OUT2_MAX:
            gates.append(f"{w['out2']} outsider buys in the seat's second before our send > {OUT2_MAX}" + (f" (+{w['out2_chain']} seen on the chain)" if w["out2_chain"] else ""))
        if not on:
            gates.append(f"safety switch off (rolling {st.mean(sc):+.3f} over {len(sc)} < {SWITCH:+.2f})")
        if state["stopped"] or state["bankroll"] < (1 - DAILY_STOP) * state["day_start"]:
            state["stopped"] = True; gates.append("daily stop")
        if state["rules_changed"]:
            gates.append("tax schedule changed (alarm): not trading")
        if mono() < state["busy_until"] or state["open"] is not None:
            gates.append("position open")
        resolve_lim = max(MAX_RESOLVE_MS, int(1000 * E0_BUNDLE_WAIT_S) + 150) if BUNDLE_MIN > 0 else MAX_RESOLVE_MS   # the resolve includes the wait for the bundle (5.52: every seat)
        if resolve_ms > resolve_lim:
            gates.append(f"resolved in {resolve_ms} ms > {resolve_lim}")
        if state["bankroll"] < STAKE_MIN:
            gates.append("bankroll below the minimum stake")
        if not hours_ok():
            gates.append(f"outside trading hours {TRADE_HOURS} UTC (hours the tables never measured)")
        if MIN_RULE_PASSING_1H > 0 and sum(1 for t in state["rule_passing"] if time.time() - t < 3600) < MIN_RULE_PASSING_1H:
            gates.append(f"fewer than {MIN_RULE_PASSING_1H} rule-passing launch scored in the last hour (dead stretch)")
        if MIN_FOLLOW_ETH_60 > 0:                                        # fail closed: no trade until the demand readout exists and clears the floor
            tm = list(state["timing"])
            if len(tm) < DEMAND_ARM_N:
                gates.append(f"demand readout not armed yet ({len(tm)} of {DEMAND_ARM_N} scored clean launches since start)")
            else:
                fe = st.mean(c for a, b, c in tm)
                if fe < MIN_FOLLOW_ETH_60:
                    gates.append(f"demand {fe:.3f} ETH over the last {len(tm)} scored launches < {MIN_FOLLOW_ETH_60} (below the tables' range)")
        if send_mode is None and SEAT in ("E1", "E2"):
            gates.append("seat's second not seen in time (stale feed): not sending")
        if SEAT == "E0" and state.get("detect") == "provider" and not E0_ALLOW_PROVIDER:
            gates.append("detection on the provider path (the sequencer feed is down): a send this late is second one, not the seat (E0_ALLOW_PROVIDER=1 after measuring the lag)")
        if state["nonce"] is None or mono() - state["chain_at"] > 30:
            gates.append("nonce/gas not fresh (RPC)")
        if SEND is not None and MAX_LIVE_TRADES > 0 and state.get("live_trades", 0) >= MAX_LIVE_TRADES:
            gates.append(f"live trade cap reached ({state.get('live_trades', 0)} of {MAX_LIVE_TRADES} since the start): not sending")
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
    h = submit(buy, "buy"); t_buy = mono(); tokens = tk; p_in = (X + net) / (Y - tk); buy_ans = SENDER.mine()
    if h:
        state["live_trades"] = state.get("live_trades", 0) + 1                # a real buy left the box (the cap counts sends, not fills)
    decision["amount_in_eth"] = amount_in / 1e18; decision["min_out_tokens"] = min_out / 1e18        # for the scorer's revert check (5.44)
    state["traded"][curve] = min(stake_usd, gross * state["eth_usd"]); state["decisions"][curve] = decision
    threading.Thread(target=score_launch, args=(curve, tk0, b_create, stake_usd, creator, src, decision), daemon=True).start()
    p_creator = (X0 + X0 * tk0 / (Y0 - tk0)) / (Y0 - tk0)
    log({"ev": "trade_decision", "seat": SEAT, "curve": curve, "token": token, "creator": creator, "resolve_ms": resolve_ms, "resolve_src": src, "named_wallets": len(named), **decision,
         "sent_ms": round((t_buy - seen_at) * 1000), "wake_to_send_ms": round((t_buy - t_wake) * 1000, 2), "send_mode": send_mode, "feed_ts_at_send": state["feed_ts"], "seat_ts": feed_ts + SEAT_SECONDS.get(SEAT, 0),
         "seat_flip_to_send_ms": round((t_buy - state["flip_at"][feed_ts + SEAT_SECONDS[SEAT]]) * 1000, 1) if (feed_ts + SEAT_SECONDS.get(SEAT, 0)) in state["flip_at"] else None,
         "stake_usd": stake_usd, "tokens_target": tk, "supply_share": tk / Y0, "fee_assumed": fee, "price_vs_creator": round((X / Y) / p_creator, 3),
         "margin_ms": MARGIN_MS if send_mode and send_mode.startswith("predict") else None})
    if h:                                                            # live: the tokens actually received, from the buy's own event
        rec = wait_receipt(h, ans=buy_ans)
        if rec is None and buy_ans and SENDER.rejected(buy_ans):
            log({"ev": "buy_rejected", "curve": curve, "hash": h, "answers": [(hh, str(d)[:120]) for hh, d in buy_ans]})
            state["traded"].pop(curve, None); release_reservation(); return
        if rec:
            if SEAT in ("E1", "E2"):
                threading.Thread(target=tune_margin, args=(rec, feed_ts + SEAT_SECONDS[SEAT]), daemon=True).start()
            if rec.get("status") != "0x1":
                log({"ev": "buy_reverted", "curve": curve, "hash": h}); state["traded"].pop(curve, None); release_reservation(); return
            for l in rec.get("logs", []):
                if l["topics"][0] == BUY_EV and l["address"].lower() == curve:
                    tokens = int(l["data"][2 + 64:2 + 128], 16) / 1e18
            t_buy = mono()
        else:
            log({"ev": "receipt_timeout", "curve": curve, "hash": h, "note": "assuming the buy landed: approving and selling the sized amount"})
    if token is None:
        tb = w.get("tb")
        if tb is not None:
            token = "0x" + tb.hex()                                       # learn_token already found it
        else:
            r = resolve_rpc(creator, deadline=HOLD - 1, lookback=120); token = r[0] if r else curve
            if not r:
                log({"ev": "alarm", "what": "token address unknown at the exit: approving on the curve will revert; close_position re-resolves on every retry", "curve": curve})
    pos = {"curve": curve, "token": token, "creator": creator, "tokens": tokens, "nonce": nonce, "t_buy": t_buy, "buy_hash": h, "approved": False, "seat_ts": feed_ts + SEAT_SECONDS.get(SEAT, 0)}
    state["open"] = pos; save_state()
    cap = (state.get("base_fee") or gas_price or 0) * SELL_GAS_HEADROOM if h else (gas_price or 0)
    pos["approve_hash"] = submit(tx_approve(pos, nonce + 1, cap), "approve"); pos["approved"] = True; save_state()
    if pos["approve_hash"]:
        threading.Thread(target=watch_approve, args=(pos,), daemon=True).start()
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
    for cv in list(state["sells"]):                                      # the same age-out for sells: only traded curves were pruned before, so the rest grew for ever (audit, Sep 16)
        if cv not in state["known_curves"] and state["sells"][cv] and now - state["sells"][cv][-1][0] > 120:
            state["sells"].pop(cv, None)
    held = (state["open"] or {}).get("curve")
    for cv, w in list(state["watch"].items()):                           # a launch thread that died before scoring used to leave its curve watched for ever, and every watched curve is scanned against every transaction
        if cv != held and now - w["since"] > 180:
            state["watch"].pop(cv, None); state["decisions"].pop(cv, None)
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
                state["buys"][to_hex].append((ts, snd, val, seen, state["blocks"], to_hex, sel.hex()))
                if to_hex in watched:
                    fold_buy(watched[to_hex], ts, snd, val, state["blocks"], to_hex, sel.hex())
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
                tax_bps = tax_bps_of(sel, words)
                log({"ev": "creation", "creator": creator, "quote": quote, "init_buy_eth": init_buy / 1e18, "feed_ts": ts, "named_wallets": len(named), "selector": sel.hex(), "tx_type": ty, "tax_bps": tax_bps})
                threading.Thread(target=handle_creation, args=(creator, quote, init_buy, seen, ts, named, state["blocks"]), kwargs={"tax_bps": tax_bps, "txh": "0x" + keccak(t).hex()}, daemon=True).start(); continue
            if val > 0 and len(data) >= 36:                                         # a router buy of some curve: sender recovered only if it names a curve we trade
                e = [seen, ts, None, val, data, t, state["blocks"], to_hex, sel.hex()]; state["valtx"].append(e)
                for cv, w in list(watched.items()):                                  # a snapshot: the score and creation threads add and pop watched curves while this loop runs
                    if w["cb"] in data or (w["tb"] is not None and w["tb"] in data):    # a router names the curve or the token (Sep 11: a router buying by token was invisible)
                        e[2] = sender_of(t); bs = named_in(data, w["named"])
                        fold_buy(w, ts, e[2], val, state["blocks"], to_hex, sel.hex(), buyers=(bs | ({e[2]} if e[2] in w["named"] else set())) or None)
                continue
            if watched and val == 0 and sel not in (BUY_SEL, SELL_SEL):
                for cv, w in list(watched.items()):                                  # a snapshot: the score and creation threads add and pop watched curves while this loop runs
                    if w["cb"] in data or (w["tb"] is not None and w["tb"] in data):    # a value-less call naming a curve we watch: a router sell, or a router buy paid in tokens
                        if sel.hex() == APPROVE_SEL or to_hex == cv:
                            continue                                                             # our own approve names the curve in its calldata: reading it as a sell fired the dump exit instantly (audit, Sep 16)
                        if ts - w["ts0"] in (1, 2):
                            fold_buy(w, ts, sender_of(t), 0.0, state["blocks"], to_hex, sel.hex())   # counted as a rival (section 23.11: a 0.001 ETH router buy the feed missed)
                        if sender_of(t) != WALLET.lower():
                            fold_sell(w, float("inf") if STOP_SELL_FRAC > 0 else 0.0)
        except Exception as e:
            log({"ev": "error", "stage": "decode", "err": str(e)[:200]})


def second_of_block(bn):
    """the chain second a block belongs to, from the feed's own bookkeeping: flip_block[ts] is the first block of second ts
    (the feed's sequenceNumber is the L2 block number, checked at 40 second boundaries on Sep 16). None while the feed has
    not passed the block yet, or when the second is older than what is kept."""
    if bn > state["feed_seq"]:
        return None
    best = None
    for t, b in list(state["flip_block"].items()):
        if b is not None and b <= bn and (best is None or t > best):
            best = t
    return best


async def chain_rivals_loop(websockets):
    """sequencer mode, PROVIDER_WS set: the provider's Buy events on watched curves are a second source of rivals. A landed buy by a
    wallet that is not the team's, in second one or two, counts whatever router sent it: the feed decoder only sees routers that
    name the curve or the token in their calldata (Sep 11 21:47: a router buying by token hid a second-one bot, -68%).
    One log subscription per watched curve, opened when the watch starts and dropped when it ends, and no block heads: the first
    version (4.95-4.99) subscribed to every Buy on the chain plus every head, 1.7 million messages and 2.9 GB a day, which is
    what ran the Sep 12 Alchemy plan dry. The second a Buy landed in comes from the feed's flip bookkeeping (second_of_block);
    a Buy the feed has not passed yet waits up to 2 s and is dropped, never assigned to the current second."""
    backoff = 0.2
    def count(res, sec):
        curve = res["address"].lower(); w = state["watch"].get(curve)
        if w is None or sec not in (1, 2):
            return
        who = "0x" + res["topics"][2][-40:].lower()
        if who in w["named"] or who == w["creator"] or who == WALLET.lower():
            return
        val = int(res["data"][2:66], 16) / 1e18
        with cond:
            w["out%d_chain" % sec] += 1; cond.notify_all()
        log({"ev": "rival_chain", "curve": curve, "second": sec, "buyer": who, "value": round(val, 4), "block": int(res["blockNumber"], 16), "feed_out": w["out1"] if sec == 1 else w["out2"]})
    def place(res):
        w = state["watch"].get(res["address"].lower())
        if w is None:
            return True
        ts = second_of_block(int(res["blockNumber"], 16))
        if ts is None:
            return False
        count(res, ts - w["ts0"]); return True
    while True:
        try:
            async with websockets.connect(PROVIDER_WS, open_timeout=10, max_size=None, ping_interval=10, ping_timeout=5, max_queue=16, compression=None) as ws:
                log({"ev": "chain_rivals_connected"}); backoff = 0.2
                subs = {}; pending = {}; held = collections.deque(); rid = 1
                while True:
                    want = set(state["watch"])                            # one subscription per watched curve, while it is watched
                    for cv in want - set(subs):
                        rid += 1; pending[rid] = cv; subs[cv] = None
                        await ws.send(json.dumps({"jsonrpc": "2.0", "id": rid, "method": "eth_subscribe", "params": ["logs", {"address": cv, "topics": [[BUY_EV]]}]}))
                    for cv in [c for c in subs if c not in want]:
                        sid = subs.pop(cv)
                        if sid:
                            rid += 1
                            await ws.send(json.dumps({"jsonrpc": "2.0", "id": rid, "method": "eth_unsubscribe", "params": [sid]}))
                    for _ in range(len(held)):                            # Buys the feed had not passed yet
                        t, r = held.popleft()
                        if not place(r) and mono() - t < 2.0:
                            held.append((t, r))
                    try:
                        d = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.1))
                    except asyncio.TimeoutError:
                        continue
                    if "id" in d:
                        cv = pending.pop(d["id"], None)
                        if cv is not None and cv in subs:
                            subs[cv] = d.get("result")
                        continue
                    if d.get("method") != "eth_subscription":
                        continue
                    res = d["params"]["result"]
                    if len(res.get("topics", [])) < 3 or "blockNumber" not in res:
                        continue
                    if not place(res):
                        held.append((mono(), res))
        except Exception as e:
            log({"ev": "feed_error", "source": "chain_rivals", "err": str(e)[:200], "retry_s": backoff}); await asyncio.sleep(backoff); backoff = min(5.0, backoff * 2)


async def provider_loop(websockets, until=None):
    """detection from a third-party node's WebSocket instead of the sequencer feed: newHeads gives the chain's second (the flip),
    the curve Buy/Sell logs carry the curve and the buyer in their topics and the amounts in their data, the factory's log
    marks a creation and one RPC call fetches its calldata (the named wallets). Everything downstream (the seat wait, the
    gates, the fold, the scorer) is unchanged. Lags the sequencer feed by the node's own processing (measured 100-300 ms on
    the replay as 10-30% fewer trades at the same return, section 23.10); E1 in predict mode is not meaningful on it."""
    global _bcache
    SUB = {"heads": None, "curve": None, "factory": None}; backoff = 0.2; state["detect"] = "provider"
    while True:
        if until is not None and mono() > until:
            return                                                       # back to the caller, which tries the sequencer feed again
        try:
            async with websockets.connect(PROVIDER_WS, open_timeout=10, max_size=None, ping_interval=10, ping_timeout=5, max_queue=4, compression=None) as ws:
                # 5.47: factory events only. The chain-wide Buy/Sell stream and newHeads were the firehose of Sep 16 (millions of messages a
                # day); the creation-second seat needs the creation, its calldata and one log read on its curve, a few hundred calls an hour
                subs = [("factory", ["logs", {"address": FACTORY_HEX}])] + ([("heads", ["newHeads"])] if PROVIDER_HEADS else [])
                for i, (name, params) in enumerate(subs):
                    await ws.send(json.dumps({"jsonrpc": "2.0", "id": i + 1, "method": "eth_subscribe", "params": params}))
                    r = json.loads(await asyncio.wait_for(ws.recv(), timeout=10)); SUB[name] = r.get("result")
                log({"ev": "feed_connected", "source": "provider", "subscriptions": SUB}); state["connected_at"] = mono(); backoff = 0.2
                state["brackets"].clear(); state["ref"] = None; state["prev_seen"] = None; _bcache["at"] = -1e9   # a new clock: the estimator restarts (24.17: it mixed two and printed -1.3 s)
                blk_ts = {}
                while True:
                    if until is not None and mono() > until:
                        return
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=2.0 if PROVIDER_HEADS else 120.0)   # creations come a few a minute; only heads tick every 100 ms
                    except asyncio.TimeoutError:
                        log({"ev": "feed_stall", "note": "no message for 2 s: reconnecting"}); break
                    seen = mono(); d = json.loads(raw)
                    if seen - last_prune_holder[0] > 30:
                        prune(seen); last_prune_holder[0] = seen
                    if d.get("method") != "eth_subscription":
                        continue
                    sub = d["params"]["subscription"]; res = d["params"]["result"]
                    if sub == SUB["heads"]:
                        ts = int(res["timestamp"], 16); bn = int(res["number"], 16); blk_ts[bn] = ts
                        if len(blk_ts) > 600:
                            for k in sorted(blk_ts)[:-300]:
                                blk_ts.pop(k, None)
                        state["blocks"] += 1
                        with cond:
                            if ts > state["last_seen_ts"] and state["last_seen_ts"]:
                                state["flip_at"].setdefault(ts, seen); state["flip_block"].setdefault(ts, bn)
                            state["last_seen_ts"] = max(state["last_seen_ts"], ts); state["feed_ts"] = max(state["feed_ts"], ts); cond.notify_all()
                        continue
                    bn = int(res["blockNumber"], 16); ts = blk_ts.get(bn) or state["feed_ts"]
                    topics = res["topics"]; data = res["data"][2:]; w = [int(data[i:i + 64], 16) for i in range(0, len(data), 64)]
                    if sub == SUB["curve"] and len(topics) >= 3:
                        curve = res["address"].lower(); who = "0x" + topics[2][-40:].lower()
                        if topics[0] == BUY_EV:
                            val = w[0] / 1e18; state["buys"][curve].append((ts, who, val, seen, state["blocks"], curve, None))
                            if curve in state["watch"]:
                                fold_buy(state["watch"][curve], ts, who, val)
                        else:
                            tk = w[1] / 1e18; state["sells"][curve].append((seen, tk))
                            if curve in state["watch"]:
                                fold_sell(state["watch"][curve], tk)
                    elif sub == SUB["factory"] and len(topics) >= 4:
                        creator = "0x" + topics[3][-40:].lower(); txh = res["transactionHash"]
                        known = ("0x" + topics[1][-40:].lower(), "0x" + topics[2][-40:].lower(), (w[2] / 1e18 if len(w) > 2 else 0.0), bn)   # token, curve, tk0, block: the log says it all
                        threading.Thread(target=provider_creation, args=(creator, txh, seen, ts, bn, known), daemon=True).start()
        except Exception as e:
            log({"ev": "feed_error", "source": "provider", "err": str(e)[:200], "retry_s": backoff}); await asyncio.sleep(backoff); backoff = min(5.0, backoff * 2)


def provider_creation(creator, txh, seen, ts, blk0, known=None):
    """the creation's calldata (quote, initial buy, named wallets) from the node, then the normal path; on the lean provider path
    (no newHeads) the block clock is set from the creation's own block"""
    try:
        if not ts:
            try:
                ts = int(rpc_seat.call("eth_getBlockByNumber", [hex(blk0), False], tries=1)["timestamp"], 16)
            except Exception:
                ts = int(time.time())
            with cond:
                state["blocks"] = max(state["blocks"], blk0); state["last_seen_ts"] = max(state["last_seen_ts"], ts); state["feed_ts"] = max(state["feed_ts"], ts); cond.notify_all()
        t = rpc.call("eth_getTransactionByHash", [txh])
        data = bytes.fromhex(t["input"][2:]); sel = data[:4]
        if sel not in CREATE_SELS:
            log({"ev": "skip", "why": "factory log from an unknown selector", "creator": creator, "selector": sel.hex()}); return
        words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
        quote = "0x" + data[4 + 32 * 2 + 12: 4 + 32 * 3].hex() if len(data) >= 4 + 32 * 4 else ZERO
        init_buy = int.from_bytes(data[4 + 32 * 3: 4 + 32 * 4], "big") if len(data) >= 4 + 32 * 4 else 0
        if quote != ZERO and int(quote, 16) < 2 ** 100:
            quote = ZERO
        named = {"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator, quote}
        state["creations"] += 1; state["last_creation_at"] = mono()
        log({"ev": "creation", "creator": creator, "quote": quote, "init_buy_eth": init_buy / 1e18, "feed_ts": ts, "named_wallets": len(named), "selector": sel.hex(), "source": "provider", "calldata_ms": round(1000 * (mono() - seen))})
        handle_creation(creator, quote, init_buy, seen, ts, named, blk0, tax_bps=tax_bps_of(sel, words), txh=txh, known=known)
    except Exception as e:
        log({"ev": "error", "stage": "provider_creation", "err": str(e)[:200]})


last_prune_holder = [0.0]


async def main():
    import websockets
    if SEAT == "E0" and not EXEMPT:
        raise SystemExit("SEAT=E0 for a wallet that is not on the creation's named list: refused. The snipe tax is keyed to the block's clock second, not to the block offset: a buy in any block that carries the creation block's timestamp pays ~98% (the live trade of Sep 18 09:43 UTC landed 3 blocks after the creation, index 1, and reverted on its minOut; report 24.19). E0_OUTSIDER no longer opts in. Use SEAT=E1 (the first block of the next second, 6.18%) or EXEMPT=1 for a named wallet.")
    if PIN_CPU:
        try:
            os.sched_setaffinity(0, {int(c) for c in PIN_CPU.split(",")})
        except Exception as e:
            log({"ev": "error", "stage": "pin_cpu", "err": str(e)[:100]})
    sys.setswitchinterval(0.0005)
    load_send_step(); load_state(); new_day_check(); threading.Thread(target=chain_loop, daemon=True).start()
    if state["open"]:
        log({"ev": "recovering_open_position", "position": state["open"]}); threading.Thread(target=close_position, args=(state["open"], "recovered after restart"), daemon=True).start()
    log({"ev": "start", "version": 5.52, "chain_rivals": bool(PROVIDER_WS), "feed_source": FEED_SOURCE, "seat": SEAT, "exempt": EXEMPT, "bundle_min": BUNDLE_MIN, "bundle_min_eth": BUNDLE_MIN_ETH, "bundle_max_eth": BUNDLE_MAX_ETH, "out1_max": OUT1_MAX, "out2_max": OUT2_MAX, "min_creator_supply": MIN_CREATOR_SUPPLY,
         "stop_sell_frac": STOP_SELL_FRAC, "take_profit": TAKE_PROFIT, "e0_outsider": E0_OUTSIDER, "tier_min_bps": TIER_MIN_BPS, "tier_max_bps": TIER_MAX_BPS, "skip_tier1_team_share": SKIP_TIER1_TEAM_SHARE, "e0_bundle_wait_s": E0_BUNDLE_WAIT_S, "e0_bundle_max_blocks": E0_BUNDLE_MAX_BLOCKS, "max_live_trades": MAX_LIVE_TRADES, "provider_fallback_s": PROVIDER_FALLBACK_S, "e0_allow_provider": E0_ALLOW_PROVIDER, "provider_heads": PROVIDER_HEADS, "feed_compression": FEED_COMPRESSION, "provider_lag_ms": PROVIDER_LAG_MS, "send_mode": SEND_MODE, "trade_hours": TRADE_HOURS, "min_rule_passing_1h": MIN_RULE_PASSING_1H, "min_follow_eth_60": MIN_FOLLOW_ETH_60, "seat_wait_ms": SEAT_WAIT_MS, "margin_ms": MARGIN_MS, "bankroll": state["bankroll"], "frac": FRAC, "stake": [STAKE_MIN, STAKE_MAX], "hold": HOLD,
         "supply_frac": SUPPLY_FRAC, "stake_min": STAKE_MIN, "stake_max": STAKE_MAX, "frac": FRAC, "slip": SLIP, "seat_wait_ms": SEAT_WAIT_MS, "hold_s": HOLD, "switch": [SWITCH_N, SWITCH], "daily_stop": DAILY_STOP, "sender_backend": SENDER_BACKEND, "dry_run": SEND is None, "wallet": WALLET})
    gc.collect(); gc.freeze(); gc.disable()                            # a generation-2 pass costs milliseconds; prune() collects when nothing is in flight
    if FEED_SOURCE == "provider":
        if not PROVIDER_WS:
            raise SystemExit("FEED_SOURCE=provider needs PROVIDER_WS (a third-party node's WebSocket endpoint)")
        last_prune_holder[0] = mono(); await provider_loop(websockets); return
    if PROVIDER_WS:
        asyncio.ensure_future(chain_rivals_loop(websockets))            # the chain's Buy events as a second rival source next to the feed
    last_prune = mono(); backoff = 0.2; refused = 0
    while True:
        try:
            async with websockets.connect(FEED_URL, open_timeout=10, max_size=None, ping_interval=10, ping_timeout=5, max_queue=4, compression=FEED_COMPRESSION) as ws:
                log({"ev": "feed_connected"}); state["connected_at"] = mono(); state["prev_seen"] = None; backoff = 0.2; state["detect"] = "sequencer"
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
                            if not warm:
                                state["feed_seq"] = max(state["feed_seq"], int(m.get("sequenceNumber") or 0))   # = the L2 block number
                            state["prev_seen"] = seen; state["prev_ts"] = ts
                            cond.notify_all()
        except Exception as e:
            refused = refused + 1 if ("rejected WebSocket connection" in str(e) or "HTTP 4" in str(e)) else 0        # an HTTP refusal, not a network drop
            blocked = "HTTP 403" in str(e)                                # their edge blocks an address for an hour after sustained rejections: do not feed the block
            if (refused >= 5 or blocked) and PROVIDER_WS:                # Robinhood's feed has shut the door: carry on from the provider's node (posture B)
                window = 3600.0 if blocked else PROVIDER_FALLBACK_S
                log({"ev": "alarm", "what": f"the sequencer feed {'blocked this address (HTTP 403)' if blocked else 'refused five connections in a row'}: detection on the provider WebSocket for {window:.0f} s, then the feed is tried again", "err": str(e)[:160]})
                last_prune_holder[0] = mono(); await provider_loop(websockets, until=mono() + window)
                log({"ev": "note", "what": "trying the sequencer feed again"}); refused = 0; backoff = 0.2; continue
            log({"ev": "feed_error", "err": str(e)[:200], "retry_s": backoff}); await asyncio.sleep(backoff); backoff = min(5.0, backoff * 2)   # 0.2 s after a drop, slower if the network is gone


if __name__ == "__main__":
    print("sniper engine v4:", ("LIVE (send step " + os.environ["SEND_MODULE"] + ")") if os.environ.get("SEND_MODULE") else "DRY RUN (submit() logs unsigned transactions and sends nothing)", "; seat", SEAT, "log", LOG_PATH, "sender backend", SENDER_BACKEND)
    asyncio.run(main())
