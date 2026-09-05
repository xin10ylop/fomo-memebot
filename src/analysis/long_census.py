#!/usr/bin/env python3
"""'Catch the tokenized-stock memes early': every LONG (stock-paired) launch of the eight-week census, valued today
(report section 15.2). Inputs: rh/launches_all.json (pull_factory_logs.py) and dex/long_tokens.json (pull_dex_long.py).
Per weekly cohort: launches, share with a DexScreener pair today, share above FDV thresholds, the concentration of value
in the top tokens, and the lottery bound: a $100 ticket on every launch at an assumed initial FDV, valued at today's FDV
with dead tokens at zero. Initial FDV assumptions bracket the Sep 3 replay (p25 $21k, median $67k).

usage: python3 long_census.py [data-root]
"""
import json, sys, os, collections, datetime

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
L = [x for x in json.load(open(os.path.join(ROOT, "rh", "launches_all.json"))) if x.get("venue") == "long"]
D = json.load(open(os.path.join(ROOT, "dex", "long_tokens.json")))
week = lambda ts: (datetime.datetime.utcfromtimestamp(ts) - datetime.timedelta(days=datetime.datetime.utcfromtimestamp(ts).weekday())).strftime("%m-%d")
coh = collections.defaultdict(list)
for x in L:
    coh[week(x["ts"])].append(x)
TH = (1e5, 1e6, 1e7, 1e8, 5e8)
print(f"LONG launches {len(L)}, with a DexScreener pair today {sum(1 for v in D.values() if v)} ({100 * sum(1 for v in D.values() if v) / len(D):.1f}%)")
print(f"{'week':6s} {'launches':>8s} {'pair':>6s} " + " ".join(f"{'>=$' + (str(int(t // 1e6)) + 'M' if t >= 1e6 else str(int(t // 1e3)) + 'k'):>7s}" for t in TH) + f" {'sum FDV $M':>10s} {'top1 %':>6s} {'top5 %':>6s} | $100 ticket on every launch, value today at FDV0 $21k / $67k")
tot_fdv = 0
for w in sorted(coh):
    g = coh[w]; n = len(g)
    fdvs = sorted(((D.get("0x" + x["t1"]) or {}).get("fdv") or 0) for x in g)
    alive = sum(1 for x in g if D.get("0x" + x["t1"]))
    s = sum(fdvs); tot_fdv += s
    cnt = " ".join(f"{sum(1 for f in fdvs if f >= t):7d}" for t in TH)
    top1 = fdvs[-1] / s * 100 if s else 0; top5 = sum(fdvs[-5:]) / s * 100 if s else 0
    m21 = (s / n) / 21_000; m67 = (s / n) / 67_000
    print(f"{w:6s} {n:8d} {alive:6d} {cnt} {s / 1e6:10.1f} {top1:6.0f} {top5:6.0f} | x{m21:6.2f} -> ${100 * m21:8,.0f} / x{m67:5.2f} -> ${100 * m67:7,.0f}")
print(f"{'all':6s} {len(L):8d} {sum(1 for v in D.values() if v):6d} " + " ".join(f"{sum(1 for v in D.values() if v and (v.get('fdv') or 0) >= t):7d}" for t in TH) + f" {tot_fdv / 1e6:10.1f}")
print("\ntop 15 LONG tokens today (FDV, liquidity, quote stock, launch week):")
rows = [((D.get("0x" + x["t1"]) or {}), x) for x in L if D.get("0x" + x["t1"]) and (D["0x" + x["t1"]].get("fdv") or 0) > 0]
rows.sort(key=lambda r: -(r[0].get("fdv") or 0))
for d, x in rows[:15]:
    print(f"  {str(d.get('symbol'))[:14]:14s} FDV ${(d.get('fdv') or 0) / 1e6:7.1f}M liq ${(d.get('liq') or 0) / 1e3:7.0f}k quote {str(d.get('quote'))[:8]:8s} week {week(x['ts'])} vol24h ${(d.get('vol24') or 0) / 1e3:6.0f}k")
q = collections.Counter((D.get("0x" + x["t1"]) or {}).get("quote") for x in L if D.get("0x" + x["t1"]))
print("\nquote assets of the surviving LONG pairs:", q.most_common(8))
