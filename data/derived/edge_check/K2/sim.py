"""K2/sim.py: the engine's gate chain over K2/table.json.gz with every setting a parameter (engine_replay.py's order: PRE creator
repeat / creator supply / creator buy, GATE bundle count / bundle ETH floor / cap / tier / position open / fleets, then the minOut
guard, then the fill at second place). Imported by the question scripts; `python3 sim.py` checks it against 24.41's three views."""
import os, json, gzip, math, statistics as st, time, calendar, random
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
T = json.load(gzip.open(os.path.join(HERE, "table.json.gz"), "rt"))
Y0 = 1e9; STAKE, GAS = 13.0, 0.33; BUSY_S = 6.0
SPLIT = calendar.timegm(time.strptime("2026-09-24 00:00", "%Y-%m-%d %H:%M"))
HOURS = {"fit": 62.1, "read": 105.7, "all": 167.8}        # engine_replay's covered hours: Sep 21 14.3 + 22 24.0 + 23 23.8 | Sep 24-27 96.0 + Sep 28 9.7
def period(x): return "fit" if x["T0"] < SPLIT else "read"
DEFAULT = dict(view="k1r", amin=2, repeat=True, supply=True, crebuy=True, nbmin=3, bmin=0.3, bmax=3.0, tier=(100, 200), slip=0.07, guard=True, ret="behind1_13_h11", busy=True)
def run(rows=None, extra=None, retfn=None, guardfn=None, gatefn=None, **kw):
    """returns a list of dicts: every launch with 'why' and, for fired ones, 'fired', 'fill', 'ret', 'usd'.
    extra(x) -> reason or None: an extra pre-gate filter; gatefn(x) -> bool (True = pass) replaces the fleets gate; guardfn(x) -> bool (True = fill)
    replaces the slip guard; retfn(x) -> return replaces the return column."""
    p = dict(DEFAULT); p.update(kw); out = []; busy_until = -1
    for x in (rows if rows is not None else T):
        why = None
        if p["repeat"] and x["repeat"] > 0: why = "PRE creator repeat"
        elif p["supply"] and x["tk0"] is not None and (x["tk0"] <= 0 or x["tk0"] >= Y0): why = "PRE no launch-block buy"
        elif p["supply"] and x["tk0"] is not None and x["tk0"] < 0.01 * Y0: why = "PRE creator supply < 1%"
        elif p["crebuy"] and (x["init_buy_eth"] or 0) > 2: why = "PRE creator buy > 2"
        if why is None and extra: why = extra(x)
        if why is None:
            if x["nb"] < p["nbmin"]: why = "GATE bundle count"
            elif x["bundle"] < p["bmin"]: why = "GATE bundle floor"
            elif p["bmax"] and x["bundle"] > p["bmax"]: why = "GATE cap"
            elif p["tier"] and not (p["tier"][0] <= x["tb"] <= p["tier"][1]): why = "GATE tier"
            elif p["busy"] and x["T0"] < busy_until: why = "GATE position open"
            elif gatefn is not None and not gatefn(x): why = "GATE rule"
            elif gatefn is None and x[f"f_{p['view']}"] < p["amin"]: why = "GATE fleets"
        r = {"x": x, "why": why}
        if why is None:
            r["fired"] = True
            if guardfn is not None: ok = guardfn(x)
            elif p["guard"] and x["tk_build"] and x["tk_seat1"]: ok = x["tk_seat1"] >= (1 - p["slip"]) * x["tk_build"]
            else: ok = True
            if not ok: r["why"] = "GUARD"; r["usd"] = -GAS
            else:
                ret = retfn(x) if retfn else x.get(p["ret"])
                if ret is None: r["why"] = "NORET"; r["usd"] = 0.0
                else: r["why"] = "FILL"; r["fill"] = True; r["ret"] = ret; r["usd"] = ret * STAKE - GAS; busy_until = x["T0"] + BUSY_S
        out.append(r)
    return out
def summ(res, per=None):
    """fires, guard, fills, mean, median, win, $ total, $/day for the subset (per = 'fit' | 'read' | None)"""
    rs = [r for r in res if per is None or period(r["x"]) == per]; hrs = HOURS[per or "all"]
    fired = [r for r in rs if r.get("fired")]; fills = [r for r in fired if r.get("fill")]; v = [r["ret"] for r in fills]
    usd = sum(r["usd"] for r in fired)
    return {"n": len(rs), "fired": len(fired), "guard": sum(1 for r in fired if r["why"] == "GUARD"), "fills": len(fills),
            "mean": st.mean(v) if v else float("nan"), "med": st.median(v) if v else float("nan"), "win": (sum(a > 0 for a in v) / len(v)) if v else float("nan"),
            "usd": usd, "usd_day": usd / hrs * 24, "fires_day": len(fired) / hrs * 24}
def line(s, label=""):
    return f"{label:38s} fired {s['fired']:4d} guard {s['guard']:4d} fills {s['fills']:4d} mean {s['mean']:+7.1%} med {s['med']:+7.1%} win {s['win']:4.0%} ${s['usd']:+8.2f} ${s['usd_day']:+6.2f}/d"
def three(res, label):
    return "\n".join(line(summ(res, per), f"{label} [{per or 'all'}]") for per in ("fit", "read", None))
def mean(v): return sum(v) / len(v) if v else float("nan")
def boot_ci(v, n=4000, seed=7):
    if len(v) < 2: return (float("nan"), float("nan"))
    rnd = random.Random(seed); ms = sorted(mean([rnd.choice(v) for _ in v]) for _ in range(n)); return ms[int(0.025 * n)], ms[int(0.975 * n)]
if __name__ == "__main__":
    for view, label in (("k2", "floor k-2 (no reg)"), ("k1r", "usual k-1 + reg"), ("k0r", "ceiling k + reg")):
        s = summ(run(view=view)); print(line(s, label))
    print("24.41: floor 45/27/18 +25.6% $45.17 | usual 129/61/68 +15.9% $97.92 | ceiling 219/118/101 +11.6% $80.65")
