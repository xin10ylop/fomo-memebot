"""crowd_rules.py: the gate priced the way the engine can actually execute it (report 24.33).

Two things separated the engine from the tables: the unit (the tables counted distinct shooter WALLETS aimed at the curve,
crowd_signal.py; engine 6.1/6.2 counted FLEETS: distinct relay targets plus direct senders, so a 51-wallet fleet behind one
relay was 51 for the tables and 1 for the engine) and the view (the tables priced block k-2 of a creation second; the feed
shows the engine blocks minted before the shot's time minus the feed lag, and the median creation second has 7 blocks, not 10,
so the shot at the tick sees block k-1). This script evaluates every rule on one raw pull (crowd_raw.py) with the same
returns (hold_grid: second place, 300 blocks, $15 model), per window and pooled, and prints the engine's view model
against the launches the engine actually judged.
    python3 src/analysis/crowd_rules.py [open_frac=0.76] [build_frac=0.71]"""
import json, sys, math, statistics as st
D = "data/derived/live_vs_table/"; US = {"0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
OPEN_F = float(sys.argv[1]) if len(sys.argv) > 1 else 0.76; BUILD_F = float(sys.argv[2]) if len(sys.argv) > 2 else 0.71
STAKE, GAS = 13.0, 0.33
W = [("Sep 18-19", "crowd_raw_sep1819.json", "hold_grid.json", 23.1), ("Sep 20-21", "crowd_raw_sep2021.json", "hold_grid_oos_sep2021.json", 34.8),
     ("Sep 22-23", "crowd_raw_sep2223.json", "hold_grid.json", 29.3), ("Sep 23 day", "crowd_raw_sep23day.json", "hold_grid_today_sep23.json", 8.8)]
def cums(r):
    """cumulative counts by block offset 0..k, both units, the engine's exclusions"""
    wallets, fleets = set(), set(); cw, cf = [], []
    for off, rows in enumerate(r["blocks"][: r["k"] + 1]):
        for t in rows:
            if t["to"] in US or t["to_token"] or t["fr"] in US: continue
            if t["direct"]:
                if not t["named_fr"]: fleets.add(t["fr"]); wallets.add(t["fr"])
            elif not t["named_data"]:
                fleets.add(t["to"])
                if not t["named_fr"]: wallets.add(t["fr"])
        cw.append(len(wallets)); cf.append(len(fleets))
    return cw, cf
def view(k, frac):
    """the last block offset visible at a moment `frac` of the way through the creation second minus the feed lag (blocks evenly spaced)"""
    return max(-1, min(k, math.floor(frac * (k + 1)) - 1))
def at(c, j): return c[j] if 0 <= j < len(c) else 0
data = []
for name, rf, hf, hours in W:
    try: R = json.load(open(D + rf))
    except FileNotFoundError: print("missing", rf); continue
    H = {r["cv"]: r for r in json.load(open(D + hf))}; rows = []
    for r in R:
        h = H.get(r["cv"]); x = h.get("behind1_15_h300") if h else None
        if x is None or (isinstance(x, float) and math.isnan(x)): continue
        cw, cf = cums(r); k = r["k"]
        rows.append({"cv": r["cv"], "k": k, "cw": cw, "cf": cf, "ret": x, "w_open": at(cw, view(k, OPEN_F)), "f_open": at(cf, view(k, OPEN_F)), "w_build": at(cw, view(k, BUILD_F)), "f_build": at(cf, view(k, BUILD_F)), "w_k2": at(cw, k - 2), "f_k2": at(cf, k - 2)})
    data.append((name, hours, rows))
def cell(f, hours):
    if len(f) < 3: return f"{len(f):3d}        -           "
    usd = st.mean([x * STAKE - GAS for x in f]); return f"{len(f):3d} {st.mean(f):+6.1%} {sum(x>0 for x in f)/len(f):3.0%} ${usd:+5.2f} ${usd*len(f)/hours*24:+5.0f}/d"
rules = [("tables as priced: wallets>=2 @k-2", lambda r: r["w_k2"] >= 2), ("engine 6.2 as built: fleets>=2 @open", lambda r: r["f_open"] >= 2),
         ("fleets>=1 @open", lambda r: r["f_open"] >= 1), ("wallets>=2 @open (unit=wallets)", lambda r: r["w_open"] >= 2), ("wallets>=3 @open", lambda r: r["w_open"] >= 3),
         ("wallets>=5 @open", lambda r: r["w_open"] >= 5), ("wallets>=10 @open", lambda r: r["w_open"] >= 10),
         ("wallets>=2 @open & >=1 @build", lambda r: r["w_open"] >= 2 and r["w_build"] >= 1), ("wallets>=2 @open & >=2 @build", lambda r: r["w_open"] >= 2 and r["w_build"] >= 2),
         ("fleets>=1 @build", lambda r: r["f_build"] >= 1), ("fleets>=2 @open & >=1 @build", lambda r: r["f_open"] >= 2 and r["f_build"] >= 1),
         ("wallets>=2 @open & fleets>=2 @open", lambda r: r["w_open"] >= 2 and r["f_open"] >= 2)]
print(f"second place, 300 blocks, $15 model; $/burst and $/day at ${STAKE:.0f} after ${GAS:.2f} gas; open view: blocks minted before {OPEN_F:.2f} s of the creation second, build view before {BUILD_F:.2f} s")
print(f"{'rule':38s}" + "".join(f"{n:>28s}" for n, _, _ in data) + f"{'pooled':>28s}")
for rn, rf in rules:
    cells = []; pool = []; hrs = 0
    for n, hours, rows in data:
        f = [r["ret"] for r in rows if rf(r)]; pool += f; hrs += hours; cells.append(cell(f, hours))
    print(f"{rn:38s}" + "".join(f"{c:>28s}" for c in cells) + f"{cell(pool, hrs):>28s}")
print("\nreturn by the block (offset from the end of the creation second) where the count first reached the rule, all windows:")
for unit, key, thr in (("wallets", "cw", 2), ("fleets", "cf", 1), ("fleets", "cf", 2)):
    buck = {}
    for n, hours, rows in data:
        for r in rows:
            j = next((i for i, a in enumerate(r[key]) if a >= thr), None)
            if j is not None: buck.setdefault(r["k"] - j, []).append(r["ret"])
    print(f"  {unit}>={thr}: " + "  ".join(f"k-{d}: n={len(buck[d])} {st.mean(buck[d]):+.0%}" for d in sorted(buck) if len(buck[d]) >= 3))
print("\nhow many blocks the creation second has (all windows):", sorted(((k, n) for k, n in __import__('collections').Counter(r['k'] + 1 for _, _, rows in data for r in rows).items())))
# the engine's own observations against the pull: which block offsets are consistent with the count it logged
obs = {"0x7f4588cb": ("open", 3), "0x1a03dc87": ("open", 1), "0xb88cdecd": ("open", 0), "0xac4d55df": ("build", 0), "0xf5737a75": ("build", 1), "0x61b5aeb4": ("build", 0), "0xacbc7874": ("build", 1),
       "0x74608565": ("build", 0), "0x1332d47c": ("build", 0), "0x4dc86962": ("build", 0), "0xea50ba0f": ("build", 0)}
print("\nthe engine's logged fleet counts (6.1 at the build on Sep 23; 6.2 at the gate's opening, Sep 23-24) against the pull's fleets by block:")
for n, hours, rows in data:
    for r in rows:
        o = obs.get(r["cv"][:10])
        if not o: continue
        ok = [j for j, a in enumerate(r["cf"]) if a == o[1]]; k = r["k"]
        print(f"  {r['cv'][:10]} k={k} ({k+1} blocks) fleets by block {r['cf']} engine {o[0]} {o[1]} -> blocks {ok} = k-{k-max(ok) if ok else '?'}..k-{k-min(ok) if ok else '?'}; model {o[0]} view: block {view(k, OPEN_F if o[0]=='open' else BUILD_F)}")
