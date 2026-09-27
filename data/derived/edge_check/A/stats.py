"""stats.py (edge_check/A): test 2 of the brief on fires.json (reviewer A's own pricing, second place, 300 blocks, $13).
Fit (73 fires, Sep 18-23) against Sep 24-27 (18 fires): bootstrap, permutation, rank test, win/dead counts, random 60-hour
stretches and runs of 18 consecutive fires inside the fit, runs of 5 losers, and the sample needed to decide.
    python3 data/derived/edge_check/A/stats.py [column=300]"""
import sys, json, random, math, statistics as st, time
sys.path.insert(0, "data/derived/edge_check/A"); from common import *
COL = sys.argv[1] if len(sys.argv) > 1 else "300"
F = json.load(open(A + "fires.json")); random.seed(20260927)
def v(x): return x["ret"][COL] if COL in x["ret"] else x["ret"][int(COL)] if COL.isdigit() and int(COL) in x["ret"] else x["ret"][COL]
for x in F: x["r"] = x["ret"][COL] if COL in x["ret"] else x["ret"][str(COL)]
fit = sorted([x for x in F if x["set"] == "fit"], key=lambda x: x["T0"]); rec = sorted([x for x in F if x["set"] == "rec"], key=lambda x: x["T0"])
a = [x["r"] for x in fit]; b = [x["r"] for x in rec]; obs = st.mean(a) - st.mean(b); mb = st.mean(b)
def desc(v): return f"n {len(v):3d} mean {st.mean(v):+6.1%} median {st.median(v):+6.1%} sd {st.stdev(v):.3f} se {st.stdev(v)/math.sqrt(len(v)):.3f} win {sum(x>0 for x in v)}/{len(v)} dead {sum(x<-0.4 for x in v)}/{len(v)}"
print(f"column {COL}\nfit    {desc(a)}\nrecent {desc(b)}\ndifference of means {obs:+.1%}; Welch t {obs/math.sqrt(st.variance(a)/len(a)+st.variance(b)/len(b)):.2f}")
N = 200000
# 1. bootstrap: 18 fires drawn from the fit's 73 with replacement, how often is the mean <= the recent mean
boot = sum(st.fmean(random.choices(a, k=len(b))) <= mb for _ in range(N)) / N
print(f"bootstrap: P(mean of {len(b)} fires drawn from the fit <= {mb:+.1%}) = {boot:.4f}")
# bootstrap CI of the recent mean and of the difference
bm = sorted(st.fmean(random.choices(b, k=len(b))) for _ in range(20000)); bd = sorted(st.fmean(random.choices(a, k=len(a))) - st.fmean(random.choices(b, k=len(b))) for _ in range(20000))
print(f"bootstrap 95% interval: recent mean [{bm[500]:+.1%}, {bm[19500]:+.1%}]; fit - recent [{bd[500]:+.1%}, {bd[19500]:+.1%}]; P(diff <= 0) {sum(d <= 0 for d in bd)/len(bd):.4f}")
# 2. permutation: pool the 91, split 73/18 at random
pool = a + b; cnt = 0
for _ in range(N):
    random.shuffle(pool)
    if st.fmean(pool[:len(a)]) - st.fmean(pool[len(a):]) >= obs: cnt += 1
print(f"permutation (one-sided, difference of means >= {obs:+.1%}): p = {cnt/N:.4f}")
# rank test (Mann-Whitney U, normal approximation with ties ignored) and a permutation of medians
allr = sorted((x, i < len(a)) for i, x in enumerate(a + b)); ranks = {}
Ra = sum(i + 1 for i, (x, isa) in enumerate(allr) if isa); U = Ra - len(a) * (len(a) + 1) / 2; mu = len(a) * len(b) / 2; sd = math.sqrt(len(a) * len(b) * (len(a) + len(b) + 1) / 12)
z = (U - mu) / sd; print(f"Mann-Whitney U {U:.0f} (null {mu:.0f}), z {z:.2f}, one-sided p {0.5*math.erfc(z/math.sqrt(2)):.4f}")
obs_md = st.median(a) - st.median(b); cnt = 0; pool = a + b
for _ in range(50000):
    random.shuffle(pool)
    if st.median(pool[:len(a)]) - st.median(pool[len(a):]) >= obs_md: cnt += 1
print(f"permutation of medians (difference {obs_md:+.1%}): p = {cnt/50000:.4f}")
# wins: Fisher exact one-sided
def comb(n, k): return math.comb(n, k)
wa = sum(x > 0 for x in a); wb = sum(x > 0 for x in b); W = wa + wb; n = len(a) + len(b)
p_f = sum(comb(W, j) * comb(n - W, len(b) - j) for j in range(0, wb + 1)) / comb(n, len(b))
print(f"wins {wa}/{len(a)} vs {wb}/{len(b)}: Fisher one-sided p (recent wins this few or fewer) = {p_f:.4f}")
# 3. random 60-hour stretches of the fit's covered time (the four windows laid end to end, gaps removed; start slid every 15 min, wrapping)
HRS = {"sep1819": 23.1, "sep2021": 34.8, "sep2223": 29.3, "sep23day": 8.8}; start = {}
for w in FIT: start[w] = min(r["T0"] for r in load_raw(w))
off = 0; pos = []
for w in FIT:
    for x in fit:
        if x["win"] == w: pos.append(((x["T0"] - start[w]) / 3600 + off, x["r"]))
    off += HRS[w]
TOT = off; means = []; counts = []
for s in [i * 0.25 for i in range(int(TOT * 4))]:
    e = s + 60; inn = [r for p, r in pos if (s <= p < e) or (e > TOT and p < e - TOT)]
    if inn: means.append(st.mean(inn)); counts.append(len(inn))
print(f"60-h stretches of the fit ({TOT:.0f} h covered, {len(means)} starts, wrapping): fires per stretch {min(counts)}-{max(counts)}; mean return min {min(means):+.1%}, 5th pct {sorted(means)[len(means)//20]:+.1%}, median {st.median(means):+.1%}; share <= {mb:+.1%}: {sum(m <= mb for m in means)/len(means):.3f}")
nw = [r for p, r in pos if p < 60]; print(f"   (no wrap: the first 60 h hold {len(nw)} fires, mean {st.mean(nw):+.1%}; the last 60 h {st.mean([r for p, r in pos if p >= TOT-60]):+.1%})")
# runs of 18 consecutive fit fires in time order
runs = [st.mean(a[i:i + len(b)]) for i in range(len(a) - len(b) + 1)]
print(f"runs of {len(b)} consecutive fit fires ({len(runs)}): mean min {min(runs):+.1%}, max {max(runs):+.1%}; share <= {mb:+.1%}: {sum(m <= mb for m in runs)/len(runs):.3f}")
# runs of 5 consecutive losers
def longest_loss(v):
    best = cur = 0
    for x in v: cur = cur + 1 if x <= 0 else 0; best = max(best, cur)
    return best
print(f"longest losing run: fit {longest_loss(a)} of {len(a)}, recent {longest_loss(b)} of {len(b)} (last five recent: {[round(x,3) for x in b[-5:]]})")
sim = sum(longest_loss(random.choices(a, k=len(b))) >= longest_loss(b) for _ in range(50000)) / 50000
print(f"P(a run of >= {longest_loss(b)} losers somewhere in {len(b)} fires drawn from the fit) = {sim:.4f}")
# 4. what would decide: fires needed so that a true mean of the fit's (+26%) vs 0 separate at one-sided 5% with 80% power, sd pooled
sdp = st.stdev(a + b); need = ((1.645 + 0.842) * sdp / st.mean(a)) ** 2
print(f"sd of all 91 fires {sdp:.3f}; fires needed to tell +{st.mean(a):.0%} from 0 (one-sided 5%, power 80%): {need:.0f}")
# sequential likelihood ratio on the recent fires: H_fit (mean = fit mean) vs H_zero (mean 0), normal with sd pooled
llr = sum(((x - 0) ** 2 - (x - st.mean(a)) ** 2) / (2 * sdp ** 2) for x in b)
print(f"log likelihood ratio (fit mean vs zero) on the {len(b)} recent fires: {llr:+.2f} (>0 favours the fit; |LLR| > 2.94 is a 95/5 SPRT boundary)")
# Paper-only (Sep 24-25: sep24paper..sep25eve2) vs live-era (Sep 25-26 night onwards)
p1 = [x["r"] for x in rec if x["win"] in ("sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2")]; p2 = [x["r"] for x in rec if x not in p1 and x["win"] not in ("sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2")]
print(f"recent split: Sep 24-25 windows {desc(p1)}\n              Sep 25 22:27 onwards {desc(p2)}")
# how many more fires until the sequential test decides, at the recent fire rate
step = st.mean(a) ** 2 / (2 * sdp ** 2); rate = len(b) / 60 * 24
print(f"SPRT drift per fire {step:.3f}: if the true mean is 0, about {(2.94 + llr) / step:.0f} more fires reach the lower boundary (-2.94); if it is the fit's, about {(2.94 - llr) / step:.0f} reach the upper; recent rate {rate:.1f} fires/day -> {(2.94 + llr) / step / rate:.1f} and {(2.94 - llr) / step / rate:.1f} days")
