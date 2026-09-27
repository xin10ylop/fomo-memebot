"""q5.py (reviewer D), brief question 5: what the whole run shows that the pieces did not.
 (a) the launch supply day by day: qualifying launches and the rule's fires per covered hour (the union of the e1_multi scan
     windows; Sep 22-23 from launches_175_sep2223.json's first and last launch, as 24.29 states the window)
 (b) the trend of the fires' return in time, all 91, at 15 and 300 blocks (least squares slope per day, Spearman rho, and a
     permutation p for the slope), and of the lift over the refused per fit/recent window
 (c) the position we get: the fires at second, third and fourth place in E1 at 15 and 300 blocks (live landed behind one on 8 of
     12 crowd fills, behind two or three on the rest, 24.29)
 (d) the one big fire: the recent 15-block mean without its largest fire, and the medians
    python3 data/derived/edge_check/D/q5.py > data/derived/edge_check/D/q5.txt"""
import sys, os, json, glob, random, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c, kit as K
random.seed(5); ALL = sorted(K.FIT + K.REC, key=lambda f: f["T0"])
iv = []
for f in glob.glob("data/derived/e1_*/e1m_*.json"):
    d = json.load(open(f)); iv.append((d["t_lo"], d["t_hi"]))
L175 = json.load(open(c.LV + "launches_175_sep2223.json")); iv.append((min(l["T0"] for l in L175), max(l["T0"] for l in L175)))
iv.sort(); U = []
for a, b in iv:
    if U and a <= U[-1][1]: U[-1][1] = max(U[-1][1], b)
    else: U.append([a, b])
def covered(t0, t1): return sum(max(0, min(b, t1) - max(a, t0)) for a, b in U) / 3600
print("(a) SUPPLY by UTC day: covered hours, qualifying launches per hour, the rule's fires per hour")
days = sorted({f["day"] for f in ALL}, key=lambda d: min(f["T0"] for f in ALL if f["day"] == d))
for d in days:
    S = [f for f in ALL if f["day"] == d]; t0 = min(f["T0"] for f in S) // 86400 * 86400; h = covered(t0, t0 + 86400)
    print(f"  {d}  covered {h:5.1f} h  launches {len(S):4d} ({len(S)/h:4.2f}/h)  fires {sum(f['fire'] for f in S):3d} ({sum(f['fire'] for f in S)/h:4.2f}/h)")
for g, S in (("fit", K.FIT), ("recent", K.REC)):
    t0 = min(f["T0"] for f in S) - 60; t1 = max(f["T0"] for f in S) + 60; h = covered(t0, t1)
    print(f"  {g:6s} covered {h:5.1f} h  launches {len(S)} ({len(S)/h:.2f}/h)  fires {sum(f['fire'] for f in S)} ({sum(f['fire'] for f in S)/h:.2f}/h)")
print("\n(b) TREND of the fires' return in time (all 91, days since the first fire)")
F = [f for f in ALL if f["fire"]]; t = [(f["T0"] - F[0]["T0"]) / 86400 for f in F]
def slope(x, y):
    mx, my = st.mean(x), st.mean(y); return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sum((a - mx) ** 2 for a in x)
def rank(v): s = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v); [r.__setitem__(i, j) for j, i in enumerate(s)]; return r
for h in (15, 60, 150, 300):
    y = [f["path"][h] for f in F]; b = slope(t, y); rt, ry = rank(t), rank(y); rho = slope(rt, ry) * st.pstdev(rt) / st.pstdev(ry)
    null = [slope(t, random.sample(y, len(y))) for _ in range(5000)]; p = sum(x <= b for x in null) / len(null)
    print(f"  h{h:<3d} slope {100*b:+5.2f} points a day, Spearman rho {rho:+.2f}, one-sided permutation p (slope this negative) {p:.3f}")
R = [f for f in ALL if not f["fire"]]; tr = [(f["T0"] - F[0]["T0"]) / 86400 for f in R]
for h in (15, 300):
    y = [f["path"][h] for f in R]; print(f"  refused h{h:<3d} slope {100*slope(tr, y):+5.2f} points a day (n {len(R)})")
print("\n(c) POSITION: the fires at second, third, fourth place in the seat block (model_eff, $13)")
for g, S in (("fit", K.FIT), ("recent", K.REC)):
    for n_ahead in (1, 2, 3):
        v15 = []; v300 = []
        for f in S:
            if not f["fire"]: continue
            L = c.tape(f["cv"]); e = c.seat_block(L, L["b0"]); v15.append(c.model_eff(L, 13 / c.E, e, n_ahead, 15)[0]); v300.append(c.model_eff(L, 13 / c.E, e, n_ahead, 300)[0])
        print(f"  {g:6s} behind {n_ahead}: h15 {c.mean(v15):+6.1%} (win {sum(x>0 for x in v15)/len(v15):3.0%})   h300 {c.mean(v300):+6.1%} (win {sum(x>0 for x in v300)/len(v300):3.0%})")
print("\n(d) THE LARGEST FIRE and the medians")
for g, S in (("fit", K.FIT), ("recent", K.REC)):
    for h in (15, 300):
        v = sorted(f["path"][h] for f in S if f["fire"])
        print(f"  {g:6s} h{h:<3d} mean {st.mean(v):+6.1%}  without the largest ({v[-1]:+.0%}) {st.mean(v[:-1]):+6.1%}  without the largest two {st.mean(v[:-2]):+6.1%}  median {st.median(v):+6.1%}  10%-trimmed {st.mean(v[len(v)//10: len(v)-len(v)//10]):+6.1%}")
