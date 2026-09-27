"""twostage.py (edge_check/G): task 4. Eight two-stage exits, declared before running (no search): take-profit +20% and +50% with a hold of
9 and of 300 blocks; a -20% stop with a hold of 9 and of 300; half at 9 and half at 60, half at 9 and half at 300 (exact: the first sale's
impact on the curve included, common.partial). A trigger reads the mark at the end of each block E1+1..E1+hold and sells at the trigger
block + lag; lag 0 (instant, as 24.34) and lag 2 (the engine's sell lands 2 blocks after its decision); the fixed hold at the same lag is
the yardstick (setting 9, the recommendation; also h15). A variant "wins" when its mean beats the fixed hold on both the fit and the recent
set. Null test (24.34's discipline): 1,000 permutations per variant in which each fire exits at the time the trigger would have fired on
another fire's path (within its period), the value read on its own path: how often the permuted variant also wins, and how often its
worst-period margin reaches the real one.
    python3 data/derived/edge_check/G/twostage.py > data/derived/edge_check/G/twostage.txt"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
from sweep import C
random.seed(11)
F = {per: [x for x in C if x["fire"] and x["set"] == per] for per in ("fit", "rec")}
def t_exit(p, kind, level, hold):
    for t in range(1, hold + 1):
        if (kind == "tp" and p[t] >= level) or (kind == "stop" and p[t] <= level): return t
    return hold
V = [("tp", 0.20, 9), ("tp", 0.50, 9), ("tp", 0.20, 300), ("tp", 0.50, 300), ("stop", -0.20, 9), ("stop", -0.20, 300)]
BASES = (9, 15)
print("variants tried: 8 (6 triggered + 2 partial); fires: fit 73, recent 19")
for lag in (0, 2):
    print(f"\n=== lag {lag} (sell lands {lag} blocks after the decision)")
    base = {(per, b): mean([x["r2"][b + lag] for x in F[per]]) for per in F for b in BASES + (337, 11)}
    print("  fixed holds: " + "  ".join(f"h{b}: fit {base[('fit', b)]:+.1%} rec {base[('rec', b)]:+.1%}" for b in BASES + (337, 11)))
    for kind, lev, hold in V:
        te = {per: [t_exit(x["r2"], kind, lev, hold) for x in F[per]] for per in F}
        m = {per: mean([x["r2"][t + lag] for x, t in zip(F[per], te[per])]) for per in F}
        trig = {per: sum(t < hold for t in te[per]) for per in F}
        win = {b: all(m[per] > base[(per, b)] for per in F) for b in BASES}
        marg = min(m[per] - base[(per, 9)] for per in F)
        nwin = 0; nge = 0; pm = {per: [] for per in F}
        for _ in range(1000):
            mm = {}
            for per in F:
                idx = list(range(len(F[per]))); random.shuffle(idx)
                mm[per] = mean([x["r2"][te[per][j] + lag] for x, j in zip(F[per], idx)]); pm[per].append(mm[per])
            nwin += all(mm[per] > base[(per, 9)] for per in F); nge += min(mm[per] - base[(per, 9)] for per in F) >= marg
        dead = {per: sum(x["r2"][t + lag] < -0.4 for x, t in zip(F[per], te[per])) / len(F[per]) for per in F}
        winr = {per: sum(x["r2"][t + lag] > 0 for x, t in zip(F[per], te[per])) / len(F[per]) for per in F}
        print(f"  {kind:4s} {lev:+.0%} hold {hold:3d}: fit {m['fit']:+6.1%} (win {winr['fit']:.0%}, dead {dead['fit']:.0%}, triggered {trig['fit']}/73)  rec {m['rec']:+6.1%} (win {winr['rec']:.0%}, dead {dead['rec']:.0%}, triggered {trig['rec']}/19)"
              f"  | beats h9 on both: {'YES' if win[9] else 'no'}, beats h15 on both: {'YES' if win[15] else 'no'}; worst-period margin over h9 {marg*100:+.1f} pts; null: permuted wins {nwin/10:.1f}%, permuted margin >= real {nge/10:.1f}%, permuted mean fit {mean(pm['fit']):+.1%} rec {mean(pm['rec']):+.1%}")
    for h1, h2 in ((9, 60), (9, 300)):
        m = {}
        for per in F:
            v = [partial(tape(x["cv"]), h1 + lag, h2 + lag, 0.5) for x in F[per]]; m[per] = mean(v)
            approx = mean([0.5 * x["r2"][h1 + lag] + 0.5 * x["r2"][h2 + lag] for x in F[per]])
        win = {b: all(m[per] > base[(per, b)] for per in F) for b in BASES}
        print(f"  half at {h1}, half at {h2}: fit {m['fit']:+6.1%}  rec {m['rec']:+6.1%}  | beats h9 on both: {'YES' if win[9] else 'no'}, beats h15 on both: {'YES' if win[15] else 'no'} (the average of the two single exits: rec {approx:+.1%})")
# how fast the dumps are: for the -20% stop at hold 300, the mark at the crossing block against the exit 2 blocks later
for per in F:
    gaps = []
    for x in F[per]:
        t = t_exit(x["r2"], "stop", -0.20, 300)
        if t < 300: gaps.append((x["r2"][t], x["r2"][t + 2], x["r2"][t - 1]))
    if gaps: print(f"\n{per}: -20% stop crossings {len(gaps)}: mark the block before {mean([g[2] for g in gaps]):+.1%}, at the crossing {mean([g[0] for g in gaps]):+.1%}, 2 blocks later {mean([g[1] for g in gaps]):+.1%}; crossings that fell more than 20 points in that one block: {sum(g[2] - g[0] > 0.20 for g in gaps)}")
