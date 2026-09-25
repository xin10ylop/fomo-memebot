"""common.py (searcher B): data loading, the engine's fleet count (crowd_rules.py cums/view/at, exec'd verbatim), pre-tick
features at the executable view, and the protocol's metrics. Run everything from the repo root:
    cd /home/user/fomo-memebot && python3 <B>/baseline.py
Read-only on the repo. No randomness anywhere."""
import json, gzip, os, sys, math, statistics as st, time, collections

REPO = "/home/user/fomo-memebot"
os.chdir(REPO)
D = "data/derived/live_vs_table/"

# --- the reference counting code: crowd_rules.py up to "rules = [" (the same pattern as src/analysis/predict_window.py line 9).
#     It defines US, STAKE, GAS, cums(), view(), at(); it also loads the four fit windows into `data` as a side effect (unused here).
_saved = list(sys.argv); sys.argv = ["x", "0.76", "0.71"]
_ns = {}
exec(open(os.path.join(REPO, "src/analysis/crowd_rules.py")).read().split("rules = [")[0], _ns)
sys.argv = _saved
cums, view, at, US, STAKE, GAS = _ns["cums"], _ns["view"], _ns["at"], _ns["US"], _ns["STAKE"], _ns["GAS"]
assert STAKE == 13.0 and GAS == 0.33

# --- windows (BRIEF.md "Data"): name, crowd_raw, hold_grid, launches, hours
FIT = [("sep1819", "crowd_raw_sep1819.json.gz", "hold_grid.json", "launches_141_creators.json", 23.1),
       ("sep2021", "crowd_raw_sep2021.json.gz", "hold_grid_oos_sep2021.json", "launches_oos_sep2021.json", 34.8),
       ("sep2223", "crowd_raw_sep2223.json.gz", "hold_grid.json", "launches_175_sep2223.json", 29.3),
       ("sep23day", "crowd_raw_sep23day.json.gz", "hold_grid_today_sep23.json", "launches_today_sep23.json", 8.8)]
VAL = [("sep24paper", "crowd_raw_sep24paper.json.gz", "hold_grid_sep24paper.json", "launches_sep24_paper.json", 9.0),
       ("sep25night", "crowd_raw_sep25night.json.gz", "hold_grid_sep25night.json", "launches_sep25night.json", 9.0),
       ("sep25am", "crowd_raw_sep25am.json.gz", "hold_grid_sep25am.json", "launches_sep25am.json", 6.6),
       ("sep25pm", "crowd_raw_sep25pm.json.gz", "hold_grid_sep25pm.json", "launches_sep25pm.json", 6.6),
       ("sep25eve2", "crowd_raw_sep25eve2.json.gz", "hold_grid_sep25eve2.json", "launches_sep25eve2.json", 2.75)]
EVE_EXTRA = ("crowd_raw_sep25eve.json.gz", "hold_grid_sep25eve.json", "launches_sep25eve.json")   # 0xf45fa520, dropped from eve2 (BRIEF)
RET_KEYS = [f"behind1_15_h{h}" for h in (15, 30, 60, 150, 300, 600)] + ["behind1_15_tp50_h600", "behind1_15_stop20_h600", "behind1_15_tp50_stop20_h600"] \
         + [f"behind1_100_h{h}" for h in (15, 30, 60, 150, 300, 600)] + ["behind1_100_tp50_h600", "behind1_100_stop20_h600", "behind1_100_tp50_stop20_h600"]

def _load(f):
    return json.load(gzip.open(D + f, "rt")) if f.endswith(".gz") else json.load(open(D + f))

def per_block(r):
    """per block offset 0..k (and k+1 = the seat block, never used for a gate): cumulative counts under cums()' exact exclusions,
    plus the shape of the crowd (shots, direct vs relay fleets, wallets per fleet). Identical fleet/wallet sets to cums()."""
    wallets, fleets = set(), set(); direct_f, relay_f = set(), set(); shots = 0; fleet_w = collections.defaultdict(set); fleet_shots = collections.Counter()
    out = []
    for off, rows in enumerate(r["blocks"][: r["k"] + 1]):
        for t in rows:
            if t["to"] in US or t["to_token"] or t["fr"] in US: continue
            if t["direct"]:
                if not t["named_fr"]:
                    fleets.add(t["fr"]); wallets.add(t["fr"]); direct_f.add(t["fr"]); shots += 1; fleet_w[t["fr"]].add(t["fr"]); fleet_shots[t["fr"]] += 1
            elif not t["named_data"]:
                fleets.add(t["to"]); relay_f.add(t["to"]); shots += 1; fleet_shots[t["to"]] += 1
                if not t["named_fr"]: wallets.add(t["fr"]); fleet_w[t["to"]].add(t["fr"])
        out.append({"f": len(fleets), "w": len(wallets), "shots": shots, "fd": len(direct_f), "fr": len(relay_f),
                    "maxw": max((len(v) for v in fleet_w.values()), default=0), "maxshots": max(fleet_shots.values(), default=0)})
    return out

def build_rows(raw_f, hg_f, la_f, only_cv=None):
    R = _load(raw_f); H = {h["cv"]: h for h in _load(hg_f)}; L = {l["cv"].lower(): l for l in _load(la_f)}
    rows = []
    for r in R:
        if only_cv and not r["cv"].startswith(only_cv): continue
        h = H.get(r["cv"]); x = h.get("behind1_15_h300") if h else None
        if x is None or (isinstance(x, float) and math.isnan(x)): continue       # the brief: skip launches without behind1_15_h300
        cw, cf = cums(r); k = r["k"]; pb = per_block(r)
        assert [p["f"] for p in pb] == cf and [p["w"] for p in pb] == cw
        la = L.get(r["cv"].lower(), {})
        g = lambda j, key: pb[j][key] if 0 <= j <= k else 0
        first = lambda n: next((j for j, a in enumerate(cf) if a >= n), None)
        row = {"cv": r["cv"], "b0": r["b0"], "T0": r["T0"], "k": k, "cf": cf, "cw": cw, "creator": (r.get("creator") or la.get("creator") or "").lower(),
               "hour": la.get("hour", time.gmtime(r["T0"]).tm_hour), "tier": la.get("tier"), "bundle_eth": la.get("bundle_eth"), "named": len(la["named"]) if "named" in la else None,
               "ret": {kk: h.get(kk) for kk in RET_KEYS}}
        for tag, j in (("k3", k - 3), ("k2", k - 2), ("k1", k - 1)):
            row["f_" + tag] = at(cf, j); row["w_" + tag] = at(cw, j)
            for key in ("shots", "fd", "fr", "maxw", "maxshots"): row[key + "_" + tag] = g(j, key)
        f1, f2 = first(1), first(2)
        row["arr1"] = (k - f1) if f1 is not None else None      # blocks before the end of the second at which the 1st / 2nd fleet showed
        row["arr2"] = (k - f2) if f2 is not None else None
        rows.append(row)
    return rows

def load(which="all"):
    out = collections.OrderedDict()
    for name, rf, hf, lf, hrs in (FIT if which in ("all", "fit") else []) + (VAL if which in ("all", "val") else []):
        rows = build_rows(rf, hf, lf)
        if name == "sep25eve2":
            have = {r["cv"] for r in rows}
            extra = [r for r in build_rows(*EVE_EXTRA) if r["cv"] not in have]
            # crowd_raw_sep25eve has TWO launches absent from eve2: 0xf45fa520 (20:07, the builder's drop; the brief says include it)
            # and 0x5ff7b2f8 (19:28, before eve2's 19:30 start; not named by the brief). Default: the brief's one; EVE_5FF=1 adds the other.
            keep = ("0xf45fa520", "0x5ff7b2f8") if os.environ.get("EVE_5FF") == "1" else ("0xf45fa520",)
            assert sorted(r["cv"][:10] for r in extra) == ["0x5ff7b2f8", "0xf45fa520"], [r["cv"][:10] for r in extra]
            rows += [r for r in extra if r["cv"][:10] in keep]
        rows.sort(key=lambda r: r["T0"])
        # creator's earlier qualifying launch the same UTC day inside the window (approximation of the engine's creator-repeat skip)
        seen = {}
        for r in rows:
            day = time.strftime("%Y%m%d", time.gmtime(r["T0"])); key = (r["creator"], day)
            r["creator_repeat"] = key in seen and bool(r["creator"]); seen.setdefault(key, r["T0"])
        out[name] = {"rows": rows, "hours": hrs}
    return out

# --- metrics (the brief's table): fires, fires/day, mean, median, win %, dead % (< -40%), $/burst at $13 after $0.33 gas, $/day
def metrics(rets, hours, stake=STAKE, gas=GAS):
    n = len(rets)
    if n == 0: return {"n": 0, "per_day": 0.0, "mean": float("nan"), "median": float("nan"), "win": float("nan"), "dead": float("nan"), "usd_burst": float("nan"), "usd_day": 0.0, "usd_total": 0.0}
    usd = [x * stake - gas for x in rets]
    return {"n": n, "per_day": n / hours * 24, "mean": st.mean(rets), "median": st.median(rets), "win": sum(x > 0 for x in rets) / n,
            "dead": sum(x < -0.4 for x in rets) / n, "usd_burst": st.mean(usd), "usd_day": sum(usd) / hours * 24, "usd_total": sum(usd)}

def fmt(m, label=""):
    if m["n"] == 0: return f"{label:14s} fires   0"
    return (f"{label:14s} fires {m['n']:3d} {m['per_day']:5.1f}/d  mean {m['mean']:+7.1%}  med {m['median']:+7.1%}  win {m['win']:4.0%}  dead {m['dead']:4.0%}"
            f"  ${m['usd_burst']:+6.2f}/burst  ${m['usd_day']:+6.1f}/day  ${m['usd_total']:+7.1f} total")

def evaluate(W, names, rule, key="behind1_15_h300", stake=STAKE, stake_key_scale=None):
    """rule(row) -> bool; returns per-window metrics and pooled (hours summed) over `names`"""
    per = collections.OrderedDict(); pool = []; hrs = 0.0
    for n in names:
        rets = [r["ret"][key] for r in W[n]["rows"] if rule(r) and r["ret"].get(key) is not None and not (isinstance(r["ret"][key], float) and math.isnan(r["ret"][key]))]
        per[n] = metrics(rets, W[n]["hours"], stake=stake); pool += rets; hrs += W[n]["hours"]
    return per, metrics(pool, hrs, stake=stake)

FIT_NAMES = [w[0] for w in FIT]; VAL_NAMES = [w[0] for w in VAL]
BASE = lambda r: r["f_k2"] >= 2
