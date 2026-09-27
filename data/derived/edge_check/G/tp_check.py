"""tp_check.py (edge_check/G): the one two-stage exit that beat the fixed hold on both periods (take-profit +20%, hold 300) put through the
same discipline as the fixed holds: its neighbourhood (take-profit 10/15/20/25/30/40%, hold 60/150/300/600: 24 cells, counted as
variants tried), lags 0/2/4, the bootstrap of its gain over setting 9 (2,000 resamples, seed 5), and each fit window and day.
    python3 data/derived/edge_check/G/tp_check.py > data/derived/edge_check/G/tp_check.txt"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
from sweep import C, sets
def t_exit(p, kind, level, hold):                                    # as twostage.py
    for t in range(1, hold + 1):
        if (kind == "tp" and p[t] >= level) or (kind == "stop" and p[t] <= level): return t
    return hold
random.seed(5); S = sets()
F = {per: [x for x in C if x["fire"] and x["set"] == per] for per in ("fit", "rec")}
def tp_vals(fs, lev, hold, lag): return [x["r2"][t_exit(x["r2"], "tp", lev, hold) + lag] for x in fs]
def fixed(fs, h, lag): return [x["r2"][h + lag] for x in fs]
print("neighbourhood, lag 2: mean fit / recent (fixed setting 9 at lag 2: fit %+.1f%% rec %+.1f%%)" % (mean(fixed(F["fit"], 9, 2)) * 100, mean(fixed(F["rec"], 9, 2)) * 100))
LEV = (0.10, 0.15, 0.20, 0.25, 0.30, 0.40); HOLD = (60, 150, 300, 600)
print(f"{'tp':>5s} " + " ".join(f"{'hold ' + str(h):>17s}" for h in HOLD))
nwin = 0
for lev in LEV:
    cells = []
    for h in HOLD:
        a, b = mean(tp_vals(F["fit"], lev, h, 2)), mean(tp_vals(F["rec"], lev, h, 2)); w = a > mean(fixed(F["fit"], 9, 2)) and b > mean(fixed(F["rec"], 9, 2)); nwin += w
        cells.append(f"{a:+6.1%}/{b:+6.1%}{'*' if w else ' '}")
    print(f"{lev:5.0%} " + " ".join(f"{c:>17s}" for c in cells))
print(f"cells beating setting 9 on both periods (*): {nwin} of {len(LEV)*len(HOLD)}")
print("\ntp +20% hold 300 by lag against the fixed setting 9 (and h15) at the same lag")
for lag in (0, 2, 4):
    print(f"  lag {lag}: " + "  ".join(f"{per}: tp {mean(tp_vals(F[per], .2, 300, lag)):+6.1%}  h9 {mean(fixed(F[per], 9, lag)):+6.1%}  h15 {mean(fixed(F[per], 15, lag)):+6.1%}" for per in F))
print("\nbootstrap (2,000) of tp20/300 - setting 9, lag 2")
for per in ("fit", "rec"):
    fs = F[per]; n = len(fs); d = [a - b for a, b in zip(tp_vals(fs, .2, 300, 2), fixed(fs, 9, 2))]; bs = []
    for _ in range(2000): bs.append(mean([d[random.randrange(n)] for _ in range(n)]))
    bs.sort(); print(f"  {per}: gain {mean(d)*100:+.1f} pts (se {se(d)*100:.1f}), 2.5-97.5% {bs[50]*100:+.1f} to {bs[1949]*100:+.1f}, P(gain > 0) {sum(x > 0 for x in bs)/20:.1f}%; median gain {median(d)*100:+.1f} pts")
print("\nby window and day, lag 2: tp20/300 against setting 9")
for name in FIT + ["rec"] + [f"Sep {d}" for d in range(18, 28)]:
    fs = [x for x in C if x["fire"] and S[name](x)]
    if fs: print(f"  {name:9s} {len(fs):3d}  tp {mean(tp_vals(fs, .2, 300, 2)):+6.1%}  s9 {mean(fixed(fs, 9, 2)):+6.1%}  diff {(mean(tp_vals(fs, .2, 300, 2)) - mean(fixed(fs, 9, 2)))*100:+5.1f} pts")
print("\nthe recent fires that never reach +20% (held to 300) against their setting-9 exit")
for per in F:
    nt = [x for x in F[per] if t_exit(x["r2"], "tp", .2, 300) == 300]
    print(f"  {per}: {len(nt)} never trigger: at 302 {mean([x['r2'][302] for x in nt]):+.1%}, at 11 {mean([x['r2'][11] for x in nt]):+.1%}; dead at 302: {sum(x['r2'][302] < -0.4 for x in nt)}")
