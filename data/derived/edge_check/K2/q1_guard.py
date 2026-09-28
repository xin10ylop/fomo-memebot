"""K2/q1_guard.py: the minOut guard. What the reverted bursts would have paid at second place; the slip swept; guards conditioned on
what the engine knows at the build (fleets, bundle, tier) or on what the chain puts ahead (the drift of the creation second after
the build view vs the buy ahead in E1). Fit Sep 21-23, read Sep 24-28, and the reverse."""
import os, sys, json, gzip, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from sim import *
P = json.load(gzip.open(os.path.join(HERE, "prices.json.gz"), "rt")); PR = P["rows"]; HS = P["HS"]; I11 = HS.index(11)
base = run()
print("== the usual view (k-1 + reg), every other setting live ==")
print(three(base, "live (slip 7%)"))
rev = [r for r in base if r["why"] == "GUARD"]
for per in ("fit", "read", None):
    v = [r["x"]["behind1_13_h11"] for r in rev if per is None or period(r["x"]) == per]
    f = [r["ret"] for r in base if r.get("fill") and (per is None or period(r["x"]) == per)]
    if v: print(f"  reverted bursts [{per or 'all'}]: n {len(v)}, second place h11 mean {st.mean(v):+.1%} med {st.median(v):+.1%} win {sum(a>0 for a in v)/len(v):.0%}, $ if filled {sum(a*13 for a in v):+.2f} (gas already paid); the fills: n {len(f)} mean {st.mean(f):+.1%}")
# the guard ratio: tokens at second place over tokens sized at the build
print("\n== reverted and filled bursts by the guard ratio q = tk_seat1 / tk_build (second place h11) ==")
fired = [r for r in base if r.get("fired")]
bins = [(0, .5), (.5, .7), (.7, .8), (.8, .85), (.85, .9), (.9, .93), (.93, .97), (.97, 1.0), (1.0, 9)]
for lo, hi in bins:
    for per in ("fit", "read"):
        v = [r["x"]["behind1_13_h11"] for r in fired if period(r["x"]) == per and r["x"]["tk_build"] and lo <= r["x"]["tk_seat1"] / r["x"]["tk_build"] < hi]
        print(f"  q in [{lo:.2f},{hi:.2f}) {per:4s}: n {len(v):3d} mean {mean(v):+7.1%} med {st.median(v) if v else float('nan'):+7.1%}")
print("\n== the slip swept (the fire set is the same; only which bursts fill changes; reverted = -$0.33) ==")
for slip in (0.03, 0.05, 0.07, 0.10, 0.15, 0.20, 0.30, 0.50, 1.0):
    res = run(slip=slip)
    a, b = summ(res, "fit"), summ(res, "read")
    print(f"  slip {slip:4.2f}: fit fills {a['fills']:3d}/{a['fired']} mean {a['mean']:+6.1%} ${a['usd']:+7.2f} ({a['usd_day']:+6.2f}/d) | read fills {b['fills']:3d}/{b['fired']} mean {b['mean']:+6.1%} ${b['usd']:+7.2f} ({b['usd_day']:+6.2f}/d)")
# decomposition on taped fires: drift of the creation second after the build view (first place vs build) and the buy ahead (second vs first)
print("\n== why the guard trips (taped fires): creation-second drift after the build view vs the buy ahead in E1 ==")
for per in ("fit", "read"):
    n = dict(drift=0, ahead=0, both=0, none=0); rows = []
    for r in fired:
        x = r["x"]; p = PR.get(x["cv"])
        if not p or period(x) != per or not x["tk_build"]: continue
        d = p["tk_p1"] / x["tk_build"]; a = p["tk_p2"] / p["tk_p1"]; q = x["tk_seat1"] / x["tk_build"]
        rows.append((d, a, q, x["behind1_13_h11"], p["e1_buys"][0][0] if p["e1_buys"] else 0.0))
        if q < 0.93: n["both" if (d < 0.93 and a < 0.93) else "drift" if d < 0.93 else "ahead" if a < 0.93 else "none"] += 1
    rv = [z for z in rows if z[2] < 0.93]
    print(f"  {per}: {len(rows)} taped fires, {len(rv)} guard trips: drift alone {n['drift']}, the buy ahead alone {n['ahead']}, both {n['both']}, neither alone (compound) {n['none']}")
    for lab, f in (("trips from drift (first place < 93% of build)", lambda z: z[2] < .93 and z[0] < .93), ("trips from the buy ahead only (drift ok)", lambda z: z[2] < .93 and z[0] >= .93)):
        v = [z[3] for z in rows if f(z)]
        print(f"     {lab:48s} n {len(v):3d} second place h11 mean {mean(v):+7.1%}")
# conditioned guards: rules chosen on one period, read on the other
print("\n== conditioned guards (pass if q >= 0.93, or the condition) ==")
def G(cond):
    return lambda x: (not (x["tk_build"] and x["tk_seat1"])) or x["tk_seat1"] >= 0.93 * x["tk_build"] or cond(x)
def drift_ok(th):
    def f(x):
        p = PR.get(x["cv"])
        if not p: return False
        return p["tk_p1"] >= th * x["tk_build"]
    return f
cands = [("fleets>=3 at view", lambda x: x["f_k1r"] >= 3), ("fleets>=4", lambda x: x["f_k1r"] >= 4), ("bundle<=1.5", lambda x: x["bundle"] <= 1.5), ("bundle>1.5", lambda x: x["bundle"] > 1.5),
         ("tier 3%", lambda x: x["tb"] == 200), ("tier <3%", lambda x: x["tb"] < 200), ("q>=0.85", lambda x: x["tk_seat1"] >= 0.85 * x["tk_build"]), ("q>=0.80", lambda x: x["tk_seat1"] >= 0.80 * x["tk_build"]),
         ("q>=0.70", lambda x: x["tk_seat1"] >= 0.70 * x["tk_build"]),
         ("drift ok (first>=0.93 build), any buy ahead [taped]", drift_ok(0.93)), ("k>=5", lambda x: x["k"] >= 5), ("k<=4", lambda x: x["k"] <= 4)]
for lab, c in cands:
    res = run(guardfn=G(c)); a, b = summ(res, "fit"), summ(res, "read")
    print(f"  {lab:52s} fit fills {a['fills']:3d} mean {a['mean']:+6.1%} ${a['usd']:+7.2f} | read fills {b['fills']:3d} mean {b['mean']:+6.1%} ${b['usd']:+7.2f} ({b['usd_day']:+5.2f}/d)")
