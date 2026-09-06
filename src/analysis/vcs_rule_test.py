#!/usr/bin/env python3
"""The "Viral Coin Sniping" cheat sheet's entry, tested on every Uniswap v4 pool that opened on one day (report 12.x).

Their rule: watch new and migrated coins; enter only after momentum is confirmed: holders rising fast (5-10 per tick),
five-minute volume rising, chart not already crashed. Measured here as: per pool, per minute after the pool's first
swap, buys in the last minute >= 5 (one swap ~ one buyer; the holder proxy), volume of the last 5 minutes greater than
the previous 5 minutes, close within 10% of the pool's high so far, at least 5 minutes of history. First qualifying
minute per pool; entry at the next swap's price; exits at 15 / 30 / 60 minutes or take-profit +50% / stop -30% within
60 minutes; a pool with no later swap exits at half its last price; costs 3% round trip plus a $300 clip's impact
against a quarter of the last five minutes' volume (capped at 10%), with at least $10k of five-minute volume required. Universe: pools whose Initialize event is on the day (Pons V2
graduations, the 0x7ed5 pad, LONG), priced through the day's quote table. Fit = 00-12 UTC, holdout = 12-24 UTC.

usage: python3 vcs_rule_test.py DAY   (run from the data root)
"""
import json, glob, sys, itertools, collections, random, statistics as st, bisect

random.seed(4); DAY = sys.argv[1]
NATIVE = "0x" + "0" * 40; WETH = "0x0bd7d308f8e1639fab988df18a8011f41eacad73"
DEC = {NATIVE: 18, WETH: 18, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 6, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 6}
PX = {NATIVE: 2445.0, WETH: 2445.0, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 1.0, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 1.0}
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


day_pools = {}
v2tok = set()
for line in open(f"rh/creates_v2_{DAY}.jsonl"):
    b, tx, topics, data = json.loads(line)
    if len(topics) >= 4:
        v2tok.add("0x" + topics[1][-40:].lower())
for x in json.load(open(f"rh/v4init_{DAY}.json")):
    c0, c1 = x["c0"].lower(), x["c1"].lower()
    if c0 in Q and c1 not in Q:
        day_pools[x["pid"].lower()] = (c0, c1, "graduated V2" if c1 in v2tok else "launched on v4")
    elif c1 in Q and c0 not in Q:
        day_pools[x["pid"].lower()] = (c1, c0, "graduated V2" if c0 in v2tok else "launched on v4")
print(f"pools opened on {DAY} with a quote side: {len(day_pools)} ({collections.Counter(v[2] for v in day_pools.values())})", file=sys.stderr)
swaps = collections.defaultdict(list)
for line in itertools.chain.from_iterable(open(p) for p in sorted(glob.glob(f"rh/v4swaps_{DAY}.p*.jsonl"))):
    try:
        b, li, tx, pid, a0, a1, sp, liq = json.loads(line)
    except Exception:
        continue
    m = day_pools.get(pid.lower())
    if not m:
        continue
    q, tok, kind = m; c0 = json.loads(line)[4]
    qa, ta = (a0, a1) if q == day_pools[pid.lower()][0] and q == (x := None) else (None, None)
    # figure out which side is the quote by matching the init record ordering
    pass
    swaps[pid.lower()].append((b, li, a0, a1))
init = {x["pid"].lower(): (x["c0"].lower(), x["c1"].lower()) for x in json.load(open(f"rh/v4init_{DAY}.json"))}
rows = []; skipped = collections.Counter()
for pid, ev in swaps.items():
    q, tok, kind = day_pools[pid]; c0, c1 = init[pid]
    ev.sort(); series = []
    for b, li, a0, a1 in ev:
        qa, ta = (a0, a1) if q == c0 else (a1, a0)
        if not qa or not ta:
            continue
        u = abs(qa) / 10 ** DEC.get(q, 18) * PX[q]; px = u / (abs(ta) / 1e18); series.append((bts(b), px, u, ta > 0))   # ta > 0: user received token = buy
    if len(series) < 20:
        skipped["<20 swaps"] += 1; continue
    t0 = series[0][0]; mins = collections.defaultdict(lambda: [0, 0.0, None, 0.0])   # minute -> [buys, vol, close, high]
    for t, px, u, buy in series:
        k = int((t - t0) // 60); m = mins[k]; m[0] += buy; m[1] += u; m[2] = px; m[3] = max(m[3], px)
    hi = 0.0; sig = None; vol_hist = {}
    for k in range(0, int((series[-1][0] - t0) // 60) + 1):
        m = mins.get(k); hi = max(hi, m[3]) if m else hi; vol_hist[k] = m[1] if m else 0.0
        if k < 10 or not m or m[2] is None:
            continue
        v5 = sum(vol_hist.get(j, 0.0) for j in range(k - 4, k + 1)); v5p = sum(vol_hist.get(j, 0.0) for j in range(k - 9, k - 4))
        if m[0] >= 5 and v5 > v5p and v5 >= 10_000 and m[2] >= 0.9 * hi:      # "strong volume bars": at least $10k in the last five minutes
            sig = (k, v5); break
    if sig is None:
        skipped["no qualifying minute"] += 1; continue
    k, v5 = sig; t_sig = t0 + (k + 1) * 60
    later = [s for s in series if s[0] >= t_sig]
    if not later:
        skipped["no swap after signal"] += 1; continue
    e = later[0][1]; t_in = later[0][0]; imp = min(0.10, 2 * 300 / max(1.0, v5 / 4)); cost = 0.03 + imp   # impact capped at 10%
    def px_at(h):
        cand = [s for s in later if s[0] <= t_in + h]
        return (cand[-1][1], True) if cand and cand[-1][0] > t_in else ((later[-1][1] * 0.5, False) if later[-1][0] <= t_in else (later[-1][1], False))
    out = {"pid": pid, "kind": kind, "t": t_in, "buys_min": mins[k][0], "v5": v5, "n_swaps": len(series)}
    for h, lab in ((900, "15m"), (1800, "30m"), (3600, "60m")):
        p, ok = px_at(h); out[lab] = p / e - 1 - cost
    tp = None
    for s in later[1:]:
        if s[0] > t_in + 3600:
            break
        if s[1] <= e * 0.7:
            tp = -0.30 - cost; break
        if s[1] >= e * 1.5:
            tp = 0.50 - cost; break
    out["tpsl"] = tp if tp is not None else out["60m"]
    rows.append(out)
print(f"pools with swaps {len(swaps)}, signals {len(rows)}, skipped {dict(skipped)}", file=sys.stderr)


def stats(rs, key):
    r = [x[key] for x in rs]
    if not r:
        return "n=0"
    toks = collections.defaultdict(list)
    for x in rs:
        toks[x["pid"]].append(x[key])
    keys = list(toks); means = []
    for _ in range(1000):
        smp = [random.choice(keys) for _ in keys]; means.append(st.mean([v for kk in smp for v in toks[kk]]))
    means.sort()
    return f"n={len(r):4d} mean {100 * st.mean(r):+6.1f}% [{100 * means[25]:+.0f}, {100 * means[975]:+.0f}] median {100 * st.median(r):+6.1f}% win {100 * sum(1 for x in r if x > 0) / len(r):3.0f}%"


import datetime
t_day = datetime.datetime.fromisoformat(DAY + "T00:00:00+00:00").timestamp()
print(f"{DAY}: VCS entry (>= 5 buys in a minute, rising 5-minute volume, within 10% of the high), net of 3% + impact for a $300 clip")
for lab, rs in (("all pools", rows), ("graduated Pons V2", [r for r in rows if r["kind"] == "graduated V2"]), ("launched on v4 (pads, LONG)", [r for r in rows if r["kind"] == "launched on v4"]), ("fit 00-12 UTC", [r for r in rows if r["t"] < t_day + 12 * 3600]), ("holdout 12-24 UTC", [r for r in rows if r["t"] >= t_day + 12 * 3600])):
    print(f"  {lab:30s} " + " | ".join(f"{k}: {stats(rs, k)}" for k in ("15m", "30m", "60m", "tpsl")))
strong = [r for r in rows if r["buys_min"] >= 10]
print(f"  {'>= 10 buys in the minute':30s} " + " | ".join(f"{k}: {stats(strong, k)}" for k in ("15m", "30m", "60m", "tpsl")))
