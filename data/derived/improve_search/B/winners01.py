"""winners01.py: the 0-1 fleet winners of the validation windows (f@k-2 < 2, behind1 h300 >= +50%) with every pre-tick feature,
against the FIT set's 0-1 fleet launches: for each feature bucket that holds the VAL winners, the FIT mean of that bucket.
    cd /home/user/fomo-memebot && python3 <B>/winners01.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
W = load()
FEAT = ("k", "bundle_eth", "named", "tier", "hour", "f_k2", "w_k2", "shots_k2", "maxw_k2", "fd_k2", "fr_k2", "arr1", "creator_repeat")
print("VAL launches with fleets@k-2 < 2 and behind1 h300 >= +50%:")
Vw = []
for n in VAL_NAMES:
    for r in W[n]["rows"]:
        if r["f_k2"] < 2 and r["ret"]["behind1_15_h300"] >= 0.5:
            Vw.append(r); print(f"  {n:10s} {time.strftime('%b %d %H:%M', time.gmtime(r['T0']))} {r['cv'][:10]} h300 {r['ret']['behind1_15_h300']:+7.1%} fleets {r['cf']} wallets {r['cw']} "
                                + " ".join(f"{f}={r[f]:.2f}" if isinstance(r[f], float) else f"{f}={r[f]}" for f in FEAT))
F01 = [r for n in FIT_NAMES for r in W[n]["rows"] if r["f_k2"] < 2]; V01 = [r for n in VAL_NAMES for r in W[n]["rows"] if r["f_k2"] < 2]
def s(x): return f"n={len(x):3d} mean {st.mean(x):+6.1%} med {st.median(x):+6.1%} win {sum(v > 0 for v in x)/len(x):3.0%}" if x else "n=0"
print(f"\nall 0-1 fleet launches: FIT {s([r['ret']['behind1_15_h300'] for r in F01])} | VAL {s([r['ret']['behind1_15_h300'] for r in V01])}")
print(f"0-1 fleet launches with h300 >= +50%: FIT {sum(r['ret']['behind1_15_h300'] >= 0.5 for r in F01)} of {len(F01)} ({sum(r['ret']['behind1_15_h300'] >= 0.5 for r in F01)/len(F01):.1%}); VAL {len(Vw)} of {len(V01)} ({len(Vw)/len(V01):.1%})")
print("\nfor each feature, the FIT 0-1 fleet launches inside the VAL winners' range [min, max] of that feature, against those outside:")
for f in ("k", "bundle_eth", "named", "tier", "hour", "w_k2", "shots_k2", "maxw_k2", "arr1"):
    vals = [r[f] for r in Vw if r[f] is not None]
    if not vals: continue
    lo, hi = min(vals), max(vals)
    inside = [r["ret"]["behind1_15_h300"] for r in F01 if r[f] is not None and lo <= r[f] <= hi]; outside = [r["ret"]["behind1_15_h300"] for r in F01 if r[f] is not None and not lo <= r[f] <= hi]
    vin = [r["ret"]["behind1_15_h300"] for r in V01 if r[f] is not None and lo <= r[f] <= hi]
    print(f"  {f:11s} VAL winners in [{lo:g}, {hi:g}]:  FIT inside {s(inside)} | FIT outside {s(outside)} | VAL inside {s(vin)}")
