"""checks.py (edge_check/F): the small numbers the report quotes that no other script prints: the committed 18 recent fires (without
the gap fire) at the settings 8 and 15 (landed) and exact h 11 / 15 / 300; the Sep 18-21 choice read on Sep 24-27 alone; the fit's
long-hold plateau read on the recent's last two days; the refused launches at the recommended setting.
    python3 data/derived/edge_check/F/checks.py > data/derived/edge_check/F/checks.txt"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from load import *
LND = np.full_like(P2, np.nan); LND[:, :1197] = (P2[:, 2:1199] + P2[:, 3:1200] + P2[:, 4:1201]) / 3
f = mask("rec18") & FIRE
print(f"committed recent (18 fires): landed S8 {LND[f][:, 8].mean():+.1%}  S15 {LND[f][:, 15].mean():+.1%}  S334 {LND[f][:, 334].mean():+.1%};  exact h11 {P2[f][:, 11].mean():+.1%}  h15 {P2[f][:, 15].mean():+.1%}  h300 {P2[f][:, 300].mean():+.1%}")
e = mask("early") & FIRE; c = LND[e].mean(0); c[0] = -9; S = int(np.argmax(c[:601]))
for s in ("late", "rec", "Sep 22", "Sep 23"):
    g = mask(s) & FIRE; print(f"Sep 18-21 choice S {S} read on {s:6s} ({g.sum():2d} fires): {LND[g][:, S].mean():+.1%}   (S8 {LND[g][:, 8].mean():+.1%}, S15 {LND[g][:, 15].mean():+.1%})")
for s in ("fit", "rec"):
    fi = mask(s) & FIRE; rf = mask(s) & ~FIRE
    print(f"{s}: refused ({rf.sum()}) landed S8 {LND[rf][:, 8].mean():+.1%}, S15 {LND[rf][:, 15].mean():+.1%}; lift of the fires S8 {100*(LND[fi][:, 8].mean()-LND[rf][:, 8].mean()):+.1f} points, S15 {100*(LND[fi][:, 15].mean()-LND[rf][:, 15].mean()):+.1f}")
for s in ("fit", "rec"):
    fi = mask(s) & FIRE; x8 = LND[fi][:, 8]; x15 = LND[fi][:, 15]
    print(f"{s}: landed S8 median {np.median(x8):+.1%} win {np.mean(x8 > 0):.0%} dead {np.mean(x8 < -0.4):.0%} sd {x8.std(ddof=1):.2f};  S15 median {np.median(x15):+.1%} win {np.mean(x15 > 0):.0%} dead {np.mean(x15 < -0.4):.0%} sd {x15.std(ddof=1):.2f}")
