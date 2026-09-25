"""explore.py: descriptive look at the fit set (and, separately, validation): returns by fleets@k-2, by hold, by feature bucket.
    cd /home/user/fomo-memebot && python3 <B>/explore.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
W = load()
def rows(names): return [r for n in names for r in W[n]["rows"]]
F, V = rows(FIT_NAMES), rows(VAL_NAMES)
def s(rs, key="behind1_15_h300"):
    x = [r["ret"][key] for r in rs if r["ret"].get(key) is not None]
    if not x: return "n=0"
    return f"n={len(x):3d} mean {st.mean(x):+6.1%} med {st.median(x):+6.1%} win {sum(v>0 for v in x)/len(x):3.0%} dead {sum(v<-0.4 for v in x)/len(x):3.0%}"
print("=== all qualifying launches by fleets@k-2 (h300)")
for lo, hi in ((0, 0), (1, 1), (2, 2), (3, 3), (4, 99)):
    print(f"  f_k2 in [{lo},{hi}]  FIT {s([r for r in F if lo <= r['f_k2'] <= hi])}   VAL {s([r for r in V if lo <= r['f_k2'] <= hi])}")
print("=== baseline fires by hold (FIT | VAL)")
for key in RET_KEYS[:9]:
    print(f"  {key:30s} FIT {s([r for r in F if BASE(r)], key)}   VAL {s([r for r in V if BASE(r)], key)}")
print("=== all qualifying launches by hold (FIT | VAL)")
for key in RET_KEYS[:9]:
    print(f"  {key:30s} FIT {s(F, key)}   VAL {s(V, key)}")
def qs(vals): vals = sorted(v for v in vals if v is not None); return [vals[int(len(vals) * q)] for q in (0.25, 0.5, 0.75)]
for feat in ("bundle_eth", "named", "tier", "k", "hour", "w_k2", "shots_k2", "maxw_k2", "maxshots_k2", "fd_k2", "fr_k2", "arr1", "arr2"):
    print(f"=== {feat}: fit quartile cuts {qs([r[feat] for r in F])}")
    cuts = sorted(set(qs([r[feat] for r in F])))
    edges = [-1e9] + cuts + [1e9]
    for sub, lab in ((lambda r: True, "all"), (BASE, "base fires"), (lambda r: r["f_k2"] < 2, "f_k2<2")):
        for a, b in zip(edges[:-1], edges[1:]):
            sel = lambda r: r[feat] is not None and a < r[feat] <= b and sub(r)
            print(f"   {lab:10s} ({a:g},{b:g}]  FIT {s([r for r in F if sel(r)])}   VAL {s([r for r in V if sel(r)])}")
