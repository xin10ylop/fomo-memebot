#!/usr/bin/env python3
"""Hindsight-free check of the dip rule on one whole day: every Uniswap v4 pool on Robinhood Chain, candles built from
the day's own swap stream, no survivor selection (report section 17.4).

15-minute candles per pool are built from every v4 Swap of the day (pools priced through v4init_all + the day's inits,
quote = ETH/WETH/USDG/stock tokens from rh/quote_prices_{DAY}.json). Universe at signal time: pools whose trailing
12-hour volume is >= VOL and whose pool is >= 1 day old (init block). Signal: close >= DD below the trailing-12h high
and in the bottom third of the trailing-12h range; one signal per pool per 6 h; entry at the next candle open; exits at
fixed 3 h / 6 h holds; costs 3% plus a constant-product impact of CLIP dollars each way against the trailing-12h
volume / 4 as a liquidity proxy (flagged). Placebo: random candles passing the same volume filter.

usage: python3 dip_rule_v4day.py DAY [VOL] [DD] [CLIP]   (run from the data root)
"""
import json, glob, sys, os, itertools, collections, random, statistics as st, bisect

random.seed(9)
DAY = sys.argv[1]; VOL = float(sys.argv[2]) if len(sys.argv) > 2 else 100_000; DD = float(sys.argv[3]) if len(sys.argv) > 3 else 0.20; CLIP = float(sys.argv[4]) if len(sys.argv) > 4 else 300.0
NATIVE = "0x" + "0" * 40; WETH = "0x0bd7d308f8e1639fab988df18a8011f41eacad73"
DEC = {NATIVE: 18, WETH: 18, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 6, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 6}
PX = {NATIVE: 2445.0, WETH: 2445.0, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 1.0, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 1.0}
FIXED = set(PX)
for c, v in json.load(open(f"rh/quote_prices_{DAY}.json")).items():
    PX[c] = v["price"]; DEC.setdefault(c, 18)
Q = set(PX)
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


pools = {}
for src in glob.glob("rh/v4init_*.json"):
    d = json.load(open(src)); d = d["pools"] if isinstance(d, dict) else d
    for x in d:
        pools[x["pid"].lower()] = (x["c0"].lower(), x["c1"].lower(), x["b"])
cand = collections.defaultdict(lambda: collections.defaultdict(lambda: [None, 0.0, 0.0, None, 0.0]))   # pid -> bucket -> [o,h,l,c,vol]
t0_day = None
for line in itertools.chain.from_iterable(open(p) for p in sorted(glob.glob(f"rh/v4swaps_{DAY}.p*.jsonl"))):
    try:
        b, li, tx, pid, a0, a1, sp, liq = json.loads(line)
    except Exception:
        continue
    m = pools.get(pid.lower())
    if not m:
        continue
    c0, c1, ib = m
    if c0 in Q and c1 not in Q:
        q, qa, ta = c0, a0, a1
    elif c1 in Q and c0 not in Q:
        q, qa, ta = c1, a1, a0
    else:
        continue
    if not qa or not ta:
        continue
    u = abs(qa) / 10 ** DEC.get(q, 18) * PX[q]; px = u / (abs(ta) / 1e18)
    t = bts(b); k = int(t // 900)
    c = cand[pid.lower()][k]
    if c[0] is None:
        c[0] = px; c[1] = px; c[2] = px
    c[1] = max(c[1], px); c[2] = min(c[2], px); c[3] = px; c[4] += u
print(f"pools with priced swaps: {len(cand)}", file=sys.stderr)
rows = []; plac = []
for pid, bk in cand.items():
    ks = sorted(bk); age_b = pools[pid][2]
    if len(ks) < 60:
        continue
    t = ks; o = [bk[k][0] for k in ks]; h = [bk[k][1] for k in ks]; l = [bk[k][2] for k in ks]; c = [bk[k][3] for k in ks]; v = [bk[k][4] for k in ks]
    last = -999
    for i in range(48, len(ks) - 13):
        if t[i] - t[i - 48] > 60 or i - last < 24:          # need ~12h of candle history (buckets are 15 min, keys are bucket numbers)
            continue
        vol12 = sum(v[i - 48:i])
        if vol12 < VOL or (t[i] * 900 - bts(age_b)) < 86400:
            continue
        hi = max(h[i - 48:i]); lo = min(l[i - 48:i])
        dip = c[i] / hi - 1 <= -DD and (hi > lo and (c[i] - lo) / (hi - lo) <= 1 / 3)
        e = o[i + 1]
        if not e:
            continue
        imp = 2 * CLIP / max(1.0, vol12 / 4)                    # crude: liquidity ~ a quarter of 12h volume
        rec = []
        for H in (12, 24):
            j = i + 1 + H
            if j < len(ks) and t[j] - t[i + 1] <= H + 4:
                rec.append(c[j] / e - 1 - 0.03 - imp)
            else:
                rec.append(None)
        if dip:
            last = i; rows.append((pid, rec))
        elif random.random() < 0.05:
            plac.append((pid, rec))


def stats(rs, idx):
    xs = [(p, r[idx]) for p, r in rs if r[idx] is not None]
    if not xs:
        return "n=0"
    toks = collections.defaultdict(list)
    for p, x in xs:
        toks[p].append(x)
    keys = list(toks); means = []
    for _ in range(1000):
        smp = [random.choice(keys) for _ in keys]; means.append(st.mean([x for k in smp for x in toks[k]]))
    means.sort(); r = [x for p, x in xs]
    return f"n={len(r):5d} pools={len(keys):4d} mean {100 * st.mean(r):+6.1f}% [{100 * means[25]:+.0f}, {100 * means[975]:+.0f}] median {100 * st.median(r):+6.1f}% win {100 * sum(1 for x in r if x > 0) / len(r):3.0f}%"


print(f"{DAY}: dip >= {100 * DD:.0f}% below the 12h high, bottom third, trailing-12h volume >= ${VOL / 1e3:.0f}k, pool >= 1 day old; net of 3% + impact for a ${CLIP:.0f} clip")
print(f"  dip signals, hold 3h : {stats(rows, 0)}")
print(f"  dip signals, hold 6h : {stats(rows, 1)}")
print(f"  placebo,     hold 3h : {stats(plac, 0)}")
print(f"  placebo,     hold 6h : {stats(plac, 1)}")
