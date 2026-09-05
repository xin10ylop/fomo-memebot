#!/usr/bin/env python3
"""How profitable is the creator fee share without the dump? (report section 13.3)

Reads the per-launch creator-seat rows (creator_seat_{day}.json from creator_seat.py) and the launch quote maps for the
five six-hour windows and prints, for one-off creators, (a) the fee share per launch by initial-buy bucket with a
20-launch batch bootstrap, (b) the no-dump result: fee share plus the initial buy marked at the end of the window
(LIFO exit value, 1% fee) and (c) the fee share by the creator's number of launches that day, tiny stakes only, which is
where the bots' first-time-creator filter shows up. USD at the study's constant prices. No keys, no transactions.

usage: python3 creator_fee_profitability.py [data-root with rh/launch_quotes_*.json]
"""
import json, sys, random, collections, statistics as st, os

random.seed(2)
ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
DER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "derived")
DAYS = ["2026-08-12", "2026-08-20", "2026-08-27", "2026-09-02", "2026-09-03"]
DEC = {"native": 18, "0x0bd7d308f8e1639fab988df18a8011f41eacad73": 18, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 6, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 6}
PX = {"native": 2445.0, "0x0bd7d308f8e1639fab988df18a8011f41eacad73": 2445.0, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 1.0, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 1.0}
FEE = 0.0005 * 2445


def usd(u, q):
    px = PX.get(q)
    return None if px is None else u * 1e18 / 10 ** DEC.get(q, 18) * px


def load(day):
    rows = json.load(open(os.path.join(DER, f"creator_seat_{day}.json")))
    qf = os.path.join(ROOT, "rh", f"launch_quotes_{day}.json")
    if not os.path.exists(qf):
        qf = os.path.join(DER, f"launch_quotes_{day}.json")
    quotes = json.load(open(qf))
    out = []
    for r in rows:
        q = quotes.get(r["curve"]); s = usd(r["q0"], q) if q else None
        if s is None:
            continue
        out.append({"serial": r["serial"], "stake": s, "fee": usd(r["fees"], q), "pnl_end": usd(r["pnl_end"], q), "pnl_60m": usd(r["pnl_60m"], q), "trades": r["n"]})
    return out


def bucket(s):
    return "<$5" if s < 5 else "$5-25" if s < 25 else "$25-100" if s < 100 else ">=$100"


BUCKETS = ["<$5", "$5-25", "$25-100", ">=$100", "all"]
data = {d: load(d) for d in DAYS}

print(f"(a) one-off creators: fee share per launch by initial buy, and a 20-launch batch (10,000 bootstrap draws) net of 20 x ${FEE:.2f} launch fees; '$/h @40' = 40 launches an hour at the mean")
print(f"{'window':10s} {'initial buy':10s} {'n':>5s} {'fee mean':>8s} {'median':>7s} {'p90':>7s} {'>fee':>5s} | {'batch mean':>10s} {'median':>7s} {'p10':>6s} {'p90':>7s} {'P<0':>5s} {'top1':>5s} | {'$/h @40':>8s}")
for day in DAYS:
    b = collections.defaultdict(list)
    for r in data[day]:
        if r["serial"] == 1:
            b[bucket(r["stake"])].append(r["fee"]); b["all"].append(r["fee"])
    for k in BUCKETS:
        fs = sorted(b[k]); n = len(fs)
        if n < 15:
            continue
        B = []; tops = []
        for _ in range(10000):
            smp = [random.choice(fs) for _ in range(20)]; s = sum(smp); B.append(s - 20 * FEE); tops.append(max(smp) / s if s > 0 else 0)
        B.sort()
        print(f"{day:10s} {k:10s} {n:5d} {st.mean(fs):8.2f} {fs[n // 2]:7.2f} {fs[9 * n // 10]:7.2f} {100 * sum(1 for x in fs if x > FEE) / n:4.0f}% | {st.mean(B):10.0f} {B[5000]:7.0f} {B[1000]:6.0f} {B[9000]:7.0f} {100 * sum(1 for x in B if x < 0) / len(B):4.0f}% {100 * st.mean(tops):4.0f}% | {40 * (st.mean(fs) - FEE):8.0f}")

print(f"\n(b) one-off creators, no dump: fee share + initial buy marked at the end of the window (LIFO exit, 1% fee) - launch fee, per launch")
print(f"{'window':10s} {'initial buy':10s} {'n':>5s} {'stake':>6s} {'fee':>7s} {'stake P&L@end':>13s} {'net':>8s} {'median':>7s} {'share>0':>7s} {'net @60m':>8s}")
for day in DAYS:
    b = collections.defaultdict(list)
    for r in data[day]:
        if r["serial"] == 1:
            b[bucket(r["stake"])].append(r); b["all"].append(r)
    for k in BUCKETS:
        g = b[k]; n = len(g)
        if n < 15:
            continue
        tot = sorted(r["fee"] + r["pnl_end"] - FEE for r in g)
        print(f"{day:10s} {k:10s} {n:5d} {st.mean(r['stake'] for r in g):6.0f} {st.mean(r['fee'] for r in g):7.2f} {st.mean(r['pnl_end'] for r in g):13.2f} {st.mean(tot):8.2f} {tot[n // 2]:7.2f} {100 * sum(1 for x in tot if x > 0) / n:6.0f}% {st.mean(r['fee'] + r['pnl_60m'] - FEE for r in g):8.2f}")

print(f"\n(c) fee share per launch by the creator's number of launches that day (initial buy < $25 only); '0 trades' = nobody but the creator traded")
print(f"{'window':10s} {'launches/day':13s} {'n':>5s} {'stake':>6s} {'fee mean':>8s} {'median':>7s} {'p90':>7s} {'>fee':>5s} {'0 trades':>8s} {'net/launch':>10s}")
for day in DAYS:
    b = collections.defaultdict(list)
    for r in data[day]:
        if r["stake"] >= 25:
            continue
        k = "1 (one-off)" if r["serial"] == 1 else "2-9" if r["serial"] < 10 else "10-49" if r["serial"] < 50 else ">=50"
        b[k].append(r)
    for k in ["1 (one-off)", "2-9", "10-49", ">=50"]:
        g = b[k]; n = len(g)
        if n < 10:
            continue
        fs = sorted(r["fee"] for r in g)
        print(f"{day:10s} {k:13s} {n:5d} {st.mean(r['stake'] for r in g):6.1f} {st.mean(fs):8.2f} {fs[n // 2]:7.2f} {fs[9 * n // 10]:7.2f} {100 * sum(1 for x in fs if x > FEE) / n:4.0f}% {100 * sum(1 for r in g if r['trades'] <= 1) / n:7.0f}% {st.mean(fs) - FEE:10.2f}")
