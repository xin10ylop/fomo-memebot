"""q2.py (reviewer D), brief question 2: the rule at 15 and at 300 blocks, day by day Sep 18-27, per window, the lift over the
refused, the paired difference, the statistics of each hold in each period, and the money at the recent launch supply.
    python3 data/derived/edge_check/D/q2.py > data/derived/edge_check/D/q2.txt"""
import sys, os, math, random, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c, kit as K
random.seed(11); ALL = K.FIT + K.REC
def row(lab, S):
    fi = [f for f in S if f["fire"]]; re = [f for f in S if not f["fire"]]
    g = lambda T, h: c.mean([f["path"][h] for f in T])
    if not fi: return f"{lab:14s} {len(S):4d} launches    0 fires"
    return (f"{lab:14s} {len(S):4d} launches {len(fi):3d} fires | h15 {g(fi,15):+6.1%} (refused {g(re,15):+6.1%}, lift {100*(g(fi,15)-g(re,15)):+5.1f}) win {sum(f['path'][15]>0 for f in fi)/len(fi):3.0%}"
            f" | h300 {g(fi,300):+6.1%} (refused {g(re,300):+6.1%}, lift {100*(g(fi,300)-g(re,300)):+5.1f}) win {sum(f['path'][300]>0 for f in fi)/len(fi):3.0%} | h60 {g(fi,60):+6.1%} h150 {g(fi,150):+6.1%}")
print("DAY BY DAY (UTC day of the launch), second place in E1, $13; the committed windows only (coverage differs by day)")
for d in sorted({f["day"] for f in ALL}, key=lambda d: min(f["T0"] for f in ALL if f["day"] == d)): print(row(d, [f for f in ALL if f["day"] == d]))
print("\nBY WINDOW")
for w in c.FIT + c.RECENT: print(row(w, [f for f in ALL if f["win"] == w]))
print("\nBY PERIOD")
cut = 1790375220   # Sep 25 22:27 UTC, A's split: the 6 fires from there on
for lab, S in (("fit", K.FIT), ("recent", K.REC), ("rec to 22:27 25", [f for f in K.REC if f["T0"] < cut]), ("rec from 22:27", [f for f in K.REC if f["T0"] >= cut])): print(row(lab, S))
print("\nSTATISTICS of the fires at each hold (mean, sd, se, median); Welch t fit vs recent; paired h15 - h300")
for h in (15, 60, 150, 300):
    a = [f["path"][h] for f in K.FIT if f["fire"]]; b = [f["path"][h] for f in K.REC if f["fire"]]
    t = (st.mean(a) - st.mean(b)) / math.sqrt(st.variance(a) / len(a) + st.variance(b) / len(b))
    print(f"  h{h:<3d} fit {st.mean(a):+6.1%} sd {st.stdev(a):.3f} se {c.se(a):.3f} med {st.median(a):+6.1%} | recent {st.mean(b):+6.1%} sd {st.stdev(b):.3f} se {c.se(b):.3f} med {st.median(b):+6.1%} | Welch t {t:+.2f}")
for hb in (300, 150):
    for g, S in (("fit", K.FIT), ("recent", K.REC), ("all 91", ALL)):
        d = [f["path"][15] - f["path"][hb] for f in S if f["fire"]]
        print(f"  paired h15 - h{hb}, {g:7s}: {st.mean(d):+6.1%} se {c.se(d):.3f} t {st.mean(d)/c.se(d):+.2f} (n {len(d)})")
print("  worst of the five windows (four fit windows + the recent set), per hold: " + "  ".join(
    f"h{h} {min([c.mean([f['path'][h] for f in K.FIT if f['fire'] and f['win'] == w]) for w in c.FIT] + [c.mean([f['path'][h] for f in K.REC if f['fire']])]):+.1%}" for h in (15, 30, 60, 150, 300, 600)))
# bootstrap of the recent h15 mean and of the probability that it is below the gas break-even
b = [f["path"][15] for f in K.REC if f["fire"]]; a = [f["path"][15] for f in K.FIT if f["fire"]]
bs = sorted(st.mean(random.choices(b, k=len(b))) for _ in range(20000))
print(f"  recent h15 bootstrap 95% [{bs[500]:+.1%}, {bs[19500]:+.1%}]; P(mean <= gas break-even {c.GAS/13:.1%}) {sum(x <= c.GAS/13 for x in bs)/len(bs):.3f}")
ba = sorted(st.mean(random.choices(a, k=len(b))) for _ in range(20000))
print(f"  18 fires drawn from the fit's h15: share <= recent's {st.mean(b):+.1%}: {sum(x <= st.mean(b) for x in ba)/len(ba):.3f}")
print("\nMONEY at $13 after $0.33 gas, per fire and per day at the recent chain rate (0.32 fires an hour; 18 fires in 60 h = 0.30)")
for h in (15, 300):
    for g, S, hrs in (("fit", K.FIT, 96.0), ("recent", K.REC, 60.0)):
        v = [f["path"][h] for f in S if f["fire"]]; u = st.mean([c.usd(x) for x in v])
        print(f"  h{h:<3d} {g:7s} ${u:+.2f}/fire  at its own rate {len(v)/hrs:.2f}/h: ${u*len(v)/hrs*24:+6.1f}/day   at 0.32/h: ${u*0.32*24:+6.1f}/day   at 0.10/h (the last 10 h): ${u*0.10*24:+5.1f}/day")
