"""K1/k1.py: the shared loader and the engine's decision chain as a function of its settings (for the variants).
decide() reproduces src/analysis/engine_replay.py exactly at its defaults (checked in check.py): pre-gate filters, bundle and tier
gates, one position at a time (6 s), the crowd gate on a chosen view, the minOut guard on the grid's k-2 sizing vs second place."""
import json, gzip, os, math, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
STAKE, GAS, Y0 = 13.0, 0.33, 1e9
HOURS = {"fit": None, "read": None}
def load():
    R = json.load(gzip.open(os.path.join(HERE, "rows.json.gz"), "rt"))
    R.sort(key=lambda r: r["T0"]); return R
# covered hours: Sep 21 09:40 - Sep 24 00:00 = 62.33 h fit; Sep 24 00:00 - Sep 28 09:40 = 105.67 h read (the replay covers 168 of 168 h)
HRS = {"fit": 62 + 20 / 60, "read": 105 + 40 / 60, "all": 168.0}
VIEWS = {"k-2": "f_k2n", "k-1": "f_k1r", "k": "f_k0r", "k-2r": "f_k2r", "k-1n": "f_k1n", "k-3": "f_k3"}
DEFAULT_F = dict(repeat=True, supply=True, cbuy=True, nb=True, bmin=True, cap=True, tier=True)
def ret_of(r, hold=11, pos="behind1", stake=13):
    return r.get(f"{pos}_{stake}_h{hold}") if pos != "behind1" or r.get(f"behind1_{stake}_h{hold}") is not None else None
def r2(r, h):
    """second place at exit block h: the grid where it has the hold, else G's curve (the replay's own substitution)"""
    v = r.get(f"behind1_13_h{h}")
    if v is not None: return v
    g = r.get("g_r2")
    return g[h] if g and h < len(g) else None
def pre_reasons(r, F):
    out = []
    if F["repeat"] and r["repeat"]: out.append("repeat")
    tk0 = r["tk0"]
    if tk0 is not None:
        if tk0 <= 0 or tk0 >= Y0: out.append("no launch-block buy") if F["supply"] else None
        elif F["supply"] and tk0 < 0.01 * Y0: out.append("supply")
    if F["cbuy"] and (r["init_buy_eth"] or 0.0) > 2: out.append("cbuy")
    return out
def gate_reasons(r, F, cap=3.0, bmin=0.3, tmin=100, tmax=200, nbmin=3):
    out = []
    if F["nb"] and r["nb"] < nbmin: out.append("nb")
    if F["bmin"] and r["bundle"] < bmin: out.append("bmin")
    if F["cap"] and cap and r["bundle"] > cap: out.append("cap")
    tb = r["tier_bps"] if r["tier_bps"] is not None else 0
    if F["tier"] and (tb < tmin or tb > tmax): out.append("tier")
    return out
def guard_pass(r, slip=0.07):
    tb, ts = r["tk_build"], r["tk_seat1"]
    if not (tb and ts): return True
    return ts >= (1 - slip) * tb
def decide(R, view="k-1", amin=2, slip=0.07, F=None, hold=11, fire_fn=None, guard_fn=None, busy=True, cap=3.0, ret_fn=None):
    """returns a list of dicts {r, why, ret, usd} in time order; fire_fn(r) overrides the crowd gate (True = fire); guard_fn(r) -> True = fills"""
    F = dict(DEFAULT_F, **(F or {})); out = []; busy_until = 0.0
    for r in R:
        d = {"r": r, "why": None, "ret": None, "usd": 0.0}
        p = pre_reasons(r, F)
        if p: d["why"] = "PRE " + p[0]; out.append(d); continue
        gts = gate_reasons(r, F, cap=cap)
        if busy and r["T0"] < busy_until: gts.append("busy")
        ok = fire_fn(r) if fire_fn else r[VIEWS[view]] >= amin
        if not ok: gts.append("crowd")
        if gts: d["why"] = "GATE " + gts[0]; out.append(d); continue
        fills = guard_fn(r) if guard_fn else guard_pass(r, slip)
        if not fills: d["why"] = "GUARD"; d["usd"] = -GAS; out.append(d); continue
        v = ret_fn(r) if ret_fn else r2(r, hold)
        if v is None: d["why"] = "NORET"; out.append(d); continue
        d["why"] = "FILL"; d["ret"] = v; d["usd"] = v * STAKE - GAS; busy_until = r["T0"] + 6.0; out.append(d)
    return out
def summ(D, part=None):
    D = [d for d in D if part is None or part == "all" or d["r"]["set"] == part]
    fired = [d for d in D if d["why"] in ("FILL", "GUARD")]; fills = [d for d in D if d["why"] == "FILL"]; v = [d["ret"] for d in fills]
    usd = sum(d["usd"] for d in fired)
    return {"fired": len(fired), "guard": len(fired) - len(fills), "fills": len(fills), "mean": st.mean(v) if v else float("nan"),
            "median": st.median(v) if v else float("nan"), "win": (sum(x > 0 for x in v) / len(v)) if v else float("nan"), "usd": usd,
            "usd_day": usd / HRS[part or "all"] * 24 if part else usd / HRS["all"] * 24, "sd": st.stdev(v) if len(v) > 1 else float("nan")}
def fmt(s):
    return f"fired {s['fired']:3d} guard {s['guard']:3d} fills {s['fills']:3d} mean {s['mean']:+6.1%} med {s['median']:+6.1%} win {s['win']:4.0%} ${s['usd']:+7.2f} ${s['usd_day']:+6.2f}/d"
def mean(v): return sum(v) / len(v) if v else float("nan")
def se(v): return st.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
def boot_ci(v, n=4000, seed=1, q=(0.05, 0.95)):
    import random
    if len(v) < 2: return (float("nan"), float("nan"))
    rnd = random.Random(seed); ms = sorted(mean([rnd.choice(v) for _ in v]) for _ in range(n)); return ms[int(q[0] * n)], ms[int(q[1] * n) - 1]
