import os, statistics as st, random, collections, datetime
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "e0_seat.py")).read().split('print("=== the creation second')[0])
def ci(xs, n=500):
    random.seed(5); b = sorted(st.mean(random.choice(xs) for _ in xs) for _ in range(n)); return b[int(0.025*n)], b[int(0.975*n)]
print("=== the 96-98% surcharges: the same launch's other buys in the same second, and the token's own tier")
for (d, w), dd in data.items():
    if d < "2026-09-16": continue
    for cv, (L, f) in dd.items():
        tier = L["tier"]; pos = L["ts"] % 1.0
        hits = [r for r in L["rows"][1:] if r[1] == "B" and r[5] - tier > 0.9]
        if hits:
            near = [(round(r[0], 2), round(100 * (r[5] - tier), 1), round(r[2], 4)) for r in L["rows"][1:] if r[1] == "B" and r[0] < 1.5]
            print(f"  {cv[:10]} tier {100*tier:.1f}%: buys in the first 1.5 s (t, surcharge %, ETH): {near[:8]}")
print("\n=== speed to money: the creation-second seat by entry time, $25, hold 2 s, tp +50%")
for pname, pf in (("NEW Sep 16-17", lambda d: d >= "2026-09-16"), ("Sep 12-15", lambda d: "2026-09-12" <= d <= "2026-09-15"), ("Sep 11", lambda d: d == "2026-09-11")):
    Ls = [L for (d, w), dd in data.items() if pf(d) for cv, (L, f) in dd.items()]
    print(f"  {pname} ({len(Ls)} launches): " + "  ".join(f"{t:.2f}s {100*st.mean(e0(L, t, 2, 0.5)[0] for L in Ls):+.1f}%" for t in (0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5)))
print("\n=== money per day at $25 (every bundled launch, one position at a time, 6 s busy), by entry time")
byday = collections.defaultdict(list)
for (d, w), dd in data.items():
    if d < "2026-09-09": continue
    for cv, (L, f) in dd.items(): byday[d].append((L["ts"], cv, L))
print(f"  {'day':6s} {'launches':>8s} " + " ".join(f"{'at %.1fs' % t:>14s}" for t in (0.2, 0.3, 0.4, 0.5)))
for d in sorted(byday):
    ls = sorted(byday[d], key=lambda x: x[0]); out = []
    for t_after in (0.2, 0.3, 0.4, 0.5):
        busy = -1e9; pl = 0; n = 0
        for ts, cv, L in ls:
            if ts < busy: continue
            r, g = e0(L, t_after, 2, 0.5); pl += r * g; n += 1; busy = ts + 6
        out.append(f"{n:4d}tr {pl:+7.0f}$")
    print(f"  {d[5:]:6s} {len(ls):8d} " + " ".join(f"{o:>14s}" for o in out))
print("\n=== the tail at 0.3 s, Sep 12-17 pooled: distribution of trade returns")
Ls = [L for (d, w), dd in data.items() if d >= "2026-09-12" for cv, (L, f) in dd.items()]
a = sorted(e0(L, 0.3, 2, 0.5)[0] for L in Ls)
print("  percentiles:", " ".join(f"p{p}: {100*a[int(len(a)*p/100)]:+.0f}%" for p in (1, 5, 10, 25, 50, 75, 90, 95, 99)))
print(f"  worst 10 trades: {[round(100*x) for x in a[:10]]}")
# a run of 20 consecutive trades from $60 at $10: how often does the bankroll halve? (the daily stop)
random.seed(6); ruin = 0; ends = []
for _ in range(3000):
    bank = 60.0
    for roi in random.sample(a, 60):
        bank += min(10.0, bank * 0.15 if bank * 0.15 > 10 else 10.0) * roi
        if bank < 30: ruin += 1; break
    ends.append(bank)
ends.sort(); print(f"  60 trades from $60 at $10, reshuffled 3000x: median end ${ends[1500]:.0f}, 5th pct ${ends[150]:.0f}, hit the -50% daily stop {100*ruin/3000:.1f}% of runs")
