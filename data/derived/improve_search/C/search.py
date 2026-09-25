"""searcher C: the brief's protocol on the fit (4 backtest windows) and validation (5 paper windows) sets.
   cd /home/user/fomo-memebot && python3 <this file>"""
import json, gzip, sys, os, math, statistics as st, itertools
os.chdir("/home/user/fomo-memebot"); sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])            # cums, view, at, US
D = "data/derived/live_vs_table/"
FIT = [("sep1819", "crowd_raw_sep1819", "hold_grid.json", "launches_141_creators.json", 23.1), ("sep2021", "crowd_raw_sep2021", "hold_grid_oos_sep2021.json", "launches_oos_sep2021.json", 34.8),
       ("sep2223", "crowd_raw_sep2223", "hold_grid.json", "launches_175_sep2223.json", 29.3), ("sep23day", "crowd_raw_sep23day", "hold_grid_today_sep23.json", "launches_today_sep23.json", 8.8)]
VAL = [("sep24paper", "crowd_raw_sep24paper", "hold_grid_sep24paper.json", "launches_sep24_paper.json", 9.0), ("sep25night", "crowd_raw_sep25night", "hold_grid_sep25night.json", "launches_sep25night.json", 9.0),
       ("sep25am", "crowd_raw_sep25am", "hold_grid_sep25am.json", "launches_sep25am.json", 6.6), ("sep25pm", "crowd_raw_sep25pm", "hold_grid_sep25pm.json", "launches_sep25pm.json", 6.6),
       ("sep25eve2", "crowd_raw_sep25eve2", "hold_grid_sep25eve2.json", "launches_sep25eve2.json", 2.75)]
STAKE, GAS = 13.0, 0.33
def load(name, rf, hf, lf, hours, extra=None):
    R = json.load(gzip.open(D + rf + ".json.gz", "rt")); H = {r["cv"]: r for r in json.load(open(D + hf))}; L = {l["cv"].lower(): l for l in json.load(open(D + lf))}
    if extra:
        R += [r for r in json.load(gzip.open(D + extra[0] + ".json.gz", "rt")) if r["cv"].startswith(extra[3])]; H.update({r["cv"]: r for r in json.load(open(D + extra[1]))}); L.update({l["cv"].lower(): l for l in json.load(open(D + extra[2]))})
    rows = []
    for r in R:
        h = H.get(r["cv"]); l = L.get(r["cv"])
        if not h or h.get("behind1_15_h300") is None or (isinstance(h["behind1_15_h300"], float) and math.isnan(h["behind1_15_h300"])): continue
        cw, cf = cums(r); k = r["k"]
        first2 = next((k - j for j, a in enumerate(cf) if a >= 2), None)          # blocks before the end where the count first reached 2
        direct = sum(1 for rows_ in r["blocks"][:k + 1] for t in rows_ if t["direct"] and not t["named_fr"] and t["fr"] not in US)
        relay = sum(1 for rows_ in r["blocks"][:k + 1] for t in rows_ if not t["direct"] and not t["named_data"] and t["to"] not in US and not t["to_token"])
        rows.append({"cv": r["cv"], "k": k, "cf": cf, "cw": cw, "f2": at(cf, k - 2), "f3": at(cf, k - 3), "f1": at(cf, k - 1), "w2": at(cw, k - 2), "first2": first2, "direct": direct, "relay": relay,
                     "h": h, "bundle_eth": (l or {}).get("bundle_eth", 0.0), "named": len((l or {}).get("named", [])), "tier": (l or {}).get("tier"), "hour": (l or {}).get("hour"), "T0": r["T0"]})
    return name, hours, rows
fit = [load(*w) for w in FIT]; val = [load(*w) for w in VAL[:-1]] + [load(*VAL[-1], extra=("crowd_raw_sep25eve", "hold_grid_sep25eve.json", "launches_sep25eve.json", "0xf45fa520"))]
def stats(rows, hours, col="behind1_15_h300", stake=STAKE):
    v = [r["h"][col] for r in rows if r["h"].get(col) is not None and not (isinstance(r["h"][col], float) and math.isnan(r["h"][col]))]
    if not v: return {"n": 0, "usd": 0.0, "perday": 0.0}
    usd = [x * stake - GAS for x in v]
    return {"n": len(v), "mean": st.mean(v), "median": st.median(v), "win": sum(x > 0 for x in v) / len(v), "dead": sum(x < -0.4 for x in v) / len(v), "usd": sum(usd), "burst": st.mean(usd), "perday": sum(usd) / hours * 24}
def evaluate(name, sel, col="behind1_15_h300", stake=STAKE):
    out = {"name": name, "fit": [], "val": []}
    for grp, key in ((fit, "fit"), (val, "val")):
        allrows = []; hrs = 0
        for wname, hours, rows in grp:
            f = [r for r in rows if sel(r)]; allrows += f; hrs += hours; out[key].append((wname, stats(f, hours, col, stake)))
        out[key + "_pooled"] = stats(allrows, hrs, col, stake)
    return out
def passes(c, base):
    fp, vp, bfp, bvp = c["fit_pooled"], c["val_pooled"], base["fit_pooled"], base["val_pooled"]; why = []
    if fp["n"] < 30: why.append(f"fit fires {fp['n']} < 30")
    if fp["perday"] <= bfp["perday"]: why.append(f"fit $/day {fp['perday']:.0f} <= baseline {bfp['perday']:.0f}")
    if any(s["n"] and s["usd"] <= 0 for _, s in c["fit"]) or any(s["n"] == 0 for _, s in c["fit"]): why.append("a fit window not positive")
    if vp["n"] == 0 or vp["usd"] < bvp["usd"] or (vp.get("mean", -9) < bvp.get("mean", -9)): why.append(f"validation ${vp['usd']:.0f}/{vp.get('mean', 0):+.0%} below baseline ${bvp['usd']:.0f}/{bvp.get('mean', 0):+.0%}")
    if fp["n"] and (fp["win"] < bfp["win"] - 0.10 or fp["dead"] > bfp["dead"] + 0.05): why.append("win/dead worse than allowed")
    return why
base = evaluate("BASELINE fleets>=2 @k-2, behind1 h300", lambda r: r["f2"] >= 2)
cands = []
for n in (1, 3, 4): cands.append(evaluate(f"fleets>={n} @k-2", (lambda n: lambda r: r["f2"] >= n)(n)))
for n in (2, 3, 5): cands.append(evaluate(f"wallets>={n} @k-2", (lambda n: lambda r: r["w2"] >= n)(n)))
cands.append(evaluate("fleets>=2 @k-2 & >=1 @k-3", lambda r: r["f2"] >= 2 and r["f3"] >= 1))
cands.append(evaluate("fleets>=2 @k-2 & first reached 2 by k-3", lambda r: r["f2"] >= 2 and r["first2"] is not None and r["first2"] >= 3))
for col in ("behind1_15_h15", "behind1_15_h30", "behind1_15_h60", "behind1_15_h150", "behind1_15_h600", "behind1_15_tp50_h600", "behind1_15_stop20_h600", "behind1_15_tp50_stop20_h600"):
    cands.append(evaluate(f"baseline gate, exit {col.split('_', 2)[2]}", lambda r: r["f2"] >= 2, col=col))
cands.append(evaluate("baseline gate, $100 column h300", lambda r: r["f2"] >= 2, col="behind1_100_h300", stake=100.0))
for x in (0.5, 0.8, 1.0, 1.5): cands.append(evaluate(f"OR bundle_eth>={x}", (lambda x: lambda r: r["f2"] >= 2 or r["bundle_eth"] >= x)(x)))
for x in (0.5, 0.8, 1.0): cands.append(evaluate(f"AND bundle_eth>={x}", (lambda x: lambda r: r["f2"] >= 2 and r["bundle_eth"] >= x)(x)))
for x in (0.5, 0.8): cands.append(evaluate(f"AND bundle_eth<{x}", (lambda x: lambda r: r["f2"] >= 2 and r["bundle_eth"] < x)(x)))
for n in (5, 8, 12): cands.append(evaluate(f"OR named>={n}", (lambda n: lambda r: r["f2"] >= 2 or r["named"] >= n)(n)))
for n in (5, 8): cands.append(evaluate(f"AND named>={n}", (lambda n: lambda r: r["f2"] >= 2 and r["named"] >= n)(n)))
for t in (0.02, 0.03): cands.append(evaluate(f"AND tier=={t}", (lambda t: lambda r: r["f2"] >= 2 and abs((r['tier'] or 0) - t) < 1e-6)(t)))
cands.append(evaluate("OR tier==0.03 & bundle>=0.8", lambda r: r["f2"] >= 2 or (abs((r['tier'] or 0) - 0.03) < 1e-6 and r["bundle_eth"] >= 0.8)))
for lo, hi in ((12, 22), (13, 21), (0, 12)): cands.append(evaluate(f"AND hour in [{lo},{hi})", (lambda lo, hi: lambda r: r["f2"] >= 2 and r["hour"] is not None and lo <= r["hour"] < hi)(lo, hi)))
cands.append(evaluate("AND k>=4", lambda r: r["f2"] >= 2 and r["k"] >= 4)); cands.append(evaluate("AND k<=6", lambda r: r["f2"] >= 2 and r["k"] <= 6))
cands.append(evaluate("OR k<=2 (un-aimable anyway)", lambda r: r["f2"] >= 2 or r["k"] <= 2))
cands.append(evaluate("AND direct shots >=1", lambda r: r["f2"] >= 2 and r["direct"] >= 1)); cands.append(evaluate("AND relay shots >=10", lambda r: r["f2"] >= 2 and r["relay"] >= 10))
cands.append(evaluate("OR wallets>=10 @k-2", lambda r: r["f2"] >= 2 or r["w2"] >= 10)); cands.append(evaluate("OR fleets>=1 @k-3", lambda r: r["f2"] >= 2 or r["f3"] >= 1))
cands.append(evaluate("fleets>=1 @k-2 & bundle>=0.8", lambda r: r["f2"] >= 1 and r["bundle_eth"] >= 0.8)); cands.append(evaluate("fleets>=1 @k-2 & named>=8", lambda r: r["f2"] >= 1 and r["named"] >= 8))
cands.append(evaluate("(borderline) fleets>=2 @k-1", lambda r: r["f1"] >= 2))
def row(c):
    fp, vp = c["fit_pooled"], c["val_pooled"]
    return f"{c['name']:42s} fit n={fp['n']:3d} {fp.get('mean', 0):+6.1%} win {fp.get('win', 0):3.0%} dead {fp.get('dead', 0):3.0%} ${fp['perday']:+5.0f}/d | val n={vp['n']:2d} {vp.get('mean', 0):+6.1%} ${vp['usd']:+6.1f}"
print("fit = 4 backtest windows (96 h); val = 5 paper windows (34 h); $ at $13 after $0.33 gas unless the $100 column\n")
print(row(base) + "  <- baseline")
print("per fit window:", " | ".join(f"{w} n={s['n']} {s.get('mean',0):+.0%} ${s['perday']:+.0f}/d" for w, s in base["fit"])); print("per val window:", " | ".join(f"{w} n={s['n']} {s.get('mean',0):+.0%} ${s['usd']:+.1f}" for w, s in base["val"])); print()
npass = 0
for c in sorted(cands, key=lambda c: -c["fit_pooled"]["perday"]):
    why = passes(c, base); npass += not why
    print(row(c) + ("  PASS" if not why else "  fail: " + "; ".join(why)))
print(f"\n{len(cands)} candidates tried, {npass} pass the protocol")
