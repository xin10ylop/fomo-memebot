#!/usr/bin/env python3
"""The liquidity-provider seat on the mania token's pool, hedged with the perp (report section 16).

Two measurements for the CASHCAT/WETH 0.3% Uniswap v3 pool (a plain v3 pool anyone can LP; the Pons/LONG v4 pools are
hooked and their fee routing is not established):
 1. the real fee yield of a full-range dollar position on Sep 3, using the in-range liquidity read from every Swap event
    (virtual full-range TVL = 2 * L * sqrtP), not the pool's TVL, which understates the denominator 4x in a concentrated pool;
 2. per day since July, from 15-minute candles: the cost of an LP that is delta-hedged every 15 minutes (loss versus
    rebalancing, the sum of 2*sqrt(1+r)/(2+r)-1 over 15-minute returns), the realised volatility, the CASHCAT funding a
    short receives, and the fee yield per day for the measured virtual TVL range.
usage: python3 lp_seat.py [data-root with rh/ and gt/]
"""
import json, math, sys, os, datetime, collections

S = sys.argv[1] if len(sys.argv) > 1 else "."
HERE = os.path.dirname(os.path.abspath(__file__))
ETH = 2445.0
d = json.load(open(os.path.join(S, "rh", "swaps_CASHCAT_WETH_v3a_2026-09-03.json")))
vals = []; vol = 0.0
for r in d:
    w = r["data"][2:]; ws = [int(w[i:i + 64], 16) for i in range(0, len(w), 64)]
    a0, a1 = [x - 2 ** 256 if x >= 2 ** 255 else x for x in ws[:2]]; sqrtP = ws[2] / 2 ** 96; L = ws[3]
    vol += abs(a1) / 1e18 * ETH; vals.append(2 * L * sqrtP / 1e18 * ETH)
vals.sort(); n = len(vals)
print(f"CASHCAT/WETH 0.3% v3, Sep 3: {n} swaps, volume ${vol / 1e6:.2f}M, LP fees ${vol * 0.003 / 1e3:.1f}k | virtual full-range TVL of the in-range liquidity: median ${vals[n // 2] / 1e6:.1f}M (p10 ${vals[n // 10] / 1e6:.1f}M, p90 ${vals[9 * n // 10] / 1e6:.1f}M) vs pool TVL $3.4M")
print(f"  fee yield of a full-range $ position on Sep 3: {100 * vol * 0.003 / vals[n // 2]:.2f}% per day (the TVL proxy would say {100 * vol * 0.003 / 3.44e6:.2f}%)")
addr = "0x020bfc650a365f8bb26819deaabf3e21291018b4"; c = sorted(json.load(open(os.path.join(S, "gt", "ohlcv", addr + ".json")))["candles"])
F = json.load(open(os.path.join(HERE, "..", "..", "data", "raw", "hyperliquid", "funding.json"))).get("CASHCAT") or []
fday = collections.defaultdict(float)
for x in F:
    t = x.get("time") or x.get("t"); fday[datetime.datetime.utcfromtimestamp(t / 1000 if t > 1e11 else t).date()] += float(x.get("fundingRate") or x.get("rate") or 0)
days = collections.defaultdict(list)
for t, o, h, l, cl, v in c:
    days[datetime.datetime.utcfromtimestamp(t).date()].append((t, o, h, l, cl, v))
rows = []
for day, cs in sorted(days.items()):
    if len(cs) < 80:
        continue
    vol = sum(x[5] for x in cs); lvr = 0.0; prev = None; rets = []
    for x in cs:
        if prev and x[4]:
            r = x[4] / prev - 1; rets.append(r); lvr += 2 * math.sqrt(1 + r) / (2 + r) - 1
        prev = x[4]
    rows.append((day, vol, lvr, math.sqrt(sum(r * r for r in rets)), fday.get(day, 0.0)))
print(f"\n{'period':14s} {'days':>4s} {'vol/day $M':>10s} {'15-min rehedged LP cost/day':>27s} {'daily vol':>9s} {'CASHCAT funding/day':>19s} | fee yield/day for a full-range position at virtual TVL $13M / $30M | net/day (fee + funding on the hedged half - LP cost), $13M")
for lab, f in (("all", lambda d: True), ("July", lambda d: d < datetime.date(2026, 8, 1)), ("Aug 1-19", lambda d: datetime.date(2026, 8, 1) <= d < datetime.date(2026, 8, 20)), ("since Aug 20", lambda d: d >= datetime.date(2026, 8, 20))):
    g = [r for r in rows if f(r[0])]
    if not g:
        continue
    n = len(g); vol = sum(r[1] for r in g) / n; lvr = sum(r[2] for r in g) / n; rv = sum(r[3] for r in g) / n; fu = sum(r[4] for r in g) / n
    fee13 = vol * 0.003 / 13.3e6; net = fee13 + 0.5 * fu + lvr
    print(f"{lab:14s} {n:4d} {vol / 1e6:10.2f} {100 * lvr:26.2f}% {100 * rv:8.1f}% {100 * fu:18.3f}% | {100 * fee13:.2f}% / {100 * vol * 0.003 / 30e6:.2f}% | {100 * net:+.2f}%")
print("worst days by rehedged LP cost:", [(str(r[0]), "%.1f%%" % (100 * r[2])) for r in sorted(rows, key=lambda r: r[2])[:5]])
