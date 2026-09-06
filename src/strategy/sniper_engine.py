#!/usr/bin/env python3
"""First-block sniper engine, dry-run by design (report section 19, docs/SNIPER_RUNBOOK.md).

What it does, live: listens to the Robinhood Chain sequencer feed, detects Pons V2 creations (factory 0xe33e...,
selector 0xf85f8e41), recovers the creator and the quote asset from the calldata, resolves the new curve from the
factory's event (creator, initial buy q0, tokens tk0), applies the launch-time filters measured in sections 14 and 19
(creator's first launch today, native-ETH quote, creator's launch-block buy at least MIN_CREATOR_SUPPLY of supply),
sizes the stake from the bankroll (FRAC of bankroll, floored and capped), builds the exact unsigned transactions
(buy on the curve now; approve + sell HOLD seconds later), hands them to submit(), and scores every eligible launch
from the curve's own Buy/Sell events 25 s later so the regime switch always has a fresh reading whether or not it
traded. Risk controls: regime switch (trade live only while the mean of the last N scored outcomes >= SWITCH),
daily stop (stop for the UTC day at -DAILY_STOP of the day's starting bankroll), latency gate (do not trade a
launch resolved later than MAX_RESOLVE_MS after the feed saw it), one position at a time, gas check (halt if the
current base fee makes a round trip cost more than GAS_MAX_SHARE of the stake).

What it does not do: sign or broadcast. submit() logs the transaction and returns None. Replace it in your own
environment with a function that signs with your key and sends eth_sendRawTransaction; the runbook says how and
what to verify on the first live trade (curve selectors, approval, minOut).

env: RPC_URL, FEED_URL, WALLET (recipient address), BANKROLL_USD, ETH_USD, LOG_PATH; see runbook for the rest.
"""
import asyncio, base64, json, os, time, threading, http.client, urllib.parse, collections, statistics as st, datetime
import rlp
from eth_account import Account

RPC_URL = os.environ.get("RPC_URL", "https://rpc.mainnet.chain.robinhood.com")
FEED_URL = os.environ.get("FEED_URL", "wss://feed.mainnet.chain.robinhood.com")
LOG_PATH = os.environ.get("LOG_PATH", "sniper_engine.jsonl")
WALLET = os.environ.get("WALLET", "0x0000000000000000000000000000000000000000").lower()
ETH_USD = float(os.environ.get("ETH_USD", "2445"))
BANKROLL = float(os.environ.get("BANKROLL_USD", "300"))
FRAC = float(os.environ.get("FRAC", "0.2")); STAKE_MIN = float(os.environ.get("STAKE_MIN", "50")); STAKE_MAX = float(os.environ.get("STAKE_MAX", "300"))
HOLD = float(os.environ.get("HOLD_S", "7")); SUPPLY_FRAC = float(os.environ.get("SUPPLY_FRAC", "0.03")); SLIP = float(os.environ.get("SLIP", "0.25"))
MIN_CREATOR_SUPPLY = float(os.environ.get("MIN_CREATOR_SUPPLY", "0.05")); MAX_CREATOR_BUY_ETH = float(os.environ.get("MAX_CREATOR_BUY_ETH", "2"))
SWITCH_N = int(os.environ.get("SWITCH_N", "30")); SWITCH = float(os.environ.get("SWITCH", "0.05")); DAILY_STOP = float(os.environ.get("DAILY_STOP", "0.30"))
MAX_RESOLVE_MS = int(os.environ.get("MAX_RESOLVE_MS", "300")); GAS_MAX_SHARE = float(os.environ.get("GAS_MAX_SHARE", "0.03")); GAS_UNITS = 500_000
FACTORY = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"; CREATE_SEL = bytes.fromhex("f85f8e41")
BUY_EV = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL_EV = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
BUY_SEL = "59a87bc1"; SELL_SEL = "d04c6983"; APPROVE_SEL = "095ea7b3"
UA = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/engine"}
SUPPLY = 1e9


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
state = {"bankroll": BANKROLL, "day": None, "day_start": BANKROLL, "stopped": False, "busy_until": 0.0, "scores": collections.deque(maxlen=SWITCH_N), "launched_today": collections.Counter(), "nonce": None}
lock = threading.Lock()


def abi_word(x):
    return x.to_bytes(32, "big").hex() if isinstance(x, int) else x[2:].rjust(64, "0")


def submit(tx, label):
    """DRY RUN: logs the exact unsigned transaction and returns None. Replace with signing + eth_sendRawTransaction in your environment."""
    log({"ev": "unsigned_tx", "label": label, "tx": tx})
    return None


def gas_ok(stake_usd):
    try:
        gp = int(rpc.call("eth_gasPrice", []), 16); cost = 2 * GAS_UNITS * gp / 1e18 * ETH_USD
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
        b0 = head - int(secs * 9.9); b = b0
        while b <= head:
            e = min(head, b + 20000)
            for l in rpc.call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(e), "address": FACTORY}]):
                if len(l["topics"]) > 3:
                    state["launched_today"]["0x" + l["topics"][3][-40:]] += 1
            b = e + 1
        log({"ev": "seeded", "creators_today": len(state["launched_today"])})
    except Exception as e:
        log({"ev": "error", "stage": "seed", "err": str(e)[:200]})


def score_launch(curve, q0, tk0, t_create):
    """25 s after creation, read the curve's events and compute what the rule would have returned (first non-creator price, 3% of supply capped at the stake, LIFO exit at HOLD s): the regime signal"""
    time.sleep(25)
    try:
        head = int(rpc.call("eth_blockNumber", []), 16)
        ev = rpc.call("eth_getLogs", [{"fromBlock": hex(head - 400), "toBlock": hex(head), "address": curve, "topics": [[BUY_EV, SELL_EV]]}])
        blk = {}
        for e in ev:
            b = int(e["blockNumber"], 16)
            if b not in blk:
                blk[b] = int(rpc.call("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)
        tr = []
        for e in ev:
            d = e["data"][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]; buy = e["topics"][0] == BUY_EV
            tr.append((blk[int(e["blockNumber"], 16)], int(e["logIndex"], 16), buy, (w[0] if buy else w[1]) / 1e18, (w[1] if buy else w[0]) / 1e18))
        tr.sort()
        first = [x for x in tr[1:] if x[2]]
        if not first or first[0][0] - t_create > 3.0:
            log({"ev": "score", "curve": curve, "result": "no first buyer within 3 s"}); return
        t_in, _, _, q1, tk1 = first[0]; p_in = q1 / tk1; stake_eth = min(STAKE_MAX, max(STAKE_MIN, state["bankroll"] * FRAC)) / ETH_USD
        tk_bot = min(SUPPLY_FRAC * SUPPLY, stake_eth / p_in); cost = tk_bot * p_in * 1.01
        stack = [[tk0, q0], [tk_bot, tk_bot * p_in]]

        def lifo(stack, tk):
            out = 0.0; need = tk
            for tokens, quote in reversed(stack):
                if need <= 0:
                    break
                take = min(tokens, need); out += quote * take / tokens; need -= take
            return out * 0.99

        out = None
        for t, li, buy, q, tk in tr[1:]:
            if t <= t_in:
                continue
            if t >= t_in + HOLD:
                out = lifo(stack, tk_bot); break
            if buy:
                stack.append([tk, q])
            else:
                need = tk
                while need > 1e-12 and stack:
                    tokens, quote = stack[-1]; take = min(tokens, need)
                    if take >= tokens - 1e-12:
                        stack.pop()
                    else:
                        stack[-1] = [tokens - take, quote * (tokens - take) / tokens]
                    need -= take
        if out is None:
            out = lifo(stack, tk_bot)
        roi = (out - cost) / cost - 1.0 / (cost * ETH_USD)   # minus ~$1 of gas
        with lock:
            state["scores"].append(roi)
            sc = list(state["scores"]); on = len(sc) >= SWITCH_N and st.mean(sc) >= SWITCH
        log({"ev": "score", "curve": curve, "roi": round(roi, 4), "t_in_s": round(t_in - t_create, 2), "n_scores": len(sc), "rolling_mean": round(st.mean(sc), 4), "switch_on": on})
    except Exception as e:
        log({"ev": "error", "stage": "score", "err": str(e)[:200]})


def handle_creation(creator, quote, init_buy_wei, seen_at):
    """resolve the curve, apply the filters, size, build the unsigned buy, schedule the sell"""
    t0 = time.time(); curve = token = None; q0 = tk0 = None
    while time.time() - t0 < 3.0:
        try:
            head = int(rpc.call("eth_blockNumber", []), 16)
            for l in rpc.call("eth_getLogs", [{"fromBlock": hex(head - 8), "toBlock": hex(head), "address": FACTORY}]):
                if len(l["topics"]) > 3 and ("0x" + l["topics"][3][-40:]).lower() == creator:
                    token = "0x" + l["topics"][1][-40:]; curve = "0x" + l["topics"][2][-40:]; d = l["data"][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
                    q0 = w[1] / 1e18; tk0 = w[2] / 1e18; break
            if curve:
                break
        except Exception:
            pass
        time.sleep(0.02)
    resolve_ms = round((time.time() - seen_at) * 1000)
    if not curve:
        log({"ev": "skip", "why": "curve not resolved in 3 s", "creator": creator}); return
    new_day_check()
    prior = state["launched_today"][creator]; state["launched_today"][creator] += 1
    reasons = []
    if prior > 0:
        reasons.append(f"creator launched {prior} times today")
    if quote != "0x" + "0" * 40:
        reasons.append("quote not native ETH")
    if tk0 < MIN_CREATOR_SUPPLY * SUPPLY:
        reasons.append(f"creator buy {100 * tk0 / SUPPLY:.1f}% of supply < {100 * MIN_CREATOR_SUPPLY:.0f}%")
    if init_buy_wei / 1e18 > MAX_CREATOR_BUY_ETH:
        reasons.append("creator buy too large")
    if reasons:
        log({"ev": "skip", "why": reasons, "curve": curve, "creator": creator, "resolve_ms": resolve_ms}); return
    threading.Thread(target=score_launch, args=(curve, q0, tk0, seen_at), daemon=True).start()
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
        if gates:
            log({"ev": "eligible_not_traded", "curve": curve, "creator": creator, "resolve_ms": resolve_ms, "gates": gates, "stake_usd": stake_usd}); return
        state["busy_until"] = time.time() + HOLD + 3
    # sizing: after the creator's buy the curve price is q0/tk0; the bot wants SUPPLY_FRAC of supply or the stake, whichever is smaller
    p_now = q0 / tk0 if tk0 else None
    stake_eth = stake_usd / ETH_USD; tk_target = min(SUPPLY_FRAC * SUPPLY, stake_eth / p_now) if p_now else 0
    amount_in = int(min(stake_eth, tk_target * p_now * (1 + SLIP)) * 1e18); min_out = int(tk_target * (1 - SLIP) * 1e18)
    try:
        nonce = int(rpc.call("eth_getTransactionCount", [WALLET, "pending"]), 16); gas_price = int(rpc.call("eth_gasPrice", []), 16)
    except Exception:
        nonce, gas_price = 0, 0
    buy = {"to": curve, "value": hex(amount_in), "data": "0x" + BUY_SEL + abi_word(amount_in) + abi_word(min_out) + abi_word(WALLET), "gas": hex(GAS_UNITS), "gasPrice": hex(gas_price), "nonce": hex(nonce), "chainId": 4663}
    log({"ev": "trade_decision", "curve": curve, "token": token, "creator": creator, "resolve_ms": resolve_ms, "stake_usd": stake_usd, "amount_in_eth": amount_in / 1e18, "min_out_tokens": min_out / 1e18, "price_after_creator": p_now})
    h = submit(buy, "buy")
    # the sell sequence HOLD seconds later: approve the curve for the tokens, then sell them all; minOut 0 because the exit is time-based (the runbook says how to bound it)
    time.sleep(HOLD)
    approve = {"to": token, "value": "0x0", "data": "0x" + APPROVE_SEL + abi_word(curve) + abi_word(2 ** 256 - 1), "gas": hex(80_000), "gasPrice": hex(gas_price), "nonce": hex(nonce + 1), "chainId": 4663}
    sell = {"to": curve, "value": "0x0", "data": "0x" + SELL_SEL + abi_word(min_out) + abi_word(0) + abi_word(WALLET), "gas": hex(GAS_UNITS), "gasPrice": hex(gas_price), "nonce": hex(nonce + 2), "chainId": 4663}
    submit(approve, "approve"); submit(sell, "sell")
    log({"ev": "trade_done_dry_run", "curve": curve, "note": "in dry run the bankroll is not changed; the score event 25 s after creation carries the simulated outcome"})


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
    new_day_check()
    log({"ev": "start", "bankroll": BANKROLL, "frac": FRAC, "stake": [STAKE_MIN, STAKE_MAX], "hold": HOLD, "min_creator_supply": MIN_CREATOR_SUPPLY, "switch": [SWITCH_N, SWITCH], "daily_stop": DAILY_STOP, "max_resolve_ms": MAX_RESOLVE_MS, "dry_run": True})
    while True:
        try:
            async with websockets.connect(FEED_URL, open_timeout=15, max_size=None, ping_interval=20) as ws:
                log({"ev": "feed_connected"})
                while True:
                    d = json.loads(await ws.recv()); seen = time.time()
                    for m in d.get("messages", []):
                        for t in decode_batch(m["message"]["message"].get("l2Msg", "")):
                            try:
                                if t[0] != 2:
                                    continue
                                body = rlp.decode(t[1:]); to = body[5]; data = body[7]
                                if len(to) != 20 or "0x" + to.hex() != FACTORY or data[:4] != CREATE_SEL:
                                    continue
                                creator = Account.recover_transaction(t).lower()
                                quote = "0x" + data[4 + 32 * 2 + 12: 4 + 32 * 3].hex(); init_buy = int.from_bytes(data[4 + 32 * 3: 4 + 32 * 4], "big")
                                log({"ev": "creation", "creator": creator, "quote": quote, "init_buy_eth": init_buy / 1e18})
                                threading.Thread(target=handle_creation, args=(creator, quote, init_buy, seen), daemon=True).start()
                            except Exception as e:
                                log({"ev": "error", "stage": "decode", "err": str(e)[:200]})
        except Exception as e:
            log({"ev": "feed_error", "err": str(e)[:200]}); await asyncio.sleep(2)


if __name__ == "__main__":
    print("sniper engine: DRY RUN (submit() logs unsigned transactions and sends nothing); log", LOG_PATH)
    asyncio.run(main())
