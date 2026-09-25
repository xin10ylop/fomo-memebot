"""a_search.py (searcher A): every candidate change to the engine's rule, scored under the brief's protocol.

Fit = the four backtest windows (thresholds are chosen on fit rows only); validation = the five paper windows (+0xf45fa520).
Executable view only: every gate and every crowd feature is read at block k-2 (or earlier, k-3). The k-1 rows are printed
apart as borderline and are never candidates. Returns: hold_grid behind1 columns ($15 model) scored at $13 after $0.33 gas.

    python3 a_search.py            # prints the summary, writes a_results.json next to this file
    python3 a_search.py --all      # also prints one line per variant"""
import os, sys, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a_common import *

HERE = os.path.dirname(os.path.abspath(__file__))
rows = load_all()
FIT_ROWS = [r for r in rows if r["set"] == "fit"]

f2 = lambda r: r["nf_k2"]; w2 = lambda r: r["nw_k2"]; f3 = lambda r: r["nf_k3"]; w3 = lambda r: r["nw_k3"]
BASE = lambda r: r["nf_k2"] >= 2
RET = lambda r: r["behind1_15_h300"]

def qthr(vals, qs=(0.2, 0.4, 0.6, 0.8)):
    """thresholds at the fit quantiles (deterministic: sorted value at floor(q*n)), distinct, sorted"""
    v = sorted(x for x in vals if x is not None)
    return sorted({v[int(q * len(v))] for q in qs}) if v else []

C = []   # (family, name, fire, ret, stake)
def add(fam, name, fire, ret=RET, stake=STAKE): C.append((fam, name, fire, ret, stake))

# ---------------------------------------------------------------- family 1: the threshold / unit / view (hold h300)
add("baseline", "fleets>=2 @k-2 (BASELINE)", BASE)
for n in (1, 3, 4, 5): add("threshold", f"fleets>={n} @k-2", lambda r, n=n: f2(r) >= n)
for n in (1, 2, 3, 4, 5, 7, 10, 15, 20, 30): add("threshold", f"wallets>={n} @k-2", lambda r, n=n: w2(r) >= n)
for n in (1, 2, 3): add("threshold", f"fleets>={n} @k-3", lambda r, n=n: f3(r) >= n)
for n in (1, 2, 3, 5): add("threshold", f"wallets>={n} @k-3", lambda r, n=n: w3(r) >= n)
add("threshold", "fleets>=2 @k-2 & fleets>=1 @k-3", lambda r: f2(r) >= 2 and f3(r) >= 1)
for m in (1, 2, 3, 5): add("threshold", f"fleets>=2 @k-2 & wallets>={m} @k-3", lambda r, m=m: f2(r) >= 2 and w3(r) >= m)
for m in (3, 4, 5, 10): add("threshold", f"fleets>=2 @k-2 & wallets>={m} @k-2", lambda r, m=m: f2(r) >= 2 and w2(r) >= m)
for m in (2, 3, 5, 10, 20, 30): add("threshold", f"fleets>=2 @k-2 OR wallets>={m} @k-2", lambda r, m=m: f2(r) >= 2 or w2(r) >= m)
for m in (2, 3, 5, 10, 20): add("threshold", f"fleets>=1 @k-2 & wallets>={m} @k-2", lambda r, m=m: f2(r) >= 1 and w2(r) >= m)
add("threshold", "fleets>=2 @k-2 OR fleets>=1 @k-3", lambda r: f2(r) >= 2 or f3(r) >= 1)
add("threshold", "fleets>=2 @k-2 OR (fleets>=1 @k-3 & wallets>=2 @k-3)", lambda r: f2(r) >= 2 or (f3(r) >= 1 and w3(r) >= 2))
for hi in (2, 3, 4): add("threshold", f"2<=fleets<={hi} @k-2", lambda r, hi=hi: 2 <= f2(r) <= hi)
add("threshold", "fleets>=2 @k-2 & fleets>=2 @k-3 (=fleets>=2 @k-3)", lambda r: f2(r) >= 2 and f3(r) >= 2)
add("threshold", "fleets>=3 @k-2 OR fleets>=2 @k-3", lambda r: f2(r) >= 3 or f3(r) >= 2)

# ---------------------------------------------------------------- family 2: the hold / exit (baseline gate and neighbours)
EXITS = ["h15", "h30", "h60", "h150", "h600", "tp50_h600", "stop20_h600", "tp50_stop20_h600"]
def tp_stop_pess(r):
    """hold_grid.py line 66 takes the tp value whenever BOTH tp and stop were hit (order unknown): pessimistic bound = the stop"""
    tp, stp, h6 = r["behind1_15_tp50_h600"], r["behind1_15_stop20_h600"], r["behind1_15_h600"]
    return stp if (tp != h6 and stp != h6) else r["behind1_15_tp50_stop20_h600"]
for gname, g in (("fleets>=2 @k-2", BASE), ("fleets>=1 @k-2", lambda r: f2(r) >= 1), ("fleets>=3 @k-2", lambda r: f2(r) >= 3)):
    for ex in EXITS: add("hold", f"{gname}, behind1 {ex}", g, lambda r, ex=ex: r[f"behind1_15_{ex}"])
    add("hold", f"{gname}, behind1 tp50_stop20_h600 PESSIMISTIC (stop first when both hit)", g, tp_stop_pess)

# ---------------------------------------------------------------- family 3: AND-filters on the baseline gate (thresholds at fit quantiles of the 73 baseline fires)
BF = [r for r in FIT_ROWS if BASE(r)]
FEATS = {"bundle_eth": lambda r: r["bundle_eth"], "named": lambda r: r["named"], "tier": lambda r: r["tier"], "k": lambda r: r["k"],
         "arr2_d (blocks before the end when the 2nd fleet showed)": lambda r: r["arr2_d"], "arr1_d": lambda r: r["arr1_d"],
         "wallets@k-2": w2, "fleets@k-2": f2, "direct fleets@k-2": lambda r: r["n_direct_k2"], "relay fleets@k-2": lambda r: r["n_relay_k2"],
         "shots@k-2": lambda r: r["shots_k2"], "shots/fleet@k-2": lambda r: r["shots_per_fleet_k2"], "wallets/fleet@k-2": lambda r: r["wallets_per_fleet_k2"],
         "max shots of one fleet@k-2": lambda r: r["max_fleet_shots_k2"], "blocks with a new fleet@k-2": lambda r: r["blocks_active_k2"],
         "wallets@k-3": w3, "fleets@k-3": f3}
for fn, fx in FEATS.items():
    for t in qthr([fx(r) for r in BF]):
        add("AND", f"BASE & {fn} >= {t:g}", lambda r, fx=fx, t=t: BASE(r) and fx(r) is not None and fx(r) >= t)
        add("AND", f"BASE & {fn} < {t:g}", lambda r, fx=fx, t=t: BASE(r) and fx(r) is not None and fx(r) < t)
add("AND", "BASE & direct fleets@k-2 >= 1 & relay fleets@k-2 >= 1", lambda r: BASE(r) and r["n_direct_k2"] >= 1 and r["n_relay_k2"] >= 1)
add("AND", "BASE & relay only (no direct fleet @k-2)", lambda r: BASE(r) and r["n_direct_k2"] == 0)
add("AND", "BASE & direct only (no relay fleet @k-2)", lambda r: BASE(r) and r["n_relay_k2"] == 0)
add("AND", "BASE & tier == 3%", lambda r: BASE(r) and abs(r["tier"] - 0.03) < 1e-9)
add("AND", "BASE & tier < 3%", lambda r: BASE(r) and r["tier"] < 0.03 - 1e-9)
add("engine-skip", "BASE & not a creator repeat (approx. of the skip the engine ALREADY runs: not a change)", lambda r: BASE(r) and not r["creator_repeat"])

# ---------------------------------------------------------------- family 5: hours of the day (AND on the baseline)
HB = {"00-06": range(0, 6), "06-12": range(6, 12), "12-18": range(12, 18), "18-24": range(18, 24)}
for hb, hr in HB.items():
    add("hours", f"BASE & hour in {hb}", lambda r, hr=hr: BASE(r) and r["hour"] in hr)
    add("hours", f"BASE & hour not in {hb}", lambda r, hr=hr: BASE(r) and r["hour"] not in hr)
add("hours", "BASE & TRADE_HOURS 12-05 (hour >= 12 or < 5)", lambda r: BASE(r) and (r["hour"] >= 12 or r["hour"] < 5))
add("hours", "BASE & hour not in 05-12", lambda r: BASE(r) and not (5 <= r["hour"] < 12))

# ---------------------------------------------------------------- family 4: OR-branches ("fire also when ...") on the refused launches
REF = [r for r in FIT_ROWS if not BASE(r)]
SUBS = {"0-1 fleets": lambda r: f2(r) <= 1, "exactly 1 fleet": lambda r: f2(r) == 1, "0 fleets": lambda r: f2(r) == 0}
LAUNCH_FEATS = {"bundle_eth": lambda r: r["bundle_eth"], "named": lambda r: r["named"], "tier": lambda r: r["tier"], "k": lambda r: r["k"], "hour": lambda r: r["hour"]}
CROWD_FEATS = {"wallets@k-2": w2, "arr1_d": lambda r: r["arr1_d"], "shots@k-2": lambda r: r["shots_k2"], "wallets/fleet@k-2": lambda r: r["wallets_per_fleet_k2"],
               "direct fleets@k-2": lambda r: r["n_direct_k2"], "relay fleets@k-2": lambda r: r["n_relay_k2"], "wallets@k-3": w3, "fleets@k-3": f3}
for sn, sf in SUBS.items():
    pop = [r for r in REF if sf(r)]
    feats = dict(LAUNCH_FEATS); feats.update(CROWD_FEATS if sn != "0 fleets" else {})
    for fn, fx in feats.items():
        for t in qthr([fx(r) for r in pop]):
            add("OR", f"BASE OR ({sn} & {fn} >= {t:g})", lambda r, sf=sf, fx=fx, t=t: BASE(r) or (sf(r) and fx(r) is not None and fx(r) >= t))
            add("OR", f"BASE OR ({sn} & {fn} < {t:g})", lambda r, sf=sf, fx=fx, t=t: BASE(r) or (sf(r) and fx(r) is not None and fx(r) < t))
    add("OR", f"BASE OR ({sn} & tier == 3%)", lambda r, sf=sf: BASE(r) or (sf(r) and abs(r["tier"] - 0.03) < 1e-9))
    add("OR", f"BASE OR ({sn} & tier < 3%)", lambda r, sf=sf: BASE(r) or (sf(r) and r["tier"] < 0.03 - 1e-9))
    for hb, hr in HB.items(): add("OR", f"BASE OR ({sn} & hour in {hb})", lambda r, sf=sf, hr=hr: BASE(r) or (sf(r) and r["hour"] in hr))

N_SEARCH = len(C)

# ---------------------------------------------------------------- scoring and the protocol
def score(c):
    fam, name, fire, ret, stake = c
    return evaluate(rows, fire, ret, stake=stake)
B = score(C[0]); assert C[0][0] == "baseline"
bf, bv = B["fit"], B["val"]

def criteria(res):
    f, v = res["fit"], res["val"]
    a = f["usd_day"] > bf["usd_day"] + 1e-9
    b = all(res[w]["n"] > 0 and res[w]["usd"] > 0 for w in FIT_NAMES)
    c = v["n"] > 0 and v["usd"] >= bv["usd"] - 1e-9 and v["mean"] >= bv["mean"] - 1e-12
    d = f["n"] > 0 and f["win"] >= bf["win"] - 0.10 - 1e-12 and f["dead"] <= bf["dead"] + 0.05 + 1e-12
    e = f["n"] >= 30
    return {"a": a, "b": b, "c": c, "d": d, "e": e}

def loo_c(fire, ret):
    """(c) re-checked with each validation launch that either rule fires on removed from BOTH sides: does (c) survive every removal?"""
    vr = [r for r in rows if r["set"] == "val"]; fails = []
    for x in vr:
        if not (fire(x) or BASE(x)): continue
        sub = [r for r in vr if r is not x]
        cand = [ret(r) for r in sub if fire(r)]; base = [RET(r) for r in sub if BASE(r)]
        cu = sum(y * STAKE - GAS for y in cand); bu = sum(y * STAKE - GAS for y in base)
        cm = st.mean(cand) if cand else -9; bm = st.mean(base) if base else -9
        if not (cu >= bu - 1e-9 and cm >= bm - 1e-12): fails.append(x["cv"][:10])
    return fails

def sig(fire, ret): return tuple(sorted((r["cv"], round(ret(r), 12)) for r in rows if fire(r)))
BSIG = sig(BASE, RET); SEEN = {}
results = []
for c in C:
    res = score(c); cr = criteria(res); passed = all(cr.values()); sg = sig(c[2], c[3])
    noop = (sg == BSIG and c[0] != "baseline"); dup = SEEN.get(sg); SEEN.setdefault(sg, c[1])
    miss = sum(not v for v in cr.values())
    # a distance-to-pass for ranking misses: number of failed criteria, then the relative $/day gap and validation gap
    gap = (max(0, bf["usd_day"] - res["fit"]["usd_day"]) / bf["usd_day"] + max(0, bv["usd"] - res["val"]["usd"]) / abs(bv["usd"])
           + max(0, (bv["mean"] - (res["val"]["mean"] if res["val"]["mean"] is not None else -1))) / abs(bv["mean"]))
    results.append({"family": c[0], "name": c[1], "res": res, "crit": cr, "pass": passed, "n_fail": miss, "gap": gap,
                    "loo_fail": loo_c(c[2], c[3]) if passed else None, "noop": noop, "dup_of": dup if dup != c[1] else None, "_c": c})
CAND = [r for r in results if r["family"] not in ("baseline", "engine-skip")]

# ---------------------------------------------------------------- borderline views (k-1): printed apart, never candidates
BORDER = [("fleets>=2 @k-1", lambda r: r["nf_k1"] >= 2), ("fleets>=3 @k-1", lambda r: r["nf_k1"] >= 3), ("wallets>=2 @k-1", lambda r: r["nw_k1"] >= 2)]

# ---------------------------------------------------------------- stake: $100 column (information; the protocol's $/day is at $13)
STAKES = [("fleets>=2 @k-2, $15 model scored at $13", BASE, lambda r: r["behind1_15_h300"], 13.0),
          ("fleets>=2 @k-2, $15 model scored at $15", BASE, lambda r: r["behind1_15_h300"], 15.0),
          ("fleets>=2 @k-2, $100 model scored at $100", BASE, lambda r: r["behind1_100_h300"], 100.0)]

def short(res):
    f, v = res["fit"], res["val"]
    fw = " ".join(f"{res[w]['usd']:+6.1f}" for w in FIT_NAMES)
    vm = f"{v['mean']:+6.1%}" if v["mean"] is not None else "     -"
    fm = f"{f['mean']:+6.1%}" if f["mean"] is not None else "     -"
    fwin = f"{f['win']:3.0%}" if f["win"] is not None else "  -"
    fdead = f"{f['dead']:3.0%}" if f["dead"] is not None else "  -"
    return (f"fit n={f['n']:3d} {fm} win {fwin} dead {fdead} ${f['usd_day']:+5.1f}/d | per-window $ [{fw}] | "
            f"val n={v['n']:2d} {vm} ${v['usd']:+6.2f}")

if __name__ == "__main__":
    out = []
    P = lambda s="": (print(s), out.append(s))
    fams = collections.Counter(r["family"] for r in results)
    P(f"variants scored: {len(results)} (baseline 1 + {len(CAND)} candidates + {fams['engine-skip']} engine-skip check) by family: {dict(fams)}")
    P(f"  distinct fire/return sets among the candidates: {len({sig(r['_c'][2], r['_c'][3]) for r in CAND})}; identical to the baseline (no-ops): {sum(r['noop'] for r in CAND)}")
    P(f"baseline: {short(B)}")
    P(f"pass thresholds: (a) fit $/day > {bf['usd_day']:.2f}; (b) $ after gas > 0 in each fit window; (c) val $ total >= {bv['usd']:.2f} AND val mean >= {bv['mean']:+.2%};"
      f" (d) fit win >= {bf['win'] - 0.10:.1%}, fit dead <= {bf['dead'] + 0.05:.1%}; (e) fit fires >= 30")
    cnt = {k: sum(r["crit"][k] for r in CAND) for k in "abcde"}
    P(f"candidates meeting each criterion alone: {cnt}")
    passes = sorted([r for r in CAND if r["pass"]], key=lambda r: -r["res"]["fit"]["usd_day"])
    P(f"\nPASSES: {len(passes)}")
    for r in passes:
        m_usd = r["res"]["val"]["usd"] - bv["usd"]; m_mean = r["res"]["val"]["mean"] - bv["mean"]
        P(f"  [{r['family']}] {r['name']}" + (f"   (same fires as: {r['dup_of']})" if r["dup_of"] else "") + f"\n      {short(r['res'])}\n      (c) margin: val ${m_usd:+.2f}, mean {m_mean:+.2%}; "
          f"(c) fails when ONE validation launch is removed from both sides: {r['loo_fail'] or 'none'}")
    for r in [r for r in results if r["family"] == "engine-skip"]:
        P(f"  (not a candidate) [{r['family']}] {r['name']}\n      {short(r['res'])}")
    # closest misses: fewest failed criteria, then smallest gap; among candidates that pass (e)
    misses = sorted([r for r in CAND if not r["pass"] and not r["noop"] and not r["dup_of"]], key=lambda r: (r["n_fail"], r["gap"]))
    P("\nCLOSEST MISSES (fewest failed criteria, then the smallest shortfall on (a)/(c)):")
    for r in misses[:15]:
        failed = "".join(k for k, v in r["crit"].items() if not v)
        P(f"  fails ({failed}) [{r['family']}] {r['name']}\n      {short(r['res'])}")
    P("\nBEST fit $/day among candidates, whatever they fail (top 10):")
    for r in sorted(CAND, key=lambda r: -r["res"]["fit"]["usd_day"])[:10]:
        failed = "".join(k for k, v in r["crit"].items() if not v)
        P(f"  fails ({failed or '-'}) [{r['family']}] {r['name']}\n      {short(r['res'])}")
    P("\nBORDERLINE (k-1 view: not executable as a headline, shown for reference only):")
    for nm, fz in BORDER: P(f"  {nm}: {short(evaluate(rows, fz))}")
    P("\nSTAKE (information; the protocol scores $/day at $13):")
    for nm, fz, rz, sk in STAKES:
        res = evaluate(rows, fz, rz, stake=sk); pw = " ".join("%+.1f" % res[w]["usd"] for w in FIT_NAMES)
        P(f"  {nm}: fit mean {res['fit']['mean']:+.1%}, ${res['fit']['usd_burst']:+.2f}/burst, ${res['fit']['usd_day']:+.1f}/d; per-window $ [{pw}]; "
          f"val mean {res['val']['mean']:+.1%}, ${res['val']['usd']:+.2f} total")
    x15 = [r["behind1_15_h300"] for r in rows if BASE(r)]; x100 = [r["behind1_100_h300"] for r in rows if BASE(r)]
    P(f"  on the {len(x15)} baseline fires (fit+val): $100-model return minus $15-model return: mean {st.mean(b - a for a, b in zip(x15, x100)):+.2%}, "
      f"median {st.median(b - a for a, b in zip(x15, x100)):+.2%}")
    if "--all" in sys.argv:
        P("\nALL VARIANTS:")
        for r in results:
            failed = "".join(k for k, v in r["crit"].items() if not v)
            P(f"  {'PASS' if r['pass'] else 'fail ' + failed:10s} [{r['family']}] {r['name']}: {short(r['res'])}")
    json.dump([{k: v for k, v in r.items() if k != "_c"} for r in results], open(os.path.join(HERE, "a_results.json"), "w"), indent=0, default=str)
    open(os.path.join(HERE, "a_search_output.txt"), "w").write("\n".join(out) + "\n")
