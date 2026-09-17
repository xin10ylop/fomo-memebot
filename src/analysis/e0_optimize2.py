import os, statistics as st, random, collections, datetime, pickle
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "e0_optimize.py")).read().split('base = {p:')[0])
def summ(rs):
    if not rs: return "n 0"
    x = sorted(rs); return f"n {len(x):5d} mean {100*st.mean(x):+6.1f}% med {100*x[len(x)//2]:+5.1f}% p5 {100*x[len(x)//20]:+5.1f}% <-30% {100*sum(v<-0.3 for v in x)/len(x):4.1f}% worst {100*x[0]:+4.0f}%"
feats_of = {p: [(pre_features(L), L) for L in Ls] for p, Ls in launches.items()}
print("=== 5. exits, second pass (no filter): shorter hold, no cap or a high cap on the winners")
for hold, tp in ((1.0, None), (1.0, 1.0), (1.5, None), (1.5, 1.0), (1.5, 0.5), (2.0, None)):
    cells = [summ([e0x(L, hold=hold, tp=tp)[0] for L in launches[p]]) for p, _ in periods]
    print(f"  hold {hold:.1f} tp {str(tp):>4s} | " + " | ".join(cells))
print("\n=== 6. combined pre-entry filters (exit: hold 1.5 s, no take-profit)")
combos = [("no filter", lambda f: True), ("tier 2-3%", lambda f: 2 <= f["tier"] <= 3), ("team share < 25%", lambda f: f["team_share"] < 0.25),
          ("tier 2-3% & team < 25%", lambda f: 2 <= f["tier"] <= 3 and f["team_share"] < 0.25), ("tier <= 3% & wallets 3-4", lambda f: f["tier"] <= 3 and f["n"] <= 4),
          ("tier 2-3% or team < 25%", lambda f: 2 <= f["tier"] <= 3 or f["team_share"] < 0.25), ("tier 2-3% & max share < 5%", lambda f: 2 <= f["tier"] <= 3 and f["max_share"] < 0.05),
          ("not (tier 1% & team >= 35%)", lambda f: not (f["tier"] == 1 and f["team_share"] >= 0.35))]
out = {}
for name, fn in combos:
    cells = []
    for p, _ in periods:
        rs = [e0x(L, hold=1.5, tp=None)[0] for f, L in feats_of[p] if fn(f)]; out[(name, p)] = rs; cells.append(summ(rs) + f"  money@$25 {25*sum(rs):+6.0f}$")
    print(f"  {name:28s} | " + " | ".join(cells))
print("\n=== 7. sizing tilt instead of a filter: full stake on tier 2-3% or team<25%, half stake on the rest (hold 1.5, no tp); money at $25 full stake, one at a time (4 s busy)")
def path(p, fn_size, stake=25, hold=1.5, tp=None, frac=0.03):
    ls = sorted(launches[p], key=lambda L: L["ts"]); busy = -1e9; pl = 0; n = 0; peak = 0; low = 0; day = collections.defaultdict(float); streak = 0; worst_streak = 0; losses = []
    for L in ls:
        if L["ts"] < busy: continue
        f = pre_features(L); sz = fn_size(f) * stake
        if sz <= 0: continue
        r, g, w = e0x(L, hold=hold, tp=tp, stake=sz, frac=frac); pl += r * g; n += 1; busy = L["ts"] + 4
        peak = max(peak, pl); low = min(low, pl - peak); day[datetime.datetime.fromtimestamp(L["ts"], datetime.timezone.utc).date()] += r * g
        streak = streak + 1 if r < 0 else 0; worst_streak = max(worst_streak, streak)
    return n, pl, low, min(day.values()) if day else 0, worst_streak
for name, fn in (("no filter, full stake", lambda f: 1.0), ("tier 2-3% only", lambda f: 1.0 if 2 <= f["tier"] <= 3 else 0.0), ("tilt: full on tier 2-3% / team<25%, half on the rest", lambda f: 1.0 if (2 <= f["tier"] <= 3 or f["team_share"] < 0.25) else 0.5), ("tilt: full on tier 2-3%, half on the rest", lambda f: 1.0 if 2 <= f["tier"] <= 3 else 0.5)):
    print(f"  {name:52s} | " + " | ".join(f"{p}: {n:4d} tr {pl:+7.0f}$ dd {low:+5.0f}$ worst day {wd:+5.0f}$ streak {ws}" for p, _ in periods for n, pl, low, wd, ws in [path(p, fn)]))
print("\n=== 8. the chosen exit by entry time (no filter, hold 1.5, no tp): the speed curve again")
for t in (0.2, 0.3, 0.4, 0.5):
    print(f"  {t:.1f}s | " + " | ".join(summ([e0x(L, t_after=t, hold=1.5, tp=None)[0] for L in launches[p]]) for p, _ in periods))
print("\n=== 9. at $150 (the capacity cap), no filter, hold 1.5, no tp: money per day, drawdown, worst day, longest losing streak")
for p, _ in periods:
    n, pl, low, wd, ws = path(p, lambda f: 1.0, stake=150); h = sum(1 for _ in launches[p])
    print(f"  {p:14s}: {n:4d} trades, {pl:+8.0f}$, max drawdown {low:+6.0f}$, worst day {wd:+6.0f}$, longest losing streak {ws}")
