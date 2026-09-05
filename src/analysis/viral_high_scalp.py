#!/usr/bin/env python3
"""'Scalp the highs of a viral meme': buy a token that is making new highs on a volume surge above a market-cap
threshold, sell higher (report section 15.1).

Universe: every token with GeckoTerminal 15-minute candles in the study (the leaderboard's memes, i.e. survivors, which
biases a momentum test upward). FDV = close x total supply (gt/pools_v3.json). Signal at candle i, using candles <= i:
FDV >= T, close is the highest close of the trailing 24 h, and the last hour's volume is >= K times the trailing-24h
hourly average ("viral"). Entry at the next candle's open; exits: take-profit +50% (the clip's $10M -> $15M), stop
-25% (stop assumed to fill first when both hit in one candle), time stop H; plus plain fixed-horizon returns with no
exits. Costs: 3% round trip (1% pool fee each side + slippage). Fit = signals before Aug 10 2026, holdout = after.
Placebo: random candles of the same tokens above the same FDV threshold with the same exits. CIs by token-clustered
bootstrap.

usage: python3 viral_high_scalp.py [data-root with gt/]
"""
import json, glob, os, sys, random, statistics as st, collections, datetime

random.seed(7)
ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
pools = json.load(open(os.path.join(ROOT, "gt", "pools_v3.json")))
SPLIT = datetime.datetime(2026, 8, 10, tzinfo=datetime.timezone.utc).timestamp()
COST = 0.03
TOK = {}
for f in glob.glob(os.path.join(ROOT, "gt", "ohlcv", "*.json")):
    a = f.split("/")[-1][:-5]; d = json.load(open(f)); c = sorted(d["candles"], key=lambda x: x[0])
    meta = pools.get(a) or {}
    try:
        sup = float(meta.get("total_supply") or 0) / 10 ** int(meta.get("decimals") or 18)
    except Exception:
        sup = 0
    if len(c) < 120 or sup <= 0:
        continue
    TOK[a] = {"net": d.get("network"), "sym": meta.get("symbol"), "sup": sup, "t": [x[0] for x in c], "o": [x[1] for x in c], "h": [x[2] for x in c], "l": [x[3] for x in c], "c": [x[4] for x in c], "v": [x[5] for x in c]}
print(f"tokens with candles and supply: {len(TOK)} ({collections.Counter(v['net'] for v in TOK.values())})")


def simulate(tk, i, tp, sl, H):
    """enter at open of candle i+1; return (net return, exit reason)"""
    o, h, l, c, t = tk["o"], tk["h"], tk["l"], tk["c"], tk["t"]
    if i + 1 >= len(c) or not o[i + 1]:
        return None
    e = o[i + 1]; end = min(len(c) - 1, i + 1 + H)
    for j in range(i + 1, end + 1):
        if t[j] - t[i + 1] > H * 900 + 3600:
            return c[j - 1] / e - 1 - COST, "gap"
        if sl and l[j] <= e * (1 - sl):
            return -sl - COST, "sl"
        if tp and h[j] >= e * (1 + tp):
            return tp - COST, "tp"
    if end < i + 1 + H and t[end] - t[i + 1] < H * 900 - 900:
        return c[end] / e - 1 - COST, "eod"
    return c[end] / e - 1 - COST, "time"


def signals(T, K, need_high=True, need_vol=True):
    out = []
    for a, tk in TOK.items():
        t, c, v = tk["t"], tk["c"], tk["v"]; last = -999
        for i in range(97, len(c) - 2):
            if t[i] - t[i - 96] > 96 * 900 + 4 * 3600 or i - last < 16:
                continue
            fdv = c[i] * tk["sup"]
            if fdv < T or not c[i]:
                continue
            if need_high and c[i] < max(c[i - 96:i]):
                continue
            v1 = sum(v[i - 3:i + 1]); v24 = sum(v[i - 96:i - 4]) / 23
            if need_vol and (v24 <= 0 or v1 < K * v24 or v1 < 20_000):
                continue
            last = i; out.append((a, i, fdv, v1))
    return out


def placebo(T, n):
    cand = []
    for a, tk in TOK.items():
        for i in range(97, len(tk["c"]) - 2):
            if tk["c"][i] * tk["sup"] >= T and sum(tk["v"][i - 3:i + 1]) >= 20_000:
                cand.append((a, i, 0, 0))
    random.shuffle(cand); return cand[:n]


def stats(rows):
    if not rows:
        return "n=0"
    r = [x[2] for x in rows]; n = len(r); toks = collections.defaultdict(list)
    for a, _, ret, _ in rows:
        toks[a].append(ret)
    keys = list(toks); means = []
    for _ in range(1000):
        smp = [random.choice(keys) for _ in keys]; vals = [x for k in smp for x in toks[k]]; means.append(st.mean(vals))
    means.sort(); reasons = collections.Counter(x[3] for x in rows)
    return f"n={n:4d} tokens={len(keys):3d} mean {100 * st.mean(r):+6.1f}% [{100 * means[25]:+.0f}, {100 * means[975]:+.0f}] median {100 * st.median(r):+6.1f}% win {100 * sum(1 for x in r if x > 0) / n:3.0f}% | exits " + " ".join(f"{k}:{100 * v / n:.0f}%" for k, v in reasons.most_common())


def run(label, sigs, tp, sl, H):
    rows = []
    for a, i, fdv, v1 in sigs:
        res = simulate(TOK[a], i, tp, sl, H)
        if res is None:
            continue
        rows.append((a, TOK[a]["t"][i], res[0], res[1]))
    fit = [x for x in rows if x[1] < SPLIT]; hold = [x for x in rows if x[1] >= SPLIT]
    print(f"{label:52s} all  {stats(rows)}")
    print(f"{'':52s} fit  {stats(fit)}")
    print(f"{'':52s} hold {stats(hold)}")


for T in (1e6, 3e6, 10e6):
    print(f"\n=== FDV >= ${T / 1e6:g}M, new 24h high, 1h volume >= 3x trailing hourly average (net of 3% costs)")
    sigs = signals(T, 3.0)
    for tp, sl, H, lab in ((0.5, 0.25, 96, "TP +50% / SL -25% / 24h"), (0.5, 0.25, 16, "TP +50% / SL -25% / 4h"), (0.3, 0.15, 16, "TP +30% / SL -15% / 4h"), (None, None, 4, "no exits, 1h"), (None, None, 16, "no exits, 4h"), (None, None, 96, "no exits, 24h")):
        run(lab, sigs, tp, sl, H)
    print("--- same threshold, new high only (no volume condition)")
    run("TP +50% / SL -25% / 24h, new high only", signals(T, 0, True, False), 0.5, 0.25, 96)
    print("--- placebo: random candles above the threshold")
    run("TP +50% / SL -25% / 24h, placebo", placebo(T, 3000), 0.5, 0.25, 96)
    run("no exits, 4h, placebo", placebo(T, 3000), None, None, 16)

print("\n=== the clip's literal rule: first time FDV crosses $10M in the data, buy, sell at $15M (+50%) or -25% or 24h")
rows = []
for a, tk in TOK.items():
    c, t = tk["c"], tk["t"]
    for i in range(1, len(c) - 2):
        if c[i] * tk["sup"] >= 10e6 and c[i - 1] * tk["sup"] < 10e6:
            res = simulate(tk, i, 0.5, 0.25, 96)
            if res:
                rows.append((a, t[i], res[0], res[1]))
            break
print(f"{'first $10M cross':52s} all  {stats(rows)}")
for a, t0, r, why in sorted(rows, key=lambda x: -x[2])[:5] + sorted(rows, key=lambda x: x[2])[:5]:
    print(f"   {TOK[a]['sym']:>10s} {datetime.datetime.utcfromtimestamp(t0):%m-%d %H:%M} {100 * r:+6.1f}% {why}")
