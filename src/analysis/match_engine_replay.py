"""the engine's own paper scores and real trades (pasted from the droplet: S/T/D lines) against the chain replay of the same
curves: per launch, engine roi vs harness roi vs independent-sim roi; any systematic gap is an execution or scoring fault"""
import sys, pickle, statistics as st, os, datetime
os.chdir("/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad")
sys.path.insert(0, "/home/user/fomo-memebot/src/analysis"); import risk_harness as RH
exec(open("/home/user/fomo-memebot/src/analysis/indep_replay.py").read().split("recs = []")[0])
PX = RH.PX
by_curve = {cv: (k, L, f) for k in data for cv, (L, f) in data[k].items()}
lines = [l.split() for l in open(sys.argv[1]) if l.strip()]
scores = [(l[1] + " " + l[2], l[3].lower(), float(l[4]), float(l[5]) if l[5] != "None" else None, float(l[6]) if l[6] != "None" else None) for l in lines if l[0] == "S"]
trades = [(l[1] + " " + l[2], l[3].lower(), l[4:]) for l in lines if l[0] == "T"]
print(f"{len(scores)} engine scores, {len(trades)} real trades pasted; {sum(1 for s in scores if s[1] in by_curve)} scores and {sum(1 for t in trades if t[1] in by_curve)} trades have the curve in the chain replay")
print(f"\n{'when':16s} {'curve':12s} {'engine':>8s} {'harness':>8s} {'indep':>8s} {'clean?':>7s} {'note'}")
rows = []
for when, cv, roi, t_in, cost in scores:
    if cv not in by_curve:
        print(f"{when:16s} {cv[:12]} {100*roi:+7.1f}%      not in the replay's windows"); continue
    k, L, f = by_curve[cv]; g = feats(L); clean = g["out1"] == 0 and not (g["rival_lag"] is not None and g["rival_lag"] < 0.3)
    stake = cost or 25.0
    x = RH.replay(L, stake / PX, hold=5.0, tp=0.5); rh = (x[0] * PX - 0.10) / (x[1] * PX) if x[1] > 1e-6 else float("nan")
    ind = sim(L, "E2", stake_usd=stake)["roi"]
    rows.append((roi + (1.0 - 0.11) / stake, rh, ind, roi)); print(f"{when:16s} {cv[:12]} {100*roi:+7.1f}% {100*rh:+7.1f}% {100*ind:+7.1f}% {'clean' if clean else 'crowded':>7s}  t_in {t_in} stake ${stake:.0f}")
if rows:
    e0 = [r[3] for r in rows]; e = [r[0] for r in rows]; h = [r[1] for r in rows if r[1] == r[1]]; i = [r[2] for r in rows]
    print(f"\nmean over the {len(rows)} matched launches: engine as logged {100*st.mean(e0):+.1f}%  |  engine with the real gas ($0.11 instead of $1.00) {100*st.mean(e):+.1f}%  |  harness {100*st.mean(h):+.1f}%  |  independent {100*st.mean(i):+.1f}%")
    d = [r[0]-r[1] for r in rows if r[1]==r[1]]
    print(f"engine(real gas) minus harness, per launch: mean {100*st.mean(d):+.2f} pts, median {100*st.median(d):+.2f} pts, within 1 pt on {100*sum(abs(x)<0.01 for x in d)/len(d):.0f}% of launches, worst {100*max(d, key=abs):+.1f} pts")
    for day in ("09-10", "09-11", "09-16"):
        rr = [r for r, l in zip(rows, [x for x in scores if x[1] in by_curve]) if l[0].startswith(day)]
        if rr: print(f"   {day}: n {len(rr)}, engine(real gas) {100*st.mean(r[0] for r in rr):+.1f}%, harness {100*st.mean(r[1] for r in rr if r[1]==r[1]):+.1f}%")
for when, cv, rest in trades:
    if cv in by_curve:
        k, L, f = by_curve[cv]; x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5)
        print(f"REAL TRADE {when} {cv[:12]}: replay says {100*(x[0]*PX-0.10)/(x[1]*PX) if x[1]>1e-6 else float('nan'):+.1f}% at $25; log: {' '.join(rest)[:120]}")
    else:
        print(f"REAL TRADE {when} {cv[:12]}: curve not in the replay windows; log: {' '.join(rest)[:120]}")
