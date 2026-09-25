"""scrutiny.py: the variants that pass all five criteria in search.py, taken apart: the launches each adds to / removes from the
baseline (FIT and VAL, with window and return), leave-one-out on the single best added launch, the delta's t-statistic,
per-window tables in the brief's format, and the threshold neighbourhood of the bundle_eth OR-branch.
    cd /home/user/fomo-memebot && python3 <B>/scrutiny.py"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
W = load()
b_fit_per, b_fit = evaluate(W, FIT_NAMES, BASE); b_val_per, b_val = evaluate(W, VAL_NAMES, BASE)
from variants import PASSED, bundle_or
def table(rule, key, label):
    print(f"  {label}")
    for names, tag, bp in ((FIT_NAMES, "FIT pooled", b_fit), (VAL_NAMES, "VAL pooled", b_val)):
        per, pool = evaluate(W, names, rule, key)
        for n, m in per.items(): print("   " + fmt(m, n))
        print("   " + fmt(pool, tag))
def diff(rule, key):
    out = {}
    for names, tag in ((FIT_NAMES, "FIT"), (VAL_NAMES, "VAL")):
        add, rem, both = [], [], []
        for n in names:
            for r in W[n]["rows"]:
                c, b = rule(r), BASE(r)
                if c and not b: add.append((n, r))
                elif b and not c: rem.append((n, r))
                elif b and c: both.append((n, r))
        out[tag] = (add, rem, both)
    return out
def usd(x): return x * STAKE - GAS
for label, rule, key in PASSED:
    print("=" * 150); print(f"{label}   hold {key}")
    table(rule, key, "candidate"); table(BASE, "behind1_15_h300", "baseline (h300)")
    d = diff(rule, key)
    for tag in ("FIT", "VAL"):
        add, rem, both = d[tag]
        # the candidate's dollars minus the baseline's, launch by launch (a hold change moves the kept fires too)
        delta = [usd(r["ret"][key]) for _, r in add] + [-usd(r["ret"]["behind1_15_h300"]) for _, r in rem] + [usd(r["ret"][key]) - usd(r["ret"]["behind1_15_h300"]) for _, r in both]
        tot = sum(delta); nz = [x for x in delta if abs(x) > 1e-12]
        t = (st.mean(nz) / (st.stdev(nz) / len(nz) ** 0.5)) if len(nz) > 2 and st.stdev(nz) > 0 else float("nan")
        best = max(nz) if nz else 0
        print(f"  {tag}: added {len(add)}, removed {len(rem)}; candidate minus baseline ${tot:+.2f} over the window set; t of the per-launch delta {t:+.2f} (n={len(nz)}); without the single best delta ${tot - best:+.2f}")
        for n, r in sorted(add, key=lambda x: x[1]["T0"]): print(f"     + {n:10s} {time.strftime('%b %d %H:%M', time.gmtime(r['T0']))} {r['cv'][:10]} k={r['k']} fleets {r['cf']} bundle {r['bundle_eth']:.2f} named {r['named']} tier {r['tier']:.3f}  {key[-12:]} {r['ret'][key]:+7.1%}")
        for n, r in sorted(rem, key=lambda x: x[1]["T0"]): print(f"     - {n:10s} {time.strftime('%b %d %H:%M', time.gmtime(r['T0']))} {r['cv'][:10]} k={r['k']} fleets {r['cf']}  h300 {r['ret']['behind1_15_h300']:+7.1%}")
print("=" * 150)
print("the bundle_eth OR-branch's neighbourhood (fire also on f@k-2==1 with bundle_eth >= c / < c), h300: FIT $/day, per-window $/burst, VAL $ total and mean")
for c, hi in [(x, True) for x in (0.3, 0.446, 0.5, 0.628, 0.7, 0.836, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0, 3.0)] + [(x, False) for x in (0.4, 0.446, 0.5, 0.55, 0.628, 0.7)]:
    per, pool = evaluate(W, FIT_NAMES, bundle_or(c, hi)); vper, vpool = evaluate(W, VAL_NAMES, bundle_or(c, hi))
    br = (lambda r: r["f_k2"] == 1 and r["bundle_eth"] is not None and (r["bundle_eth"] >= c if hi else r["bundle_eth"] < c))
    _, bf = evaluate(W, FIT_NAMES, br); _, bv = evaluate(W, VAL_NAMES, br)
    print(f"  bundle {'>=' if hi else '< '} {c:5.3f}: FIT n={pool['n']:3d} {pool['mean']:+6.1%} ${pool['usd_day']:5.1f}/d  per-window $/burst " + " ".join(f"{m['usd_burst']:+5.2f}" for m in per.values())
          + f"  | VAL n={vpool['n']:2d} {vpool['mean']:+6.1%} ${vpool['usd_total']:+6.1f}  | the branch alone: FIT n={bf['n']:2d} {bf['mean']:+6.1%} med {bf['median']:+6.1%}, VAL n={bv['n']:2d} {bv['mean']:+6.1%} med {bv['median']:+6.1%}")
print("\nf@k-2==1 launches (FIT) by bundle_eth bucket, h300:")
for a, b in ((0, 0.446), (0.446, 0.628), (0.628, 0.836), (0.836, 1.0), (1.0, 1.5), (1.5, 99)):
    for names, tag in ((FIT_NAMES, "FIT"), (VAL_NAMES, "VAL")):
        x = [r["ret"]["behind1_15_h300"] for n in names for r in W[n]["rows"] if r["f_k2"] == 1 and a <= r["bundle_eth"] < b]
        print(f"   [{a:.3f},{b:.3f}) {tag}: n={len(x):3d} " + (f"mean {st.mean(x):+6.1%} med {st.median(x):+6.1%} win {sum(v>0 for v in x)/len(x):3.0%}" if x else ""), end="   ")
    print()
