"""R1 common loader: the engine_replay dumps (rows_k2 / rows_k1reg / rows_kreg, run by run_replay.sh at slip 0.20, Sep 21 09:40 - Sep 28 21:00)
and the raw crowd rows per launch. Fit = Sep 21-23, read = Sep 24-28. $13 a fire, gas $0.33 a burst."""
import json, gzip, glob, os, calendar, time, math, statistics as st
ROOT = "/home/user/fomo-memebot"; HERE = os.path.dirname(os.path.abspath(__file__)); D = f"{ROOT}/data/derived/live_vs_table"
STAKE, GAS = 13.0, 0.33
US = {"0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
SPLIT = calendar.timegm(time.strptime("2026-09-24 00:00", "%Y-%m-%d %H:%M"))
SWITCH = calendar.timegm(time.strptime("2026-09-28 12:27", "%Y-%m-%d %H:%M"))
def load_view(v):
    return {r["cv"]: r for r in json.load(open(f"{HERE}/rows_{v}.json"))}
def crowd():
    out = {}
    for f in sorted(glob.glob(f"{D}/crowd_raw_*.json.gz")) + sorted(glob.glob(f"{D}/crowd_raw_*.json")):
        try:
            R = json.load(gzip.open(f, "rt")) if f.endswith(".gz") else json.load(open(f))
        except Exception:
            continue
        for r in R:
            out.setdefault(r["cv"].lower(), r)
    return out
def period(t): return "fit" if t < SPLIT else "read"
def eligible(r):
    """reached the crowd gate: every pre-gate and bundle/cap/tier gate passed"""
    return r["why"] in ("FILL", "GUARD no fill") or r["why"].startswith("GATE attackers")
def usd(r, slip=0.20, hold="11"):
    """the burst's $ at second place: a fill if the seat block's tokens are within the slip of the build's sizing"""
    g = r.get("guard_ratio")
    if g is not None and g < 1 - slip: return -GAS
    x = (r.get("ret") or {}).get(hold)
    if x is None: return None
    return x * STAKE - GAS
def summ(vals):
    v = [x for x in vals if x is not None]
    if not v: return "n=0"
    return f"n={len(v)} ${sum(v):+.2f} mean ${st.mean(v):+.2f}/fire"
def days(p):
    """covered days per period (from the replay's hours: fit Sep 21 09:40-Sep 23 = 62.1 h, read Sep 24-Sep 28 21:00 = 116.3 h)"""
    return {"fit": 62.1 / 24, "read": 116.3 / 24}[p]
