"""robust.py (edge_check/F), task 3. (a) Bootstrap the fires (2,000 resamples, seed 7) of the fit, the recent and the pooled set:
the distribution of the optimal h (argmax of the resampled mean curve over 1..600) and of the mean at h = 15 and at each candidate,
with the paired chance that the candidate beats 15. (b) Leave one fit window out: choose h on the other three, read it on the one
left out. (c) The sell landing late: every candidate at h, h+2, h+4 on both periods.
    python3 data/derived/edge_check/F/robust.py > data/derived/edge_check/F/robust.txt"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from load import *
CAND = [8, 9, 11, 15, 20, 30, 150, 200, 240, 250, 300, 337]; B = 2000; rng = np.random.default_rng(7)
BINS = [(1, 9), (10, 30), (31, 100), (101, 200), (201, 300), (301, 400), (401, 600)]
print(f"(a) bootstrap, {B} resamples of the fires with replacement, optimum over h 1..600; candidates {CAND}")
for s in ("fit", "rec", "all"):
    M = P2[mask(s) & FIRE][:, :601]; n = len(M); idx = rng.integers(0, n, (B, n)); C = M[idx].mean(1); C[:, 0] = -9
    opt = C.argmax(1); q = np.percentile(opt, [5, 25, 50, 75, 95])
    print(f"\n{s}: {n} fires. optimal h percentiles 5/25/50/75/95: {' / '.join(str(int(x)) for x in q)}; share by range: " + "  ".join(f"{a}-{b} {np.mean((opt >= a) & (opt <= b)):.0%}" for a, b in BINS))
    top = np.bincount(opt, minlength=601); print("   most frequent optima: " + ", ".join(f"h{h} {top[h]/B:.1%}" for h in np.argsort(-top)[:8]))
    for h in CAND:
        v = C[:, h]; p = np.percentile(v, [2.5, 50, 97.5])
        print(f"   h {h:3d}: point {M[:, h].mean():+6.1%}  bootstrap 2.5/50/97.5% {p[0]:+6.1%} {p[1]:+6.1%} {p[2]:+6.1%}  P(mean<0) {np.mean(v < 0):5.1%}  P(beats h15) {np.mean(v > C[:, 15]):4.0%}  P(beats h300) {np.mean(v > C[:, 300]):4.0%}")
print("\n(b) leave one fit window out: choose on the other three fit windows (h 1..600), read on the window left out")
for w in FITW:
    tr = (SET == "fit") & (WIN != w) & FIRE; te = (WIN == w) & FIRE; c = P2[tr].mean(0); c[0] = -9; h = int(np.argmax(c[:601]))
    se = P2[tr][:, h].std(ddof=1) / np.sqrt(tr.sum()); ok = [x for x in range(1, 601) if c[x] >= c[h] - se]
    run = [x for x in ok if all(y in ok for y in range(min(x, h), max(x, h) + 1))]
    print(f"   leave {w:8s} out: trained on {tr.sum()} fires -> h {h} ({c[h]:+.1%}, plateau {run[0]}-{run[-1]}); on {w} ({te.sum()} fires): at h {h} {P2[te][:, h].mean():+.1%}, at 15 {P2[te][:, 15].mean():+.1%}, at 11 {P2[te][:, 11].mean():+.1%}, at 240 {P2[te][:, 240].mean():+.1%}, at 300 {P2[te][:, 300].mean():+.1%}")
print("\n(c) the sell landing late: mean (and $ a fire) at h, h+2, h+4")
for h in CAND:
    line = f"   h {h:3d}: "
    for s in ("fit", "rec"):
        f = mask(s) & FIRE; st = stats(P2[f], G[f])
        line += f"{s} " + " / ".join(f"{st['mean'][h+d]:+6.1%}" for d in (0, 2, 4)) + f"  (${st['usd'][h]:+.2f} / ${st['usd'][h+2]:+.2f} / ${st['usd'][h+4]:+.2f})    "
    print(line)
# the day-by-day consistency of the candidates: days with at least 3 fires, how many are positive
print("\n(d) days with >= 3 fires (Sep 18, 20, 21, 22, 23, 24, 25, 26): mean by day at each candidate, positive days")
dd = [d for d in DAYS if (mask(d) & FIRE).sum() >= 3]
for h in CAND:
    v = [P2[mask(d) & FIRE][:, h].mean() for d in dd]
    print(f"   h {h:3d}: " + " ".join(f"{x:+6.1%}" for x in v) + f"   positive {sum(x > 0 for x in v)}/{len(v)}; recent days {sum(x > 0 for x in v[-3:])}/3")
print("\n(e) the same bootstrap on the landed curve (the engine's setting S, the sell landing at S+2..S+4, each fire averaged over the three)")
LND = np.full_like(P2, np.nan); LND[:, :1197] = (P2[:, 2:1199] + P2[:, 3:1200] + P2[:, 4:1201]) / 3; rng = np.random.default_rng(7)
for s in ("fit", "rec", "all"):
    M = LND[mask(s) & FIRE][:, :601]; n = len(M); idx = rng.integers(0, n, (B, n)); C = M[idx].mean(1); C[:, 0] = -9; opt = C.argmax(1)
    print(f"{s}: optimal setting percentiles 5/25/50/75/95: {' / '.join(str(int(x)) for x in np.percentile(opt, [5, 25, 50, 75, 95]))}; share by range: " + "  ".join(f"{a}-{b} {np.mean((opt >= a) & (opt <= b)):.0%}" for a, b in BINS))
    for S in (8, 9, 15, 240, 300, 334):
        v = C[:, S]; p = np.percentile(v, [2.5, 50, 97.5])
        print(f"   S {S:3d}: point {M[:, S].mean():+6.1%}  bootstrap 2.5/50/97.5% {p[0]:+6.1%} {p[1]:+6.1%} {p[2]:+6.1%}  P(mean<0) {np.mean(v < 0):5.1%}  P(beats S15) {np.mean(v > C[:, 15]):4.0%}  P(beats S8) {np.mean(v > C[:, 8]):4.0%}")
