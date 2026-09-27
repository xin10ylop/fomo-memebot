"""VH verification 3: the null test exactly (recent: full enumeration; fit: exact count of 7-subsets by DP) and by Monte Carlo
with other seeds; P(both) = P(fit) * P(rec) since the draws are independent per period."""
import sys, itertools, random
from fractions import Fraction
sys.path.insert(0, "/home/user/fomo-memebot/data/derived/edge_check/VH/rerun"); from common import *
P = load()
def R(x, h): return x["r11"] if h == 11 else x["r15"]
def exact_p(vals, kdrop, thresh_mean):
    """share of kdrop-subsets whose REMOVAL leaves a kept mean >= thresh_mean (i.e. dropped sum <= total - thresh*kept)"""
    n = len(vals); kept = n - kdrop; lim = sum(vals) - thresh_mean * kept + 1e-12
    # DP over integer micro-units of the dropped sum
    sc = 10**6; iv = [round(v * sc) for v in vals]; L = round(lim * sc)
    from collections import defaultdict
    dp = [defaultdict(int) for _ in range(kdrop + 1)]; dp[0][0] = 1
    for v in iv:
        for j in range(kdrop - 1, -1, -1):
            for s, c in list(dp[j].items()): dp[j + 1][s + v] += c
    good = sum(c for s, c in dp[kdrop].items() if s <= L); tot = sum(dp[kdrop].values())
    return good, tot
for key in ("fire_eng", "fire_tab"):
    for h in (11, 15):
        out = []
        for s in ("fit", "rec"):
            F = [x for x in P if x["set"] == s and x[key] and R(x, h) is not None]
            K = [x for x in F if x["bundle"] <= 3.0]; v = [R(x, h) for x in F]; m = mean([R(x, h) for x in K])
            g, t = exact_p(v, len(F) - len(K), m); out.append((s, len(F), len(F) - len(K), m, g, t))
        pf = out[0][4] / out[0][5]; pr = out[1][4] / out[1][5]
        rng = random.Random(12345); N = 100000; a = b = ab = 0
        vf = [R(x, h) for x in P if x["set"] == "fit" and x[key] and R(x, h) is not None]; vr = [R(x, h) for x in P if x["set"] == "rec" and x[key] and R(x, h) is not None]
        kf = out[0][1] - out[0][2]; kr = out[1][1] - out[1][2]
        for _ in range(N):
            okf = mean(rng.sample(vf, kf)) >= out[0][3] - 1e-12; okr = mean(rng.sample(vr, kr)) >= out[1][3] - 1e-12; a += okf; b += okr; ab += okf and okr
        print(f"{key} h{h}: fit n {out[0][1]} drop {out[0][2]} kept mean {out[0][3]:+.4f} exact P {out[0][4]}/{out[0][5]} = {pf:.6f}; "
              f"rec n {out[1][1]} drop {out[1][2]} kept mean {out[1][3]:+.4f} exact P {out[1][4]}/{out[1][5]} = {pr:.4f}; exact P(both) {pf*pr:.2e};"
              f" MC seed 12345 N={N}: fit {a/N:.5f} rec {b/N:.4f} both {ab/N:.6f}")
# the template filter's null, exact
TF = json.load(open("/home/user/fomo-memebot/data/derived/edge_check/VH/rerun/template_flags.json"))["3_5"]
for key in ("fire_eng",):
    for h in (11, 15):
        ps = []
        for s in ("fit", "rec"):
            F = [x for x in P if x["set"] == s and x[key] and R(x, h) is not None]; K = [x for x in F if not TF[x["cv"]]["flag"]]
            g, t = exact_p([R(x, h) for x in F], len(F) - len(K), mean([R(x, h) for x in K])); ps.append(g / t)
        print(f"template 3_5 {key} h{h}: exact P fit {ps[0]:.4f} rec {ps[1]:.4f} both {ps[0]*ps[1]:.4f}")
