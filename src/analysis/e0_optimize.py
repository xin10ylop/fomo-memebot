"""the creation-second seat, optimised the honest way: features that are observable BEFORE the send (the creation message and
the launch block only), exits, sizing; fitted on Sep 7-10, then judged on Sep 11, Sep 12-15 and Sep 16-17 untouched; every
candidate reported. Risk first: p5, share below -30%, worst, drawdown on the money path."""
import os, statistics as st, random, collections, datetime, pickle
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "e0_seat.py")).read().split('print("=== the creation second')[0])
def e0x(L, t_after=0.3, hold=2.0, tp=0.5, stop=None, dump=None, frac=0.03, stake=25, surcharge=0.0618):
    """like e0 plus a stop-loss (sell 0.3 s after the price is stop below entry) and a dump stop (a single sell of dump x supply)"""
    rows = L["rows"]; tier = L["tier"]; X, Y = X0, Y0; i = 0
    for i, r in enumerate(rows):
        if i > 0 and r[0] >= t_after: break
        if r[1] == "B": X += r[4]; Y -= r[3]
        else: X -= r[4]; Y += r[3]
    else: i = len(rows)
    fee = tier + surcharge; stake_eth = stake / PX; tk = frac * Y0; net = X * tk / (Y - tk); gross = net / (1 - fee)
    if gross > stake_eth: gross = stake_eth; net = gross * (1 - fee); tk = Y * net / (X + net)
    X += net; Y -= tk; p_in = X / Y; t_out = t_after + hold + 0.3; why = "hold"
    for r in rows[i:]:
        if r[0] >= t_out: break
        if r[1] == "B":
            got = Y - X * Y / (X + r[4])
            if got < r[3] * 0.9: continue
            X += r[4]; Y -= got
        else:
            s_ = min(r[3], Y0 - Y - tk); g = X - X * Y / (Y + s_); X -= g; Y += s_
            if dump and r[3] >= dump * Y0 and t_out > r[0] + 0.3: t_out = r[0] + 0.3; why = "dump"
        if tp and X / Y >= p_in * (1 + tp) and t_out > r[0] + 0.3: t_out = r[0] + 0.3; why = "tp"
        if stop and X / Y <= p_in * (1 - stop) and t_out > r[0] + 0.3: t_out = r[0] + 0.3; why = "stop"
    out = (X - X * Y / (Y + tk)) * (1 - tier)
    return ((out - gross) * PX - 0.11) / (gross * PX), gross * PX, why
def pre_features(L):
    """what the creation message and the launch block tell us before we send"""
    rows = L["rows"]; tier = L["tier"]; pos = L["ts"] % 1.0
    bundle = [r for r in rows[1:] if r[1] == "B" and r[0] < 1.0 - pos and r[5] - tier <= 0.0008]
    eth = sum(r[2] for r in bundle); n = len(bundle); shares = [r[3] / Y0 for r in bundle]
    return dict(tier=round(100 * tier), n=n, eth=eth, tk0=rows[0][3] / Y0, max_share=max(shares) if shares else 0.0, team_share=sum(shares) + rows[0][3] / Y0,
                even=(max(shares) / min(shares) if shares and min(shares) > 0 else 99), hour=datetime.datetime.fromtimestamp(L["ts"], datetime.timezone.utc).hour)
periods = [("FIT Sep 7-10", lambda d: "2026-09-07" <= d <= "2026-09-10"), ("Sep 11", lambda d: d == "2026-09-11"), ("Sep 12-15", lambda d: "2026-09-12" <= d <= "2026-09-15"), ("Sep 16-17", lambda d: d >= "2026-09-16")]
launches = {p: [] for p, _ in periods}
for (d, w), dd in data.items():
    for p, pf in periods:
        if pf(d):
            for cv, (L, f) in dd.items(): launches[p].append(L)
base = {p: [(e0x(L), pre_features(L), L) for L in Ls] for p, Ls in launches.items()}
def summ(rs):
    if not rs: return "n 0"
    x = sorted(rs); return f"n {len(x):5d} mean {100*st.mean(x):+6.1f}% med {100*x[len(x)//2]:+5.1f}% p5 {100*x[len(x)//20]:+5.1f}% <-30% {100*sum(v<-0.3 for v in x)/len(x):4.1f}% worst {100*x[0]:+4.0f}%"
print("=== 1. what the losers and the winners look like (FIT period, entry 0.3 s, hold 2, tp 0.5), pre-entry features only")
fit = base["FIT Sep 7-10"]
los = [(f, w) for (r, g, w), f, L in fit if r < -0.3]; win = [(f, w) for (r, g, w), f, L in fit if r > 0.3]; mid = [(f, w) for (r, g, w), f, L in fit if -0.3 <= r <= 0.3]
for name, grp in (("losers <-30%", los), ("winners >+30%", win), ("the middle", mid)):
    fs = [f for f, w in grp]
    print(f"  {name:14s} n {len(fs):5d} | tier median {st.median(f['tier'] for f in fs):.0f}% | bundle ETH median {st.median(f['eth'] for f in fs):.2f} | wallets median {st.median(f['n'] for f in fs):.0f} | creator share med {100*st.median(f['tk0'] for f in fs):.1f}% | max wallet share med {100*st.median(f['max_share'] for f in fs):.1f}% | team share med {100*st.median(f['team_share'] for f in fs):.0f}% | exits: {dict(collections.Counter(w for f, w in grp))}")
print("\n=== 2. pre-entry filters, fitted on Sep 7-10 and judged on the rest (base exit: 0.3 s, hold 2, tp 0.5, $25)")
cands = [("no filter", lambda f: True),
         ("tier <= 3%", lambda f: f["tier"] <= 3), ("tier <= 2%", lambda f: f["tier"] <= 2), ("tier == 1%", lambda f: f["tier"] == 1), ("tier 2-3%", lambda f: 2 <= f["tier"] <= 3),
         ("bundle >= 0.5 ETH", lambda f: f["eth"] >= 0.5), ("bundle 0.3-1.2 ETH", lambda f: 0.3 <= f["eth"] <= 1.2), ("bundle > 1.2 ETH", lambda f: f["eth"] > 1.2),
         ("wallets >= 5", lambda f: f["n"] >= 5), ("wallets 3-4", lambda f: f["n"] <= 4), ("wallets >= 8", lambda f: f["n"] >= 8),
         ("creator >= 3%", lambda f: f["tk0"] >= 0.03), ("creator < 3%", lambda f: f["tk0"] < 0.03), ("creator >= 5%", lambda f: f["tk0"] >= 0.05),
         ("max wallet share < 5%", lambda f: f["max_share"] < 0.05), ("max wallet share >= 5%", lambda f: f["max_share"] >= 0.05),
         ("team share < 25%", lambda f: f["team_share"] < 0.25), ("team share >= 25%", lambda f: f["team_share"] >= 0.25), ("team share >= 35%", lambda f: f["team_share"] >= 0.35),
         ("even bundle (max/min < 2)", lambda f: f["even"] < 2), ("uneven bundle (max/min >= 2)", lambda f: f["even"] >= 2),
         ("tier<=3% & team share>=25%", lambda f: f["tier"] <= 3 and f["team_share"] >= 0.25),
         ("tier<=3% & bundle>=0.5", lambda f: f["tier"] <= 3 and f["eth"] >= 0.5)]
print(f"  {'filter':30s} | " + " | ".join(f"{p:^62s}" for p, _ in periods))
for name, fn in cands:
    cells = []
    for p, _ in periods:
        rs = [r for (r, g, w), f, L in base[p] if fn(f)]; cells.append(summ(rs))
    print(f"  {name:30s} | " + " | ".join(cells))
print("\n=== 3. exits: hold, take-profit, stop-loss, dump stop (no filter), fit and out of sample")
exits = [(2, 0.5, None, None), (1, 0.5, None, None), (1.5, 0.5, None, None), (3, 0.5, None, None), (2, 0.3, None, None), (2, 1.0, None, None), (2, None, None, None),
         (2, 0.5, 0.15, None), (2, 0.5, 0.25, None), (2, 0.5, None, 0.02), (2, 0.5, None, 0.01), (2, 0.5, 0.25, 0.02), (3, 0.5, 0.25, 0.02), (1.5, 0.3, 0.25, 0.02)]
print(f"  {'hold tp stop dump':22s} | " + " | ".join(f"{p:^62s}" for p, _ in periods))
for hold, tp, stop, dump in exits:
    cells = []
    for p, _ in periods:
        rs = [e0x(L, hold=hold, tp=tp, stop=stop, dump=dump)[0] for L in launches[p]]; cells.append(summ(rs))
    print(f"  {hold:4.1f} {str(tp):>4s} {str(stop):>5s} {str(dump):>5s} | " + " | ".join(cells))
print("\n=== 4. sizing at a $150 stake: the supply fraction (impact vs size), Sep 12-17")
Ls = launches["Sep 12-15"] + launches["Sep 16-17"]
for frac in (0.01, 0.02, 0.03, 0.05):
    res = [e0x(L, frac=frac, stake=150) for L in Ls]; rs = [r for r, g, w in res]
    print(f"  frac {100*frac:.0f}%: spent/trade ${st.mean(g for r, g, w in res):5.0f}  {summ(rs)}  $/trade {st.mean(r*g for r, g, w in res):+.2f}")
pickle.dump({p: [(r, g, w, f) for (r, g, w), f, L in base[p]] for p in base}, open("e0_opt_base.pkl", "wb"))
