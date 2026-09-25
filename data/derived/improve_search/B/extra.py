"""extra.py: (1) the stake: $15-model vs $100-model returns for the baseline gate, (2) the engine's own pre-gate filters that the
tables can approximate (creator repeat, one position at a time, un-aimable k<=2) applied to baseline AND the nine variants,
(3) the k-1 borderline version of each variant (information only, never the headline), (4) stage 2: pairwise combinations of the
AND-filters and OR-branches that were fit-qualified in search.py.
    cd /home/user/fomo-memebot && python3 <B>/extra.py"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from variants import PASSED
W = load()
b_fit_per, b_fit = evaluate(W, FIT_NAMES, BASE); b_val_per, b_val = evaluate(W, VAL_NAMES, BASE)

print("=== (1) the stake, baseline gate (fleets>=2 @k-2), behind one, per fire; $ at the stake after $0.33 gas")
for key, stake in (("behind1_15_h300", 13.0), ("behind1_15_h300", 15.0), ("behind1_100_h300", 100.0), ("behind1_15_h150", 13.0), ("behind1_100_h150", 100.0), ("behind1_15_h600", 13.0), ("behind1_100_h600", 100.0)):
    for names, tag in ((FIT_NAMES, "FIT"), (VAL_NAMES, "VAL")):
        per, pool = evaluate(W, names, BASE, key, stake=stake)
        print(f"  {key:18s} at ${stake:5.0f}  {fmt(pool, tag)}")
x15 = [r["ret"]["behind1_15_h300"] for n in FIT_NAMES for r in W[n]["rows"] if BASE(r)]; x100 = [r["ret"]["behind1_100_h300"] for n in FIT_NAMES for r in W[n]["rows"] if BASE(r)]
print(f"  FIT: the $100 return is below the $15 return on {sum(b < a for a, b in zip(x15, x100))} of {len(x15)} fires; mean gap {st.mean(a - b for a, b in zip(x15, x100)):+.1%} (price impact of the larger buy + the 3% supply cap)")

def engine_filtered(names, rule, key, hold_blocks):
    """creator repeat skipped, k<=2 skipped (un-aimable), one position at a time (a fire inside the previous fire's hold is skipped;
    10 blocks a second, per the brief's '300 blocks ~30 s')"""
    per = collections.OrderedDict(); pool = []; hrs = 0
    for n in names:
        busy_until = -1; rets = []
        for r in W[n]["rows"]:
            if not rule(r) or r["creator_repeat"] or r["k"] <= 2: continue
            if r["T0"] < busy_until: continue
            busy_until = r["T0"] + hold_blocks / 10.0; rets.append(r["ret"][key])
        per[n] = metrics(rets, W[n]["hours"]); pool += rets; hrs += W[n]["hours"]
    return per, metrics(pool, hrs)
HB = lambda key: 600 if "h600" in key else int(key.split("_h")[-1])
print("\n=== (2) with the engine's approximable pre-gate filters (creator repeat, k<=2, one position at a time) on BOTH sides")
ebf_per, ebf = engine_filtered(FIT_NAMES, BASE, "behind1_15_h300", 300); ebv_per, ebv = engine_filtered(VAL_NAMES, BASE, "behind1_15_h300", 300)
print("  baseline      " + fmt(ebf, "FIT") + "\n                " + fmt(ebv, "VAL"))
for label, rule, key in PASSED:
    fp, f = engine_filtered(FIT_NAMES, rule, key, HB(key)); vp, v = engine_filtered(VAL_NAMES, rule, key, HB(key))
    a = f["usd_day"] > ebf["usd_day"]; b = all(m["n"] and m["usd_burst"] > 0 for m in fp.values()); c = v["usd_total"] >= ebv["usd_total"] and v["mean"] >= ebv["mean"]
    d = f["win"] >= ebf["win"] - 0.1 and f["dead"] <= ebf["dead"] + 0.05; e = f["n"] >= 30
    print(f"  {label} {key[-5:]}\n    {fmt(f, 'FIT')}\n    {fmt(v, 'VAL')}   criteria {''.join(k_ if ok else '-' for k_, ok in zip('abcde', (a, b, c, d, e)))}")

print("\n=== (3) the k-1 borderline of each (the same rule with k-2 replaced by k-1; NOT executable as a headline)")
bk1 = lambda r: r["f_k1"] >= 2
for names, tag in ((FIT_NAMES, "FIT"), (VAL_NAMES, "VAL")): print("  baseline@k-1  " + fmt(evaluate(W, names, bk1)[1], tag))
for label, rule, key in PASSED:
    rk1 = lambda r, rule=rule: rule({**r, "f_k2": r["f_k1"], "w_k2": r["w_k1"], "fr_k2": r["fr_k1"], "maxshots_k2": r["maxshots_k1"], "fd_k2": r["fd_k1"]})
    print(f"  {label} {key[-5:]} @k-1\n    " + fmt(evaluate(W, FIT_NAMES, rk1, key)[1], "FIT") + "\n    " + fmt(evaluate(W, VAL_NAMES, rk1, key)[1], "VAL"))

print("\n=== (4) stage 2: every AND-filter x OR-branch pair among the fit-qualified components, all nine holds")
from variants import STAGE2
n2 = 0; ok2 = []
for lab, rule, key in STAGE2:
    fp, f = evaluate(W, FIT_NAMES, rule, key); vp, v = evaluate(W, VAL_NAMES, rule, key); n2 += 1
    cr = (f["usd_day"] > b_fit["usd_day"], all(m["n"] and m["usd_burst"] > 0 for m in fp.values()), v["n"] > 0 and v["usd_total"] >= b_val["usd_total"] and v["mean"] >= b_val["mean"],
          f["win"] >= b_fit["win"] - 0.1 and f["dead"] <= b_fit["dead"] + 0.05, f["n"] >= 30)
    if all(cr): ok2.append((f["usd_day"], lab, key, f, v))
print(f"  {n2} stage-2 variants; {len(ok2)} meet all five:")
for _, lab, key, f, v in sorted(ok2, key=lambda x: -x[0]):
    print(f"   {lab:52s} {key[-12:]:12s} FIT n={f['n']:3d} {f['mean']:+6.1%} win {f['win']:3.0%} dead {f['dead']:3.0%} ${f['usd_day']:5.1f}/d | VAL n={v['n']:2d} {v['mean']:+6.1%} ${v['usd_total']:+6.1f}")
