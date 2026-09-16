"""Are the seats the bots now leave alone the same launches as before, or the ones they have learned to skip?
For each day: what a clean launch looks like (team size, team ETH, creator's own supply) against what a crowded one
looks like, and what each pays. If the clean ones used to look like the crowded ones and now look worse, the bots are
picking and we are getting their leavings."""
import sys, statistics as st, collections, datetime, random
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX
data = RH.load(); data.update(RH.load_new())
days = collections.defaultdict(lambda: dict(clean=[], crowd=[]))
for k in sorted(data):
    for cv, (L, f) in data[k].items():
        d = datetime.datetime.fromtimestamp(L["ts"], datetime.timezone.utc).strftime("%m-%d")
        x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5)
        if x[1] <= 1e-6 or x[4] == "reverted":
            continue
        roi = (x[0] * PX - 0.10) / (x[1] * PX)
        rec = dict(n=f["bundle_n"], eth=f["bundle_eth"], tk0=f["tk0"], roi=roi,
                   feth=sum(r[2] for r in L["rows"] if r[1] == "B" and x[2] <= r[0] < x[3]))
        days[d]["clean" if f["out1_n"] == 0 else "crowd"].append(rec)
print(f"{'day':6s} | {'seats left clean':>32s} | {'seats the bots took':>32s}")
print(f"{'':6s} | {'n':>4s} {'team':>5s} {'ETH':>6s} {'creator%':>8s} {'pays':>6s} | {'n':>4s} {'team':>5s} {'ETH':>6s} {'creator%':>8s} {'pays':>6s}")
for d in sorted(days):
    c, w = days[d]["clean"], days[d]["crowd"]
    if not c and not w:
        continue
    f = lambda xs, k: st.mean(x[k] for x in xs) if xs else float("nan")
    print(f"{d:6s} | {len(c):4d} {f(c,'n'):5.1f} {f(c,'eth'):6.2f} {100*f(c,'tk0'):7.1f}% {100*f(c,'roi'):+5.0f}% | "
          f"{len(w):4d} {f(w,'n'):5.1f} {f(w,'eth'):6.2f} {100*f(w,'tk0'):7.1f}% {100*f(w,'roi'):+5.0f}%")
early = [x for d, D in days.items() if d <= "09-03" for x in D["clean"]]
late = [x for d, D in days.items() if d >= "09-09" for x in D["clean"]]
ecr = [x for d, D in days.items() if d <= "09-03" for x in D["crowd"]]
lcr = [x for d, D in days.items() if d >= "09-09" for x in D["crowd"]]
def desc(name, xs):
    if not xs:
        return
    print(f"{name:42s} n {len(xs):5d}  team {st.mean(x['n'] for x in xs):5.1f}  ETH {st.mean(x['eth'] for x in xs):5.2f}  "
          f"creator {100*st.mean(x['tk0'] for x in xs):4.1f}%  buyers after {st.mean(x['feth'] for x in xs):.3f}  pays {100*st.mean(x['roi'] for x in xs):+5.1f}%  win {100*sum(1 for x in xs if x['roi']>0)/len(xs):3.0f}%")
print()
desc("clean seats, Aug 12 - Sep 3", early); desc("clean seats, Sep 9 - Sep 11", late)
desc("seats the bots took, Aug 12 - Sep 3", ecr); desc("seats the bots took, Sep 9 - Sep 11", lcr)
# the same launch shape, then and now: does a clean launch of the same size still pay?
print("\nclean seats by the team's ETH, then and now (does the same kind of launch still pay?)")
bins = [(0.3, 0.5), (0.5, 0.8), (0.8, 1.2), (1.2, 2.0), (2.0, 99)]
for lo, hi in bins:
    e = [x['roi'] for x in early if lo <= x['eth'] < hi]; l = [x['roi'] for x in late if lo <= x['eth'] < hi]
    print(f"   team ETH {lo:.1f}-{hi:.1f}: then n {len(e):4d} {100*st.mean(e) if e else 0:+6.1f}%   now n {len(l):4d} {100*st.mean(l) if l else 0:+6.1f}%")
if late:
    random.seed(2); b = sorted(st.mean(random.choice(late)['roi'] for _ in late) for _ in range(4000))
    print(f"\nrecent clean seats (Sep 9-11): mean {100*st.mean(x['roi'] for x in late):+.1f}%, "
          f"95% interval [{100*b[100]:+.1f}%, {100*b[-100]:+.1f}%] -> " + ("still positive" if b[100] > 0 else "cannot tell it from zero"))
