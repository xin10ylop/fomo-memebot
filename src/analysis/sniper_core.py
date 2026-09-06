"""Shared core of the sniper simulations (report sections 14, 19, 20): block times, USD, LIFO curve exits, launch loading, the rule.
Import-safe: nothing runs at import. GAS is a module variable (dollars per round trip) that callers may set.
"""
#!/usr/bin/env python3
"""Capacity, compounding, drawdown and regime switch for the first-block sniper (report section 19).

Standalone re-implementation of sniper_sim.py's rule on the five six-hour windows: buy right after the creator at the
first non-creator price, size min(3% of supply, STAKE), exact LIFO curve exit HOLD seconds later (or a take-profit),
fees 1% each way, GAS dollars per round trip. Filters: creator's first launch of the day, ETH-quoted, optionally the
creator's launch-block buy >= 5% of supply. Reports per window and stake: per-launch ROI with CI, net $, launches,
overlap (how often a hold is still open when the next qualifying launch arrives), the day's cumulative P&L path and its
maximum drawdown, the rolling-score regime switch (trade live only when the mean outcome of the last N scored launches
is above THRESH; every launch is always scored) against always-on, and a compounding schedule.

usage: python3 sniper_capacity.py [GAS_USD_PER_ROUND_TRIP]   (run from the data root)
"""
import json, glob, bisect, datetime, collections, statistics as st, random, sys, os

GAS = 1.0
HERE = os.path.dirname(os.path.abspath(__file__))
tm = json.load(open(os.path.join(HERE, "..", "..", "data", "derived", "token_metrics.json")))
DEC = {"native": 18, "0x0bd7d308f8e1639fab988df18a8011f41eacad73": 18, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 6, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 6}
PX = {"native": 2445.0, "0x0bd7d308f8e1639fab988df18a8011f41eacad73": 2445.0, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 1.0, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 1.0}
blocks = {}
for f in glob.glob("rh/blocks/blocks*.json"):
    try:
        blocks.update(json.load(open(f)))
    except Exception:
        pass
pts = sorted((int(k, 16), v) for k, v in blocks.items()); xs = [p[0] for p in pts]; ys = [p[1] for p in pts]


def bts(b):
    i = bisect.bisect_left(xs, b)
    if i <= 0:
        return ys[0] - (xs[0] - b) / 9.9
    if i >= len(xs):
        return ys[-1] + (b - xs[-1]) / 9.9
    x0, y0, x1, y1 = xs[i - 1], ys[i - 1], xs[i], ys[i]; return y0 + (y1 - y0) * (b - x0) / (x1 - x0)


def usd(units, q):
    px = PX.get(q) or tm.get(q, {}).get("price"); return units * 1e18 / 10 ** DEC.get(q, 18) * px if px else None


def lifo_value(stack, tk):
    out = 0.0; need = tk
    for tokens, quote in reversed(stack):
        if need <= 0:
            break
        take = min(tokens, need); out += quote * take / tokens; need -= take
    return out * 0.99


def load(day):
    creates = {}
    for line in open(f"rh/creates_v2_{day}.jsonl"):
        b, tx, topics, data = json.loads(line)
        if len(topics) < 4:
            continue
        cv = "0x" + topics[2][-40:].lower(); d = data[2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
        creates[cv] = {"ts": bts(b), "creator": "0x" + topics[3][-40:].lower(), "q0": w[1] / 1e18, "tk0": w[2] / 1e18}
    trades = collections.defaultdict(list)
    for line in open(f"rh/v2curve_{day}_12-18.jsonl"):
        b, li, tx, addr, t0, data = json.loads(line)
        if addr not in creates:
            continue
        d = data[2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]; buy = t0 == "0xec36bf57"
        trades[addr].append((b, li, buy, (w[0] if buy else w[1]) / 1e18, (w[1] if buy else w[0]) / 1e18))
    quotes = json.load(open(f"rh/launch_quotes_{day}.json"))
    prior = collections.defaultdict(list)
    for cv, m in creates.items():
        prior[m["creator"]].append(m["ts"])
    for k in prior:
        prior[k].sort()
    return creates, trades, quotes, prior


def sim(cv, creates, trades, quotes, stake, hold=7.0, tp=None, frac=0.05):
    m = creates[cv]; tr = sorted(trades.get(cv, []))
    if len(tr) < 2:
        return None
    t0 = m["ts"]; evs = [(bts(b) - t0, buy, q, tk) for b, li, buy, q, tk in tr]
    first = [e for e in evs[1:] if e[1]]
    if not first:
        return None
    t_in, _, q1, tk1 = first[0]
    if t_in > 3.0:
        return None
    p_in = q1 / tk1; q = quotes.get(cv, "native"); pu = usd(p_in, q)
    if pu is None:
        return None
    tk_bot = frac * 1e9
    if tk_bot * pu > stake:
        tk_bot = stake / pu
    cost = tk_bot * p_in * 1.01
    stack = [[m["tk0"], m["q0"]], [tk_bot, tk_bot * p_in]]; out = None; t_out = t_in + hold
    for t, buy, qq, tk in evs[1:]:
        if t <= t_in:
            continue
        if t >= t_in + hold:                      # the sniper sells at t_in + hold: value the curve as it stands before this later event
            out = lifo_value(stack, tk_bot); break
        if buy:
            stack.append([tk, qq])
        else:
            need = tk
            while need > 1e-12 and stack:
                tokens, quote = stack[-1]; take = min(tokens, need)
                if take >= tokens - 1e-12:
                    stack.pop()
                else:
                    stack[-1] = [tokens - take, quote * (tokens - take) / tokens]
                need -= take
        v = lifo_value(stack, tk_bot)
        if tp and v >= tp * cost:
            out = v; t_out = t; break
    if out is None:
        out = lifo_value(stack, tk_bot)
    pnl_u = usd(out - cost, q); cost_u = usd(cost, q)
    return pnl_u - GAS, cost_u, t0 + t_in, t0 + t_out


def ci(v, B=400):
    n = len(v); bs = sorted(st.mean(random.choices(v, k=n)) for _ in range(B)); return bs[int(0.025 * B)], bs[int(0.975 * B)]




def sim_all(cv, creates, trades, quotes, stake, hold=7.0, frac=0.05):
    """the rule on every eligible launch: when an outside buyer arrived within 3 s the bot is assumed first at that price
    (sim); when nobody did, the bot still bought, 0.2 s after creation at 1.05x the creator's average price (the
    measured first-outside-buy impact), and sold back at hold. Returns (pnl_usd, cost_usd, t_in, t_out, kind)."""
    m = creates[cv]; tr = sorted(trades.get(cv, []))
    if len(tr) < 1:
        return None
    t0 = m["ts"]; evs = [(bts(b) - t0, buy, q, tk) for b, li, buy, q, tk in tr]
    first = [e for e in evs[1:] if e[1]]
    q = quotes.get(cv, "native")
    if first and first[0][0] <= 3.0:
        r = sim(cv, creates, trades, quotes, stake, hold, None, frac)
        return (r + ("followed",)) if r else None
    if m["tk0"] <= 0 or m["q0"] <= 0:
        return None
    p_in = m["q0"] / m["tk0"] * 1.05; pu = usd(p_in, q)
    if pu is None:
        return None
    t_in = 0.2; tk_bot = min(frac * 1e9, stake / pu); cost = tk_bot * p_in * 1.01
    stack = [[m["tk0"], m["q0"]], [tk_bot, tk_bot * p_in]]
    for t, buy, qq, tk in evs[1:]:
        if t <= t_in:
            continue
        if t >= t_in + hold:
            break
        if buy:
            stack.append([tk, qq])
        else:
            need = tk
            while need > 1e-12 and stack:
                tokens, quote = stack[-1]; take = min(tokens, need)
                if take >= tokens - 1e-12:
                    stack.pop()
                else:
                    stack[-1] = [tokens - take, quote * (tokens - take) / tokens]
                need -= take
    out = lifo_value(stack, tk_bot)
    return (usd(out - cost, q) - GAS, usd(cost, q), t0 + t_in, t0 + t_in + hold, "no_follower")
