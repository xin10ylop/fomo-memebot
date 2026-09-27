"""world.py (edge_check/A): test 5. The sequencer's cadence (blocks in the creation second and the next two, from the crowd
files' k over every launch and from the tapes' block stamps), the curves' runtime code (eth_getCode hash on 4 fit and 4 recent
fire curves, the factory, and the curve's creation selector), and the fleets around our own bursts (Sep 26 09:15 onward).
The fee schedule by second is in price.txt (implied fee from the curve state before every buy and sell of the 91 tapes).
    python3 data/derived/edge_check/A/world.py"""
import sys, json, gzip, hashlib, collections, statistics as st, time
sys.path.insert(0, "data/derived/edge_check/A"); sys.path.insert(0, "src/analysis")
from common import *
import live_vs_table as lv
T = json.load(gzip.open(A + "tapes.json.gz", "rt")); F = json.load(open(A + "fires_features.json"))
print("=== blocks in the creation second after b0 (k), every qualifying launch")
for s, ws in (("fit", FIT), ("recent", REC)):
    ks = [r["k"] for r in all_launches(ws)]; c = collections.Counter(ks)
    print(f"  {s:6s} n {len(ks)} mean k {st.mean(ks):.2f}  distribution {dict(sorted(c.items()))}")
print("=== blocks per second, seconds T0+1 and T0+2 (the tapes' stamps b0..b0+30, fires)")
for s in ("fit", "rec"):
    n1, n2 = [], []
    for x in F:
        if x["set"] != s: continue
        ts = [v for kk, v in T[x["cv"]]["ts"].items()]; c = collections.Counter(ts); n1.append(c.get(x["T0"] + 1, 0)); n2.append(c.get(x["T0"] + 2, 0))
    print(f"  {s:4s} second +1: mean {st.mean(n1):.2f} blocks {dict(sorted(collections.Counter(n1).items()))}; second +2: mean {st.mean(n2):.2f} {dict(sorted(collections.Counter(n2).items()))}")
print("=== creation selector of every fire's creation tx:", dict(collections.Counter(T[x["cv"]]["sel"] for x in F)))
print("=== runtime code (current state; a curve's code does not change unless it is a proxy)")
fit = sorted([x for x in F if x["set"] == "fit"], key=lambda x: x["T0"]); rec = sorted([x for x in F if x["set"] == "rec"], key=lambda x: x["T0"])
codes = {}
pick = [fit[0], fit[len(fit)//3], fit[2*len(fit)//3], fit[-1], rec[0], rec[len(rec)//3], rec[2*len(rec)//3], rec[-1]]
for x in pick:
    code = lv.call("eth_getCode", [x["cv"], "latest"]); time.sleep(0.15); codes[x["cv"]] = bytes.fromhex(code[2:])
    print(f"  {x['set']:4s} {hms(x['T0'])} {x['cv'][:10]} code {len(code)//2 - 1} bytes sha256 {hashlib.sha256(code.encode()).hexdigest()[:16]}")
cs = list(codes.values()); diff = sorted({i for c in cs[1:] for i in range(min(len(c), len(cs[0]))) if c[i] != cs[0][i]})
runs = []; 
for i in diff:
    if runs and i <= runs[-1][1] + 32: runs[-1][1] = i
    else: runs.append([i, i])
print(f"  the 8 curves' codes differ from the first at {len(diff)} byte positions, in {len(runs)} runs: {[(a, b - a + 1) for a, b in runs][:12]} (embedded immutables if short and fixed)")
code = lv.call("eth_getCode", [lv.V2F, "latest"]); print(f"  factory {lv.V2F[:10]} code {len(code)//2 - 1} bytes sha256 {hashlib.sha256(code.encode()).hexdigest()[:16]}")
print("=== fires after our first live burst (Sep 26 09:24 UTC) vs the recent fires before it")
import calendar; t_live = calendar.timegm((2026, 9, 26, 9, 15, 0))  # live from Sep 26 09:15 UTC (runbook 5q)
for name, S in (("before", [x for x in rec if x["T0"] < t_live]), ("after", [x for x in rec if x["T0"] >= t_live])):
    v = lambda f: st.mean([f(x) for x in S])
    print(f"  {name:6s} n {len(S)} h300 mean {v(lambda x: x['ret']['300']):+.1%}  h15 {v(lambda x: x['ret']['15']):+.1%}  rival shots by k-2 {v(lambda x: x['shots_k2']):.1f}  seat-block buys {v(lambda x: x['seat_buys']):.1f}  outsider ETH to +300 {v(lambda x: x['out_eth_total']):.2f}  named sold by +300 {v(lambda x: x['named_sold_frac']['300'] or 0):.0%}")
# does anyone trade within 3 blocks of our 300-block exit more than elsewhere? events per block in bE1+297..303 vs bE1+200..296
for s in ("fit", "rec"):
    near, base = [], []
    for x in F:
        if x["set"] != s: continue
        c = collections.Counter(e["bn"] - x["bE1"] for e in T[x["cv"]]["rows"] if e["k"] == "S")
        near.append(sum(c.get(i, 0) for i in range(297, 304)) / 7); base.append(sum(c.get(i, 0) for i in range(200, 297)) / 97)
    print(f"  sells per block at seat+297..303 {st.mean(near):.3f} vs seat+200..296 {st.mean(base):.3f} ({s})")
