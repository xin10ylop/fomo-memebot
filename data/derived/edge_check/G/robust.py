"""robust.py (edge_check/G): task 3. (a) Bootstrap the fires (2,000 resamples, seed 7) of the fit, the recent set and the pooled 92:
the distribution of the optimal h (argmax over 1..600 and over 1..60), of the mean at h = 15 and at the candidates, and of the paired
gain candidate - h15. (b) Leave-one-window-out on the fit: choose on three windows, read on the fourth (1..600 and 1..60). (c) The late
sell: every candidate at h, h+2, h+4 and the landed mean (average of h+2, h+3, h+4), fit / recent / pooled; the landed curve's own
optimum (the engine setting) chosen on each set and read on the other.
    python3 data/derived/edge_check/G/robust.py > data/derived/edge_check/G/robust.txt"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
from sweep import C, sets
from choose import choose, runs, mcurve
S = sets(); random.seed(7)
CAND = [15, 8, 9, 10, 11, 13, 337, 334]
P = {n: [x["r2"] for x in C if x["fire"] and S[n](x)] for n in ("fit", "rec", "Sep18-21", "Sep22-27")}; P["pooled"] = P["fit"] + P["rec"]
def q(v, p): s = sorted(v); return s[min(len(s) - 1, int(p * len(s)))]
print("(a) bootstrap, 2,000 resamples of the fires")
for name in ("fit", "rec", "pooled"):
    F = P[name]; n = len(F); arg600 = []; arg60 = []; mh = {h: [] for h in CAND}; gain = {h: [] for h in CAND}
    for _ in range(2000):
        B = [F[random.randrange(n)] for _ in range(n)]
        m = [sum(p[h] for p in B) / n for h in range(601)]
        arg600.append(max(range(1, 601), key=lambda h: m[h])); arg60.append(max(range(1, 61), key=lambda h: m[h]))
        for h in CAND: mh[h].append(m[h]); gain[h].append(m[h] - m[15])
    bands = [(1, 20), (21, 60), (61, 200), (201, 400), (401, 600)]
    print(f"\n {name} ({n} fires): optimal h over 1..600: " + ", ".join(f"{a}-{b}: {sum(a <= x <= b for x in arg600)/20:.1f}%" for a, b in bands) + f"; median {q(arg600, .5)}, 5-95% {q(arg600, .05)}-{q(arg600, .95)}")
    print(f"   optimal h over 1..60: median {q(arg60, .5)}, 5-95% {q(arg60, .05)}-{q(arg60, .95)}; share in 7-16: {sum(7 <= x <= 16 for x in arg60)/20:.1f}%, in 8-13: {sum(8 <= x <= 13 for x in arg60)/20:.1f}%")
    lg = {h: [] for h in (8, 9, 10, 11)}
    for _ in range(2000):
        B = [F[random.randrange(n)] for _ in range(n)]
        l15 = mean([mean([p[15 + j] for j in (2, 3, 4)]) for p in B])
        for h in lg: lg[h].append(mean([mean([p[h + j] for j in (2, 3, 4)]) for p in B]) - l15)
    print("   landed gain over setting 15 (sell at h+2..h+4 averaged): " + "; ".join(f"setting {h}: {mean(lg[h])*100:+.1f} pts, 2.5-97.5% {q(lg[h], .025)*100:+.1f} to {q(lg[h], .975)*100:+.1f}, P(gain > 0) {sum(x > 0 for x in lg[h])/20:.1f}%" for h in lg))
    for h in CAND:
        print(f"   h{h:<4d} mean {mean(mh[h]):+6.1%}  2.5-97.5% {q(mh[h], .025):+6.1%} to {q(mh[h], .975):+6.1%}  P(mean > 0) {sum(x > 0 for x in mh[h])/20:5.1f}%" + ("" if h == 15 else f"  | gain over h15 {mean(gain[h])*100:+5.1f} pts, 2.5-97.5% {q(gain[h], .025)*100:+5.1f} to {q(gain[h], .975)*100:+5.1f}, P(gain > 0) {sum(x > 0 for x in gain[h])/20:5.1f}%"))
print("\n(b) leave one fit window out: choose on the other three, read on the one left out")
for w in FIT:
    rest = [x["r2"] for x in C if x["fire"] and x["set"] == "fit" and x["win"] != w]; out = [x["r2"] for x in C if x["fire"] and x["win"] == w]
    mo = mcurve(out, 1, 600)
    for lo, hi in ((1, 600), (1, 60)):
        hs, ms, s, (a, b), on = choose(rest, lo, hi)
        print(f" leave out {w:8s} ({len(out):2d} fires), range {lo}-{hi}: chosen h {hs:3d} ({ms:+.1%} on the other {len(rest)}, plateau {a}-{b}); on {w}: h{hs} {mo[hs]:+.1%}, h15 {mo[15]:+.1%}, h10 {mo[10]:+.1%}, h9 {mo[9]:+.1%}, h300 {mo[300]:+.1%}")
print("\n(c) the late sell: each candidate at h, h+2, h+4 and landed (mean of h+2..h+4)")
def landed(F, h): return mean([mean([p[h + j] for j in (2, 3, 4)]) for p in F])
for h in CAND:
    print(f" h{h:<4d} " + "   ".join(f"{name}: {mean([p[h] for p in P[name]]):+6.1%} / +2 {mean([p[h+2] for p in P[name]]):+6.1%} / +4 {mean([p[h+4] for p in P[name]]):+6.1%} / landed {landed(P[name], h):+6.1%}" for name in ("fit", "rec")))
print("\n the engine setting chosen on the landed curve (sell lands at h+2..h+4), 1..60 and 1..600; plateau = within one se of the optimum")
def lcurve(F, lo, hi): return {h: landed(F, h) for h in range(lo, hi + 1)}
for cs, rs in (("fit", "rec"), ("rec", "fit"), ("Sep18-21", "Sep22-27"), ("pooled", None)):
    for lo, hi in ((1, 60), (1, 600)):
        m = lcurve(P[cs], lo, hi); hs = max(m, key=lambda h: m[h]); s = se([mean([p[hs + j] for j in (2, 3, 4)]) for p in P[cs]])
        on = sorted(h for h in m if m[h] >= m[hs] - s); a = b = hs
        while a - 1 in m and m[a - 1] >= m[hs] - s: a -= 1
        while b + 1 in m and m[b + 1] >= m[hs] - s: b += 1
        rd = f"; read on {rs}: landed {landed(P[rs], hs):+.1%} (setting 15 landed {landed(P[rs], 15):+.1%})" if rs else ""
        print(f"  choose on {cs:8s} {lo}-{hi}: setting {hs} landed {m[hs]:+.1%} (se {s:.1%}), setting 15 landed {m.get(15, landed(P[cs], 15)):+.1%}; plateau {a}-{b} ({runs(on)}){rd}")
print("\n(d) by window and by day: landed mean (sell at h+2..h+4) at settings 8, 9, 10, 11, 15, 300; n fires")
for name in ["fit"] + FIT + ["rec"] + [f"Sep {d}" for d in range(18, 28)]:
    F = [x["r2"] for x in C if x["fire"] and S[name](x)]
    if not F: continue
    print(f"  {name:9s} {len(F):3d} " + "  ".join(f"s{h} {landed(F, h):+6.1%}" for h in (8, 9, 10, 11, 15, 300)) + f"   s9 - s15 {(landed(F, 9) - landed(F, 15))*100:+5.1f} pts")
