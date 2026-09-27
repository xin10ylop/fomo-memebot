"""landed.py (edge_check/F), tasks 2-3 as the engine runs it: the engine's sell lands 2-4 blocks after its hold setting S, so a
setting's return per fire is the average of the fire's returns at S+2, S+3 and S+4. The same choices as choose.py on that landed
curve (choose on one set, read on the other, plateau = within one standard error of the optimum), then every setting against
S = 15 paired fire by fire (bootstrap 2,000, seed 7): the gain and the chance it is positive, on each period.
    python3 data/derived/edge_check/F/landed.py > data/derived/edge_check/F/landed.txt"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from load import *
LND = np.full_like(P2, np.nan); LND[:, :1197] = (P2[:, 2:1199] + P2[:, 3:1200] + P2[:, 4:1201]) / 3     # LND[:, S] = landed return of setting S
def cur(s): f = mask(s) & FIRE; return LND[f]
def choose(src, dst, hmax=600):
    A = cur(src); B = cur(dst); m = A.mean(0); se = A.std(0, ddof=1) / np.sqrt(len(A)); m[0] = -9; S = int(np.argmax(m[: hmax + 1])); thr = m[S] - se[S]
    ok = [s for s in range(1, hmax + 1) if m[s] >= thr]; run = [s for s in ok if all(x in ok for x in range(min(s, S), max(s, S) + 1))]
    Bm = B.mean(0); pl = list(range(run[0], run[-1] + 1))
    print(f"choose the setting on {src} ({len(A)} fires), read on {dst} ({len(B)}): S = {S} (lands {S+2}-{S+4}) {src} {m[S]:+.1%} (se {se[S]:.1%}) -> {dst} {Bm[S]:+.1%};"
          f" plateau S {run[0]}-{run[-1]} ({len(pl)} settings, {len(ok)} anywhere); {dst} over the plateau {Bm[pl].mean():+.1%} ({Bm[pl].min():+.1%} .. {Bm[pl].max():+.1%}); S 15: {src} {m[15]:+.1%}, {dst} {Bm[15]:+.1%}")
for a, b in (("fit", "rec"), ("rec", "fit"), ("early", "late"), ("late", "early")): choose(a, b)
print("\nlanded curve (mean of the fires' returns at S+2..S+4) by setting S")
print(f"{'S':>4s} " + " ".join(f"{s:>8s}" for s in ("fit", "rec", "early", "late", "all")) + "   fit $/fire  rec $/fire")
for S in list(range(1, 31)) + [40, 60, 100, 150, 200, 240, 250, 300, 337, 400, 600]:
    print(f"{S:4d} " + " ".join(f"{cur(s).mean(0)[S]:+8.1%}" for s in ("fit", "rec", "early", "late", "all")) + "".join(f"  {np.mean(cur(s)[:, S] * G[mask(s) & FIRE] * E) - GAS:+10.2f}" for s in ("fit", "rec")))
print("\npaired against S = 15 (fire by fire, same fires): gain in points, bootstrap 2.5/97.5%, P(gain > 0)")
rng = np.random.default_rng(7)
for s in ("fit", "rec", "early", "late"):
    A = cur(s); n = len(A); idx = rng.integers(0, n, (2000, n))
    line = f"{s:5s} ({n:2d}) "
    for S in (7, 8, 9, 10, 11, 12, 13, 20, 240, 300):
        d = A[:, S] - A[:, 15]; bs = d[idx].mean(1); line += f" S{S}: {100*d.mean():+.1f} [{100*np.percentile(bs,2.5):+.1f},{100*np.percentile(bs,97.5):+.1f}] {np.mean(bs>0):.0%} |"
    print(line)
print("\nby fit window and by day (days with >= 3 fires): landed mean at S = 8, 9, 15, 240, 300 and the paired gain of 8 and 9 over 15 (points)")
for s in FITW + [d for d in DAYS if (mask(d) & FIRE).sum() >= 3]:
    A = cur(s); print(f"   {s:9s} ({len(A):2d}) S8 {A[:, 8].mean():+6.1%}  S9 {A[:, 9].mean():+6.1%}  S15 {A[:, 15].mean():+6.1%}  S240 {A[:, 240].mean():+6.1%}  S300 {A[:, 300].mean():+6.1%}   8-15 {100*(A[:, 8]-A[:, 15]).mean():+5.1f}  9-15 {100*(A[:, 9]-A[:, 15]).mean():+5.1f}")
print("\nleave one fit window out, the setting chosen on the other three: among all settings 1..600, and among the short ones 1..60; read on the window left out")
for w in FITW:
    tr = cur("fit")[WIN[mask("fit") & FIRE] != w]; te = cur(w); m = tr.mean(0); m[0] = -9
    a = int(np.argmax(m[:601])); b = int(np.argmax(m[:61]))
    print(f"   leave {w:8s} out: all -> S {a} (train {m[a]:+.1%}; left out {te[:, a].mean():+.1%})   short -> S {b} (train {m[b]:+.1%}; left out {te[:, b].mean():+.1%})   left out at S15 {te[:, 15].mean():+.1%}")
print("\nthe landing lag: exact-block mean at S+1 .. S+5 for S = 8, 9, 15")
for S in (8, 9, 15):
    print(f"   S {S:2d}: " + "   ".join(f"{s} " + " ".join(f"{P2[mask(s) & FIRE][:, S + d].mean():+.1%}" for d in range(1, 6)) for s in ("fit", "rec")))
