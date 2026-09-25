"""a_common.py (searcher A): load every window, count fleets EXACTLY as src/analysis/crowd_rules.py cums() does (the file's
text before "rules = [" is exec'd, the pattern of src/analysis/predict_window.py line 9), join returns by cv, and build the
pre-tick features at the executable view (block k-2). Read-only on the repo.

Usage: imported by a_baseline.py / a_search.py.  REPO env var overrides the repo path (default /home/user/fomo-memebot)."""
import json, gzip, os, sys, math, statistics as st, collections

REPO = os.environ.get("REPO", "/home/user/fomo-memebot")
D = os.path.join(REPO, "data/derived/live_vs_table/")
STAKE, GAS = 13.0, 0.33

# ---- crowd_rules.py's own cums()/view()/at(), exec'd from the file text before "rules = [" (runs from the repo root because
# that prefix also loads the four fit windows with relative paths; we keep its `data` to cross-check our join).
_argv, _cwd = sys.argv, os.getcwd()
sys.argv = ["x", "0.76", "0.71"]; os.chdir(REPO)
CR = {}
exec(open(os.path.join(REPO, "src/analysis/crowd_rules.py")).read().split("rules = [")[0], CR)
sys.argv = _argv; os.chdir(_cwd)
cums, view, at, US = CR["cums"], CR["view"], CR["at"], CR["US"]

# ---- windows: (name, set, crowd_raw file(s), hold_grid file, launches file, hours)
FIT = [("sep1819", "crowd_raw_sep1819.json.gz", "hold_grid.json", "launches_141_creators.json", 23.1),
       ("sep2021", "crowd_raw_sep2021.json.gz", "hold_grid_oos_sep2021.json", "launches_oos_sep2021.json", 34.8),
       ("sep2223", "crowd_raw_sep2223.json.gz", "hold_grid.json", "launches_175_sep2223.json", 29.3),
       ("sep23day", "crowd_raw_sep23day.json.gz", "hold_grid_today_sep23.json", "launches_today_sep23.json", 8.8)]
VAL = [("sep24paper", "crowd_raw_sep24paper.json.gz", "hold_grid_sep24paper.json", "launches_sep24_paper.json", 9.0),
       ("sep25night", "crowd_raw_sep25night.json.gz", "hold_grid_sep25night.json", "launches_sep25night.json", 9.0),
       ("sep25am", "crowd_raw_sep25am.json.gz", "hold_grid_sep25am.json", "launches_sep25am.json", 6.6),
       ("sep25pm", "crowd_raw_sep25pm.json.gz", "hold_grid_sep25pm.json", "launches_sep25pm.json", 6.6),
       ("sep25eve2", "crowd_raw_sep25eve2.json.gz", "hold_grid_sep25eve2.json", "launches_sep25eve2.json", 2.75)]
# the brief: crowd_raw_sep25eve is a subset of eve2 plus 0xf45fa520, which the builder dropped from eve2: include it in eve2
EXTRA = {"sep25eve2": ("crowd_raw_sep25eve.json.gz", "hold_grid_sep25eve.json", "launches_sep25eve.json", {"0xf45fa520"})}
HOURS = {w[0]: w[4] for w in FIT + VAL}
FIT_NAMES = [w[0] for w in FIT]; VAL_NAMES = [w[0] for w in VAL]

RET_KEYS = [f"{p}_{s}_{h}" for p in ("first", "behind1") for s in (15, 100)
            for h in ("h15", "h30", "h60", "h150", "h300", "h600", "tp50_h600", "stop20_h600", "tp50_stop20_h600")]

def _load(f):
    p = D + f
    return json.load(gzip.open(p, "rt")) if p.endswith(".gz") else json.load(open(p))

def _nan(x): return x is None or (isinstance(x, float) and math.isnan(x))

def crowd_features(r, j):
    """features from blocks[0..j] only (j = the view's last block offset; j < 0 -> nothing seen), same exclusions as cums()"""
    fleets, wallets, direct_f, relay_f = set(), set(), set(), set(); shots = collections.Counter(); first_blk = {}
    for off, rows in enumerate(r["blocks"][: max(0, j + 1)] if j >= 0 else []):
        for t in rows:
            if t["to"] in US or t["to_token"] or t["fr"] in US: continue
            if t["direct"]:
                if not t["named_fr"]:
                    fleets.add(t["fr"]); wallets.add(t["fr"]); direct_f.add(t["fr"]); shots[t["fr"]] += 1; first_blk.setdefault(t["fr"], off)
            elif not t["named_data"]:
                fleets.add(t["to"]); relay_f.add(t["to"]); shots[t["to"]] += 1; first_blk.setdefault(t["to"], off)
                if not t["named_fr"]: wallets.add(t["fr"])
    nf, nw = len(fleets), len(wallets); ns = sum(shots.values())
    return {"nf": nf, "nw": nw, "n_direct": len(direct_f), "n_relay": len(relay_f), "shots": ns,
            "shots_per_fleet": ns / nf if nf else 0.0, "wallets_per_fleet": nw / nf if nf else 0.0,
            "max_fleet_shots": max(shots.values()) if shots else 0,
            "blocks_active": len({b for b in first_blk.values()})}

def load_all(verbose=False):
    """one row per launch with a behind1_15_h300 value: window, set, cv, T0, k, cf/cw (cums), returns, launch and crowd features"""
    out = []
    for group, W in (("fit", FIT), ("val", VAL)):
        for name, rf, hf, lf, hours in W:
            srcs = [(rf, hf, lf, None)]
            if name in EXTRA: srcs.append(EXTRA[name])
            seen = set()
            for rf_, hf_, lf_, only in srcs:
                R = _load(rf_); H = {h["cv"]: h for h in _load(hf_)}; L = {l["cv"].lower(): l for l in _load(lf_)}
                for r in R:
                    if only is not None and r["cv"][:10] not in only: continue
                    if r["cv"] in seen: continue
                    h = H.get(r["cv"]); x = h.get("behind1_15_h300") if h else None
                    if _nan(x): continue
                    seen.add(r["cv"])
                    cw, cf = cums(r); k = r["k"]; la = L.get(r["cv"].lower(), {})
                    row = {"win": name, "set": group, "cv": r["cv"], "T0": r["T0"], "k": k, "cf": cf, "cw": cw,
                           "creator": (r.get("creator") or la.get("creator") or "").lower(),
                           "bundle_eth": la.get("bundle_eth"), "named": len(la.get("named") or r.get("named") or []),
                           "tier": la.get("tier"), "hour": la.get("hour"), "has_launch": bool(la)}
                    for key in RET_KEYS: row[key] = h.get(key)
                    row["ret"] = x
                    for tag, j in (("k2", k - 2), ("k3", k - 3), ("k1", k - 1)):
                        fe = crowd_features(r, j)
                        assert fe["nf"] == at(cf, j) and fe["nw"] == at(cw, j), (r["cv"], tag)   # identical to cums()
                        for a, b in fe.items(): row[f"{a}_{tag}"] = b
                    # the block offset where the fleet count first reached n (distance from the end of the second), seen by k-2
                    for n in (1, 2):
                        jf = next((i for i, a in enumerate(cf) if a >= n), None)
                        row[f"arr{n}_d"] = (k - jf) if (jf is not None and jf <= k - 2) else None   # None: not reached by k-2
                    out.append(row)
    # creator repeat inside the scored population (approximation of the engine's 'second launch of the day', which counts every
    # factory launch of the creator that UTC day, not only the qualifying ones)
    byc = collections.defaultdict(list)
    for r in sorted(out, key=lambda r: r["T0"]):
        day = r["T0"] // 86400; r["creator_repeat"] = int(any(d == day for d in byc[r["creator"]])); byc[r["creator"]].append(day)
    if verbose:
        for w in FIT_NAMES + VAL_NAMES: print(w, sum(r["win"] == w for r in out), "launches scored")
    return out

def crosscheck_crowd_rules(rows):
    """our fit rows against crowd_rules.py's own `data` (same cv set, same ret, same f_k2)"""
    ours = {(r["cv"], r["win"]): r for r in rows if r["set"] == "fit"}
    names = dict(zip(["Sep 18-19", "Sep 20-21", "Sep 22-23", "Sep 23 day"], FIT_NAMES)); n = bad = 0
    for nm, hours, crs in CR["data"]:
        for c in crs:
            o = ours.get((c["cv"], names[nm])); n += 1
            if o is None or o["ret"] != c["ret"] or at(o["cf"], o["k"] - 2) != c["f_k2"] or o["cf"] != c["cf"]: bad += 1
    return n, bad

# ---- metrics
def stats(xs, hours, stake=STAKE, gas=GAS, scale=1.0):
    """xs: returns (fraction) of the fires; dollars = x*stake - gas"""
    n = len(xs)
    if n == 0: return {"n": 0, "per_day": 0.0, "mean": None, "median": None, "win": None, "dead": None, "usd_burst": None, "usd_day": 0.0, "usd": 0.0}
    usd = [x * stake - gas for x in xs]
    return {"n": n, "per_day": n / hours * 24, "mean": st.mean(xs), "median": st.median(xs), "win": sum(x > 0 for x in xs) / n,
            "dead": sum(x < -0.4 for x in xs) / n, "usd_burst": st.mean(usd), "usd_day": sum(usd) / hours * 24, "usd": sum(usd),
            "se": (st.stdev(xs) / math.sqrt(n)) if n > 1 else None}

def evaluate(rows, fire, retf=lambda r: r["ret"], stake=STAKE, gas=GAS):
    """per window, pooled fit, pooled val. fire(r) -> bool; retf(r) -> return of a fire (None = cannot be scored, skipped)"""
    res = {}
    for w in FIT_NAMES + VAL_NAMES:
        xs = [retf(r) for r in rows if r["win"] == w and fire(r)]; xs = [x for x in xs if not _nan(x)]
        res[w] = stats(xs, HOURS[w], stake, gas)
    for grp, names in (("fit", FIT_NAMES), ("val", VAL_NAMES)):
        xs = [retf(r) for r in rows if r["win"] in names and fire(r)]; xs = [x for x in xs if not _nan(x)]
        res[grp] = stats(xs, sum(HOURS[w] for w in names), stake, gas)
    return res

def fmt(s):
    if s["n"] == 0: return f"{0:3d} {0:5.1f}/d        -        -     -     -        -        $+0/d"
    return (f"{s['n']:3d} {s['per_day']:5.1f}/d {s['mean']:+7.1%} {s['median']:+7.1%} {s['win']:4.0%} {s['dead']:4.0%} "
            f"${s['usd_burst']:+6.2f} ${s['usd_day']:+5.0f}/d")

HDR = f"{'window':11s} {'n':>3s} {'fires/d':>7s} {'mean':>7s} {'median':>7s} {'win':>4s} {'dead':>4s} {'$/burst':>7s} {'$/day':>8s}"

def table(label, res, out=print):
    out(f"--- {label}")
    out(HDR)
    for w in FIT_NAMES: out(f"{w:11s} {fmt(res[w])}")
    out(f"{'FIT pooled':11s} {fmt(res['fit'])}   ($ total {res['fit']['usd']:+.2f}, 96.0 h)")
    for w in VAL_NAMES: out(f"{w:11s} {fmt(res[w])}")
    out(f"{'VAL pooled':11s} {fmt(res['val'])}   ($ total {res['val']['usd']:+.2f}, 33.95 h)")
