"""stake_engine.py: the engine's own fires (fleets >= 2 at k-2 counting only shots after registration, 24.38) priced at stakes $13-$500
with the 11-block exit (setting 9 as it lands), second place, the audited model (stake_scale.model_eff). $/day at full fill from each
period's own fire rate.   python3 src/analysis/stake_engine.py"""
import json, gzip, sys, os, statistics as st, concurrent.futures as futures, time
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, "src/analysis")
import live_vs_table as lv
sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])
exec(open("src/analysis/stake_scale.py").read().split("\nfor name, cf, hours in W:")[0])
src = open("src/analysis/fleet_variants.py").read()
fk = src[src.index("def fleets_k2"):src.index("seen = set(); pop")]
exec(fk)
LV = "data/derived/live_vs_table/"; EC = "data/derived/edge_check/"
def raw(w): return json.load(gzip.open((EC + "A/" if w.startswith("gap") else LV) + f"crowd_raw_{w}.json.gz", "rt"))
SETS = {"fit (96 h)": (96.0, ["sep1819", "sep2021", "sep2223", "sep23day"]),
        "recent (about 67 h)": (66.8, ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night", "gapA", "gapB"])}
STAKES = (13, 50, 100, 200, 300, 500); HOLD = 11
def price(r):
    cv, b0 = r["cv"], r["b0"]
    for a in range(4):
        try:
            L = lv.launch(cv, b0 + 12, b0 + 60)
            if L is None or L["tier"] is None: return None
            ts = L["ts"]; T0 = L["T0"]
            bE1 = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
            if bE1 is None: return None
            return {s: model_eff(L, s / E, bE1, 1, HOLD) for s in STAKES}
        except Exception:
            time.sleep(2 * (a + 1))
    return None
for name, (hours, ws) in SETS.items():
    seen = set(); fires = []
    for w in ws:
        for r in raw(w):
            if r["cv"] in seen: continue
            seen.add(r["cv"])
            if fleets_k2(r, engine=True)[0] >= 2: fires.append(r)
    with futures.ThreadPoolExecutor(4) as ex: res = [x for x in ex.map(price, fires) if x]
    print(f"\n=== {name}: {len(res)} of {len(fires)} engine fires priced, exit at E1+{HOLD}, second place; {len(fires)/hours*24:.1f} fires a day")
    for s in STAKES:
        v = [(rr * g * E - GAS, g * E, rr) for rr, g in (x[s] for x in res)]
        print(f"  ${s:<4d} deployed ${st.mean(p for _, p, _ in v):4.0f}  return {st.mean(rr for _, _, rr in v):+6.1%}  $/fire {st.mean(u for u, _, _ in v):+7.2f}  $/day full fill {sum(u for u, _, _ in v)/hours*24:+7.1f}")
