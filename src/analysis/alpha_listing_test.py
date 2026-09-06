#!/usr/bin/env python3
"""Listing catalysts: the reaction to a Binance Alpha listing, with the catalyst scalp's exits (report section 18.3).

Events: Binance Alpha tokens whose listingTime falls in the study window (binance/alpha_listings_window.json from the
public token list; note the list holds currently listed tokens, so delisted ones are missing). For each, the token's
top pool on GeckoTerminal and 15-minute candles around the listing time. Measures: return from the first candle
after listing to +15 min, +1 h, +4 h, +24 h; the scalp rule on 15-minute candles (stop -22%, TP +50%, trail 25%
after +30%, 24 h max); and the pre-listing run-up (−24 h to listing), i.e. how anticipated the catalyst was.

usage: python3 alpha_listing_test.py   (run from the data root; needs gt/ and binance/)
"""
import json, sys, os, bisect, statistics as st
sys.path.insert(0, "/home/user/fomo-memebot/src/collect")
from gt_common import get, discover, best_pool, fetch_ohlcv, NET

ev = json.load(open("binance/alpha_listings_window.json"))
pools = json.load(open("gt/pools_v3.json")) if os.path.exists("gt/pools_v3.json") else {}
out = []
for e in ev:
    net = NET.get(e["chain"].lower()) or e["chain"].lower(); a = e["addr"]
    if a not in pools or not pools[a].get("pools"):
        discover(net, [a], pools)
    P = pools.get(a) or {}
    if not P.get("pools"):
        alt = [k for k, v in pools.items() if (v.get("symbol") or "").lower() == e["symbol"].lower() and v.get("network") == net and v.get("pools")]
        if alt:
            a = alt[0]; P = pools[a]; print(f"  {e['symbol']:10s} matched by symbol to {a}")
    import datetime as _dt
    def created_ts(q):
        try:
            return _dt.datetime.fromisoformat(q["created"].replace("Z", "+00:00")).timestamp()
        except Exception:
            return None
    cands = [q for q in P.get("pools", []) if q.get("base") and (created_ts(q) or 0) <= e["ts"]]
    bp = max(cands, key=lambda q: q["liq"]) if cands else best_pool(P)
    if not bp:
        print(f"  {e['symbol']:10s} no pool on GeckoTerminal"); continue
    cf = f"gt/alpha_{a}_{bp['address'][:10]}.json"
    c = json.load(open(cf)) if os.path.exists(cf) else fetch_ohlcv(net, bp["address"], 15, e["ts"] - 2 * 86400, max_pages=12)
    json.dump(c, open(cf, "w"))
    t = [x[0] for x in c]; i = bisect.bisect_left(t, e["ts"])
    if not t or i >= len(t) or i == 0 or t[i] - e["ts"] > 3600:
        c = fetch_ohlcv(net, bp["address"], 60, e["ts"] - 2 * 86400, max_pages=6); json.dump(c, open(cf.replace(".json", "_h.json"), "w"))
    t = [x[0] for x in c]; o = [x[1] for x in c]; h = [x[2] for x in c]; l = [x[3] for x in c]; cl = [x[4] for x in c]
    i = bisect.bisect_left(t, e["ts"])
    if i >= len(t) or i == 0 or t[i] - e["ts"] > 3600:
        print(f"  {e['symbol']:10s} no candle at listing time (first candle {t[0] if t else None}, last {t[-1] if t else None})"); continue
    en = o[i]
    def at(sec):
        j = bisect.bisect_right(t, e["ts"] + sec) - 1; return cl[j] / en - 1 if j >= i else None
    step = 4 if (len(t) > 1 and t[1] - t[0] >= 3600) else 1; span = 96 // step
    pre = cl[i - 1] / cl[max(0, i - span - 1)] - 1 if i >= 2 else None
    hi = en; ret = None; why = "time"
    for j in range(i + 1, min(len(t), i + span + 1)):
        hi = max(hi, h[j])
        if l[j] <= en * 0.78:
            ret, why = -0.22, "stop"; break
        if h[j] >= en * 1.5:
            ret, why = 0.50, "tp"; break
        if hi / en - 1 >= 0.30 and cl[j] <= hi * 0.75:
            ret, why = cl[j] / en - 1, "trail"; break
    if ret is None:
        ret = at(86400)
    out.append({**e, "pre24h": pre, "r15m": at(900), "r1h": at(3600), "r4h": at(14400), "r24h": at(86400), "scalp": (ret - 0.03) if ret is not None else None, "why": why, "mfe24": max(h[i:i + span + 1]) / en - 1})
print(f"{'listed':12s} {'symbol':10s} {'chain':6s} {'run-up 24h before':>17s} {'+15m':>7s} {'+1h':>7s} {'+4h':>7s} {'+24h':>7s} {'MFE 24h':>8s} {'scalp net':>9s} exit")
import datetime
for r in sorted(out, key=lambda r: r["ts"]):
    f = lambda x: "n/a" if x is None else f"{100 * x:+.0f}%"
    print(f"{datetime.datetime.utcfromtimestamp(r['ts']):%m-%d %H:%M}  {r['symbol']:10s} {r['chain']:6s} {f(r['pre24h']):>17s} {f(r['r15m']):>7s} {f(r['r1h']):>7s} {f(r['r4h']):>7s} {f(r['r24h']):>7s} {f(r['mfe24']):>8s} {f(r['scalp']):>9s} {r['why']}")
if out:
    for k in ("r15m", "r1h", "r4h", "r24h", "scalp"):
        v = [r[k] for r in out if r[k] is not None]
        if v:
            print(f"  {k:6s} n={len(v)} mean {100 * st.mean(v):+.1f}% median {100 * st.median(v):+.1f}% positive {100 * sum(1 for x in v if x > 0) / len(v):.0f}%")
json.dump(out, open("/home/user/fomo-memebot/data/derived/alpha_listing_test.json", "w"))
