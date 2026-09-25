"""a_diagnose.py (searcher A): how robust is each variant that clears the five criteria of the protocol?
  1. the fires it ADDS to / REMOVES from the baseline, per window (is the fit gain from every window or from one?)
  2. its threshold neighbours on the same fit-quantile grid (does it pass only at one cut?)
  3. a null test: the OR-branch family of a_search.py re-run with RANDOM features (same sub-populations, same fit-quantile
     cuts, same directions, 200 seeds): how often does noise clear all five criteria?
  4. the engine's own skips applied to both sides (one position at a time for the hold, creator repeat)
  5. the full per-window table the brief asks for, for the baseline and each pass
    python3 a_diagnose.py"""
import os, sys, random; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a_search as S
from a_common import *

rows, BASE, RET = S.rows, S.BASE, S.RET
bf, bv = S.bf, S.bv
passes = sorted([r for r in S.CAND if r["pass"] and not r["dup_of"]], key=lambda r: -r["res"]["fit"]["usd_day"])
out = []
def P(s=""): print(s); out.append(s)

P(f"=== 5. per-window tables (the brief's format): baseline and the {len(passes)} distinct variants that clear (a)-(e)")
table("BASELINE fleets>=2 @k-2, behind1 h300", S.B, P)
for r in passes:
    table(f"[{r['family']}] {r['name']}", r["res"], P); v = r["res"]["val"]
    P(f"    (d) read on the validation set instead: win {v['win']:.1%} vs >= {bv['win'] - 0.10:.1%}, dead {v['dead']:.1%} vs <= {bv['dead'] + 0.05:.1%}: "
      + ("holds" if v["win"] >= bv["win"] - 0.10 - 1e-12 and v["dead"] <= bv["dead"] + 0.05 + 1e-12 else "FAILS"))

misses = sorted([r for r in S.CAND if not r["pass"] and not r["noop"] and not r["dup_of"]], key=lambda r: (r["n_fail"], r["gap"]))
P("\n=== 5b. the three closest misses (fewest failed criteria, then the smallest shortfall), full tables")
for r in misses[:3]:
    f = r["res"]["fit"]; why = []
    if not r["crit"]["a"]: why.append(f"(a) fit ${f['usd_day']:.1f}/d <= ${bf['usd_day']:.1f}/d")
    if not r["crit"]["b"]: why.append("(b) a fit window <= $0: " + ", ".join(w for w in FIT_NAMES if r["res"][w]["usd"] <= 0))
    if not r["crit"]["c"]: why.append(f"(c) val ${r['res']['val']['usd']:.2f} / {r['res']['val']['mean'] or 0:+.1%} vs ${bv['usd']:.2f} / {bv['mean']:+.1%}")
    if not r["crit"]["d"]: why.append(f"(d) fit win {f['win']:.1%} (floor {bf['win'] - 0.10:.1%}), dead {f['dead']:.1%} (ceiling {bf['dead'] + 0.05:.1%})")
    if not r["crit"]["e"]: why.append(f"(e) {f['n']} fit fires < 30")
    table(f"[{r['family']}] {r['name']}  FAILS: " + "; ".join(why), r["res"], P)

P("\n=== 1. what each pass changes against the baseline (fires added / removed), per window, $ at $13 after gas")
for r in passes:
    fam, name, fire, ret, stake = r["_c"]
    P(f"--- {name}")
    for grp in FIT_NAMES + ["FIT"] + VAL_NAMES + ["VAL"]:
        names = FIT_NAMES if grp == "FIT" else VAL_NAMES if grp == "VAL" else [grp]
        W = [x for x in rows if x["win"] in names]
        add = [ret(x) for x in W if fire(x) and not BASE(x)]; rem = [RET(x) for x in W if BASE(x) and not fire(x)]
        chg = [ret(x) - RET(x) for x in W if fire(x) and BASE(x) and ret(x) != RET(x)]
        s = f"  {grp:10s} added {len(add):3d}"
        if add: s += f" mean {st.mean(add):+7.1%} median {st.median(add):+7.1%} win {sum(v > 0 for v in add)/len(add):4.0%} ${sum(v * STAKE - GAS for v in add):+7.2f}"
        s += f" | removed {len(rem):2d}"
        if rem: s += f" mean {st.mean(rem):+7.1%} ${sum(v * STAKE - GAS for v in rem):+7.2f}"
        if chg: s += f" | re-priced {len(chg)} ${sum(v * STAKE for v in chg):+.2f}"
        P(s)
    # (a) re-checked with each fit launch removed from BOTH sides (does the fit $/day gain rest on one launch?)
    FR = [x for x in rows if x["set"] == "fit"]; ca = sum(ret(x) * STAKE - GAS for x in FR if fire(x)); ba = sum(RET(x) * STAKE - GAS for x in FR if BASE(x))
    flips = [(x["cv"][:10], x["win"], ret(x) if fire(x) else RET(x)) for x in FR if (fire(x) or BASE(x))
             and not (ca - ((ret(x) * STAKE - GAS) if fire(x) else 0) > ba - ((RET(x) * STAKE - GAS) if BASE(x) else 0) + 1e-9)]
    P(f"  (a) margin: fit ${ca - ba:+.2f} over 96 h (${(ca - ba) / 96 * 24:+.2f}/d); (a) fails when ONE fit launch is removed from both sides: "
      + (", ".join(f"{c} {w} {v:+.1%}" for c, w, v in flips) if flips else "none"))
    va = sorted([(ret(x), x["cv"][:10], x["win"], x["nf_k2"], x["k"]) for x in rows if x["set"] == "val" and fire(x) and not BASE(x)], reverse=True)
    P("  validation launches it adds: " + ", ".join(f"{c} {w} {v:+.1%}" for v, c, w, n, k in va))

P("\n=== 2. threshold neighbours (same family, same feature, every fit-quantile cut): which cuts pass, and what each fails")
import re
done_feats = set()
for r in passes:
    m = re.match(r"BASE OR \((.+) & (.+) (>=|<) ([0-9.e+-]+)\)", r["name"])
    if not m or m.group(2) in done_feats: continue
    sub, feat = m.group(1), m.group(2); done_feats.add(feat)
    P(f"--- {sub} & {feat}")
    for x in S.results:
        mm = re.match(r"BASE OR \((.+) & (.+) (>=|<) ([0-9.e+-]+)\)", x["name"])
        if mm and mm.group(2) == feat and mm.group(1) in (sub, "0-1 fleets", "exactly 1 fleet"):
            failed = "".join(k for k, v in x["crit"].items() if not v) or "PASS"
            P(f"  {failed:6s} {x['name']}: {S.short(x['res'])}")

P("\n=== 3. null test: the OR family with random features (uniform, fixed seeds 0..199)")
REF_FIT = [x for x in rows if x["set"] == "fit" and not BASE(x)]
real_or = [x for x in S.CAND if x["family"] == "OR"]
real_pass = sum(x["pass"] for x in real_or); real_distinct = len({S.sig(x["_c"][2], x["_c"][3]) for x in real_or if x["pass"]})
tot = npass = seeds_with_pass = 0
for seed in range(200):
    rnd = random.Random(seed); fv = {x["cv"] + x["win"]: rnd.random() for x in rows}
    fx = lambda x, fv=fv: fv[x["cv"] + x["win"]]; any_pass = False
    for sn, sf in S.SUBS.items():
        pop = [x for x in REF_FIT if sf(x)]
        for t in S.qthr([fx(x) for x in pop]):
            for d in (">=", "<"):
                fire = (lambda x, sf=sf, t=t: BASE(x) or (sf(x) and fx(x) >= t)) if d == ">=" else (lambda x, sf=sf, t=t: BASE(x) or (sf(x) and fx(x) < t))
                cr = S.criteria(evaluate(rows, fire)); tot += 1
                if all(cr.values()): npass += 1; any_pass = True
    seeds_with_pass += any_pass
P(f"  random features: {npass} of {tot} variants clear (a)-(e) = {npass/tot:.1%}; {seeds_with_pass} of 200 random features have at least one passing cut (of 24 cuts each)")
P(f"  real features:   {real_pass} of {len(real_or)} OR variants clear (a)-(e) = {real_pass/len(real_or):.1%} ({real_distinct} distinct fire sets)")

P("\n=== 4. the engine's own skips applied to BOTH sides (not in the brief's baseline numbers): one position at a time, creator repeat")
def engine_skips(fire, hold_blocks=300, block_s=0.1):
    """fires the engine would take: skip a creator's repeat launch of the day (qualifying launches only: an approximation), then one
    position at a time (skip a fire whose T0 falls inside the previous fire's hold, hold_blocks * block_s seconds after its tick)"""
    keep = set()
    for w in FIT_NAMES + VAL_NAMES:
        busy = -1
        for x in sorted([x for x in rows if x["win"] == w and fire(x) and not x["creator_repeat"]], key=lambda x: x["T0"]):
            if x["T0"] <= busy: continue
            keep.add(x["cv"] + w); busy = x["T0"] + 1 + hold_blocks * block_s
    return lambda x: (x["cv"] + x["win"]) in keep
b_sk = evaluate(rows, engine_skips(BASE))
P(f"  baseline with skips: {S.short(b_sk)}")
for r in passes:
    fam, name, fire, ret, stake = r["_c"]
    res = evaluate(rows, engine_skips(fire), ret); f, v = res["fit"], res["val"]
    ok = (f["usd_day"] > b_sk["fit"]["usd_day"], all(res[w]["usd"] > 0 for w in FIT_NAMES), v["usd"] >= b_sk["val"]["usd"] - 1e-9 and v["mean"] >= b_sk["val"]["mean"] - 1e-12,
          f["win"] >= b_sk["fit"]["win"] - 0.10 and f["dead"] <= b_sk["fit"]["dead"] + 0.05, f["n"] >= 30)
    P(f"  {name}: {S.short(res)}  criteria vs the skipped baseline: {''.join('abcde'[i] if not o else '' for i, o in enumerate(ok)) or 'all pass'}")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "a_diagnose_output.txt"), "w").write("\n".join(out) + "\n")
