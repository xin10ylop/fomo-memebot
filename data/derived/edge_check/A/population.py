"""population.py (edge_check/A): the whole qualifying population (every launch of the crowd files, deduplicated), priced by
the stored hold_grid column the rule is scored on (behind1_15_h300: second place, 300 blocks, $15), fit windows vs Sep 24-27:
the fired set against the refused set (the gate's lift), by fleets at k-2, by window and by UTC day.
    python3 data/derived/edge_check/A/population.py"""
import sys, json, time, statistics as st, collections
sys.path.insert(0, "data/derived/edge_check/A")
from common import *
H = {}
for w in FIT + REC: H.update({x["cv"]: x for x in json.load(open(D + HG[w]))})
def s(v):
    if not v: return "   0"
    return f"{len(v):4d} mean {st.mean(v):+6.1%} med {st.median(v):+6.1%} win {sum(x > 0 for x in v)/len(v):4.0%} dead {sum(x < -0.4 for x in v)/len(v):4.0%}"
rows = []
for name, ws in (("fit", FIT), ("recent", REC)):
    for r in all_launches(ws):
        cf = fleets_by_block(r); rows.append({"set": name, "win": r["win"], "T0": r["T0"], "k": r["k"], "f2": at(cf, r["k"] - 2), "f1": at(cf, r["k"] - 1), "fk": at(cf, r["k"]),
                                              "ret": H[r["cv"]]["behind1_15_h300"], "h15": H[r["cv"]]["behind1_15_h15"], "h60": H[r["cv"]]["behind1_15_h60"]})
print("=== the gate's lift: fired (fleets >= 2 at k-2) vs refused, hold_grid behind1_15_h300")
for name in ("fit", "recent"):
    R = [x for x in rows if x["set"] == name]; f = [x["ret"] for x in R if x["f2"] >= 2]; nf = [x["ret"] for x in R if x["f2"] < 2]
    print(f"{name:7s} all  {s([x['ret'] for x in R])}\n        fired {s(f)}\n        refused {s(nf)}\n        lift (fired - refused mean) {st.mean(f) - st.mean(nf):+.1%}")
print("\n=== by fleets at k-2 (0, 1, 2, 3+)")
for name in ("fit", "recent"):
    R = [x for x in rows if x["set"] == name]
    for b in (0, 1, 2, 3):
        v = [x["ret"] for x in R if (x["f2"] == b if b < 3 else x["f2"] >= 3)]; print(f"{name:7s} fleets {b}{'+' if b == 3 else ' '} {s(v)}")
print("\n=== by fleets at k-1 >= 2 (the borderline view) and at k (end of the creation second) >= 2")
for name in ("fit", "recent"):
    R = [x for x in rows if x["set"] == name]
    print(f"{name:7s} k-1>=2 {s([x['ret'] for x in R if x['f1'] >= 2])}\n{name:7s} k>=2   {s([x['ret'] for x in R if x['fk'] >= 2])}\n{name:7s} k-1>=2 but k-2<2 (the added borderline) {s([x['ret'] for x in R if x['f1'] >= 2 and x['f2'] < 2])}")
print("\n=== by UTC day: launches, fires, fires per launch, fired mean, refused mean")
days = collections.OrderedDict()
for x in sorted(rows, key=lambda x: x["T0"]): days.setdefault(time.strftime("%b %d", time.gmtime(x["T0"])), []).append(x)
for d, R in days.items():
    f = [x["ret"] for x in R if x["f2"] >= 2]; nf = [x["ret"] for x in R if x["f2"] < 2]
    print(f"{d}  launches {len(R):3d}  fires {len(f):3d} ({len(f)/len(R):4.0%})  fired {s(f) if f else '   0'}\n{'':8s}refused {s(nf)}")
print("\n=== by window")
for w in FIT + REC:
    R = [x for x in rows if x["win"] == w]
    if not R: continue
    f = [x["ret"] for x in R if x["f2"] >= 2]; nf = [x["ret"] for x in R if x["f2"] < 2]
    print(f"{w:13s} launches {len(R):3d} fires {len(f):3d}  fired {s(f) if len(f) else '   0'}  | refused mean {(st.mean(nf) if nf else float('nan')):+6.1%}")
# the lift's uncertainty: bootstrap the fired and refused sets within each period
import random; random.seed(7)
def lift(R, n=20000):
    f = [x["ret"] for x in R if x["f2"] >= 2]; nf = [x["ret"] for x in R if x["f2"] < 2]
    return sorted(st.fmean(random.choices(f, k=len(f))) - st.fmean(random.choices(nf, k=len(nf))) for _ in range(n))
Lf = lift([x for x in rows if x["set"] == "fit"]); Lr = lift([x for x in rows if x["set"] == "recent"])
print(f"\n=== bootstrap of the lift (fired mean - refused mean): fit 95% [{Lf[500]:+.1%}, {Lf[19500]:+.1%}]; recent 95% [{Lr[500]:+.1%}, {Lr[19500]:+.1%}]")
dd = sorted(a - b for a, b in zip(random.sample(Lf, len(Lf)), Lr))
print(f"    fit lift - recent lift: 95% [{dd[500]:+.1%}, {dd[19500]:+.1%}], P(<= 0) {sum(d <= 0 for d in dd)/len(dd):.4f}; share of recent-lift draws >= the fit's point lift: {sum(l >= st.mean([x['ret'] for x in rows if x['set']=='fit' and x['f2']>=2]) - st.mean([x['ret'] for x in rows if x['set']=='fit' and x['f2']<2]) for l in Lr)/len(Lr):.4f}")
