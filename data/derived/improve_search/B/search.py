"""search.py (searcher B): every candidate rule scored on the FIT windows, the protocol's criteria (a),(b),(d),(e) checked on FIT,
then (c) on the VALIDATION windows. Executable views only: every gate and feature reads blocks <= k-2 of the creation second
(or launch-level fields the brief lists as pre-tick: bundle_eth, named, tier, hour, k, creator). Writes search_results.json.
    cd /home/user/fomo-memebot && python3 <B>/search.py [--show N]"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
HERE = os.path.dirname(os.path.abspath(__file__))
W = load()
F_ALL = [r for n in FIT_NAMES for r in W[n]["rows"]]
HOLDS = RET_KEYS[:9]                       # behind1 $15 model: h15..h600, tp50_h600, stop20_h600, tp50_stop20_h600
BKEY = "behind1_15_h300"

# ---------- the baseline, both sets
b_fit_per, b_fit = evaluate(W, FIT_NAMES, BASE, BKEY); b_val_per, b_val = evaluate(W, VAL_NAMES, BASE, BKEY)

# ---------- gates (unit / threshold / view), all at k-2 or earlier
G = collections.OrderedDict()
for n in (1, 2, 3, 4): G[f"fleets>={n}@k-2"] = (lambda n: lambda r: r["f_k2"] >= n)(n)
for n in (1, 2, 3, 5, 10): G[f"wallets>={n}@k-2"] = (lambda n: lambda r: r["w_k2"] >= n)(n)
for n in (1, 2): G[f"fleets>={n}@k-3"] = (lambda n: lambda r: r["f_k3"] >= n)(n)
G["fleets>=2@k-2 & fleets>=1@k-3"] = lambda r: r["f_k2"] >= 2 and r["f_k3"] >= 1
for n in (1, 2, 5): G[f"fleets>=2@k-2 & wallets>={n}@k-3"] = (lambda n: lambda r: r["f_k2"] >= 2 and r["w_k3"] >= n)(n)
for n in (3, 5, 10): G[f"fleets>=2@k-2 & wallets>={n}@k-2"] = (lambda n: lambda r: r["f_k2"] >= 2 and r["w_k2"] >= n)(n)
for n in (2, 3, 5, 10, 20): G[f"fleets>=2@k-2 | wallets>={n}@k-2"] = (lambda n: lambda r: r["f_k2"] >= 2 or r["w_k2"] >= n)(n)
for n in (2, 3, 5, 10): G[f"fleets>=1@k-2 & wallets>={n}@k-2"] = (lambda n: lambda r: r["f_k2"] >= 1 and r["w_k2"] >= n)(n)
G["fleets>=2@k-2 | fleets>=1@k-3"] = lambda r: r["f_k2"] >= 2 or r["f_k3"] >= 1
for n in (2, 3, 5): G[f"fleets>=2@k-2 | shots>={n}@k-2"] = (lambda n: lambda r: r["f_k2"] >= 2 or r["shots_k2"] >= n)(n)
G["fleets>=2@k-2 | wallets>=2@k-3"] = lambda r: r["f_k2"] >= 2 or r["w_k3"] >= 2

# ---------- pre-tick features (cut points: fit-set quartiles of the qualifying launches, or natural values)
def q(feat, p): v = sorted(r[feat] for r in F_ALL if r[feat] is not None); return v[int(len(v) * p)]
C = collections.OrderedDict()
for p in (0.25, 0.5, 0.75):
    c = q("bundle_eth", p); C[f"bundle_eth>={c:.3f}"] = (lambda c: lambda r: r["bundle_eth"] is not None and r["bundle_eth"] >= c)(c); C[f"bundle_eth<{c:.3f}"] = (lambda c: lambda r: r["bundle_eth"] is not None and r["bundle_eth"] < c)(c)
for c in (1.0, 1.5): C[f"bundle_eth>={c}"] = (lambda c: lambda r: r["bundle_eth"] is not None and r["bundle_eth"] >= c)(c)
for c in (4, 5, 6, 10, 15): C[f"named>={c}"] = (lambda c: lambda r: r["named"] is not None and r["named"] >= c)(c); C[f"named<{c}"] = (lambda c: lambda r: r["named"] is not None and r["named"] < c)(c)
C["tier==2%"] = lambda r: r["tier"] is not None and r["tier"] <= 0.0205; C["tier>2%"] = lambda r: r["tier"] is not None and r["tier"] > 0.0205; C["tier==3%"] = lambda r: r["tier"] is not None and r["tier"] >= 0.0295
for c in (3, 4, 5, 6, 7, 8): C[f"k>={c}"] = (lambda c: lambda r: r["k"] >= c)(c)
for c in (4, 5, 6, 7): C[f"k<={c}"] = (lambda c: lambda r: r["k"] <= c)(c)
HB = {"h00-05": range(0, 6), "h06-11": range(6, 12), "h12-17": range(12, 18), "h18-23": range(18, 24)}
for nm, hs in HB.items(): C[f"not {nm}"] = (lambda hs: lambda r: r["hour"] not in hs)(hs); C[f"only {nm}"] = (lambda hs: lambda r: r["hour"] in hs)(hs)
C["TRADE_HOURS 12-05"] = lambda r: r["hour"] >= 12 or r["hour"] < 5
for c in (2, 3, 4, 5): C[f"arr1>={c}"] = (lambda c: lambda r: r["arr1"] is not None and r["arr1"] >= c)(c)       # first fleet seen >= c blocks before the end (c>=2: by k-2)
for c in (3, 4, 5): C[f"arr2>={c}"] = (lambda c: lambda r: r["arr2"] is not None and r["arr2"] >= c)(c)
for c in (1, 2, 3, 5, 10, 20): C[f"w@k-2>={c}"] = (lambda c: lambda r: r["w_k2"] >= c)(c)
for c in (2, 3, 5, 10): C[f"maxw@k-2>={c}"] = (lambda c: lambda r: r["maxw_k2"] >= c)(c); C[f"maxw@k-2<{c}"] = (lambda c: lambda r: r["maxw_k2"] < c)(c)
for c in (2, 3, 5, 10): C[f"maxshots@k-2>={c}"] = (lambda c: lambda r: r["maxshots_k2"] >= c)(c)
for c in (2, 5, 10, 20): C[f"shots@k-2>={c}"] = (lambda c: lambda r: r["shots_k2"] >= c)(c); C[f"shots@k-2<{c}"] = (lambda c: lambda r: r["shots_k2"] < c)(c)
C["direct fleets@k-2==0"] = lambda r: r["fd_k2"] == 0; C["direct fleets@k-2>=1"] = lambda r: r["fd_k2"] >= 1
C["relay fleets@k-2>=1"] = lambda r: r["fr_k2"] >= 1; C["relay fleets@k-2>=2"] = lambda r: r["fr_k2"] >= 2
C["not creator repeat"] = lambda r: not r["creator_repeat"]

CANDS = collections.OrderedDict()
for gn, g in G.items(): CANDS[gn] = g
for cn, c in C.items():
    CANDS[f"BASE & {cn}"] = (lambda c: lambda r: BASE(r) and c(r))(c)
    CANDS[f"BASE | (f@k-2==1 & {cn})"] = (lambda c: lambda r: BASE(r) or (r["f_k2"] == 1 and c(r)))(c)
    CANDS[f"BASE | (f@k-2==0 & {cn})"] = (lambda c: lambda r: BASE(r) or (r["f_k2"] == 0 and c(r)))(c)
    CANDS[f"BASE | (f@k-2<2 & {cn})"] = (lambda c: lambda r: BASE(r) or (r["f_k2"] < 2 and c(r)))(c)

def crit(fit_per, fit, val):
    a = fit["usd_day"] > b_fit["usd_day"]
    b = all(m["n"] > 0 and m["usd_burst"] > 0 for m in fit_per.values())
    c = val["n"] > 0 and val["usd_total"] >= b_val["usd_total"] and val["mean"] >= b_val["mean"]
    d = fit["n"] > 0 and fit["win"] >= b_fit["win"] - 0.10 and fit["dead"] <= b_fit["dead"] + 0.05
    e = fit["n"] >= 30
    return {"a": a, "b": b, "c": c, "d": d, "e": e}

# executability: the engine cannot aim at a creation in the last 1-2 blocks of its second (k <= 2; report 24.33 addendum 4), so every
# candidate fires only on k >= 3 (no baseline fire has k <= 2, so the baseline is unchanged). RAW=1 drops this (the tables' view).
AIM = os.environ.get("RAW") != "1"
if AIM: CANDS = collections.OrderedDict((cn, (lambda rule: lambda r: r["k"] >= 3 and rule(r))(rule)) for cn, rule in CANDS.items())
print("un-aimable k<=2 launches excluded from every candidate:", AIM)
res = []; seen_sets = {}
for cn, rule in CANDS.items():
    for hk in HOLDS:
        fp, fpool = evaluate(W, FIT_NAMES, rule, hk); vp, vpool = evaluate(W, VAL_NAMES, rule, hk)
        cr = crit(fp, fpool, vpool)
        fit_set = tuple(sorted(r["cv"] for n in FIT_NAMES for r in W[n]["rows"] if rule(r)))
        val_set = tuple(sorted(r["cv"] for n in VAL_NAMES for r in W[n]["rows"] if rule(r)))
        res.append({"cand": cn, "hold": hk, "fit": fpool, "fit_per": fp, "val": vpool, "val_per": vp, "crit": cr,
                    "fitq": cr["a"] and cr["b"] and cr["d"] and cr["e"], "pass": all(cr.values()), "key": (fit_set, val_set, hk)})
distinct = len({r["key"] for r in res})
nq = [r for r in res if r["fitq"]]; npass = [r for r in res if r["pass"]]
print(f"baseline FIT: {fmt(b_fit)}\nbaseline VAL: {fmt(b_val)}")
print(f"\ncandidates: {len(CANDS)} rules x {len(HOLDS)} holds = {len(res)} variants ({distinct} distinct fire-set/hold combinations)")
print(f"fit-qualified (a,b,d,e on FIT): {len(nq)}; pass all five (incl. c on VAL): {len(npass)}")
# criterion counts
for k_ in "abcde": print(f"  criterion {k_} met by {sum(r['crit'][k_] for r in res)}")
show = int(sys.argv[sys.argv.index("--show") + 1]) if "--show" in sys.argv else 40
def line(r): return (f"{r['cand'][:58]:58s} {r['hold'].replace('behind1_15_',''):14s} FIT n={r['fit']['n']:3d} {r['fit']['mean']:+6.1%} win {r['fit']['win']:3.0%} dead {r['fit']['dead']:3.0%} ${r['fit']['usd_day']:5.1f}/d"
                     f" | VAL n={r['val']['n']:3d} {r['val']['mean']:+6.1%} ${r['val']['usd_total']:+6.1f} | {''.join(k_ if v else '-' for k_, v in r['crit'].items())}")
print("\n=== fit-qualified variants, by FIT $/day (criteria string: a letter = met)")
for r in sorted(nq, key=lambda r: -r["fit"]["usd_day"])[:show]: print(line(r))
print("\n=== all variants by FIT $/day, top", show)
for r in sorted(res, key=lambda r: -r["fit"]["usd_day"])[:show]: print(line(r))
json.dump([{k_: v for k_, v in r.items() if k_ != "key"} for r in res], open(os.path.join(HERE, "search_results%s.json" % ("" if AIM else "_raw")), "w"), default=float)
