"""q3.py (reviewer D), brief question 3: rules that name no fleet. Families, all tradable at the time they act:
  pre-tick (at block k-2, the rule's view): wallets, shots, direct senders, relays, ETH shot (D/shots.json.gz, if pulled)
  creator history (causal: only launches earlier in time): the creator or a named wallet seen before; the template's past
     outcome (its earlier launches' 300-block return, known 30 s after each) ; skip when bad
  the bundle's own behaviour after entry: sell LAT blocks after the bundle's cumulative sold share crosses x, else at H
  the crowd after the seat as a hold rule (the discovery made tradable): at E1+15 keep to H only if the outsiders' distinct
     wallets (or ETH) in E1+1..E1+15 reach m, else sell at 15
Protocol (24.34): fit on the four fit windows, read on the recent 11; and the reverse. A variant PASSES when on the fit it beats
the baseline's $/day, is positive on each fit window, keeps win within 10 and dead within 5 points of the baseline, fires >= 30,
and on the recent set matches or beats the baseline's $/day. Null: the feature permuted across launches (within each period),
the same count of passes, 200 permutations; and the fit-selected variant's recent gain against the permuted ones.
    python3 data/derived/edge_check/D/q3.py [baseline_hold=300] > data/derived/edge_check/D/q3_h300.txt"""
import sys, os, json, gzip, random, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kit as K, common as c
BH = int(sys.argv[1]) if len(sys.argv) > 1 else 300; LAT = 3; NPERM = 200; random.seed(7)
FE = sorted(K.FE, key=lambda f: f["T0"])
# --- ETH shot by k-2 (direct and relay shots aimed at the curve, the engine's exclusions), if the pull exists
SH = {}
if os.path.exists(c.DD + "shots.json.gz"):
    raw = {r["cv"]: r for r in c.all_records()}
    for s in json.load(gzip.open(c.DD + "shots.json.gz", "rt")):
        r = raw[s["cv"]]; k = r["k"]; eth = 0.0; eth_d = 0.0; n = 0
        excl = set()
        for off in range(0, max(0, k - 1)):
            cr = r["blocks"][off]; idx = {(t["fr"], t["ix"]): t for t in cr}
            for t in s["blocks"][off]:
                x = idx.get((t["fr"], t["ix"]))
                if x is None or x["to"] in c.US or x["to_token"] or x["fr"] in c.US: continue
                if x["direct"] and x["named_fr"]: continue
                if not x["direct"] and x["named_data"]: continue
                eth += t["value"]; n += 1
                if x["direct"]: eth_d += t["value"]
        SH[s["cv"]] = (eth, eth_d)
for f in FE: f["eth_k2"], f["ethd_k2"] = SH.get(f["cv"], (None, None))
# --- creator history, causal
seen_ids = set(); comp = {}; comp_hist = collections.defaultdict(list)
def root(x):
    while comp.get(x, x) != x: x = comp[x]
    return x
for f in FE:
    ids = ["c:" + f["creator"]] + ["n:" + w for w in f["named"]]
    f["seen_before"] = any(x in seen_ids for x in ids)
    rs = {root(x) for x in ids if x in comp}
    hist = [h for rr in rs for h in comp_hist[rr] if h[0] < f["T0"] - 60]          # earlier launches of the template, outcome known
    f["tmpl_n"] = len(hist); f["tmpl_mean"] = c.mean([h[1] for h in hist]) if hist else None
    f["tmpl_last"] = sorted(hist)[-1][1] if hist else None
    for x in ids: comp.setdefault(x, x)
    r0 = root(ids[0])
    for x in ids[1:]:
        rx = root(x)
        if rx != r0: comp[rx] = r0; comp_hist[r0] += comp_hist.pop(rx, [])
    comp_hist[r0].append((f["T0"], f["path"][300])); seen_ids |= set(ids)
def bsell_exit(f, x, H):
    for d, sh in f["bsell"]:
        if sh >= x and sh > 0: return min(H, max(0, d) + LAT)
    return H
FAM = collections.OrderedDict()
FAM["wallets>=t @k-2 (gate)"] = [(f"wallets>={t}", (lambda t: lambda f: BH if f["k2"]["w"] >= t else None)(t)) for t in (1, 2, 3, 4, 6, 10)]
FAM["shots>=t @k-2 (gate)"] = [(f"shots>={t}", (lambda t: lambda f: BH if f["k2"]["s"] >= t else None)(t)) for t in (1, 2, 3, 5, 10, 20)]
FAM["direct senders>=t @k-2 (gate)"] = [(f"direct>={t}", (lambda t: lambda f: BH if f["k2"]["d"] >= t else None)(t)) for t in (1, 2, 3)]
FAM["relays>=t @k-2 (gate)"] = [(f"relays>={t}", (lambda t: lambda f: BH if f["k2"]["r"] >= t else None)(t)) for t in (1, 2, 3)]
if SH:
    FAM["ETH shot>=e @k-2 (gate)"] = [(f"eth>={e}", (lambda e: lambda f: BH if (f["eth_k2"] or 0) >= e else None)(e)) for e in (0.01, 0.05, 0.1, 0.3, 1.0)]
    FAM["rule & ETH shot>=e"] = [(f"rule&eth>={e}", (lambda e: lambda f: BH if f["fire"] and (f["eth_k2"] or 0) >= e else None)(e)) for e in (0.01, 0.05, 0.1, 0.3, 1.0)]
FAM["rule & skip seen-before creator/named"] = [("rule&new-operator", lambda f: BH if f["fire"] and not f["seen_before"] else None)]
FAM["rule & skip template with past mean < m"] = [(f"rule&tmpl_mean>={m}", (lambda m: lambda f: BH if f["fire"] and (f["tmpl_mean"] is None or f["tmpl_mean"] >= m) else None)(m)) for m in (-0.2, -0.1, 0.0, 0.1)]
FAM["rule & skip template >= n past launches"] = [(f"rule&tmpl_n<{n}", (lambda n: lambda f: BH if f["fire"] and f["tmpl_n"] < n else None)(n)) for n in (1, 2, 3, 5)]
FAM["rule, sell LAT after bundle sold >= x"] = [(f"bundle-exit x>={x} H{H}", (lambda x, H: lambda f: bsell_exit(f, x, H) if f["fire"] else None)(x, H)) for x in (1e-9, 0.05, 0.1, 0.25, 0.5) for H in (150, 300, 600)]
FAM["rule, hold to H if outsider wallets(+1..15)>=m else 15"] = [(f"crowd-hold ow15>={m} H{H}", (lambda m, H: lambda f: (H if f["ow15"] >= m else 15) if f["fire"] else None)(m, H)) for m in (1, 2, 3, 4, 6, 8) for H in (60, 150, 300)]
FAM["rule, hold to H if outsider ETH(+1..15)>=e else 15"] = [(f"crowd-hold oeth15>={e} H{H}", (lambda e, H: lambda f: (H if f["oeth15"] >= e else 15) if f["fire"] else None)(e, H)) for e in (0.05, 0.1, 0.2, 0.5) for H in (150, 300)]
FEAT_OF = {"wallets": ("k2", "w"), "shots": ("k2", "s"), "direct": ("k2", "d"), "relays": ("k2", "r")}
base = K.evaluate(lambda f: BH if f["fire"] else None)
def passes(res, base, fit_first=True):
    a, b = (res["fit"], res["recent"]) if fit_first else (res["recent"], res["fit"])
    A, B = (base["fit"], base["recent"]) if fit_first else (base["recent"], base["fit"])
    ok = a[4] > A[4] and a[0] >= (30 if fit_first else 8) and a[2] >= A[2] - 0.10 and a[3] <= A[3] + 0.05 and b[4] >= B[4]
    if fit_first: ok = ok and all(v > 0 for v in res["wins"].values())
    return ok
PERM_KEYS = ["k2", "eth_k2", "ethd_k2", "seen_before", "tmpl_n", "tmpl_mean", "tmpl_last", "bsell", "ow15", "oeth15"]
def permuted(seed):
    """a copy of the launches with every tested feature shuffled across launches within each period (the rule's fire flag, the
    price path and the window stay with the launch); exit features are shuffled among the rule's fires only"""
    rnd = random.Random(seed); out = []
    for g in ("fit", "recent"):
        S = [dict(f) for f in FE if f["grp"] == g]
        for key in PERM_KEYS:
            pool = S if key in ("k2", "eth_k2", "ethd_k2", "seen_before", "tmpl_n", "tmpl_mean", "tmpl_last") else [f for f in S if f["fire"]]
            vals = [f[key] for f in pool]; rnd.shuffle(vals)
            for f, v in zip(pool, vals): f[key] = v
        out += S
    return out
def with_set(S, fn):
    K.FIT[:] = [f for f in S if f["grp"] == "fit"]; K.REC[:] = [f for f in S if f["grp"] == "recent"]; return fn()
ORIG = list(FE)
print(f"baseline: the rule, hold {BH}")
print(K.line(f"baseline h{BH}", base)); print()
summary = []
for fam, variants in FAM.items():
    print(f"== {fam}")
    real = with_set(ORIG, lambda: [(n, K.evaluate(p)) for n, p in variants])
    for n, res in real: print(K.line(n, res), " PASS" if passes(res, base) else "", " PASS-rev" if passes(res, base, False) else "")
    npass = sum(passes(res, base) for _, res in real); npass_rev = sum(passes(res, base, False) for _, res in real)
    # fit-selected variant (best fit $/day among those positive on every fit window with >= 30 fires), its recent reading
    def pick(rs):
        ok = [(res["fit"][4], n, res) for n, res in rs if res["fit"][0] >= 30 and all(v > 0 for v in res["wins"].values())]
        return max(ok, key=lambda x: x[0]) if ok else None
    sel = pick(real); gain_real = (sel[2]["recent"][4] - base["recent"][4]) if sel else None
    null_pass = []; null_gain = []
    for s in range(NPERM):
        P = permuted(1000 + s)
        rs = with_set(P, lambda: [(n, K.evaluate(p)) for n, p in variants])
        null_pass.append(sum(passes(res, base) for _, res in rs)); sp = pick(rs)
        null_gain.append((sp[2]["recent"][4] - base["recent"][4]) if sp else -1e9)
    with_set(ORIG, lambda: None)
    pnull = sum(g >= gain_real for g in null_gain) / NPERM if gain_real is not None else float("nan")
    print(f"   passes {npass}/{len(variants)} (reverse {npass_rev}); permuted feature: mean passes {sum(null_pass)/NPERM:.2f}/{len(variants)}, share of permutations with >= {npass} passes {sum(x >= npass for x in null_pass)/NPERM:.2f}")
    if sel: print(f"   fit-selected: {sel[1]} -> recent ${sel[2]['recent'][4]:+.1f}/d (baseline ${base['recent'][4]:+.1f}); gain {gain_real:+.1f}; permuted gains >= this: {pnull:.2f}")
    print(); summary.append((fam, npass, len(variants), sum(null_pass) / NPERM, sel[1] if sel else None, gain_real, pnull))
print("summary: family | passes | permuted mean passes | fit-selected -> recent gain over baseline $/day | p (permuted gain >= real)")
for s in summary: print(f"  {s[0]:52s} {s[1]}/{s[2]}  null {s[3]:.2f}  {s[4]}  {s[5] if s[5] is None else round(s[5],1)}  p {s[6]:.2f}")
