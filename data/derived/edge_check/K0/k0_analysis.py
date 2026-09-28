"""K0 (the assistant's own analysis for brief K): the engine replay's rows at the three gate views, fit Sep 21-23 / test Sep 24-28"""
import json, statistics as st, time, gzip, collections, sys
STAKE, GAS = 13.0, 0.33
def fit(x): return x["T0"] < 1790121600   # Sep 24 00:00 UTC
def line(v, label):
    if not v: return f"  {label:56s} n=0"
    usd = sum(x * STAKE - GAS for x in v)
    return f"  {label:56s} n={len(v):3d} mean {st.mean(v):+7.1%} med {st.median(v):+6.1%} win {sum(x>0 for x in v)/len(v):3.0%} ${usd:+8.2f}"
G = {x["cv"].lower(): x for x in json.load(gzip.open("data/derived/edge_check/G/curves.json.gz", "rt"))}
for name, key in (("rows_k1reg", "f_k1"), ("rows_k2", "f_k2"), ("rows_kreg", "f_k")):
    R = json.load(open(f"data/derived/edge_check/K0/{name}.json")); print(f"\n===== {name}: {len(R)} launches")
    fired = [x for x in R if x.get("fired")]; fills = [x for x in fired if x["why"] == "FILL"]; guard = [x for x in fired if x["why"].startswith("GUARD")]
    print("a. the guard: the reverted bursts had they filled (second place, exit 11) against the actual fills")
    for part, f in (("fit", fit), ("test", lambda x: not fit(x))):
        print(line([x["ret"]["11"] for x in guard if f(x) and x["ret"]["11"] is not None], f"{part}: reverted bursts as fills"))
        print(line([x["ret"]["11"] for x in fills if f(x)], f"{part}: actual fills"))
    for lo, hi in ((0.85, 0.93), (0.75, 0.85), (0.0, 0.75)):
        print(line([x["ret"]["11"] for x in guard if x.get("guard_ratio") is not None and lo <= x["guard_ratio"] < hi and x["ret"]["11"] is not None], f"  reverted, seat/build tokens in [{lo:.2f},{hi:.2f})"))
    print("b. launches the pre-gate filters removed: what they would do at this view's gate, then the guard")
    for why in ("PRE creator supply < 1%", "PRE creator repeat", "GATE bundle ETH > 3.0 (cap)", "GATE bundle 0 < 3", "GATE bundle 2 < 3"):
        xs = [x for x in R if x["why"] == why]; would = [x for x in xs if x[key] >= 2]; ok = [x for x in would if x.get("guard_ratio") is None or x["guard_ratio"] >= 0.93]
        for part, f in (("fit", fit), ("test", lambda x: not fit(x))):
            print(line([x["ret"]["11"] for x in ok if f(x) and x["ret"]["11"] is not None], f"{part}: {why[:34]}: {sum(1 for x in xs if f(x))} removed, {sum(1 for x in would if f(x))} fire, fills"))
    print("d. the same fills at first place vs second place (exit 11)")
    for part, f in (("fit", fit), ("test", lambda x: not fit(x))):
        print(line([x["ret"]["11"] for x in fills if f(x)], f"{part}: second place")); print(line([x["ret_first"]["11"] for x in fills if f(x) and x["ret_first"]["11"] is not None], f"{part}: first place"))
    print("e. exit rules on the fills that have a full curve (G): take-profit / stop checked block by block, else the fixed exit at 11")
    for part, f in (("fit", fit), ("test", lambda x: not fit(x))):
        fs = [x for x in fills if f(x) and x["cv"] in G]; print(line([G[x["cv"]]["r2"][11] for x in fs], f"{part}: fixed exit 11 ({len(fs)} with a curve)"))
        for tp in (0.10, 0.20, 0.30, 0.50):
            for stop in (None, 0.10):
                v = []
                for x in fs:
                    r2 = G[x["cv"]]["r2"]; e = r2[11]
                    for hh in range(1, 12):
                        if r2[hh] >= tp or (stop is not None and r2[hh] <= -stop): e = r2[hh]; break
                    v.append(e)
                print(line(v, f"{part}: take +{tp:.0%}{' / stop -%d%%' % (stop * 100) if stop else ''} else 11"))
        for hh in (5, 7, 9, 13, 20, 30):
            print(line([G[x["cv"]]["r2"][hh] for x in fs], f"{part}: fixed exit {hh}"))
    print("g. the gate's threshold at this view (the engine's filters as now, then the guard; exit 11)")
    for thr in (1, 2, 3, 4):
        for part, f in (("fit", fit), ("test", lambda x: not fit(x))):
            xs = [x for x in R if f(x) and not x["why"].startswith("PRE") and not x["why"].startswith("GATE bundle") and x[key] >= thr and (x.get("guard_ratio") is None or x["guard_ratio"] >= 0.93) and x["ret"]["11"] is not None]
            print(line([x["ret"]["11"] for x in xs], f"{part}: fleets >= {thr}"))
    print("h. by tier and by bundle size, this view's fills (exit 11)")
    for part, f in (("fit", fit), ("test", lambda x: not fit(x))):
        for lab, g in (("tier 2%", lambda x: abs(x["tier"] - 0.02) < 0.003), ("tier 3%", lambda x: abs(x["tier"] - 0.03) < 0.003), ("bundle < 0.6", lambda x: x["bundle"] < 0.6), ("bundle 0.6-1.2", lambda x: 0.6 <= x["bundle"] < 1.2), ("bundle >= 1.2", lambda x: x["bundle"] >= 1.2)):
            print(line([x["ret"]["11"] for x in fills if f(x) and g(x)], f"{part}: {lab}"))
