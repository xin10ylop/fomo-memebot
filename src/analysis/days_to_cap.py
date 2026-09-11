"""how long from the live wallet to the $300 cap: every measured trading day (12:00 -> 05:00 UTC), replayed with the engine's
sizing (15%, $25 floor, $300 cap, one position at a time, gas $0.10, daily stop -50%), then day sequences: yesterday repeated,
the measured days in order, and bootstrapped full days (one afternoon + one evening + one night drawn from the measured ones)."""
import sys, statistics as st, collections, datetime, random
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX; START = 92.0; CAP_BANK = 300 / 0.15
data = RH.load(); data.update(RH.load_new())
recs = []
for k, launches in data.items():
    for cv, (L, f) in launches.items():
        kept = f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)
        by = {}
        for stk in RH.STAKES:
            x = RH.replay(L, stk / PX, hold=5.0, tp=0.5); by[stk] = (x[0] * PX - 0.10, x[1] * PX, L["ts"] + x[2], L["ts"] + x[3], x[4])
        h = int(f["hour"]); hour_ok = h >= 12 or h < 5
        recs.append(dict(k=k, t=by[25][2], kept=kept and by[25][4] != "reverted" and hour_ok, by=by, hour=h,
                         day=datetime.datetime.utcfromtimestamp(by[25][2] - 6 * 3600).strftime("%m-%d"), roi=by[25][0] / by[25][1] if by[25][1] > 1e-6 else 0.0))
recs.sort(key=lambda x: x["t"])
kept = [x for x in recs if x["kept"]]
def roi_at(x, stake):
    near = min(RH.STAKES, key=lambda s_: abs(s_ - stake)); rr = x["by"][near]
    if rr[4] == "reverted" or rr[1] <= 1e-6: return None, 0.0
    return rr[0] / rr[1], rr[3]
def run_day(xs, bank, frac=0.15, cap=300.0, stop=0.5):
    """replay one day's kept launches in time order from bank; returns end bank, trades, stopped"""
    start = bank; busy = -1e9; n = 0
    for x in xs:
        if x["t"] < busy: continue
        if bank < start * stop: return bank, n, True
        stake = min(max(bank * frac, 25.0), min(cap, bank)); r, exit_t = roi_at(x, stake)
        if r is None: continue
        bank += stake * r; busy = exit_t; n += 1
    return bank, n, False
days = collections.defaultdict(list)
for x in kept: days[x["day"]].append(x)
blocks = collections.defaultdict(set)
for x in recs: blocks[x["day"]].add(x["k"][1])
print(f"=== {len(kept)} rule-passing launches on {len(days)} measured trading days (12:00 -> 05:00 UTC); stake = 15% of bankroll, $25 floor, $300 cap")
print(f"the $300 stake is reached at a bankroll of ${CAP_BANK:,.0f}\n")
print(f"{'day':6s} {'blocks measured':22s} {'trades':>6s} {'ROI@$25':>8s} {'ROI@$300':>9s} {'$25 flat':>9s} {'from $92':>9s} {'from $500':>10s} {'from $2,000':>11s}")
for d in sorted(days):
    xs = days[d]; r25 = st.mean(x["roi"] for x in xs); r300 = st.mean(r for r in (roi_at(x, 300)[0] for x in xs) if r is not None)
    flat = sum(x["by"][25][0] for x in xs)
    e92 = run_day(xs, 92.0); e500 = run_day(xs, 500.0); e2k = run_day(xs, 2000.0)
    print(f"{d:6s} {', '.join(sorted(blocks[d])):22s} {len(xs):6d} {100*r25:+7.1f}% {100*r300:+8.1f}% {flat:+9.0f} {e92[0]-92:+9.0f} {e500[0]-500:+10.0f} {e2k[0]-2000:+11.0f}{'  stop' if e2k[2] or e92[2] else ''}")
def until_cap(day_seq, bank=START, limit=60):
    """day_seq yields lists of launches; returns the day count at which bank first reaches CAP_BANK (None if not within limit) and the path"""
    path = [bank]
    for i, xs in enumerate(day_seq, 1):
        bank = run_day(xs, bank)[0]; path.append(bank)
        if bank >= CAP_BANK: return i, path
        if i >= limit: return None, path
    return None, path
# 1. yesterday repeated
y = days["09-10"]
def rep(xs):
    while True: yield xs
n, path = until_cap(rep(y))
print(f"\n--- yesterday (09-10, all three blocks) repeated: reaches ${CAP_BANK:,.0f} on day {n}; path " + " -> ".join(f"${b:,.0f}" for b in path[:n + 1]))
# 2. the measured days in order (partial days as measured), from $92
bank = START; print("\n--- the measured days in order from $92 (a day with only the afternoon measured counts only the afternoon):")
for d in sorted(days):
    b2, nt, stopped = run_day(days[d], bank); print(f"   {d}: ${bank:,.0f} -> ${b2:,.0f} ({nt} trades{', stopped' if stopped else ''})"); bank = b2
    if bank >= CAP_BANK: print(f"   cap reached on {d}"); break
# 3. bootstrapped full days
byblock = collections.defaultdict(dict)
for x in kept:
    b = x["k"][1]; byblock[b].setdefault(x["day"], []).append(x)
print("\n--- block-days available: " + ", ".join(f"{b}: {len(v)}" for b, v in sorted(byblock.items())))
random.seed(7)
def boot_day():
    xs = []
    for b, shift in (("12-18", 0), ("18-24", 0), ("0-6", 0)):
        d = random.choice(list(byblock[b])); xs += byblock[b][d]
    return xs   # blocks are disjoint in the hour of day, so time order within the day is by hour
def boot_seq():
    while True:
        xs = boot_day(); xs = sorted(xs, key=lambda x: (x["hour"] < 12, x["hour"], x["t"]))
        yield xs
res = []; ends7 = []
for _ in range(3000):
    n, path = until_cap(boot_seq()); res.append(n if n else 61); ends7.append(path[min(7, len(path) - 1)])
res.sort(); ends7.sort()
q = lambda a, p: a[int(p * (len(a) - 1))]
print(f"\n--- bootstrapped full days from $92: days to ${CAP_BANK:,.0f}: median {q(res,0.5)}, 10th-90th pct {q(res,0.1)}-{q(res,0.9)}, worst of 3000 runs {res[-1]}; never within 60 days: {sum(1 for r in res if r == 61)}")
print(f"    bankroll after 7 days: median ${q(ends7,0.5):,.0f}, 10th pct ${q(ends7,0.1):,.0f}, 90th pct ${q(ends7,0.9):,.0f}")
# what a day at the cap makes
atcap = [run_day(days[d], 2000.0)[0] - 2000 for d in sorted(days)]
print(f"\n--- a day at the cap ($2,000, $300 stakes): mean {st.mean(atcap):+,.0f} across the measured (partial) days, best {max(atcap):+,.0f}, worst {min(atcap):+,.0f}")
full = [d for d in days if {"12-18", "18-24", "0-6"} <= blocks[d]]
if full: print("    full days only: " + ", ".join(f"{d} {run_day(days[d], 2000.0)[0]-2000:+,.0f}" for d in sorted(full)))
