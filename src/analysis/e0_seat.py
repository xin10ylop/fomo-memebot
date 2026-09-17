"""the creation second itself: what an outsider pays there by block after the creation block, how fast the fastest bots are,
and what a seat 0.1-0.7 s after the creation block would pay at the 6.18% surcharge, ahead of the team's second-one
round and of every bot. Then hold/take-profit variants, tails, and money per day."""
import os, statistics as st, random, collections, datetime
exec(open("/home/user/fomo-memebot/src/analysis/indep_replay.py").read().split("recs = []")[0])
def ci(xs, n=600):
    random.seed(4); b = sorted(st.mean(random.choice(xs) for _ in xs) for _ in range(n)); return b[int(0.025*n)], b[int(0.975*n)]
def e0(L, t_after, hold, tp, surcharge=0.0618, stake=25):
    """enter t_after seconds after the creation block (rows with t < t_after already landed), paying tier + surcharge"""
    rows = L["rows"]; tier = L["tier"]; X, Y = X0, Y0; i = 0
    for i, r in enumerate(rows):
        if i > 0 and r[0] >= t_after: break
        if r[1] == "B": X += r[4]; Y -= r[3]
        else: X -= r[4]; Y += r[3]
    else: i = len(rows)
    fee = tier + surcharge; stake_eth = stake / PX; tk = 0.03 * Y0; net = X * tk / (Y - tk); gross = net / (1 - fee)
    if gross > stake_eth: gross = stake_eth; net = gross * (1 - fee); tk = Y * net / (X + net)
    X += net; Y -= tk; p_in = X / Y; t_out = t_after + hold + 0.3
    for r in rows[i:]:
        if r[0] >= t_out: break
        if r[1] == "B":
            got = Y - X * Y / (X + r[4])
            if got < r[3] * 0.9: continue
            X += r[4]; Y -= got
        else:
            s = min(r[3], Y0 - Y - tk); g = X - X * Y / (Y + s); X -= g; Y += s
        if tp and X / Y >= p_in * (1 + tp) and t_out > r[0] + 0.3: t_out = r[0] + 0.3
    out = (X - X * Y / (Y + tk)) * (1 - tier)
    return ((out - gross) * PX - 0.11) / (gross * PX), gross * PX
print("=== the creation second on Sep 16-17: outsider buys (surcharged) by time after the creation block, and what they paid")
by = collections.defaultdict(list)
for (d, w), dd in data.items():
    if d < "2026-09-16": continue
    for cv, (L, f) in dd.items():
        tier = L["tier"]; pos = L["ts"] % 1.0
        for r in L["rows"][1:]:
            if r[1] == "B" and r[0] < 1.0 - pos and r[5] - tier > 0.001: by[round(r[0], 1)].append(round(100 * (r[5] - tier), 1))
for t in sorted(by): print(f"   {t:.1f} s after creation: {len(by[t]):3d} outsider buys, surcharge {collections.Counter(by[t]).most_common(3)}")
for pname, pf in (("NEW Sep 16-17", lambda d: d >= "2026-09-16"), ("Sep 12-15", lambda d: "2026-09-12" <= d <= "2026-09-15"), ("Sep 11", lambda d: d == "2026-09-11"), ("Sep 7-10", lambda d: "2026-09-07" <= d <= "2026-09-10")):
    Ls = [L for (d, w), dd in data.items() if pf(d) for cv, (L, f) in dd.items()]
    print(f"\n=== {pname}: {len(Ls)} bundled launches; seat in the creation second at the 6.18% surcharge, $25")
    print(f"    {'enter at':>9s} {'hold':>4s} {'tp':>4s} {'mean':>7s} {'95%':>17s} {'median':>7s} {'win':>4s} {'worst':>6s} {'<-30%':>6s} {'$/trade':>8s}")
    for t_after in (0.2, 0.3, 0.5, 0.7):
        for hold, tp in ((1, 0.5), (2, 0.5), (3, 0.5), (2, None)):
            res = [e0(L, t_after, hold, tp) for L in Ls]; a = [r for r, g in res]; lo, hi = ci(a)
            print(f"    {t_after:8.1f}s {hold:4d} {str(tp):>4s} {100*st.mean(a):+6.1f}% [{100*lo:+6.1f}%,{100*hi:+6.1f}%] {100*st.median(a):+6.1f}% {100*sum(x>0 for x in a)/len(a):3.0f}% {100*min(a):+5.0f}% {100*sum(x<-0.3 for x in a)/len(a):5.1f}% {st.mean(r*g for r, g in res):+8.2f}")
print("\n=== money per day at $25, seat 0.3 s after creation, hold 2 s, tp 0.5, every bundled launch, one at a time (8 s busy)")
byday = collections.defaultdict(list)
for (d, w), dd in data.items():
    if d < "2026-09-09": continue
    for cv, (L, f) in dd.items(): byday[d].append((L["ts"], L))
for d in sorted(byday):
    ls = sorted(byday[d]); busy = -1e9; pl = 0; n = 0
    for ts, L in ls:
        if ts < busy: continue
        r, g = e0(L, 0.3, 2, 0.5); pl += r * g; n += 1; busy = ts + 8
    print(f"   {d[5:]}: {n:4d} trades, {pl:+8.0f} $")
