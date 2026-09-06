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

random.seed(0)
GAS = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
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


def sim(cv, creates, trades, quotes, stake, hold=7.0, tp=None):
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
    tk_bot = 0.03e9
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


DAYS = ["2026-08-12", "2026-08-20", "2026-08-27", "2026-09-02", "2026-09-03"]
STAKES = [20, 50, 100, 200, 300, 500, 1000, 2000]
data = {d: load(d) for d in DAYS}
print(f"gas ${GAS:.2f} per round trip; rule: creator's first launch today, ETH-quoted, buy at the first non-creator price, 3% of supply capped at the stake, exit 7 s later\n")
print("(a) per-launch ROI and net $ per six-hour window by stake (base filter; 'stake' column = creator buy >= 5% of supply filter at the same stake)")
print(f"{'window':10s} {'stake':>6s} {'n':>4s} {'mean ROI':>9s} {'CI':>12s} {'median':>7s} {'win':>4s} {'net $':>8s} {'$/launch':>8s} {'overlap':>7s} {'max DD $':>8s} || {'n':>4s} {'mean ROI':>9s} {'net $':>8s} {'max DD $':>8s}  (creator buy >= 5%)")
results = {}
for day in DAYS:
    creates, trades, quotes, prior = data[day]
    t0d = datetime.datetime.fromisoformat(day + "T00:00:00+00:00").timestamp()
    elig = [cv for cv, m in creates.items() if t0d + 12 * 3600 <= m["ts"] < t0d + 18 * 3600 - 1800 and bisect.bisect_left(prior[m["creator"]], m["ts"]) == 0 and quotes.get(cv) == "native"]
    for stake in STAKES:
        cols = []
        for flt in (lambda cv: True, lambda cv: creates[cv]["tk0"] >= 0.05e9):
            rows = []
            for cv in elig:
                if not flt(cv):
                    continue
                r = sim(cv, creates, trades, quotes, stake)
                if r:
                    rows.append(r)
            rows.sort(key=lambda r: r[2])
            if len(rows) < 20:
                cols.append(None); continue
            roi = [p / c for p, c, a, b in rows]; lo, hi = ci(roi); net = sum(p for p, c, a, b in rows)
            cum = 0.0; peak = 0.0; dd = 0.0
            for p, c, a, b in rows:
                cum += p; peak = max(peak, cum); dd = min(dd, cum - peak)
            overlap = sum(1 for i in range(1, len(rows)) if rows[i][2] < rows[i - 1][3]) / len(rows)
            cols.append({"n": len(rows), "mean": st.mean(roi), "lo": lo, "hi": hi, "med": st.median(roi), "win": sum(1 for x in roi if x > 0) / len(roi), "net": net, "dd": dd, "overlap": overlap, "rows": rows})
        results[(day, stake)] = cols
        a, b2 = cols
        if a:
            line = f"{day:10s} {stake:6d} {a['n']:4d} {100 * a['mean']:+8.1f}% [{100 * a['lo']:+4.0f},{100 * a['hi']:+4.0f}] {100 * a['med']:+6.0f}% {100 * a['win']:3.0f}% {a['net']:8,.0f} {a['net'] / a['n']:8,.1f} {100 * a['overlap']:6.0f}% {a['dd']:8,.0f}"
            line += f" || {b2['n']:4d} {100 * b2['mean']:+8.1f}% {b2['net']:8,.0f} {b2['dd']:8,.0f}" if b2 else " || (too few)"
            print(line)
    print()

for fi, flab in ((0, "base filter"), (1, "creator buy >= 5% of supply")):
    print(f"(b) regime switch, {flab}: score every eligible launch (outcome known 7 s later); trade live only while the mean of the last 30 scored outcomes is >= +5% of stake; $300 stake, one position at a time")
    print(f"{'window':10s} {'always-on net $':>15s} {'switched net $':>14s} {'live share':>10s} {'always-on max DD':>16s} {'switched max DD':>15s} {'switched, 1 at a time':>21s}")
    for day in DAYS:
        cols = results.get((day, 300))
        if not cols or not cols[fi]:
            print(f"{day:10s} (too few)"); continue
        rows = cols[fi]["rows"]; hist = []; cum_a = cum_s = cum_1 = 0.0; pk_a = pk_s = 0.0; dd_a = dd_s = 0.0; live = 0; busy = 0
        for p, c, a, b in rows:
            on = len(hist) >= 30 and st.mean(hist[-30:]) >= 0.05
            cum_a += p; pk_a = max(pk_a, cum_a); dd_a = min(dd_a, cum_a - pk_a)
            if on:
                cum_s += p; live += 1
                if a >= busy:
                    cum_1 += p; busy = b
            pk_s = max(pk_s, cum_s); dd_s = min(dd_s, cum_s - pk_s)
            hist.append(p / c)
        print(f"{day:10s} {cum_a:15,.0f} {cum_s:14,.0f} {100 * live / len(rows):9.0f}% {dd_a:16,.0f} {dd_s:15,.0f} {cum_1:21,.0f}")
    print()

print("(c) compounding from a small bankroll: stake = clamp(bankroll x FRAC, 50, 300), one position at a time, regime switch on, trades in time order; ROI at the stake actually used is taken from the nearest simulated stake; stops for the day at -30% of the starting bankroll or when it cannot fund a $50 stake")
for day in ("2026-09-02", "2026-09-03", "2026-08-27", "2026-08-20"):
    for fi, flab in ((0, "base"), (1, "creator buy >= 5%")):
        for start, FRAC in ((300, 0.2), (500, 0.2), (1000, 0.2), (300, 0.5)):
            by_stake = {stk: {r[2]: r for r in results[(day, stk)][fi]["rows"]} for stk in STAKES if results.get((day, stk)) and results[(day, stk)][fi]}
            if 300 not in by_stake:
                continue
            bank = float(start); path = [bank]; busy = 0; hist = []; n = 0; stopped = False
            for t_in, r300 in sorted(by_stake[300].items()):
                on = len(hist) >= 30 and st.mean(hist[-30:]) >= 0.05; hist.append(r300[0] / r300[1])
                if bank < 0.7 * start:
                    stopped = True                     # daily stop: down 30% from the starting bankroll, stop for the day
                if not on or t_in < busy or stopped:
                    continue
                stake = min(max(bank * FRAC, 50.0), 300.0)
                if bank < 50:
                    break
                near = min(by_stake, key=lambda s_: abs(s_ - stake)); rr = by_stake[near].get(t_in)
                if not rr:
                    continue
                bank += stake * (rr[0] / rr[1]); busy = rr[3]; path.append(bank); n += 1
            print(f"  {day} {flab:20s} start ${start:>5,} sizing {100 * FRAC:.0f}%: end ${bank:8,.0f} after {n:3d} trades, low ${min(path):,.0f}{' (daily stop hit)' if stopped else ''}")
