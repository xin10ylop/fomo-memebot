#!/usr/bin/env python3
"""Skill or beta: do the consistent wallets' entries and exits beat random timing on the same tokens? (report section 17)

For every closed round trip of the given wallets whose token has GeckoTerminal 15-minute candles: the trip's actual
return; the token's candle return over the same interval (execution check); a placebo of 20 entries at random times
within +-24 h of the real entry with the same hold length (timing alpha = actual - placebo median); the entry context
(token return over the prior 1 h / 6 h / 24 h, entry price relative to the trailing-24h high and low); and the exit
context (share of the maximum favourable excursion during the hold that was captured).

usage: python3 wallet_timing.py TAG WALLET [WALLET ...]   (run from the data root with gt/)
"""
import json, sys, os, glob, bisect, random, statistics as st, collections

random.seed(5)
HERE = os.path.dirname(os.path.abspath(__file__)); TAG = sys.argv[1]; wallets = [w.lower() for w in sys.argv[2:]]
H = json.load(open(os.path.join(HERE, "..", "..", "data", "derived", f"wallet_history_{TAG}.json")))
tm = json.load(open(os.path.join(HERE, "..", "..", "data", "derived", "token_metrics.json")))
C = {}
for f in glob.glob("gt/ohlcv/*.json"):
    d = json.load(open(f)); c = sorted(d["candles"])
    if len(c) > 50:
        C[f.split("/")[-1][:-5]] = ([x[0] for x in c], [x[4] for x in c], [x[2] for x in c], [x[3] for x in c])


def px_at(tok, t):
    t_, cl, h, l = C[tok]; i = bisect.bisect_right(t_, t) - 1
    return cl[i] if 0 <= i < len(cl) and t - t_[i] < 3600 else None


def ret(tok, t0, t1):
    a, b = px_at(tok, t0), px_at(tok, t1); return (b / a - 1) if a and b else None


def mfe(tok, t0, t1):
    t_, cl, h, l = C[tok]; i0 = bisect.bisect_right(t_, t0) - 1; i1 = bisect.bisect_right(t_, t1) - 1
    if i0 < 0 or i1 <= i0:
        return None
    e = cl[i0]; return max(h[i0 + 1:i1 + 1]) / e - 1 if e else None


def ctx(tok, t):
    t_, cl, h, l = C[tok]; i = bisect.bisect_right(t_, t) - 1
    if i < 96:
        return None
    e = cl[i]; hi = max(h[i - 96:i]); lo = min(l[i - 96:i])
    return {"r1h": cl[i] / cl[i - 4] - 1 if cl[i - 4] else None, "r6h": cl[i] / cl[i - 24] - 1 if cl[i - 24] else None, "r24h": cl[i] / cl[i - 96] - 1 if cl[i - 96] else None, "pos24": (e - lo) / (hi - lo) if hi > lo else None, "dd_from_high": e / hi - 1 if hi else None}


pooled = []
for w in wallets:
    v = H.get(w)
    if not v:
        continue
    rows = []
    for tok, p in v["tokens"].items():
        if tok not in C:
            continue
        for c in p["closed"]:
            if c["cost"] <= 0:
                continue
            hold = c["t_out"] - c["t_in"]
            if hold < 900:
                continue
            actual = c["proceeds"] / c["cost"] - 1; cand = ret(tok, c["t_in"], c["t_out"])
            plac = [r for r in (ret(tok, c["t_in"] + random.uniform(-86400, 86400), c["t_in"] + random.uniform(-86400, 86400) + hold) for _ in range(20)) if r is not None]
            k = ctx(tok, c["t_in"]); m = mfe(tok, c["t_in"], c["t_out"])
            rows.append({"tok": tok, "sym": tm.get(tok, {}).get("symbol") or tok[:8], "cost": c["cost"], "hold": hold, "actual": actual, "candle": cand, "placebo": st.median(plac) if len(plac) >= 5 else None, "ctx": k, "mfe": m, "t_in": c["t_in"]})
    if not rows:
        print(f"{w[:12]}: no candle-covered trips"); continue
    pooled += rows
    def m(key, f=lambda x: x):
        xs = [f(r[key]) for r in rows if r.get(key) is not None]; return (st.median(xs), len(xs)) if xs else (None, 0)
    ta = [r["actual"] - r["placebo"] for r in rows if r["placebo"] is not None]
    wt = sum(r["cost"] for r in rows); ta_w = sum((r["actual"] - r["placebo"]) * r["cost"] for r in rows if r["placebo"] is not None) / max(1e-9, sum(r["cost"] for r in rows if r["placebo"] is not None))
    ctxs = [r["ctx"] for r in rows if r["ctx"]]
    cap = [r["actual"] / r["mfe"] for r in rows if r.get("mfe") and r["mfe"] > 0.05]
    print(f"\n=== {w[:12]}  candle-covered trips {len(rows)} of {v['summary']['closed_trips']} ({100 * len(rows) / v['summary']['closed_trips']:.0f}%), tokens {len({r['tok'] for r in rows})}")
    print(f"  actual return median {100 * m('actual')[0]:+.1f}% | candle return over the same interval median {100 * m('candle')[0]:+.1f}% | placebo (random timing, same token & hold) median {100 * m('placebo')[0]:+.1f}%")
    print(f"  timing alpha (actual - placebo): median {100 * st.median(ta):+.1f}%, mean {100 * st.mean(ta):+.1f}%, cost-weighted {100 * ta_w:+.1f}%, share > 0: {100 * sum(1 for x in ta if x > 0) / len(ta):.0f}% (n={len(ta)})")
    if ctxs:
        r1 = [c["r1h"] for c in ctxs if c["r1h"] is not None]; r6 = [c["r6h"] for c in ctxs if c["r6h"] is not None]; r24 = [c["r24h"] for c in ctxs if c["r24h"] is not None]; pos = [c["pos24"] for c in ctxs if c["pos24"] is not None]; dd = [c["dd_from_high"] for c in ctxs if c["dd_from_high"] is not None]
        print(f"  entry context: token return before entry, median 1h {100 * st.median(r1):+.1f}% / 6h {100 * st.median(r6):+.1f}% / 24h {100 * st.median(r24):+.1f}% | entry position in the trailing-24h range median {100 * st.median(pos):.0f}% (0 = at the low) | drawdown from 24h high median {100 * st.median(dd):.0f}% | entries in the bottom third of the range {100 * sum(1 for x in pos if x < 1 / 3) / len(pos):.0f}%, top third {100 * sum(1 for x in pos if x > 2 / 3) / len(pos):.0f}%")
    if cap:
        print(f"  exit: share of the max favourable excursion captured, median {100 * st.median(cap):.0f}% (trips with MFE > 5%: {len(cap)})")
    byhold = collections.defaultdict(list)
    for r in rows:
        if r["placebo"] is not None:
            byhold["<6h" if r["hold"] < 21600 else "6-48h" if r["hold"] < 172800 else ">48h"].append(r["actual"] - r["placebo"])
    print("  timing alpha by hold: " + " | ".join(f"{k}: median {100 * st.median(v):+.1f}% (n={len(v)})" for k, v in sorted(byhold.items())))
if pooled:
    ta = [r["actual"] - r["placebo"] for r in pooled if r["placebo"] is not None]
    print(f"\nPOOLED over {len(pooled)} trips: timing alpha median {100 * st.median(ta):+.1f}% mean {100 * st.mean(ta):+.1f}% share>0 {100 * sum(1 for x in ta if x > 0) / len(ta):.0f}% | actual median {100 * st.median([r['actual'] for r in pooled]):+.1f}% placebo median {100 * st.median([r['placebo'] for r in pooled if r['placebo'] is not None]):+.1f}%")
