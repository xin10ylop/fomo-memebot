#!/usr/bin/env python3
"""First-block sniper engine v3, dry-run by design (report sections 20-22, docs/SNIPER_RUNBOOK.md).

Live, it listens to the Robinhood Chain sequencer feed, decodes legacy, type-1 and type-2 transactions, detects Pons V2
creations (factory 0xe33e..., selectors 0xf85f8e41 and 0x3f707e6b), reads the creator, the quote asset, the initial buy
and the creator's exempt (named) wallets from the calldata, and resolves the new curve from the feed itself: the named
wallets buy it inside the creation second and the address they buy is the curve. Buys of a curve are recognised whether
they call the curve directly or go through a router (any value-carrying transaction whose calldata names the curve).
Gates (section 21.6): bundle of >= BUNDLE_MIN named wallets and >= BUNDLE_MIN_ETH, creator's launch buy >=
MIN_CREATOR_SUPPLY of supply, and no non-named buyer of the curve during second one. Seat: E2 (second whole second after
the creation's timestamp, +0.19%), E1 (+6.18%), E0 only for an exempt wallet. Sizing on the curve as the feed shows it
at send time, minOut at SLIP below the sized tokens (a wrong-second landing reverts for gas). Sends in react mode (when
the feed shows the seat's second) or predict mode (at the seat's boundary derived from the creation's own second plus
MARGIN_MS). Live: reads the tokens received from the buy's event, approves at once, sells the balance HOLD s after the
buy landed (or at once if a dump is seen and STOP_SELL_FRAC > 0), tunes MARGIN_MS from where the buy landed. Every
rule-passing launch is scored 25 s after creation with the simulator's exact-curve replay; the dry-run bankroll
follows those scores; the feed's gate readings are checked against the chain's at score time. State (bankroll, day,
scores, open position) is persisted next to the log and recovered on restart.

What it does not do: sign or broadcast. submit(tx, label) logs the transaction and returns None; replace it with a
function that signs with your key, sends through your provider endpoint (and the sequencer as a second endpoint) and
returns the hash. The runbook says what to verify on the first live trade.
"""
import asyncio, base64, json, os, time, math, threading, http.client, urllib.parse, urllib.request, collections, statistics as st, datetime
import rlp
from eth_account import Account

RPC_URL = os.environ.get("RPC_URL", "https://rpc.mainnet.chain.robinhood.com")
FEED_URL = os.environ.get("FEED_URL", "wss://feed.mainnet.chain.robinhood.com")
LOG_PATH = os.environ.get("LOG_PATH", "sniper_engine.jsonl"); STATE_PATH = LOG_PATH + ".state.json"
WALLET = os.environ.get("WALLET", "0x0000000000000000000000000000000000000000").lower()
ETH_USD = float(os.environ.get("ETH_USD", "2445")); ETH_USD_URL = os.environ.get("ETH_USD_URL", "https://api.coinbase.com/v2/prices/ETH-USD/spot")
BANKROLL = float(os.environ.get("BANKROLL_USD", "300"))
FRAC = float(os.environ.get("FRAC", "0.2")); STAKE_MIN = float(os.environ.get("STAKE_MIN", "50")); STAKE_MAX = float(os.environ.get("STAKE_MAX", "300"))
HOLD = float(os.environ.get("HOLD_S", "7")); SUPPLY_FRAC = float(os.environ.get("SUPPLY_FRAC", "0.03")); SLIP = float(os.environ.get("SLIP", "0.25"))
SEAT = os.environ.get("SEAT", "E2").upper(); EXEMPT = os.environ.get("EXEMPT", "0") == "1"
BUNDLE_MIN = int(os.environ.get("BUNDLE_MIN", "3" if SEAT in ("E1", "E2") else "0"))
BUNDLE_MIN_ETH = float(os.environ.get("BUNDLE_MIN_ETH", "0.3"))
OUT1_MAX = int(os.environ.get("OUT1_MAX", "0"))
TIER_ASSUMED = float(os.environ.get("TIER_ASSUMED", "0.05"))
STOP_SELL_FRAC = float(os.environ.get("STOP_SELL_FRAC", "0"))
SEND_MODE = os.environ.get("SEND_MODE", "react"); MARGIN_MS = float(os.environ.get("MARGIN_MS", "25"))
MAX_LATE_S = float(os.environ.get("MAX_LATE_S", "0.5"))              # do not send more than this far into the seat's second
MIN_CREATOR_SUPPLY = float(os.environ.get("MIN_CREATOR_SUPPLY", "0.01")); MAX_CREATOR_BUY_ETH = float(os.environ.get("MAX_CREATOR_BUY_ETH", "2"))
SWITCH_N = int(os.environ.get("SWITCH_N", "15")); SWITCH = float(os.environ.get("SWITCH", "-0.10")); DAILY_STOP = float(os.environ.get("DAILY_STOP", "0.50"))
MAX_RESOLVE_MS = int(os.environ.get("MAX_RESOLVE_MS", "1500"))
GAS_MAX_SHARE = float(os.environ.get("GAS_MAX_SHARE", "0.03"))
GAS_BUY, GAS_APPROVE, GAS_SELL = 500_000, 80_000, 200_000
FACTORY = bytes.fromhex("e33e9e479df8802cb0866d5d05258bec4cf62948"); CREATE_SELS = {bytes.fromhex("f85f8e41"), bytes.fromhex("3f707e6b")}
FACTORY_HEX = "0x" + FACTORY.hex()
BUY_EV = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL_EV = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
BUY_SEL = bytes.fromhex("59a87bc1"); SELL_SEL = bytes.fromhex("d04c6983"); APPROVE_SEL = "095ea7b3"
UA = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/engine"}
X0, Y0 = 1.68, 1e9
SURCHARGE = {"E0": 0.0, "E1": 0.0618, "E2": 0.0019}; SEAT_SECONDS = {"E0": 0, "E1": 1, "E2": 2}
ZERO = "0x" + "0" * 40


def log(ev):
    ev["t"] = time.time()
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(ev) + "\n")


class Rpc:
    def __init__(self, url):
        u = urllib.parse.urlparse(url); self.host = u.netloc; self.path = u.path or "/"; self.local = threading.local()

    def call(self, method, params):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        for i in range(3):
            try:
                c = getattr(self.local, "c", None)
                if c is None:
                    c = http.client.HTTPSConnection(self.host, timeout=10); self.local.c = c
                c.request("POST", self.path, body=body, headers=UA); r = c.getresponse(); d = json.loads(r.read())
                if "error" in d:
                    raise RuntimeError(d["error"])
                return d["result"]
            except Exception:
                self.local.c = None
                if i == 2:
                    raise
                time.sleep(0.03)


rpc = Rpc(RPC_URL)
state = {"bankroll": BANKROLL, "day": None, "day_start": BANKROLL, "stopped": False, "busy_until": 0.0, "scores": collections.deque(maxlen=SWITCH_N),
         "launched_today": collections.Counter(), "seeded": False, "feed_ts": 0, "last_seen_ts": 0, "traded": {}, "eth_usd": ETH_USD,
         "buys": collections.defaultdict(list),        # curve -> [(ts, sender, value_eth, seen)] direct buys
         "sells": collections.defaultdict(list),       # curve -> [(seen, tokens)] direct sells
         "valtx": collections.deque(maxlen=4000),      # (seen, ts, sender, value_eth, data) value-carrying non-direct txs: router buys
         "known_curves": {}, "flips": collections.deque(maxlen=600), "flip_at": {}, "connected_at": 0.0,
         "nonce": None, "gas_price": None, "chain_at": 0.0, "open": None, "decisions": {}}
lock = threading.Lock()


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
    """DRY RUN: logs the exact unsigned transaction and returns None. Replace with signing + eth_sendRawTransaction through the
    provider endpoint with the sequencer as a second endpoint; return the transaction hash."""
    log({"ev": "unsigned_tx", "label": label, "tx": tx})
    return None


def chain_loop():
    """nonce, gas price and the ETH price, refreshed in the background so the critical path never waits on the RPC"""
    n = 0
    while True:
        try:
            state["nonce"] = int(rpc.call("eth_getTransactionCount", [WALLET, "pending"]), 16); state["gas_price"] = int(rpc.call("eth_gasPrice", []), 16); state["chain_at"] = time.time()
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
            ph = boundary_phase()
            if ph is not None:
                log({"ev": "boundary", "phase_local_s": round(ph, 4), "flips": len(state["flips"]), "margin_ms": MARGIN_MS})
        n += 1; time.sleep(3)


def boundary_phase():
    """the sequencer's second boundary in local wall-clock phase: the low edge (2nd percentile) of the phases at which the
    feed's L2 timestamp was seen to flip (flips are visible at block granularity, so the true boundary is the low edge)"""
    ph = sorted(t % 1.0 for t in state["flips"])
    if len(ph) < 30:
        return None
    gaps = [(ph[(i + 1) % len(ph)] - ph[i]) % 1.0 for i in range(len(ph))]
    k = max(range(len(ph)), key=lambda i: gaps[i]); base = ph[(k + 1) % len(ph)]
    rot = sorted((x - base) % 1.0 for x in ph)
    return (base + rot[int(0.02 * len(rot))]) % 1.0


def wait_for_second(feed_ts, seconds, seen_at, deadline=3.5):
    """block until it is time to send for the seat. react: when the feed shows the seat's second. predict: at the seat's
    boundary derived from the creation's own second (the local time the feed first showed feed_ts + 1, snapped to the
    estimated boundary edge) plus MARGIN_MS. Returns the mode used, or None when the seat's second is already more than
    MAX_LATE_S old or was never seen (do not send on stale data)."""
    target_ts = feed_ts + seconds
    if SEND_MODE == "predict" and seconds >= 1:
        ph = boundary_phase()
        while feed_ts + 1 not in state["flip_at"] and time.time() - seen_at < deadline and state["feed_ts"] < target_ts:
            time.sleep(0.002)
        if feed_ts + 1 in state["flip_at"] and ph is not None:
            f1 = state["flip_at"][feed_ts + 1]; edge = f1 - ((f1 - ph) % 1.0)          # the boundary of second feed_ts+1 in local time
            target = edge + (seconds - 1) + MARGIN_MS / 1000.0
            while time.time() < target and state["feed_ts"] < target_ts and time.time() - seen_at < deadline:
                time.sleep(0.001)
            if state["feed_ts"] > target_ts:
                return None
            if state["feed_ts"] == target_ts and time.time() - state["flip_at"].get(target_ts, time.time()) > MAX_LATE_S:
                return None
            return "predict" if state["feed_ts"] < target_ts else "predict-late"
    while state["feed_ts"] < target_ts and time.time() - seen_at < deadline:
        time.sleep(0.002)
    if state["feed_ts"] != target_ts or time.time() - state["flip_at"].get(target_ts, time.time()) > MAX_LATE_S:
        return None
    return "react"


def tune_margin(receipt, seat_ts):
    """live only: learn MARGIN_MS from where the buy landed (reverted and stamped before the seat's second: +20 ms; landed
    in the seat's second but not its first block: -5 ms; first block: keep)"""
    global MARGIN_MS
    try:
        b = int(receipt["blockNumber"], 16); ts = int(rpc.call("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)
        prev = int(rpc.call("eth_getBlockByNumber", [hex(b - 1), False])["timestamp"], 16)
        if ts < seat_ts:
            MARGIN_MS += 20; where = "early"
        elif prev < ts:
            where = "first block"
        else:
            MARGIN_MS = max(5.0, MARGIN_MS - 5); where = "later block"
        log({"ev": "landing", "block": b, "block_ts": ts, "seat_ts": seat_ts, "where": where, "margin_ms": MARGIN_MS, "status": receipt.get("status")}); save_state()
    except Exception as e:
        log({"ev": "error", "stage": "tune_margin", "err": str(e)[:200]})


def gas_cost_usd():
    gp = state["gas_price"]
    return (GAS_BUY + GAS_APPROVE + GAS_SELL) * gp / 1e18 * state["eth_usd"] if gp else None


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


def curve_buys(curve, since_ts=None):
    """every buy of the curve seen on the feed: direct calls and value-carrying transactions whose calldata names the curve"""
    cb = bytes.fromhex(curve[2:]); out = list(state["buys"].get(curve, []))
    for seen, ts_, snd, val, data in list(state["valtx"]):
        if cb in data:
            out.append((ts_, snd, val, seen))
    if since_ts is not None:
        out = [b for b in out if b[0] >= since_ts]
    return out


def curve_state(curve, tk0, feed_ts):
    """the curve's reserves at send time, rebuilt from the feed: the creator's launch buy (from the calldata), every buy seen
    (ETH value net of a 1% fee; router buys carry their whole value, an over-estimate) and every direct sell"""
    net0 = X0 * tk0 / (Y0 - tk0); X = X0 + net0; Y = Y0 - tk0
    for ts_, snd, val, seen in curve_buys(curve, feed_ts):
        if val > 0:
            net = val * 0.99; tk = Y - X * Y / (X + net); X += net; Y -= tk
    for seen, tk in state["sells"].get(curve, []):
        if 0 < tk < Y0:
            g = X - X * Y / (Y + tk); X -= g; Y += tk
    return X, Y


def size_buy(X, Y, stake_eth, seat):
    fee = TIER_ASSUMED + SURCHARGE[seat]; tk = SUPPLY_FRAC * Y0
    net = X * tk / (Y - tk); gross = net / (1 - fee)
    if gross > stake_eth:
        gross = stake_eth; net = gross * (1 - fee); tk = Y * net / (X + net)
    return tk, net, gross, fee


def exact_score(events, b_create, tk0, stake_eth, seat, tol=0.10, slip=0.3, hold=HOLD, frac=SUPPLY_FRAC, gated=True, stop_sell_frac=None):
    """the simulator's replay (sniper_exact.replay) on the curve's own Buy/Sell events. Returns (pnl_usd, cost_usd, t_in, tier,
    label_bundle, label_bundle_eth, label_out1) or "filtered" or None."""
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
    lab = (len(bundle_rows), sum(r[2] for r in bundle_rows), sum(1 for r in rows[1:] if r[1] == "B" and 0.05 <= r[5] - tier <= 0.075))
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
    X += net; Y -= tk_bot; held = Y0 - Y - tk_bot; phantom = 0.0; t_exit = t_in + hold + slip
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
    out = (X - X * Y / (Y + tk_bot)) * (1 - tier)
    return ((out - gross) * state["eth_usd"] - 1.0, gross * state["eth_usd"], t_in, tier) + lab


def resolve_rpc(creator, deadline=3.0, lookback=40):
    """the curve from the factory's event: (token, curve, tk0, b_create) or None"""
    t0 = time.time()
    while time.time() - t0 < deadline:
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
        r = exact_score(events, b_create, tk0, stake_usd / state["eth_usd"], SEAT, gated=BUNDLE_MIN > 0, stop_sell_frac=STOP_SELL_FRAC if STOP_SELL_FRAC > 0 else None)
        if r is None:
            log({"ev": "score", "curve": curve, "result": "no usable launch-block buy"}); return
        if decision is not None:                                        # what the feed said at decision time vs what the chain says
            lab = r[-3:]
            log({"ev": "gate_check", "curve": curve, "feed": decision, "chain": {"bundle": lab[0], "bundle_eth": round(lab[1], 4), "out1": lab[2]}, "src": src})
        if r[0] == "filtered":
            log({"ev": "score", "curve": curve, "result": "outside the rule on the chain's reading"}); state["traded"].pop(curve, None); return
        pnl, cost, t_in, tier = r[:4]; roi = pnl / cost
        with lock:
            state["scores"].append(roi); sc = list(state["scores"]); on = len(sc) < SWITCH_N or st.mean(sc) >= SWITCH
            traded = state["traded"].pop(curve, None)
            if traded is not None:
                state["bankroll"] += min(traded, cost) * roi
        save_state()
        log({"ev": "score", "curve": curve, "roi": round(roi, 4), "pnl_usd": round(pnl, 2), "cost_usd": round(cost, 2), "tier": round(tier, 4), "t_in_s": round(t_in, 2),
             "n_scores": len(sc), "rolling_mean": round(st.mean(sc), 4), "switch_on": on, "traded_dry_run": traded is not None, "bankroll": round(state["bankroll"], 2)})
    except Exception as e:
        log({"ev": "error", "stage": "score", "err": str(e)[:200]})


def wait_receipt(h, timeout=10.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
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
        approve = {"to": pos["token"], "value": "0x0", "data": "0x" + APPROVE_SEL + abi_word(pos["curve"]) + abi_word(2 ** 256 - 1), "gas": hex(GAS_APPROVE), "gasPrice": hex(gp), "nonce": hex(nonce + 1), "chainId": 4663}
        ha = submit(approve, "approve"); pos["approved"] = True; pos["approve_hash"] = ha
    sell = {"to": pos["curve"], "value": "0x0", "data": "0x" + SELL_SEL.hex() + abi_word(int(pos["tokens"] * 1e18)) + abi_word(0) + abi_word(WALLET), "gas": hex(GAS_SELL), "gasPrice": hex(gp), "nonce": hex(nonce + 2), "chainId": 4663}
    hs = submit(sell, "sell")
    log({"ev": "trade_done", "curve": pos["curve"], "tokens_sold": pos["tokens"], "held_s": round(time.time() - pos["t_buy"], 2), "exit": why, "dry_run": hs is None and pos.get("buy_hash") is None, "sell_hash": hs})
    state["open"] = None; save_state()


def handle_creation(creator, quote, init_buy_wei, seen_at, feed_ts, named):
    """resolve the curve, apply the gates, size on the feed-tracked curve, take the seat, build the buy, then approve and sell"""
    curve = token = None; tk0 = None; b_create = None; src = None; named = set(named)
    if SEAT in ("E1", "E2") and BUNDLE_MIN > 0 and quote == ZERO and len(named) >= BUNDLE_MIN:
        while state["feed_ts"] <= feed_ts and time.time() - seen_at < 1.5:
            time.sleep(0.003)
        cands = collections.Counter()
        for cv, lst in list(state["buys"].items()):
            if cv in state["known_curves"]:
                continue
            cands[cv] += sum(1 for ts_, snd, val, seen in lst if snd in named and ts_ >= feed_ts)
        if cands:
            a, c = cands.most_common(1)[0]
            if c >= BUNDLE_MIN:
                curve = a; src = "feed"
                net0 = init_buy_wei / 1e18 * 0.99; tk0 = Y0 - X0 * Y0 / (X0 + net0) if net0 > 0 else 0.0
    if curve is None:
        r = resolve_rpc(creator)
        if r:
            token, curve, tk0, b_create = r; src = "rpc"
    resolve_ms = round((time.time() - seen_at) * 1000)
    if not curve:
        log({"ev": "skip", "why": "curve not resolved in 3 s", "creator": creator, "named_wallets": len(named)}); return
    state["known_curves"][curve] = time.time()
    new_day_check()
    with lock:
        prior = state["launched_today"][creator]; state["launched_today"][creator] += 1
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
    # the seat's wait: the bundle and second one must be fully visible before the gates are read
    send_mode = None
    if SEAT in ("E1", "E2"):
        send_mode = wait_for_second(feed_ts, SEAT_SECONDS[SEAT], seen_at)
    buys = curve_buys(curve, feed_ts)
    bundle = sum(1 for ts_, snd, val, seen in buys if snd in named and ts_ == feed_ts)
    bundle_eth = sum(val for ts_, snd, val, seen in buys if snd in named and ts_ <= feed_ts + 1)
    out1 = sum(1 for ts_, snd, val, seen in buys if snd not in named and snd != creator and ts_ == feed_ts + 1)
    decision = {"bundle": bundle, "bundle_eth": round(bundle_eth, 4), "out1": out1}
    with lock:
        sc = list(state["scores"]); on = len(sc) < SWITCH_N or st.mean(sc) >= SWITCH
        stake_usd = min(STAKE_MAX, max(STAKE_MIN, state["bankroll"] * FRAC)); gates = []
        if bundle < BUNDLE_MIN:
            gates.append(f"bundle {bundle} < {BUNDLE_MIN}")
        if bundle_eth < BUNDLE_MIN_ETH:
            gates.append(f"bundle {bundle_eth:.3f} ETH < {BUNDLE_MIN_ETH}")
        if SEAT == "E2" and out1 > OUT1_MAX:
            gates.append(f"{out1} outsider buys in second one > {OUT1_MAX}")
        if not on:
            gates.append(f"safety switch off (rolling {st.mean(sc):+.3f} over {len(sc)} < {SWITCH:+.2f})")
        if state["stopped"] or state["bankroll"] < (1 - DAILY_STOP) * state["day_start"]:
            state["stopped"] = True; gates.append("daily stop")
        if time.time() < state["busy_until"] or state["open"] is not None:
            gates.append("position open")
        if resolve_ms > MAX_RESOLVE_MS:
            gates.append(f"resolved in {resolve_ms} ms > {MAX_RESOLVE_MS}")
        if state["bankroll"] < STAKE_MIN:
            gates.append("bankroll below the minimum stake")
        if send_mode is None and SEAT in ("E1", "E2"):
            gates.append("seat's second not seen in time (stale feed): not sending")
        if state["nonce"] is None or time.time() - state["chain_at"] > 30:
            gates.append("nonce/gas not fresh (RPC)")
        gc = gas_cost_usd()
        if gc is not None and gc > GAS_MAX_SHARE * stake_usd:
            gates.append(f"gas ${gc:.2f} per round trip > {100 * GAS_MAX_SHARE:.0f}% of stake")
        if not gates:
            state["busy_until"] = time.time() + HOLD + 3; nonce = state["nonce"]; state["nonce"] += 3; gas_price = state["gas_price"]
    threading.Thread(target=score_launch, args=(curve, tk0, b_create, stake_usd, creator, src, decision), daemon=True).start()
    if gates:
        log({"ev": "eligible_not_traded", "curve": curve, "creator": creator, "resolve_ms": resolve_ms, "resolve_src": src, "named_wallets": len(named), **decision, "gates": gates, "stake_usd": stake_usd}); return
    X, Y = curve_state(curve, tk0, feed_ts); stake_eth = stake_usd / state["eth_usd"]
    tk, net, gross, fee = size_buy(X, Y, stake_eth, SEAT)
    amount_in = int(gross * 1e18); min_out = int(tk * (1 - SLIP) * 1e18)
    buy = {"to": curve, "value": hex(amount_in), "data": "0x" + BUY_SEL.hex() + abi_word(amount_in) + abi_word(min_out) + abi_word(WALLET), "gas": hex(GAS_BUY), "gasPrice": hex(gas_price), "nonce": hex(nonce), "chainId": 4663}
    p_creator = (X0 + X0 * tk0 / (Y0 - tk0)) / (Y0 - tk0)
    log({"ev": "trade_decision", "seat": SEAT, "curve": curve, "token": token, "creator": creator, "resolve_ms": resolve_ms, "resolve_src": src, "named_wallets": len(named), **decision,
         "sent_ms": round((time.time() - seen_at) * 1000), "send_mode": send_mode, "feed_ts_at_send": state["feed_ts"], "seat_ts": feed_ts + SEAT_SECONDS.get(SEAT, 0), "stake_usd": stake_usd,
         "amount_in_eth": amount_in / 1e18, "tokens_target": tk, "supply_share": tk / Y0, "min_out_tokens": min_out / 1e18, "fee_assumed": fee, "price_vs_creator": round((X / Y) / p_creator, 3)})
    h = submit(buy, "buy"); t_buy = time.time(); tokens = tk
    state["traded"][curve] = min(stake_usd, gross * state["eth_usd"]); state["decisions"][curve] = decision
    if h:                                                            # live: the tokens actually received, from the buy's own event
        rec = wait_receipt(h)
        if rec:
            if SEAT in ("E1", "E2"):
                tune_margin(rec, feed_ts + SEAT_SECONDS[SEAT])
            if rec.get("status") != "0x1":
                log({"ev": "buy_reverted", "curve": curve, "hash": h}); state["traded"].pop(curve, None); state["busy_until"] = 0.0; return
            for l in rec.get("logs", []):
                if l["topics"][0] == BUY_EV and l["address"].lower() == curve:
                    tokens = int(l["data"][2 + 64:2 + 128], 16) / 1e18
            t_buy = time.time()
        else:
            log({"ev": "receipt_timeout", "curve": curve, "hash": h, "note": "assuming the buy landed: approving and selling the sized amount"})
    if token is None:
        r = resolve_rpc(creator, deadline=HOLD - 1, lookback=120); token = r[0] if r else curve
    pos = {"curve": curve, "token": token, "tokens": tokens, "nonce": nonce, "t_buy": t_buy, "buy_hash": h, "approved": False, "seat_ts": feed_ts + SEAT_SECONDS.get(SEAT, 0)}
    state["open"] = pos; save_state()
    gp = gas_price or 0
    approve = {"to": token, "value": "0x0", "data": "0x" + APPROVE_SEL + abi_word(curve) + abi_word(2 ** 256 - 1), "gas": hex(GAS_APPROVE), "gasPrice": hex(gp), "nonce": hex(nonce + 1), "chainId": 4663}
    pos["approve_hash"] = submit(approve, "approve"); pos["approved"] = True; save_state()
    why = "hold"
    while time.time() - t_buy < HOLD:
        if STOP_SELL_FRAC > 0:
            dump = next((tk_ for at, tk_ in reversed(state["sells"].get(curve, [])) if at > t_buy and tk_ >= STOP_SELL_FRAC * Y0), None)
            if dump is not None:
                why = f"dump {100 * dump / Y0:.1f}% of supply"; break
        time.sleep(0.005)
    close_position(pos, why)


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
        state["flip_at"].pop(ts_, None)


async def main():
    import websockets
    if SEAT == "E0" and not EXEMPT:
        raise SystemExit("SEAT=E0 needs an address exempt from the snipe surcharge (EXEMPT=1); anyone else pays 93-98% in the creation second. Use SEAT=E2 (runbook).")
    load_state(); new_day_check(); threading.Thread(target=chain_loop, daemon=True).start()
    if state["open"]:
        log({"ev": "recovering_open_position", "position": state["open"]}); threading.Thread(target=close_position, args=(state["open"], "recovered after restart"), daemon=True).start()
    log({"ev": "start", "seat": SEAT, "exempt": EXEMPT, "bundle_min": BUNDLE_MIN, "bundle_min_eth": BUNDLE_MIN_ETH, "out1_max": OUT1_MAX, "min_creator_supply": MIN_CREATOR_SUPPLY, "stop_sell_frac": STOP_SELL_FRAC,
         "send_mode": SEND_MODE, "margin_ms": MARGIN_MS, "bankroll": state["bankroll"], "frac": FRAC, "stake": [STAKE_MIN, STAKE_MAX], "hold": HOLD, "supply_frac": SUPPLY_FRAC, "switch": [SWITCH_N, SWITCH], "daily_stop": DAILY_STOP, "dry_run": True})
    last_prune = time.time()
    while True:
        try:
            async with websockets.connect(FEED_URL, open_timeout=15, max_size=None, ping_interval=20) as ws:
                log({"ev": "feed_connected"}); state["connected_at"] = time.time()
                while True:
                    d = json.loads(await ws.recv()); seen = time.time()
                    warm = seen - state["connected_at"] < 5.0            # the feed replays a backlog on connect: no flips, no trades from it
                    if seen - last_prune > 30:
                        prune(seen); last_prune = seen
                    for m in d.get("messages", []):
                        inner = m["message"]["message"]; hdr = inner.get("header", {})
                        ts = int(hdr.get("timestamp", 0) or 0) if int(hdr.get("kind", 0) or 0) == 3 else 0   # L2 messages only: batch reports carry L1 time
                        if ts:
                            if ts > state["last_seen_ts"] and state["last_seen_ts"] and not warm:
                                state["flips"].append(seen); state["flip_at"].setdefault(ts, seen)
                            state["last_seen_ts"] = max(state["last_seen_ts"], ts); state["feed_ts"] = max(state["feed_ts"], ts)
                        if warm:
                            continue
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
                                    snd = Account.recover_transaction(t).lower()
                                    state["buys"][to_hex].append((ts, snd, val, seen)); continue
                                if sel == SELL_SEL and len(data) >= 36:                                 # direct curve sell
                                    state["sells"][to_hex].append((seen, int.from_bytes(data[4:36], "big") / 1e18)); continue
                                if to == FACTORY and sel in CREATE_SELS:                                 # creation
                                    creator = Account.recover_transaction(t).lower()
                                    words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
                                    quote = "0x" + data[4 + 32 * 2 + 12: 4 + 32 * 3].hex() if len(data) >= 4 + 32 * 4 else ZERO
                                    init_buy = int.from_bytes(data[4 + 32 * 3: 4 + 32 * 4], "big") if len(data) >= 4 + 32 * 4 else 0
                                    if quote != ZERO and int(quote, 16) < 2 ** 100:                     # unknown layout: not an address, let the RPC path decide
                                        quote = ZERO
                                    named = {"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator, quote}
                                    log({"ev": "creation", "creator": creator, "quote": quote, "init_buy_eth": init_buy / 1e18, "feed_ts": ts, "named_wallets": len(named), "selector": sel.hex(), "tx_type": ty})
                                    threading.Thread(target=handle_creation, args=(creator, quote, init_buy, seen, ts, named), daemon=True).start(); continue
                                if val > 0 and len(data) >= 36:                                         # a router buy of some curve: matched by calldata at decision time
                                    snd = Account.recover_transaction(t).lower(); state["valtx"].append((seen, ts, snd, val, bytes(data)))
                                    if state["open"] is None:
                                        continue
                                if state["open"] is not None and val == 0 and bytes.fromhex(state["open"]["curve"][2:]) in data and sel not in (BUY_SEL, SELL_SEL):
                                    state["sells"][state["open"]["curve"]].append((seen, float("inf")))   # router sell touching our curve during the hold
                            except Exception as e:
                                log({"ev": "error", "stage": "decode", "err": str(e)[:200]})
        except Exception as e:
            log({"ev": "feed_error", "err": str(e)[:200]}); await asyncio.sleep(2)


if __name__ == "__main__":
    print("sniper engine v3: DRY RUN (submit() logs unsigned transactions and sends nothing); seat", SEAT, "log", LOG_PATH)
    asyncio.run(main())
