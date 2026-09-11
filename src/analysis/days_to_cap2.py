import sys, random, statistics as st, datetime, collections
exec(open(__file__.replace("days_to_cap2.py", "days_to_cap.py")).read().split("# 1. yesterday repeated")[0])   # reuse the loader, run_day, until_cap, days
def rep(xs):
    while True: yield xs
print("=== each recent full day repeated (12:00 -> 05:00 UTC), from $92:")
for d in ("09-07", "09-08", "09-09", "09-10"):
    n, path = until_cap(rep(days[d])); print(f"   {d} x{n}: " + " -> ".join(f"${b:,.0f}" for b in path[:n + 1]))
# the engine takes fewer launches than the replay: paper overnight Sep 10 18:20 -> Sep 11 04:00 scored 50 launches and took 36 trades
t0 = datetime.datetime(2026, 9, 10, 18, 20, tzinfo=datetime.timezone.utc).timestamp(); t1 = datetime.datetime(2026, 9, 11, 4, 0, tzinfo=datetime.timezone.utc).timestamp()
w = [x for x in kept if t0 <= x["t"] <= t1]; b, n, _ = run_day(w, 92.0, cap=25.0)
print(f"\n=== replay of the paper night (Sep 10 18:20 -> Sep 11 04:00): {len(w)} rule-passing launches, {n} one-at-a-time trades at $25, mean {100*st.mean(x['roi'] for x in w):+.1f}%; the engine scored 50 and took 36 paper trades")
# recent regime bootstrap (Sep 7-10 full days only), with and without a one-third trade shortfall
recent = [days[d] for d in ("09-07", "09-08", "09-09", "09-10")]
def seq(thin):
    while True:
        xs = random.choice(recent)
        yield [x for x in xs if random.random() >= thin]
random.seed(3)
for thin in (0.0, 0.35):
    res = []; e7 = []
    for _ in range(3000):
        n, path = until_cap(seq(thin)); res.append(n if n else 61); e7.append(path[min(7, len(path) - 1)])
    res.sort(); e7.sort(); q = lambda a, p: a[int(p * (len(a) - 1))]
    print(f"=== last four full days bootstrapped, {int(thin*100)}% of launches missed by the engine: days to $2,000 median {q(res,0.5)}, 10th-90th {q(res,0.1)}-{q(res,0.9)}, worst {res[-1]}; after 7 days median ${q(e7,0.5):,.0f} (10th ${q(e7,0.1):,.0f}, 90th ${q(e7,0.9):,.0f})")
# the day at which the stake leaves the $25 floor ($167) and per-day profit at the cap for the recent days with a third missed
print("\n=== a day at the cap ($300 stakes) on the recent days, all launches / two thirds of them:")
random.seed(5)
for d in ("09-07", "09-08", "09-09", "09-10"):
    full_ = run_day(days[d], 2000.0)[0] - 2000; thin_ = st.mean(run_day([x for x in days[d] if random.random() >= 0.35], 2000.0)[0] - 2000 for _ in range(50))
    print(f"   {d}: {full_:+,.0f} / {thin_:+,.0f}")
