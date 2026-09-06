#!/usr/bin/env python3
"""First-block sniper engine v2, dry-run by design (report section 20, docs/SNIPER_RUNBOOK.md).

Live, it listens to the Robinhood Chain sequencer feed, detects Pons V2 creations (factory 0xe33e..., selector
0xf85f8e41), recovers the creator and the quote asset from the calldata, resolves the new curve from the factory's
event (creator, launch-block buy q0 / tk0), applies the launch-time filters (creator's first launch today, native-ETH
quote, creator's launch-block buy at least MIN_CREATOR_SUPPLY of supply), sizes the buy on the exact constant-product
curve (virtual reserves 1.68 ETH / 1e9 tokens, section 20), takes its SEAT:
  E0  submit at once, in front of the first outside buyer. Only for an address exempt from the snipe surcharge: anyone
      else buying in the creation second pays a 93-98% tax (EXEMPT=1 is required to start in this seat);
  E1  wait for the first feed message stamped in the next whole second, then submit: +6.18% surcharge, in front of the
      non-exempt bots. E2 waits one more second and pays +0.19%, behind the second-one bots. Section 20 shows this seat only pays on launches whose creator bundle bought with BUNDLE_MIN or
      more named wallets in the creation second, and only on peak-flow days; the engine counts those buys on the feed;
builds the unsigned buy, then (live) reads the tokens actually received from the buy receipt, approves the curve right
away so the exit is a single transaction, and sells exactly that balance HOLD seconds after the buy landed. Every
eligible launch is scored 25 s after creation with the same exact-curve replay as the offline simulator
(src/analysis/sniper_exact.py), so the regime switch always has a fresh reading, and in dry run the bankroll follows
those scores for the launches it would have traded. Risk controls: regime switch (trade only while the mean of the
last N scored outcomes >= SWITCH), daily stop (-DAILY_STOP of the day's starting bankroll), latency gate (do not trade a
launch resolved later than MAX_RESOLVE_MS after the feed saw it), one position at a time, gas check.

What it does not do: sign or broadcast. submit() logs the transaction and returns None. Replace it with a function that
signs with your key and sends eth_sendRawTransaction; the runbook says what to verify on the first live trade.

env: RPC_URL, FEED_URL, WALLET, BANKROLL_USD, ETH_USD, LOG_PATH, SEAT (E0|E1), EXEMPT (1|0), SUPPLY_FRAC, and the rest below.
"""
import asyncio, base64, json, os, time, math, threading, http.client, urllib.parse, urllib.request, collections, statistics as st, datetime
import rlp
from eth_account import Account

RPC_URL = os.environ.get("RPC_URL", "https://rpc.mainnet.chain.robinhood.com")
FEED_URL = os.environ.get("FEED_URL", "wss://feed.mainnet.chain.robinhood.com")
LOG_PATH = os.environ.get("LOG_PATH", "sniper_engine.jsonl")
WALLET = os.environ.get("WALLET", "0x0000000000000000000000000000000000000000").lower()
ETH_USD = float(os.environ.get("ETH_USD", "2445")); ETH_USD_URL = os.environ.get("ETH_USD_URL", "https://api.coinbase.com/v2/prices/ETH-USD/spot")
BANKROLL = float(os.environ.get("BANKROLL_USD", "300"))
FRAC = float(os.environ.get("FRAC", "0.2")); STAKE_MIN = float(os.environ.get("STAKE_MIN", "50")); STAKE_MAX = float(os.environ.get("STAKE_MAX", "300"))
HOLD = float(os.environ.get("HOLD_S", "7")); SUPPLY_FRAC = float(os.environ.get("SUPPLY_FRAC", "0.03")); SLIP = float(os.environ.get("SLIP", "0.25"))
SEAT = os.environ.get("SEAT", "E1").upper(); EXEMPT = os.environ.get("EXEMPT", "0") == "1"
BUNDLE_MIN = int(os.environ.get("BUNDLE_MIN", "3" if SEAT in ("E1", "E2") else "0"))   # E1 only trades launches whose creator bundle bought with >= BUNDLE_MIN named wallets in the creation second (section 20.6)
TIER_ASSUMED = float(os.environ.get("TIER_ASSUMED", "0.05"))
SEND_MODE = os.environ.get("SEND_MODE", "react")                   # react: send when the feed shows the seat's second; predict: send at the estimated boundary + MARGIN_MS
MARGIN_MS = float(os.environ.get("MARGIN_MS", "25"))                 # predict mode: how far past the estimated boundary to send (covers boundary error and one-way delay)     # the creator-set fee tier is unknown before the buy lands: size the ETH for the worst common tier
MIN_CREATOR_SUPPLY = float(os.environ.get("MIN_CREATOR_SUPPLY", "0.0")); MAX_CREATOR_BUY_ETH = float(os.environ.get("MAX_CREATOR_BUY_ETH", "2"))
SWITCH_N = int(os.environ.get("SWITCH_N", "30")); SWITCH = float(os.environ.get("SWITCH", "0.05")); DAILY_STOP = float(os.environ.get("DAILY_STOP", "0.30"))
MAX_RESOLVE_MS = int(os.environ.get("MAX_RESOLVE_MS", "300")); GAS_MAX_SHARE = float(os.environ.get("GAS_MAX_SHARE", "0.03"))
GAS_BUY, GAS_APPROVE, GAS_SELL = 500_000, 80_000, 200_000        # observed: direct curve buys ~450k, approve ~46k, direct curve sell ~81k
FACTORY = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"; CREATE_SEL = bytes.fromhex("f85f8e41")
BUY_EV = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL_EV = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
BUY_SEL = "59a87bc1"; SELL_SEL = "d04c6983"; APPROVE_SEL = "095ea7b3"
UA = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/engine"}
X0, Y0 = 1.68, 1e9                                                  # virtual reserves (section 20)
SURCHARGE = {"E0": 0.0, "E1": 0.0618, "E2": 0.0019}                 # by seat: creation second (exempt only), next second, the one after
SEAT_SECONDS = {"E0": 0, "E1": 1, "E2": 2}


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
         "launched_today": collections.Counter(), "feed_ts": 0, "traded": {}, "eth_usd": ETH_USD, "recent_buys": collections.deque(maxlen=20000), "first_seen": {}, "known_curves": set(), "flips": collections.deque(maxlen=600), "connected_at": 0.0, "last_seen_ts": 0}
lock = threading.Lock()


def abi_word(x):
    return x.to_bytes(32, "big").hex() if isinstance(x, int) else x[2:].rjust(64, "0")


def submit(tx, label):
    """DRY RUN: logs the exact unsigned transaction and returns None. Replace with signing + eth_sendRawTransaction (return the hash)."""
    log({"ev": "unsigned_tx", "label": label, "tx": tx})
    return None


def price_loop():
    while True:
        ph = boundary_phase()
        if ph is not None:
            log({"ev": "boundary", "phase_local_s": round(ph, 4), "flips": len(state["flips"])})
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(ETH_USD_URL, headers={"User-Agent": UA["User-Agent"]}), timeout=10))
            px = float(d["data"]["amount"])
            if 100 < px < 100000:
                state["eth_usd"] = px
        except Exception:
            pass
        time.sleep(300)


def boundary_phase():
    """the sequencer's second boundary in local wall-clock phase: the low edge (2nd percentile) of the phases at which the
    feed's L2 timestamp was seen to flip, over the last few hundred flips (flips are visible at block granularity, so
    the true boundary is the low edge, not the median). None until 30 flips have been seen."""
    ph = sorted(t % 1.0 for t in state["flips"])
    if len(ph) < 30:
        return None
    gaps = [(ph[(i + 1) % len(ph)] - ph[i]) % 1.0 for i in range(len(ph))]
    k = max(range(len(ph)), key=lambda i: gaps[i]); base = ph[(k + 1) % len(ph)]
    rot = sorted((x - base) % 1.0 for x in ph)
    return (base + rot[int(0.02 * len(rot))]) % 1.0


def wait_for_second(feed_ts, seconds, seen_at, deadline=3.5):
    """block until it is time to send for the seat: react mode waits to see the seat's second on the feed; predict mode
    sends at the estimated boundary of that second plus MARGIN_MS (falls back to react while the estimate is not ready).
    Returns the mode used."""
    if SEND_MODE == "predict":
        ph = boundary_phase()
        if ph is not None:
            # the creation's second started at the last boundary before it was seen; the seat's second starts `seconds` later
            now = time.time(); last_boundary = math.floor(now - ph) + ph
            if last_boundary > seen_at:
                last_boundary -= 1.0
            target = last_boundary + seconds + MARGIN_MS / 1000.0
            while time.time() < target and time.time() - seen_at < deadline:
                time.sleep(0.001)
            if state["feed_ts"] >= feed_ts + seconds:                  # the feed already shows the seat's second: we are late, go now
                return "predict-late"
            return "predict"
    while state["feed_ts"] < feed_ts + seconds and time.time() - seen_at < deadline:
        time.sleep(0.003)
    return "react"


def tune_margin(receipt, seat_ts):
    """live only: learn MARGIN_MS from where the buy landed. Reverted with a block stamped before the seat's second means
    we sent too early (the 93-98% tax would have applied; minOut saved us): add 20 ms. Landed in the seat's second but
    not in its first block: take 5 ms off (floor 5). Landed in the first block: keep."""
    global MARGIN_MS
    try:
        b = int(receipt["blockNumber"], 16); blk = rpc.call("eth_getBlockByNumber", [hex(b), False]); ts = int(blk["timestamp"], 16)
        prev = int(rpc.call("eth_getBlockByNumber", [hex(b - 1), False])["timestamp"], 16)
        if ts < seat_ts:
            MARGIN_MS += 20; where = "early"
        elif prev < ts:
            where = "first block"
        else:
            MARGIN_MS = max(5.0, MARGIN_MS - 5); where = "later block"
        log({"ev": "landing", "block": b, "block_ts": ts, "seat_ts": seat_ts, "where": where, "margin_ms": MARGIN_MS, "status": receipt.get("status")})
    except Exception as e:
        log({"ev": "error", "stage": "tune_margin", "err": str(e)[:200]})


def gas_ok(stake_usd):
    try:
        gp = int(rpc.call("eth_gasPrice", []), 16); cost = (GAS_BUY + GAS_APPROVE + GAS_SELL) * gp / 1e18 * state["eth_usd"]
        return cost <= GAS_MAX_SHARE * stake_usd, cost
    except Exception:
        return True, None


def new_day_check():
    d = datetime.datetime.utcnow().date()
    if state["day"] != d:
        state["day"] = d; state["day_start"] = state["bankroll"]; state["stopped"] = False; state["launched_today"].clear()
        seed_launched_today()


def seed_launched_today():
    """creators that already launched today, so 'first launch of the day' is exact from the moment the engine starts"""
    try:
        head = int(rpc.call("eth_blockNumber", []), 16)
        secs = (datetime.datetime.utcnow() - datetime.datetime.combine(datetime.datetime.utcnow().date(), datetime.time())).total_seconds()
        b = head - int(secs * 9.9)
        while b <= head:
            e = min(head, b + 20000)
            for l in rpc.call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "address": FACTORY}]):
                if len(l["topics"]) > 3:
                    state["launched_today"]["0x" + l["topics"][3][-40:]] += 1
            b = e + 1
        log({"ev": "seeded", "creators_today": len(state["launched_today"])})
    except Exception as e:
        log({"ev": "error", "stage": "seed", "err": str(e)[:200]})


def size_buy(tk0, stake_eth, seat):
    """exact curve after the creator's buy; returns (tokens targeted, net ETH into the curve, gross ETH to send, fee rate assumed)"""
    net0 = X0 * tk0 / (Y0 - tk0); X = X0 + net0; Y = Y0 - tk0
    fee = TIER_ASSUMED + SURCHARGE[seat]
    tk = SUPPLY_FRAC * Y0; net = X * tk / (Y - tk); gross = net / (1 - fee)
    if gross > stake_eth:
        gross = stake_eth; net = gross * (1 - fee); tk = Y * net / (X + net)
    return tk, net, gross, fee


def exact_score(events, b_create, tk0, stake_eth, seat, tol=0.10, slip=0.3, hold=HOLD, frac=SUPPLY_FRAC, bundle_min=0):
    """the offline simulator's replay (sniper_exact.replay) on the curve's own Buy/Sell events: label each event's implied tax
    from the exact curve state, seat the sniper, replay the later flow on the modified curve, sell hold s after entry."""
    rows = []; X, Y = X0, Y0; tier = None
    for i, (b, li, buy, q, tk, fee) in enumerate(events):
        t = (b - b_create) / 9.9
        if buy:
            if tk <= 0 or tk >= Y or q <= 0:
                return None
            net = X * tk / (Y - tk); tax = 1 - net / q
            if i == 0:
                tier = max(0.0, min(tax, 0.2))
            rows.append((t, "B", q, tk, net, tax)); X += net; Y -= tk
        else:
            gross = X - X * Y / (Y + tk); rows.append((t, "S", q, tk, gross, 1 - q / gross if gross > 0 else 0.0)); X -= gross; Y += tk
    if tier is None or rows[0][1] != "B":
        return None
    if bundle_min:                                                    # the simulator's bundle count: unsurcharged buys inside the creation second, before any surcharged buy
        first_taxed = next((r[0] for r in rows[1:] if r[1] == "B" and r[5] - tier > 0.001), 9e9)
        if sum(1 for r in rows[1:] if r[1] == "B" and r[0] < min(1.0, first_taxed) and r[5] - tier <= 0.0008) < bundle_min:
            return "filtered"
    X, Y = X0, Y0; X += rows[0][4]; Y -= rows[0][3]
    lo, hi, fb = {"E0": (-1.0, 0.0008, 0.1), "E1": (0.05, 0.075, 1.0), "E2": (0.0012, 0.0035, 2.0)}[seat]
    idx = next((i for i in range(1, len(rows)) if rows[i][1] == "B" and rows[i][0] <= 3.0 and lo <= rows[i][5] - tier <= hi), None)
    if idx is None:
        idx = next((i for i in range(1, len(rows)) if rows[i][0] >= fb), len(rows)); t_in = fb
    else:
        t_in = rows[idx][0]
    for r in rows[1:idx]:
        if r[1] == "B":
            X += r[4]; Y -= r[3]
        else:
            X -= r[4]; Y += r[3]
    fee = tier + SURCHARGE[seat]
    tk_bot = frac * Y0; net = X * tk_bot / (Y - tk_bot); gross = net / (1 - fee)
    if gross > stake_eth:
        gross = stake_eth; net = gross * (1 - fee); tk_bot = Y * net / (X + net)
    X += net; Y -= tk_bot; held = Y0 - Y - tk_bot; phantom = 0.0
    for r in rows[idx:]:
        t, k, q, tk, net_obs, tax = r
        if t >= t_in + hold + slip:
            break
        if k == "B":
            tokens = Y - X * Y / (X + net_obs)
            if tokens < tk * (1 - tol):
                phantom += tk; continue
            X += net_obs; Y -= tokens; held += tokens
        else:
            share = held / (held + phantom) if held + phantom > 0 else 1.0
            s = min(tk * share, held); g = X - X * Y / (Y + s); X -= g; Y += s; held -= s; phantom = max(0.0, phantom - (tk - s))
    out = (X - X * Y / (Y + tk_bot)) * (1 - tier)
    return (out - gross) * state["eth_usd"] - 1.0, gross * state["eth_usd"], t_in, tier


def score_launch(curve, tk0, b_create, stake_usd, creator=None, src=None):
    """25 s after creation: the regime signal, and in dry run the bankroll update for launches the engine would have traded"""
    time.sleep(25)
    try:
        if b_create is None:                                            # feed-resolved launch: confirm the curve against the factory event and get its block
            r = resolve_rpc(creator, deadline=5.0, lookback=600)          # the creation is ~250 blocks back by now
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
        r = exact_score(events, b_create, tk0, stake_usd / state["eth_usd"], SEAT, bundle_min=BUNDLE_MIN)
        if r is None:
            log({"ev": "score", "curve": curve, "result": "no usable launch-block buy"}); return
        if r == "filtered":
            log({"ev": "score", "curve": curve, "result": f"bundle below {BUNDLE_MIN}: not scored"}); state["traded"].pop(curve, None); return
        pnl, cost, t_in, tier = r; roi = pnl / cost
        with lock:
            state["scores"].append(roi); sc = list(state["scores"]); on = len(sc) >= SWITCH_N and st.mean(sc) >= SWITCH
            traded = state["traded"].pop(curve, None)
            if traded is not None:
                state["bankroll"] += min(traded, cost) * roi
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


def resolve_rpc(creator, deadline=3.0, lookback=40):
    """the curve from the factory's event: (token, curve, tk0, b_create) or None"""
    t0 = time.time()
    while time.time() - t0 < deadline:
        try:
            head = int(rpc.call("eth_blockNumber", []), 16)
            for l in rpc.call("eth_getLogs", [{"fromBlock": hex(head - lookback), "toBlock": hex(head), "address": FACTORY}]):
                if len(l["topics"]) > 3 and ("0x" + l["topics"][3][-40:]).lower() == creator:
                    d = l["data"][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
                    return "0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:], w[2] / 1e18, int(l["blockNumber"], 16)
        except Exception:
            pass
        time.sleep(0.02)
    return None


def handle_creation(creator, quote, init_buy_wei, seen_at, feed_ts, named=frozenset()):
    """resolve the curve (from the feed when the creator's named wallets reveal it, else from the factory event), apply the
    filters, size on the exact curve, take the seat, build the buy, then approve and sell"""
    t0 = time.time(); curve = token = None; tk0 = None; b_create = None; src = None; bundle = None; named = set(named)
    if SEAT in ("E1", "E2") and BUNDLE_MIN > 0 and quote == "0x" + "0" * 40 and len(named) >= BUNDLE_MIN:
        # feed-only path: the wallets the creator named in the calldata buy the new curve inside the creation second, so
        # the address they buy is the curve. Matching buyers to the named list is exact; no RPC on the critical path.
        while state["feed_ts"] <= feed_ts and time.time() - seen_at < 1.5:
            time.sleep(0.003)
        cands = collections.Counter(a for ts_, a, snd in list(state["recent_buys"]) if snd in named and ts_ >= feed_ts and a not in state["known_curves"])
        if cands:
            a, c = cands.most_common(1)[0]
            if c >= BUNDLE_MIN:
                curve, bundle = a, c; src = "feed"; token = None
                net0 = init_buy_wei / 1e18 * (1 - 0.01); tk0 = Y0 - X0 * Y0 / (X0 + net0) if net0 > 0 else 0.0   # creator's tokens at the 1% tier (within 4% at 5%)
    if curve is None:
        r = resolve_rpc(creator)
        if r:
            token, curve, tk0, b_create = r; src = "rpc"
    resolve_ms = round((time.time() - seen_at) * 1000)
    if not curve:
        log({"ev": "skip", "why": "curve not resolved in 3 s", "creator": creator, "named_wallets": len(named)}); return
    state["known_curves"].add(curve)
    new_day_check()
    prior = state["launched_today"][creator]; state["launched_today"][creator] += 1
    reasons = []
    if prior > 0:
        reasons.append(f"creator launched {prior} times today")
    if quote != "0x" + "0" * 40:
        reasons.append("quote not native ETH")
    if tk0 <= 0 or tk0 >= Y0:
        reasons.append("no usable launch-block buy")
    if tk0 < MIN_CREATOR_SUPPLY * Y0:
        reasons.append(f"creator buy {100 * tk0 / Y0:.1f}% of supply < {100 * MIN_CREATOR_SUPPLY:.0f}%")
    if init_buy_wei / 1e18 > MAX_CREATOR_BUY_ETH:
        reasons.append("creator buy too large")
    if reasons:
        log({"ev": "skip", "why": reasons, "curve": curve, "creator": creator, "resolve_ms": resolve_ms, "resolve_src": src, "named_wallets": len(named)}); return
    with lock:
        sc = list(state["scores"]); on = len(sc) >= SWITCH_N and st.mean(sc) >= SWITCH
        stake_usd = min(STAKE_MAX, max(STAKE_MIN, state["bankroll"] * FRAC))
        gates = []
        if not on:
            gates.append(f"regime switch off (rolling {st.mean(sc) if sc else 0:+.3f} over {len(sc)})")
        if state["stopped"] or state["bankroll"] < (1 - DAILY_STOP) * state["day_start"]:
            state["stopped"] = True; gates.append("daily stop")
        if time.time() < state["busy_until"]:
            gates.append("position open")
        if resolve_ms > MAX_RESOLVE_MS:
            gates.append(f"resolved in {resolve_ms} ms > {MAX_RESOLVE_MS}")
        if state["bankroll"] < STAKE_MIN:
            gates.append("bankroll below the minimum stake")
        ok, gas_cost = gas_ok(stake_usd)
        if not ok:
            gates.append(f"gas ${gas_cost:.2f} per round trip > {100 * GAS_MAX_SHARE:.0f}% of stake")
    threading.Thread(target=score_launch, args=(curve, tk0, b_create, stake_usd, creator, src), daemon=True).start()
    if gates:
        log({"ev": "eligible_not_traded", "curve": curve, "creator": creator, "resolve_ms": resolve_ms, "resolve_src": src, "named_wallets": len(named), "bundle": bundle, "gates": gates, "stake_usd": stake_usd}); return
    with lock:
        state["busy_until"] = time.time() + HOLD + 3
    stake_eth = stake_usd / state["eth_usd"]
    tk, net, gross, fee = size_buy(tk0, stake_eth, SEAT)
    amount_in = int(gross * 1e18); min_out = int(tk * (1 - SLIP) * 1e18)
    try:
        nonce = int(rpc.call("eth_getTransactionCount", [WALLET, "pending"]), 16); gas_price = int(rpc.call("eth_gasPrice", []), 16)
    except Exception:
        nonce, gas_price = 0, 0
    send_mode = None
    if SEAT in ("E1", "E2"):                                          # not exempt: never land in the creation second (93-98% tax); wait for the seat's second
        send_mode = wait_for_second(feed_ts, SEAT_SECONDS[SEAT], seen_at)
        if bundle is None:
            bundle = sum(1 for ts_, to_, snd in list(state["recent_buys"]) if to_ == curve and (snd in named or ts_ == feed_ts))   # the named wallets' buys (or any direct buy inside the creation second)
        if bundle < BUNDLE_MIN:
            log({"ev": "eligible_not_traded", "curve": curve, "creator": creator, "resolve_ms": resolve_ms, "gates": [f"bundle {bundle} < {BUNDLE_MIN}"], "stake_usd": stake_usd})
            with lock:
                state["busy_until"] = 0.0
            return
    buy = {"to": curve, "value": hex(amount_in), "data": "0x" + BUY_SEL + abi_word(amount_in) + abi_word(min_out) + abi_word(WALLET), "gas": hex(GAS_BUY), "gasPrice": hex(gas_price), "nonce": hex(nonce), "chainId": 4663}
    log({"ev": "trade_decision", "seat": SEAT, "curve": curve, "token": token, "creator": creator, "resolve_ms": resolve_ms, "resolve_src": src, "named_wallets": len(named), "bundle": bundle, "sent_ms": round((time.time() - seen_at) * 1000), "send_mode": send_mode, "feed_ts_at_send": state["feed_ts"], "seat_ts": feed_ts + SEAT_SECONDS.get(SEAT, 0), "stake_usd": stake_usd,
         "amount_in_eth": amount_in / 1e18, "tokens_target": tk, "supply_share": tk / Y0, "min_out_tokens": min_out / 1e18, "fee_assumed": fee})
    h = submit(buy, "buy"); t_buy = time.time(); tokens = tk
    with lock:
        state["traded"][curve] = min(stake_usd, gross * state["eth_usd"])
    if h:                                                            # live: the tokens actually received, from the buy's own event
        rec = wait_receipt(h)
        if rec and SEAT in ("E1", "E2"):
            tune_margin(rec, feed_ts + SEAT_SECONDS[SEAT])
        if not rec or rec.get("status") != "0x1":
            log({"ev": "buy_failed_or_reverted", "curve": curve, "hash": h}); state["traded"].pop(curve, None); return
        for l in rec.get("logs", []):
            if l["topics"][0] == BUY_EV and l["address"].lower() == curve:
                tokens = int(l["data"][2 + 64:2 + 128], 16) / 1e18
        t_buy = time.time()
    if token is None:                                                 # feed-resolved: the token address comes from the factory event, needed only for the approve
        r = resolve_rpc(creator, deadline=HOLD - 1, lookback=120)
        token = r[0] if r else curve
    approve = {"to": token, "value": "0x0", "data": "0x" + APPROVE_SEL + abi_word(curve) + abi_word(2 ** 256 - 1), "gas": hex(GAS_APPROVE), "gasPrice": hex(gas_price), "nonce": hex(nonce + 1), "chainId": 4663}
    submit(approve, "approve")                                       # right after the buy, so the exit is one transaction
    time.sleep(max(0.0, HOLD - (time.time() - t_buy)))
    sell = {"to": curve, "value": "0x0", "data": "0x" + SELL_SEL + abi_word(int(tokens * 1e18)) + abi_word(0) + abi_word(WALLET), "gas": hex(GAS_SELL), "gasPrice": hex(gas_price), "nonce": hex(nonce + 2), "chainId": 4663}
    submit(sell, "sell")
    log({"ev": "trade_done", "curve": curve, "tokens_sold": tokens, "dry_run": h is None, "note": "dry run: the bankroll follows the exact-curve score 25 s after creation"})


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


async def main():
    import websockets
    if SEAT == "E0" and not EXEMPT:
        raise SystemExit("SEAT=E0 needs an address exempt from the snipe surcharge (EXEMPT=1); anyone else pays 93-98% in the creation second. Use SEAT=E1 or get the exemption first (runbook).")
    new_day_check(); threading.Thread(target=price_loop, daemon=True).start()
    log({"ev": "start", "seat": SEAT, "exempt": EXEMPT, "bundle_min": BUNDLE_MIN, "send_mode": SEND_MODE, "margin_ms": MARGIN_MS, "bankroll": BANKROLL, "frac": FRAC, "stake": [STAKE_MIN, STAKE_MAX], "hold": HOLD, "supply_frac": SUPPLY_FRAC, "switch": [SWITCH_N, SWITCH], "daily_stop": DAILY_STOP, "max_resolve_ms": MAX_RESOLVE_MS, "dry_run": True})
    while True:
        try:
            async with websockets.connect(FEED_URL, open_timeout=15, max_size=None, ping_interval=20) as ws:
                log({"ev": "feed_connected"}); state["connected_at"] = time.time()
                while True:
                    d = json.loads(await ws.recv()); seen = time.time()
                    warm = seen - state["connected_at"] < 5.0            # the feed replays a backlog on connect: no flips, no trades from it
                    for m in d.get("messages", []):
                        inner = m["message"]["message"]; hdr = inner.get("header", {})
                        ts = int(hdr.get("timestamp", 0) or 0) if int(hdr.get("kind", 0) or 0) == 3 else 0   # L2 messages only: batch reports carry L1 time
                        if ts:
                            if ts > state["last_seen_ts"] and state["last_seen_ts"] and not warm:
                                state["flips"].append(seen)
                            state["last_seen_ts"] = max(state["last_seen_ts"], ts); state["feed_ts"] = max(state["feed_ts"], ts)
                        if warm:
                            continue
                        for t in decode_batch(inner.get("l2Msg", "")):
                            try:
                                if t[0] != 2:
                                    continue
                                body = rlp.decode(t[1:]); to = body[5]; data = body[7]
                                if len(to) == 20 and data[:4].hex() == BUY_SEL:
                                    a = "0x" + to.hex()
                                    try:
                                        snd = Account.recover_transaction(t).lower()               # ~70 us; the buyer, matched against the creation's named wallets
                                    except Exception:
                                        snd = None
                                    state["recent_buys"].append((ts, a, snd)); state["first_seen"].setdefault(a, seen); continue
                                if len(to) != 20 or "0x" + to.hex() != FACTORY or data[:4] != CREATE_SEL:
                                    continue
                                creator = Account.recover_transaction(t).lower()
                                quote = "0x" + data[4 + 32 * 2 + 12: 4 + 32 * 3].hex(); init_buy = int.from_bytes(data[4 + 32 * 3: 4 + 32 * 4], "big")
                                words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
                                named = {"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator, quote}
                                log({"ev": "creation", "creator": creator, "quote": quote, "init_buy_eth": init_buy / 1e18, "feed_ts": ts, "named_wallets": len(named)})
                                threading.Thread(target=handle_creation, args=(creator, quote, init_buy, seen, ts, named), daemon=True).start()
                            except Exception as e:
                                log({"ev": "error", "stage": "decode", "err": str(e)[:200]})
        except Exception as e:
            log({"ev": "feed_error", "err": str(e)[:200]}); await asyncio.sleep(2)


if __name__ == "__main__":
    print("sniper engine v2: DRY RUN (submit() logs unsigned transactions and sends nothing); seat", SEAT, "log", LOG_PATH)
    asyncio.run(main())
