"""verify.py (verifier VI): independent recomputation of reviewer I's headline numbers without importing I/common.py.
Population from crowd_raw files (fit / rec = 11 files + gapA/gapB / late = sep27pm, sep27eve), dedupe by curve first-file-wins;
engine fires via fleet_variants.fleets_k2 (exec'd whole-function from the source), tables via crowd_rules cums/at.
Bundle recomputed from tapes (own code, e1_multi's rule); late launches' bundle from e1m_sep27{pm,eve}.json.
Returns: G/curves.json.gz r2[h]; late: hold_grid behind1_15_h15.  Hours: fit 96.0; rec union of e1m/gap bounds.
    python3 data/derived/edge_check/VI/verify.py"""
import json, gzip, os, sys, math, statistics as st, collections, random
os.chdir("/home/user/fomo-memebot")
sys.argv = ["x", "0.76", "0.71"]; exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])
src = open("src/analysis/fleet_variants.py").read(); exec(src[src.index("def fleets_k2"):src.index("seen = set(); pop =")])
LV = "data/derived/live_vs_table/"; EC = "data/derived/edge_check/"
FIT = ["sep1819", "sep2021", "sep2223", "sep23day"]
REC = ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night", "gapA", "gapB"]
LATE = ["sep27pm", "sep27eve"]
def raw(w): return json.load(gzip.open((EC + "A/" if w.startswith("gap") else LV) + f"crowd_raw_{w}.json.gz", "rt"))
curves = {c["cv"]: c for c in json.load(gzip.open(EC + "G/curves.json.gz", "rt"))}
# tapes (own loader)
T = {}
for f in ("A/tapes.json.gz", "A/tapes_gapA.json.gz", "A/tapes_gapB.json.gz", "A/tapes_chk27.json.gz", "C/tapes_extra.json.gz"):
    for cv, L in json.load(gzip.open(EC + f, "rt")).items(): T.setdefault(cv.lower(), L)
for d in ("B/tapes/", "D/tapes/"):
    for f in os.listdir(EC + d):
        T.setdefault(f[:-5].lower(), json.load(open(EC + d + f)))
X0, Y0 = 1.68, 1e9
def tape_bundle(L, upto=None, engine_close=False):
    """e1_multi's bundle: creation-second buys after the first whose fee == tier (0.0008). upto: only blocks b0+off with off <= upto.
    engine_close: stop at the first creation-second buy after the first whose fee != tier (an outsider's taxed buy: closes the engine's bundle)"""
    ts = {int(k): v for k, v in L["ts"].items()}; T0 = L["T0"]; tier = L["tier"]; X, Y = X0, Y0; b = 0.0
    rows = sorted(L["rows"], key=lambda r: (r["bn"], r["li"]))
    for i, r in enumerate(rows):
        if ts.get(r["bn"], 9e18) != T0: break
        if r["k"] == "B":
            if 0 < r["tk"] < Y:
                net = X * r["tk"] / (Y - r["tk"]); fee = 1 - net / r["eth"] if r["eth"] > 0 else 1; X, Y = X + X * r["tk"] / (Y - r["tk"]), Y - r["tk"]
                if i > 0:
                    if abs(fee - tier) <= 0.0008:
                        if upto is None or r["bn"] - L["b0"] <= upto: b += r["eth"]
                    elif engine_close: break
        else: X, Y = X - X * r["tk"] / (Y + r["tk"]), Y + r["tk"]
    return b
late_b = {}
for w in LATE:
    for l in json.load(open(f"data/derived/e1_sep24/e1m_{w}.json"))["launches"]: late_b[l["cv"].lower()] = l["bundle_eth"]
HG = {}
for w in LATE:
    for x in json.load(open(LV + f"hold_grid_{w}.json")): HG[x["cv"].lower()] = x
seen = set(); P = []
for w in FIT + REC + LATE:
    for r in raw(w):
        if r["cv"] in seen: continue
        seen.add(r["cv"]); cv = r["cv"].lower()
        per = "fit" if w in FIT else ("late" if w in LATE else "rec")
        L = T.get(cv)
        b = tape_bundle(L) if (L and L.get("tier") is not None) else late_b.get(cv)
        c = curves.get(r["cv"])
        if c: ret = {11: c["r2"][11], 15: c["r2"][15], 300: c["r2"][300]}; g = c["g"]
        else:
            x = HG.get(cv); ret = {11: None, 15: x["behind1_15_h15"] if x else None, 300: x["behind1_15_h300"] if x else None}; g = 13 / 2570
        P.append({"cv": r["cv"], "T0": r["T0"], "k": r["k"], "per": per, "win": w, "raw": r,
                  "fe": fleets_k2(r, engine=True)[0] >= 2, "ft": at(cums(r)[1], r["k"] - 2) >= 2, "b": b, "ret": ret, "g": g, "named": set(x.lower() for x in r["named"])})
P.sort(key=lambda d: d["T0"])
print(f"population: fit {sum(d['per']=='fit' for d in P)}, rec {sum(d['per']=='rec' for d in P)}, late {sum(d['per']=='late' for d in P)}; bundle missing {sum(d['b'] is None for d in P)}")
miss = [d for d in P if d["per"] != "late" and d["ret"][11] is None]
print(f"fit/rec launches with no curves return (silently dropped by stats?): {len(miss)}")
print(f"late fires with no h15 price: {[d['cv'][:10] for d in P if d['per']=='late' and (d['fe'] or d['ft']) and d['ret'][15] is None]}")
def hours_union(iv):
    iv = sorted(iv); tot = 0; cur = None
    for a, b in iv:
        if cur is None or a > cur[1]:
            if cur: tot += cur[1] - cur[0]
            cur = [a, b]
        else: cur[1] = max(cur[1], b)
    return (tot + (cur[1] - cur[0] if cur else 0)) / 3600
E1M = {"sep24paper": "e1m_sep24"}
def bnd(w):
    if w.startswith("gap"): d = json.load(open(EC + f"A/launches_{w}.json"))
    else: d = json.load(open("data/derived/e1_sep24/" + E1M.get(w, "e1m_" + w) + ".json"))
    return d["t_lo"], d["t_hi"]
HR = {"fit": 96.0, "rec": hours_union([bnd(w) for w in REC]), "rec+late": hours_union([bnd(w) for w in REC + LATE])}
print(f"hours: rec {HR['rec']:.2f}, rec+late {HR['rec+late']:.2f}")
def S(fs, h, hrs):
    v = [d for d in fs if d["ret"][h] is not None]
    u = sum(d["ret"][h] * d["g"] * 2570 - 0.33 for d in v)
    return len(v), st.mean(d["ret"][h] for d in v), sum(d["ret"][h] > 0 for d in v) / len(v), sum(d["ret"][h] < -0.4 for d in v) / len(v), u, u / hrs * 24
def fires(pop, per): k = "fe" if pop == "engine" else "ft"; ps = {"fit": ("fit",), "rec": ("rec",), "rec+late": ("rec", "late")}[per]; return [d for d in P if d[k] and d["per"] in ps]
print("\npop     h  period    filter   n   mean   win  dead   $total   $/day")
for pop in ("engine", "tables"):
    for h, per in ((11, "fit"), (11, "rec"), (15, "fit"), (15, "rec"), (15, "rec+late")):
        F = fires(pop, per)
        for name, keep in (("none", lambda d: True), ("cap3.0", lambda d: d["b"] <= 3.0)):
            n, m, wn, dd, u, day = S([d for d in F if keep(d)], h, HR[per])
            print(f"{pop:7s} {h:2d} {per:9s} {name:7s} {n:3d} {m:+6.1%} {wn:4.0%} {dd:4.0%} {u:+8.2f} {day:+7.2f}")
# the fit windows' 2-3 ETH engine fires at h11
f23 = [d for d in fires("engine", "fit") if 2.0 < d["b"] <= 3.0]
print(f"\nfit engine fires with bundle in (2,3]: {len(f23)} mean h11 {st.mean(d['ret'][11] for d in f23):+.1%}: " + ", ".join(f"{d['b']:.3f}:{d['ret'][11]:+.1%}" for d in f23))
f153 = [d for d in fires("engine", "fit") if 1.5 < d["b"] <= 3.0]
print(f"fit engine fires with bundle in (1.5,3]: {len(f153)} h11 " + ", ".join(f"{d['b']:.3f}:{d['ret'][11]:+.1%}" for d in sorted(f153, key=lambda d: -d['ret'][11])))
# all launches above 3 ETH
big = [d for d in P if d["b"] is not None and d["b"] > 3.0]
print(f"\nlaunches above 3 ETH: {len(big)}; h15 max {max(d['ret'][15] for d in big):+.1%}; flat h15==h300: {sum(abs(d['ret'][15]-d['ret'][300])<1e-9 for d in big)}")
# look-ahead: the cap on the k-2 view and on an engine-style closed bundle
print("\ncapped fires (either count) : whole-second bundle / by k-2 / engine-close (stop at first taxed outsider buy) / engine-close by k-2")
for d in P:
    if (d["fe"] or d["ft"]) and d["b"] > 3.0:
        L = T.get(d["cv"].lower())
        if not L: print(f"  {d['cv'][:10]} {d['per']:4s} k {d['k']} bundle {d['b']:.3f}  NO TAPE"); continue
        print(f"  {d['cv'][:10]} {d['per']:4s} k {d['k']} bundle {d['b']:.3f} / k-2 {tape_bundle(L, d['k']-2):.3f} / eclose {tape_bundle(L, None, True):.3f} / eclose k-2 {tape_bundle(L, d['k']-2, True):.3f}")
chg = [d for d in P if (d["fe"] or d["ft"]) and T.get(d["cv"].lower()) and ((d["b"] > 3.0) != (tape_bundle(T[d["cv"].lower()], d["k"] - 2) > 3.0))]
print(f"fires whose cap-3.0 decision changes on the k-2 view: {len(chg)}")
chg2 = [d for d in P if (d["fe"] or d["ft"]) and T.get(d["cv"].lower()) and ((d["b"] > 3.0) != (tape_bundle(T[d["cv"].lower()], d["k"] - 2, True) > 3.0))]
print(f"fires whose cap-3.0 decision changes on the engine-close k-2 view: {len(chg2)} {[x['cv'][:10] for x in chg2]}")
# ---- causal template: brute force rebuild from scratch for every launch ----
def build(launches, share=3):
    comps = []
    for d in launches:
        hit = [c for c in comps if len(d["named"] & c[0]) >= share]
        w = set(d["named"]); n = 1
        for c in hit: w |= c[0]; n += c[1]; comps.remove(c)
        comps.append([w, n])
    return comps
bf = {}
for i, d in enumerate(P):
    prior = [x for x in P if x["T0"] < d["T0"]]
    comps = build(prior)
    bf[d["cv"]] = any(n >= 5 and len(d["named"] & w) >= 3 for w, n in comps)
sys.path.insert(0, EC + "I"); import importlib; cI = importlib.import_module("common")
fl, _ = cI.template_flags(cI.load())
dis = [cv for cv in bf if bf[cv] != fl[cv]]
print(f"\ncausal template: brute-force rebuild (only strictly earlier launches) vs I's incremental flags: {len(dis)} disagreements of {len(bf)}; flagged {sum(bf.values())}")
# any flagged launch whose matched template contains a launch at/after its own T0? (by construction of 'prior' no)
# ---- null test re-run with other seeds and 20,000 draws ----
def null(pop, h, rp, keep, N=20000, seed=0):
    Ff = fires(pop, "fit"); Fr = [d for d in fires(pop, rp) if d["ret"][h] is not None or d["ret"][15] is not None]
    def u(d): r = d["ret"][h] if d["ret"][h] is not None else None; return None if r is None else r * d["g"] * 2570 - 0.33
    Ff = [d for d in Ff if u(d) is not None]; Fr = [d for d in Fr if u(d) is not None]
    kf = [d for d in Ff if keep(d)]; kr = [d for d in Fr if keep(d)]; mf, mr = len(Ff) - len(kf), len(Fr) - len(kr)
    of, orr = sum(map(u, kf)), sum(map(u, kr)); uf = [u(d) for d in Ff]; ur = [u(d) for d in Fr]; tf, tr = sum(uf), sum(ur)
    rng = random.Random(seed); a = b = c = 0
    for _ in range(N):
        A = (tf - sum(rng.sample(uf, mf))) >= of - 1e-9; B = (tr - sum(rng.sample(ur, mr)) if mr else tr) >= orr - 1e-9
        a += A; b += B; c += A and B
    return mf, mr, a / N, b / N, c / N
print("\nnull, cap 3.0, 20,000 draws, seeds 0/1/2 (p_fit, p_rec, p_both):")
for pop, h, rp in (("engine", 11, "rec"), ("engine", 15, "rec"), ("engine", 15, "rec+late"), ("tables", 11, "rec"), ("tables", 15, "rec"), ("tables", 15, "rec+late")):
    res = [null(pop, h, rp, lambda d: d["b"] <= 3.0, seed=s) for s in (0, 1, 2)]
    print(f"  {pop:7s} h{h} {rp:9s} drop {res[0][0]}/{res[0][1]}: " + "  ".join(f"({x[2]:.4f}, {x[3]:.3f}, {x[4]:.4f})" for x in res))
