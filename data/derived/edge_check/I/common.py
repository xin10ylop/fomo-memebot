"""common.py (reviewer I): the population, the two fire counts, the returns, the two filters and the statistics used by every
reviewer-I script. Run from anywhere; it changes to the repository root. No RPC: every input is a file already in the repo.

Population: the crowd files of the fit (sep1819, sep2021, sep2223, sep23day: 563 launches) and the recent windows
(sep24paper .. sep27night, round 1 A's gapA and gapB, then sep27pm and sep27eve), de-duplicated by curve, first file wins
(the order FIT + REC + GAPS + LATE; FIT + REC + GAPS is edge_check/G's order, so every launch keeps G's window label).
Fires: tables = fleets >= 2 at block k-2 (crowd_rules.cums/at, as reach_table.py); engine = fleet_variants.fleets_k2(r,
engine=True) >= 2 (shots in blocks up to the first named buy's block dropped), the function exec'd from
src/analysis/fleet_variants.py so it is the file's own code.
Returns: edge_check/G/curves.json.gz r2[h] (second place in E1, $13 at 2570 $/ETH, exit h blocks after E1, model_eff).
sep27pm and sep27eve (24 launches) are not in curves.json.gz and no tape of them is in the repo: they are priced only at
h15 from live_vs_table/hold_grid_sep27{pm,eve}.json behind1_15_h15 (second place, $15, later buys folded by tokens;
check_late.py measures that column against r2[15] on the launches that have both) and have no h11.
Bundle: bundle_eth from the live_vs_table/launches_*.json and A/launches_gap*.json files (the e1m pull's own number:
creation-second buys after the first at fee == tier); bundle_check.py recomputes it from the tape rows as e1_multi does.
Hours: the union of each window's [min T0, max T0] span (the fit is 96.0 h)."""
import json, gzip, os, sys, math, time, collections, random, statistics as st
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
os.chdir(ROOT)
_argv = list(sys.argv); sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])                 # cums, at, US
sys.argv = _argv
_fv = open("src/analysis/fleet_variants.py").read()
exec(_fv[_fv.index("def fleets_k2"):_fv.index("seen = set(); pop =")])                   # fleets_k2(r, nohelper, engine)
LV = "data/derived/live_vs_table/"; EC = "data/derived/edge_check/"; I = EC + "I/"
FIT = ["sep1819", "sep2021", "sep2223", "sep23day"]
REC = ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night"]
GAPS = ["gapA", "gapB"]; LATE = ["sep27pm", "sep27eve"]
E = 2570.0; GAS = 0.33; STAKE = 13.0
CAPS = (1.0, 1.5, 2.0, 3.0)
def _raw(w): return json.load(gzip.open((EC + "A/" if w in GAPS else LV) + f"crowd_raw_{w}.json.gz", "rt"))
def _bundles():
    out = {}
    for f in sorted(os.listdir(LV)):
        if f.startswith("launches_") and f.endswith(".json"):
            d = json.load(open(LV + f)); d = d.get("launches", []) if isinstance(d, dict) else d
            for l in d:
                if isinstance(l, dict) and "cv" in l and "bundle_eth" in l: out.setdefault(l["cv"].lower(), l["bundle_eth"])
    for f in ("launches_gapA.json", "launches_gapB.json", "launches_chk27.json"):
        d = json.load(open(EC + "A/" + f)); d = d.get("launches", []) if isinstance(d, dict) else d
        for l in d:
            if isinstance(l, dict) and "cv" in l and "bundle_eth" in l: out.setdefault(l["cv"].lower(), l["bundle_eth"])
    return out
_POP = None
def load():
    """every launch once, T0 order, with: win, per (fit/rec/late), fire_t, fire_e, bundle, named (set), r (h -> return or None), g"""
    global _POP
    if _POP is not None: return _POP
    C = {c["cv"]: c for c in json.load(gzip.open(EC + "G/curves.json.gz", "rt"))}
    HG = {}
    for w in LATE:
        for x in json.load(open(LV + f"hold_grid_{w}.json")): HG[x["cv"].lower()] = x
    B = _bundles(); seen = set(); out = []
    for w in FIT + REC + GAPS + LATE:
        for r in _raw(w):
            if r["cv"] in seen: continue
            seen.add(r["cv"])
            cf = cums(r)[1]; c = C.get(r["cv"])
            d = {"cv": r["cv"], "T0": r["T0"], "k": r["k"], "win": w, "per": "fit" if w in FIT else ("late" if w in LATE else "rec"),
                 "fire_t": at(cf, r["k"] - 2) >= 2, "fire_e": fleets_k2(r, engine=True)[0] >= 2, "fk2_t": at(cf, r["k"] - 2),
                 "fk2_e": fleets_k2(r, engine=True)[0], "named": set(x.lower() for x in r["named"]), "bundle": B.get(r["cv"].lower())}
            if c is not None: d["r"] = {h: c["r2"][h] for h in (11, 15, 300)}; d["g"] = c["g"]; d["src"] = "curves"
            else:
                x = HG.get(r["cv"].lower()); d["r"] = {11: None, 15: x["behind1_15_h15"] if x else None, 300: x["behind1_15_h300"] if x else None}
                d["g"] = STAKE / E; d["src"] = "hold_grid"
            out.append(d)
    out.sort(key=lambda d: d["T0"]); _POP = out; return out
E1M = {"sep24paper": "e1m_sep24", "sep25night": "e1m_sep25night", "sep25am": "e1m_sep25am", "sep25pm": "e1m_sep25pm", "sep25eve": "e1m_sep25eve",
       "sep25eve2": "e1m_sep25eve2", "sep26night": "e1m_sep26night", "sep26am": "e1m_sep26am", "sep26pm": "e1m_sep26pm", "sep26restart": "e1m_sep26restart",
       "sep27night": "e1m_sep27night", "sep27pm": "e1m_sep27pm", "sep27eve": "e1m_sep27eve"}
def bounds(w):
    """the window's pulled time bounds [t_lo, t_hi] (the e1m pull, or A's gap pull)"""
    d = json.load(open(EC + f"A/launches_{w}.json")) if w in GAPS else json.load(open(f"data/derived/e1_sep24/{E1M[w]}.json"))
    return d["t_lo"], d["t_hi"]
def _union(iv):
    iv = sorted(iv); tot = 0; cur = None
    for a, b in iv:
        if cur is None or a > cur[1]: tot += (cur[1] - cur[0]) if cur else 0; cur = [a, b]
        else: cur[1] = max(cur[1], b)
    return (tot + ((cur[1] - cur[0]) if cur else 0)) / 3600.0
def hours_bounds(wins): return _union([bounds(w) for w in wins])
FIT_HOURS = 96.0                                      # the fit's canonical hours (reach_table.py SETS; = the T0-span union below)
def period_hours(per):
    """fit 96 h; recent: the union of the windows' pulled bounds (rec: 11 files + 2 gaps; late adds sep27pm, sep27eve)"""
    if per == "fit": return FIT_HOURS
    return hours_bounds(REC + GAPS + (LATE if per == "rec+late" else []))
def hours(pop):
    """distinct hours: the union of the windows' [min T0, max T0] spans (the launches' own T0s)"""
    sp = collections.defaultdict(list)
    for d in pop: sp[d["win"]].append(d["T0"])
    iv = sorted((min(v), max(v)) for v in sp.values()); tot = 0; cur = None
    for a, b in iv:
        if cur is None or a > cur[1]: tot += (cur[1] - cur[0]) if cur else 0; cur = [a, b]
        else: cur[1] = max(cur[1], b)
    tot += (cur[1] - cur[0]) if cur else 0
    return tot / 3600.0
# ---------------- the template filter (causal) ----------------
def template_flags(pop, share=3, min_n=5, link=None):
    """flag[cv] = True when the launch's named set shares >= share wallets with the wallet union of a template of >= min_n
    launches, the template built only from launches with a strictly earlier T0. A template grows by the same test: a launch
    joins (and merges) every template whose wallet union it shares >= link (default = share) wallets with."""
    link = share if link is None else link
    comps = []                                        # each: [set of wallets, n launches]
    flag = {}; info = {}; by_t = collections.defaultdict(list)
    for d in pop: by_t[d["T0"]].append(d)
    for t in sorted(by_t):
        grp = by_t[t]
        for d in grp:                                 # query against launches strictly before t
            best = max(((len(d["named"] & w), n) for w, n in comps if n >= min_n and len(d["named"] & w) >= share), default=None)
            flag[d["cv"]] = best is not None; info[d["cv"]] = best
        for d in grp:                                 # then add this second's launches
            hit = [c for c in comps if len(d["named"] & c[0]) >= link]
            if hit:
                w = set(d["named"]); n = 1
                for c in hit: w |= c[0]; n += c[1]; comps.remove(c)
                comps.append([w, n])
            else: comps.append([set(d["named"]), 1])
    return flag, info
# ---------------- statistics ----------------
def usd(d, h): return d["r"][h] * d["g"] * E - GAS
def stats(fs, h, hrs):
    v = [d["r"][h] for d in fs if d["r"][h] is not None]
    if not v: return {"n": 0, "mean": float("nan"), "med": float("nan"), "win": float("nan"), "dead": float("nan"), "usd": 0.0, "day": 0.0, "se": float("nan")}
    u = sum(usd(d, h) for d in fs if d["r"][h] is not None)
    return {"n": len(v), "mean": st.mean(v), "med": st.median(v), "win": sum(x > 0 for x in v) / len(v), "dead": sum(x < -0.4 for x in v) / len(v),
            "usd": u, "day": u / hrs * 24.0, "se": (st.stdev(v) / math.sqrt(len(v))) if len(v) > 1 else float("nan")}
def fmt(s):
    if not s["n"]: return f"{0:3d} fires"
    return f"{s['n']:3d} fires  mean {s['mean']:+6.1%}  med {s['med']:+6.1%}  win {s['win']:4.0%}  dead {s['dead']:3.0%}  ${s['usd']:+7.2f} total  ${s['day']:+6.2f}/day"
def hms(t): return time.strftime("%b %d %H:%M", time.gmtime(t))
# ---------------- the filters, the sets ----------------
_FLAG = None
def flags():
    global _FLAG
    if _FLAG is None: _FLAG = template_flags(load())[0]
    return _FLAG
def variants():
    """(name, keep(d)) for: no filter; bundle caps; the causal template filter; both"""
    F = flags()
    v = [("none", lambda d: True)]
    v += [(f"cap{c:.1f}", (lambda d, c=c: d["bundle"] <= c)) for c in CAPS]
    v += [("tmpl", lambda d: not F[d["cv"]])]
    v += [(f"tmpl+cap{c:.1f}", (lambda d, c=c: d["bundle"] <= c and not F[d["cv"]])) for c in CAPS]
    return v
POPS = {"engine": "fire_e", "tables": "fire_t"}
def fires(pop, per, win=None):
    """the fires of population pop ('engine' / 'tables') in period per ('fit', 'rec', 'rec+late', 'late'), optionally one window"""
    key = POPS[pop]; pers = {"fit": ("fit",), "rec": ("rec",), "rec+late": ("rec", "late"), "late": ("late",)}[per]
    return [d for d in load() if d[key] and d["per"] in pers and (win is None or d["win"] == win)]
def win_hours(w):
    """a fit window's T0 span (the four sum to the fit's 96.0 h)"""
    t = [d["T0"] for d in load() if d["win"] == w]; return (max(t) - min(t)) / 3600.0
