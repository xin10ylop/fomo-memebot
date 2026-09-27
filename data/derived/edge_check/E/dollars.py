"""dollars.py (edge_check/E): $ a day at $13 at the recent supply (0.32 fires an hour = 7.68 a day), for h = 15, the fit's optimum,
the recent optimum and the recommendation, on the fit's and on the recent per-fire returns. Full fill: every burst fills at
second place. Live mix (24.29/24.31, as C/stats15.py): half the bursts fill; of the fills two thirds at second place, one third
at third place; gas $0.33 on every burst. Two bases: the sell exactly at E1+h (the tables), and the engine's setting h with the
sell landing 2-4 blocks late (mean of E1+h+2..h+4).
    python3 data/derived/edge_check/E/dollars.py > data/derived/edge_check/E/dollars.txt"""
import sys, os, json, gzip
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
P = json.load(gzip.open(c.EE + "paths.json.gz", "rt")); FPD = 0.32 * 24
def val(x, key, h, landing): return np.mean([x[key][h + d] for d in (2, 3, 4)]) if landing else x[key][h]
print(f"supply {FPD:.2f} fires a day; $13 at {c.E:.0f} $/ETH; gas ${c.GAS} a burst")
for landing in (False, True):
    print(f"\n=== {'the engine setting h, the sell landing at E1+h+2..h+4' if landing else 'the sell exactly at E1+h (the tables)'}")
    for name, h in (("h = 15", 15), ("fit optimum (h 337; setting 334)", 334 if landing else 337), ("recent optimum (h 11; setting 8)", 8 if landing else 11), ("recommendation, h = 9", 9)):
        for s in ("fit", "rec"):
            F = [x for x in P if x["fire"] and x["set"] == s]
            u2 = np.array([val(x, "p1", h, landing) * x["g"] * c.E for x in F]); u3 = np.array([val(x, "p2", h, landing) * x["g2"] * c.E for x in F])
            full = u2.mean() - c.GAS; mix = 0.5 * (2 / 3 * u2.mean() + 1 / 3 * u3.mean()) - c.GAS
            r2 = np.mean([val(x, "p1", h, landing) for x in F]); r3 = np.mean([val(x, "p2", h, landing) for x in F])
            print(f"  {name:34s} on the {s} returns ({len(F):2d} fires; 2nd {r2:+6.1%}, 3rd {r3:+6.1%}): full fill ${full:+.2f}/burst ${full*FPD:+6.1f}/day   live mix ${mix:+.2f}/burst ${mix*FPD:+6.1f}/day ${mix*FPD*7:+6.1f}/week")
