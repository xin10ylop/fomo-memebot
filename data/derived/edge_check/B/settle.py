"""settle.py (reviewer B): how many more fires decide between the fit's mean and the recent mean, and by when at the recent fire
rate; the $/day at the recent launch rate under each mean. Normal model with the pooled per-fire sd.
    python3 data/derived/edge_check/B/settle.py"""
import sys, os, json, math, statistics as st, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
F = json.load(open(c.B + "features.json"))
a = [f["ret"]["300"] for f in F if f["fire"] and f["grp"] == "fit"]; b = [f["ret"]["300"] for f in F if f["fire"] and f["grp"] == "recent"]
m1, m0 = st.mean(a), st.mean(b); sd = st.stdev(a + b)
iv = sorted((d["t_lo"], d["t_hi"]) for d in (json.load(open(f)) for f in glob.glob("data/derived/e1_sep24/e1m_*.json"))); u = []
for x, y in iv:
    if u and x <= u[-1][1]: u[-1][1] = max(u[-1][1], y)
    else: u.append([x, y])
hours = sum(y - x for x, y in u) / 3600; rate = len(b) / hours
llr = sum(((x - m1) ** 2 - (x - m0) ** 2) / (2 * sd ** 2) for x in b)   # log L(recent mean) - log L(fit mean)
print(f"pooled sd {sd:.3f}; recent coverage {hours:.1f} h (union of the e1m windows), {len(b)} fires = {rate:.2f}/h = {rate*24:.1f}/day")
print(f"log likelihood ratio of the 18 recent fires, mean {m0:+.1%} against mean {m1:+.1%}: {llr:+.2f} (odds {math.exp(llr):.1f}:1 for the recent mean)")
step = (m1 - m0) ** 2 / (2 * sd ** 2)
for odds in (20, 100):
    need = max(0.0, (math.log(odds) - llr) / step); print(f"  to {odds}:1 for the recent mean if it is true: about {need:.0f} more fires = {need/rate/24:.1f} days of full coverage")
    need2 = (math.log(odds) + llr) / step; print(f"  to {odds}:1 for the fit mean if it is true: about {need2:.0f} more fires = {need2/rate/24:.1f} days")
for hw in (15, 10):
    n = (1.96 * sd / hw * 100) ** 2; print(f"  fires for a 95% half-width of {hw} points on the period's mean: {n:.0f} ({max(0, n - len(b))/rate/24:.1f} more days)")
print(f"$/day at $13 after $0.33 gas at the recent fire rate: fit mean {(m1*13-0.33)*rate*24:+.1f}, recent mean {(m0*13-0.33)*rate*24:+.1f}; the fit's own rate 73/96 h: {(m1*13-0.33)*73/96*24:+.1f}")
