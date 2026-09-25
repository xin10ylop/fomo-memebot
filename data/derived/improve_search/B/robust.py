"""robust.py: is each five-criteria pass proven? For every pass (the nine of search.py and the stage-2 unions of extra.py) the
candidate-minus-baseline dollars launch by launch (added fires, removed fires, and hold changes on shared fires), then:
  VAL one-launch test: neutralise the single launch that adds most to the candidate's VAL margin (score it as the baseline does)
      and re-check (c) strictly (candidate VAL $ total > baseline AND mean/fire > baseline). Fails, or a tie before it => "barely
      clears (c)" => NOT PROVEN (the brief's rule).
  FIT one-launch test: the same on FIT for (a) (candidate FIT $/day > baseline).
  paired t of the per-launch deltas (launches where the two rules differ).
    cd /home/user/fomo-memebot && python3 <B>/robust.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from variants import PASSED, STAGE2
W = load()
BK = "behind1_15_h300"
_, b_fit = evaluate(W, FIT_NAMES, BASE); _, b_val = evaluate(W, VAL_NAMES, BASE)
usd = lambda x: x * STAKE - GAS
def five(rule, key):
    fp, f = evaluate(W, FIT_NAMES, rule, key); vp, v = evaluate(W, VAL_NAMES, rule, key)
    return all((f["usd_day"] > b_fit["usd_day"], all(m["n"] and m["usd_burst"] > 0 for m in fp.values()), v["n"] > 0 and v["usd_total"] >= b_val["usd_total"] and v["mean"] >= b_val["mean"],
                f["win"] >= b_fit["win"] - 0.1 and f["dead"] <= b_fit["dead"] + 0.05, f["n"] >= 30)), f, v
def parts(names, rule, key):
    """per launch: (baseline return or None, candidate return or None)"""
    out = []
    for n in names:
        for r in W[n]["rows"]:
            b = r["ret"][BK] if BASE(r) else None; c = r["ret"][key] if rule(r) else None
            if b is not None or c is not None: out.append((r["cv"], b, c))
    return out
def loo(names, rule, key, hours):
    P = parts(names, rule, key)
    d = [((usd(c) if c is not None else 0) - (usd(b) if b is not None else 0), cv, b, c) for cv, b, c in P]
    diff = [x for x in d if abs(x[0]) > 1e-12]
    t = st.mean(x[0] for x in diff) / (st.stdev(x[0] for x in diff) / len(diff) ** 0.5) if len(diff) > 2 and st.stdev(x[0] for x in diff) > 0 else float("nan")
    if not diff: return {"t": t, "n_diff": 0, "tie": True}
    best = max(diff, key=lambda x: x[0])
    rets = [(b if cv == best[1] else c) for cv, b, c in P if (b if cv == best[1] else c) is not None]   # the best-contributing launch scored as the baseline scores it
    tot = sum(usd(x) for x in rets)
    return {"t": t, "n_diff": len(diff), "tie": False, "best_cv": best[1][:10], "best_delta": best[0], "loo_total": tot, "loo_mean": st.mean(rets) if rets else float("nan"), "loo_n": len(rets), "loo_usd_day": tot / hours * 24}
HF = sum(W[n]["hours"] for n in FIT_NAMES); HV = sum(W[n]["hours"] for n in VAL_NAMES)
rows = [(lab, rule, key, "stage 1") for lab, rule, key in PASSED] + [(lab, rule, key, "stage 2") for lab, rule, key in STAGE2 if five(rule, key)[0]]
print(f"baseline FIT ${b_fit['usd_day']:.2f}/day; VAL ${b_val['usd_total']:.2f} total, {b_val['mean']:+.2%} a fire\n")
print(f"{'variant':60s} {'hold':6s} {'FIT $/d':>8s} {'VAL $':>7s} {'VAL mean':>8s} | {'t FIT':>6s} {'t VAL':>6s} | FIT one-launch: $/d, (a) | VAL one-launch: $ total, mean, (c) strict | verdict")
for lab, rule, key, stage in rows:
    ok, f, v = five(rule, key)
    lf = loo(FIT_NAMES, rule, key, HF); lv_ = loo(VAL_NAMES, rule, key, HV)
    a_loo = (not lf["tie"]) and lf["loo_usd_day"] > b_fit["usd_day"]
    c_loo = (not lv_["tie"]) and lv_["loo_total"] > b_val["usd_total"] + 1e-9 and lv_["loo_mean"] > b_val["mean"] + 1e-12
    verdict = "NOT PROVEN (VAL tie: same fires as the baseline)" if lv_["tie"] else ("NOT PROVEN (barely clears c: one launch)" if not c_loo else ("c survives one launch; FIT gain rests on one launch" if not a_loo else "survives both one-launch tests"))
    fl = f"${lf['loo_usd_day']:6.1f} {'a' if a_loo else '-'} (drop {lf.get('best_cv')})" if not lf["tie"] else "tie"
    vl = f"${lv_['loo_total']:+6.1f} {lv_['loo_mean']:+6.1%} {'c' if c_loo else '-'} (drop {lv_.get('best_cv')})" if not lv_["tie"] else "tie"
    print(f"{stage} {lab[:52]:52s} {key.replace('behind1_15_',''):6s} {f['usd_day']:8.1f} {v['usd_total']:+7.1f} {v['mean']:+8.1%} | {lf['t']:+6.2f} {lv_['t']:+6.2f} | {fl:34s} | {vl:44s} | {verdict}")
