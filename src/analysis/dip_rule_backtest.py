#!/usr/bin/env python3
"""The dip-buyer wallet's behaviour as a rule, tested on every token with 15-minute candles (report section 17.4).

Rule (from wallet 0x6ac5's measured entries): token pool at least 1 day old, trailing-24h candle volume >= VOL,
entry when the close is >= DD below the trailing-24h high and in the bottom third of the trailing-24h range, one
entry per token per 6 h; exits at fixed horizons (6 h / 12 h / 24 h) or TP +15% / SL -15% / 24 h; costs 3% round
trip. Fit = before Aug 10, holdout = after; token-clustered bootstrap CIs; placebo = random candles of the same tokens
passing the volume filter. The universe (leaderboard-traded tokens) is survivor-biased, which flatters the result.

usage: python3 dip_rule_backtest.py [data-root with gt/]
"""
import json, glob, os, sys, random, statistics as st, collections, datetime

random.seed(3)
ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SPLIT = datetime.datetime(2026, 8, 10, tzinfo=datetime.timezone.utc).timestamp(); COST = 0.03
TOK = {}
for f in glob.glob(os.path.join(ROOT, "gt", "ohlcv", "*.json")):
    d = json.load(open(f)); c = sorted(d["candles"], key=lambda x: x[0])
    if len(c) < 120 or d.get("network") != "robinhood":
        continue
    TOK[f.split("/")[-1][:-5]] = {"t": [x[0] for x in c], "o": [x[1] for x in c], "h": [x[2] for x in c], "l": [x[3] for x in c], "c": [x[4] for x in c], "v": [x[5] for x in c], "created": (d.get("pool") or {}).get("created")}


def simulate(tk, i, tp, sl, H):
    o, h, l, c, t = tk["o"], tk["h"], tk["l"], tk["c"], tk["t"]
    if i + 1 >= len(c) or not o[i + 1]:
        return None
    e = o[i + 1]; end = min(len(c) - 1, i + 1 + H)
    for j in range(i + 1, end + 1):
        if t[j] - t[i + 1] > H * 900 + 3600:
            return c[j - 1] / e - 1 - COST
        if sl and l[j] <= e * (1 - sl):
            return -sl - COST
        if tp and h[j] >= e * (1 + tp):
            return tp - COST
    return c[end] / e - 1 - COST


def signals(DD, VOL, need_dip=True):
    out = []
    for a, tk in TOK.items():
        t, c, h, l, v = tk["t"], tk["c"], tk["h"], tk["l"], tk["v"]; last = -999
        for i in range(97, len(c) - 2):
            if t[i] - t[i - 96] > 96 * 900 + 4 * 3600 or i - last < 24 or not c[i]:
                continue
            if sum(v[i - 96:i]) < VOL:
                continue
            hi = max(h[i - 96:i]); lo = min(l[i - 96:i])
            if need_dip:
                if hi <= 0 or c[i] / hi - 1 > -DD or (hi > lo and (c[i] - lo) / (hi - lo) > 1 / 3):
                    continue
            elif random.random() > 0.15:
                continue
            last = i; out.append((a, i))
    return out


def stats(rows):
    if not rows:
        return "n=0"
    r = [x[2] for x in rows]; n = len(r); toks = collections.defaultdict(list)
    for a, _, ret in rows:
        toks[a].append(ret)
    keys = list(toks); means = []
    for _ in range(1000):
        smp = [random.choice(keys) for _ in keys]; means.append(st.mean([x for k in smp for x in toks[k]]))
    means.sort()
    return f"n={n:5d} tokens={len(keys):3d} mean {100 * st.mean(r):+6.1f}% [{100 * means[25]:+.0f}, {100 * means[975]:+.0f}] median {100 * st.median(r):+6.1f}% win {100 * sum(1 for x in r if x > 0) / n:3.0f}%"


def run(label, sigs, tp, sl, H):
    rows = []
    for a, i in sigs:
        res = simulate(TOK[a], i, tp, sl, H)
        if res is not None:
            rows.append((a, TOK[a]["t"][i], res))
    fit = [x for x in rows if x[1] < SPLIT]; hold = [x for x in rows if x[1] >= SPLIT]
    print(f"{label:46s} all  {stats(rows)}\n{'':46s} fit  {stats(fit)}\n{'':46s} hold {stats(hold)}")


print(f"tokens {len(TOK)} (Robinhood, 15-minute candles)")
for DD, VOL in ((0.20, 200_000), (0.20, 1_000_000), (0.30, 200_000), (0.15, 200_000)):
    sigs = signals(DD, VOL)
    print(f"\n=== dip >= {100 * DD:.0f}% below the 24h high, bottom third of the range, trailing-24h volume >= ${VOL / 1e6:g}M; net of 3% costs")
    for tp, sl, H, lab in ((None, None, 24, "hold 6h"), (None, None, 48, "hold 12h"), (None, None, 96, "hold 24h"), (0.15, 0.15, 96, "TP +15% / SL -15% / 24h"), (0.30, 0.20, 96, "TP +30% / SL -20% / 24h")):
        run(lab, sigs, tp, sl, H)
    print("--- placebo: random candles, same volume filter, hold 12h")
    run("placebo hold 12h", signals(DD, VOL, need_dip=False), None, None, 48)
