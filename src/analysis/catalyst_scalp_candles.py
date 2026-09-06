#!/usr/bin/env python3
"""The catalyst scalp on every chain with one-minute candles (report section 18.2): leaderboard buys on Solana, BSC,
Base and Robinhood matched to GeckoTerminal 1-minute candles. Entry at the open of the first full minute after the
fill (about 60 s of latency), stop -22% on lows, take-profit +50% on highs, trailing stop 25% below the running high
after +30%, exit at 30 minutes; costs 3% flat (no pool-depth model here). Cohorts by audience and chain; placebo =
the same rule from a random minute 60-90 minutes before the fill (its 30-minute hold ends before the fill).
usage: python3 catalyst_scalp_candles.py   (run from the data root)
"""
import json, glob, os, bisect, random, collections, statistics as st

random.seed(8)
lb = {}
for w in ["24h", "7d", "30d", "all"]:
    for t in json.load(open(f"fapi/lb/{w}.json"))["traders"]:
        lb[t["handle"]] = t
C = {}
for f in glob.glob("gt/ohlcv1m/*.json"):
    d = json.load(open(f)); c = sorted(d["candles"], key=lambda x: x[0])
    if len(c) > 60:
        C[f.split("/")[-1][:-5]] = ([x[0] for x in c], [x[1] for x in c], [x[2] for x in c], [x[3] for x in c], [x[4] for x in c], d.get("network"))
events = []
for f in glob.glob("rh/logs/*.ledger.json"):
    h = f.split("/")[-1][:-12]; fol = lb.get(h, {}).get("followers") or 0
    for r in json.load(open(f)):
        if r["side"] == "buy" and (r["usd"] or 0) >= 1000 and r["ts"]:
            events.append({"h": h, "fol": fol, "tok": r["token"], "ts": r["ts"], "usd": r["usd"], "chain": "robinhood"})
for f in glob.glob("helius/parsed/*.ledger.json"):
    h = f.split("/")[-1][:-12]; fol = lb.get(h, {}).get("followers") or 0
    for r in json.load(open(f)).get("rows", []):
        if r.get("side") == "buy" and (r.get("usd") or 0) >= 1000 and r.get("ts"):
            events.append({"h": h, "fol": fol, "tok": r["mint"], "ts": r["ts"], "usd": r["usd"], "chain": "solana"})
print(f"leader buys >= $1k: {len(events)}; tokens with 1m candles: {len(C)}")


def sim(tok, ts, start_offset=60):
    t, o, h, l, c, net = C[tok]; i = bisect.bisect_left(t, ts + start_offset)
    if i >= len(t) or t[i] - (ts + start_offset) > 180 or not o[i]:
        return None
    e = o[i]; hi = e; ret = None; why = "time"
    for j in range(i + 1, min(len(t), i + 31)):
        if t[j] - t[i] > 40 * 60:
            break
        hi = max(hi, h[j])
        if l[j] <= e * 0.78:
            ret, why = -0.22, "stop"; break
        if h[j] >= e * 1.5:
            ret, why = 0.50, "tp"; break
        if hi / e - 1 >= 0.30 and c[j] <= hi * 0.75:
            ret, why = c[j] / e - 1, "trail"; break
    if ret is None:
        j = min(len(t) - 1, i + 30); ret = c[j] / e - 1
    return ret - 0.03, why, hi / e - 1


rows = []; plac = []
for ev in events:
    if ev["tok"] not in C:
        continue
    r = sim(ev["tok"], ev["ts"])
    if r:
        rows.append({**ev, "ret": r[0], "why": r[1], "mfe": r[2]})
    p = sim(ev["tok"], ev["ts"] - random.randint(3600, 5400), 0)   # placebo window ends before the fill: no overlap with the catalyst
    if p:
        plac.append({**ev, "ret": p[0], "why": p[1]})
print(f"events with candle paths: {len(rows)} ({collections.Counter(r['chain'] for r in rows)}), placebo {len(plac)}")


def stats(rs):
    if not rs:
        return "n=0"
    r = [x["ret"] for x in rs]; keys = collections.defaultdict(list)
    for x in rs:
        keys[x["h"]].append(x["ret"])
    ks = list(keys); means = []
    for _ in range(500):
        smp = [random.choice(ks) for _ in ks]; means.append(st.mean([v for k in smp for v in keys[k]]))
    means.sort(); why = collections.Counter(x["why"] for x in rs)
    return f"n={len(r):4d} posters={len(ks):3d} mean {100 * st.mean(r):+6.1f}% [{100 * means[12]:+.0f}, {100 * means[487]:+.0f}] median {100 * st.median(r):+6.1f}% win {100 * sum(1 for x in r if x > 0) / len(r):3.0f}% | " + " ".join(f"{k}:{100 * v / len(r):.0f}%" for k, v in why.most_common())


print("\nentry 60 s after the fill; stop -22%, TP +50%, trail 25% after +30%, 30 min; costs 3%")
for lab, rs in (("all", rows), ("followers >= 100k", [r for r in rows if r["fol"] >= 100_000]), ("followers >= 300k", [r for r in rows if r["fol"] >= 300_000]), ("solana", [r for r in rows if r["chain"] == "solana"]), ("solana, followers >= 100k", [r for r in rows if r["chain"] == "solana" and r["fol"] >= 100_000]), ("robinhood", [r for r in rows if r["chain"] == "robinhood"]), ("fill >= $5k", [r for r in rows if r["usd"] >= 5000]), ("placebo 60-90 min earlier", plac)):
    print(f"  {label:28s} {stats(rs)}" if (label := lab) else "")
