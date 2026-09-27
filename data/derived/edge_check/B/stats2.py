"""stats2.py (reviewer B), test 2: is +3.5% on 18 fires unusual for the fit's distribution? Bootstrap, permutation, rank test,
consecutive stretches of the fit, and the day-by-day series Sep 18-27, from features.json (h300 returns at $13 = reach_table).
    python3 data/derived/edge_check/B/stats2.py"""
import sys, os, json, random, collections, statistics as st, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
F = json.load(open(c.B + "features.json")); random.seed(7); N = 100000
fit = sorted([f for f in F if f["fire"] and f["grp"] == "fit"], key=lambda f: f["T0"]); rec = sorted([f for f in F if f["fire"] and f["grp"] == "recent"], key=lambda f: f["T0"])
a = [f["ret"]["300"] for f in fit]; b = [f["ret"]["300"] for f in rec]; obs = st.mean(b); d_obs = st.mean(a) - st.mean(b)
print(f"fit {len(a)} mean {st.mean(a):+.1%} sd {st.stdev(a):.3f} median {st.median(a):+.1%} | recent {len(b)} mean {obs:+.1%} sd {st.stdev(b):.3f} median {st.median(b):+.1%}")
boot = sum(st.mean(random.choices(a, k=len(b))) <= obs for _ in range(N)) / N
print(f"bootstrap: 18 fires drawn from the fit's 73 read <= {obs:+.1%} in {boot:.2%} of {N} draws")
pool = a + b; perm = 0
for _ in range(N):
    random.shuffle(pool)
    if st.mean(pool[:len(a)]) - st.mean(pool[len(a):]) >= d_obs: perm += 1
print(f"permutation (one-sided, fit - recent >= {d_obs:+.1%}): p = {perm/N:.4f}")
# Mann-Whitney U, normal approximation
allv = sorted([(x, 0) for x in a] + [(x, 1) for x in b]); ranks = {}
for i, (x, g) in enumerate(allv): ranks.setdefault(x, []).append(i + 1)
rs = sum(st.mean(ranks[x]) for x in b); n1, n2 = len(a), len(b); U = rs - n2 * (n2 + 1) / 2; mu = n1 * n2 / 2; sd = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
print(f"rank test (Mann-Whitney U, recent below fit): U = {U:.0f}, z = {(U - mu)/sd:+.2f}, one-sided p = {0.5*math.erfc(-((U-mu)/sd)/math.sqrt(2)):.4f}")
t = (st.mean(a) - obs) / math.sqrt(st.variance(a) / n1 + st.variance(b) / n2); print(f"Welch t = {t:.2f}")
wins = [sum(x > 0 for x in random.choices(a, k=18)) for _ in range(N)]; w_obs = sum(x > 0 for x in b)
print(f"win count: recent {w_obs}/18; the fit's win rate gives <= {w_obs} of 18 in {sum(w <= w_obs for w in wins)/N:.2%} of draws")
cons = [st.mean(a[i:i + 18]) for i in range(len(a) - 17)]
print(f"18 consecutive fit fires (time order): {len(cons)} stretches, min {min(cons):+.1%}, max {max(cons):+.1%}, share <= {obs:+.1%}: {sum(x <= obs for x in cons)/len(cons):.2f}")
# a 60-hour stretch of the fit timeline: the four windows laid end to end (their own spans from first to last launch), wrapped
spans = []
for w in c.FIT:
    T = sorted(r["T0"] for r in c.load([w])); spans.append((w, T[0], T[-1]))
off = 0; tl = []
for w, lo, hi in spans:
    for f in fit:
        if f["win"] == w: tl.append((off + f["T0"] - lo, f["ret"]["300"]))
    off += hi - lo
tot = off; res = []
for s in range(0, int(tot), 600):
    v = [x for tt, x in tl if (tt - s) % tot < 60 * 3600]
    if v: res.append((st.mean(v), len(v)))
print(f"60-hour stretches of the fit timeline ({tot/3600:.0f} h of launches, wrapped, every 10 min): {len(res)}, fires per stretch {min(n for _, n in res)}-{max(n for _, n in res)}, mean min {min(m for m, _ in res):+.1%}, share <= {obs:+.1%}: {sum(m <= obs for m, _ in res)/len(res):.2f}")
print("\nper window:")
for w in c.FIT + ["recent"]:
    v = [f["ret"]["300"] for f in (fit if w != "recent" else rec) if w == "recent" or f["win"] == w]
    print(f"  {w:10s} n={len(v):3d} mean {st.mean(v):+6.1%} median {st.median(v):+6.1%} win {sum(x>0 for x in v)/len(v):.0%} dead {sum(x<-0.4 for x in v)/len(v):.0%}")
print("\nday by day (UTC): launches in the crowd files, fires, fire mean h300, win, the fires' returns")
pop = c.load(c.FIT) + c.load(c.RECENT); byday = collections.Counter(time.strftime("%m-%d", time.gmtime(r["T0"])) for r in pop)
fd = collections.defaultdict(list)
for f in fit + rec: fd[time.strftime("%m-%d", time.gmtime(f["T0"]))].append(f["ret"]["300"])
for d in sorted(byday):
    v = fd.get(d, [])
    print(f"  {d}  launches {byday[d]:3d}  fires {len(v):2d}  " + (f"mean {st.mean(v):+6.1%}  win {sum(x>0 for x in v)/len(v):3.0%}  " + " ".join(f"{x:+.0%}" for x in v) if v else ""))
