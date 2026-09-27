"""fleet_variants.py: the crowd gate counted four ways on every launch of the fit and recent windows (Sep 27, the 12:47 miss):
  tables   crowd_rules.cums as the backtest counts it
  nohelper relay calls whose SENDER is a named wallet do not count (the bundle's own helper contract; the engine's intent,
           note_attack's docstring, but neither the engine nor cums checks the sender)
  engine   only shots in blocks after the curve is registered on the engine's watch list count; registration is taken as
           the first block holding a named wallet's buy (j): shots in blocks <= j were processed before the watch existed
  both     nohelper and engine together
Returns from edge_check/G/curves.json.gz (second place in E1, $13, every exit h after E1): h = 11 (setting 9 as it lands),
15 and 300.   python3 src/analysis/fleet_variants.py"""
import json, gzip, sys, os, statistics as st
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.argv = ["x", "0.76", "0.71"]; exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])
LV = "data/derived/live_vs_table/"; EC = "data/derived/edge_check/"
FIT = ["sep1819", "sep2021", "sep2223", "sep23day"]
REC = ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night", "gapA", "gapB"]
curves = {c["cv"]: c for c in json.load(gzip.open(EC + "G/curves.json.gz", "rt"))}
def raw(w): return json.load(gzip.open((EC + "A/" if w.startswith("gap") else LV) + f"crowd_raw_{w}.json.gz", "rt"))
def fleets_k2(r, nohelper=False, engine=False):
    j = next((i for i, rows in enumerate(r["blocks"]) if any(x.get("named_fr") or x.get("named_data") for x in rows)), -1)
    f = set()
    for off, rows in enumerate(r["blocks"][: max(0, r["k"] - 1)]):          # blocks 0 .. k-2
        if engine and off <= j: continue
        for t in rows:
            if t["to"] in US or t["to_token"] or t["fr"] in US: continue
            if t["direct"]:
                if not t["named_fr"]: f.add(t["fr"])
            elif not t["named_data"] and not (nohelper and t["named_fr"]):
                f.add(t["to"])
    return len(f), j
seen = set(); pop = {"fit": [], "recent": []}
for s, ws in (("fit", FIT), ("recent", REC)):
    for w in ws:
        for r in raw(w):
            if r["cv"] in seen or r["cv"] not in curves: continue
            seen.add(r["cv"]); pop[s].append(r)
for s in ("fit", "recent"):
    rs = pop[s]
    base = [r for r in rs if at(cums(r)[1], r["k"] - 2) >= 2]
    print(f"\n=== {s}: {len(rs)} launches, {len(base)} fires by the tables' count (check: fleets_k2 agrees on {sum(1 for r in rs if (fleets_k2(r)[0] >= 2) == (at(cums(r)[1], r['k'] - 2) >= 2))} of {len(rs)})")
    for name, kw in (("tables", {}), ("nohelper", {"nohelper": True}), ("engine", {"engine": True}), ("both", {"nohelper": True, "engine": True})):
        fires = [r for r in rs if fleets_k2(r, **kw)[0] >= 2]
        def m(h, fs=fires): return st.mean(curves[r["cv"]]["r2"][h] for r in fs) if fs else float("nan")
        print(f"  {name:9s} {len(fires):3d} fires  h11 {m(11):+6.1%}  h15 {m(15):+6.1%}  h300 {m(300):+6.1%}   $ at h11 after gas {sum(curves[r['cv']]['r2'][11] * 13 - 0.33 for r in fires):+7.2f}")
    lost = [r for r in base if fleets_k2(r, nohelper=True)[0] < 2]
    blind = [r for r in base if fleets_k2(r, engine=True)[0] < 2]
    def mm(fs, h): return st.mean(curves[r["cv"]]["r2"][h] for r in fs) if fs else float("nan")
    print(f"  fires that exist only because of a named-sender relay: {len(lost)}  h11 {mm(lost, 11):+.1%}  h15 {mm(lost, 15):+.1%}  h300 {mm(lost, 300):+.1%}")
    print(f"  fires the engine cannot see (a fleet only before registration): {len(blind)}  h11 {mm(blind, 11):+.1%}  h15 {mm(blind, 15):+.1%}  h300 {mm(blind, 300):+.1%}")
