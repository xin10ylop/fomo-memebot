"""common.py (reviewer D): loaders shared by every script in this folder. Run the scripts from the repository root.
- the 15 crowd files (4 fit windows Sep 18-23, 11 recent windows Sep 24-27), de-duplicated by curve, first file wins
- the rule's count (crowd_rules.cums / at, exactly as reach_table.py: fleets >= 2 at block k-2)
- tapes: D/tapes/<cv>.json (pulled here), else B/tapes/<cv>.json (round 1, checked against A/tapes.json.gz by check_tapes.py)
- pricing: stake_scale.model_eff, $13 at ETH $2,570, second place in the seat block E1 (n_ahead=1), gas $0.33, SUR, CAP
"""
import json, gzip, os, sys, time, statistics as st, math, random
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "src/analysis"))
_saved = list(sys.argv); sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])                    # cums, at, US
exec(open("src/analysis/stake_scale.py").read().split("\nfor name, cf, hours in W:")[0])   # model_eff, E, GAS, lv
sys.argv = _saved
import live_vs_table as lv
LV = "data/derived/live_vs_table/"; DD = "data/derived/edge_check/D/"; BB = "data/derived/edge_check/B/"
FIT = ["sep1819", "sep2021", "sep2223", "sep23day"]
RECENT = ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night"]
HOURS = {"fit": 96.0, "recent": 60.0}                   # reach_table.py's hours (the brief's $/day basis)
FIT_W_HOURS = {"sep1819": 23.1, "sep2021": 34.8, "sep2223": 29.3, "sep23day": 8.8}   # crowd_rules.py
STAKE = 13.0
def load(files, dedup=True):
    out, seen = [], set()
    for f in files:
        p = LV + f"crowd_raw_{f}.json.gz"
        for r in json.load(gzip.open(p, "rt")):
            if dedup and r["cv"] in seen: continue
            seen.add(r["cv"]); r["win"] = f; out.append(r)
    return out
def all_records():
    out = []
    for grp, files in (("fit", FIT), ("recent", RECENT)):
        for r in load(files): r["grp"] = grp; out.append(r)
    seen = set(); res = []
    for r in out:
        if r["cv"] in seen: continue
        seen.add(r["cv"]); res.append(r)
    return res
def fire(r):
    cw, cf = cums(r); return at(cf, r["k"] - 2) >= 2
def tape(cv):
    for p in (DD + f"tapes/{cv}.json", BB + f"tapes/{cv}.json"):
        if os.path.exists(p):
            L = json.load(open(p)); L["ts"] = {int(k): v for k, v in L["ts"].items()}; return L
    return None
def seat_block(L, b0):
    ts, T0 = L["ts"], L["T0"]
    return next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
def usd(ret): return ret * STAKE - GAS
def day(T): return time.strftime("%b %d", time.gmtime(T))
def hhmm(T): return time.strftime("%b %d %H:%M", time.gmtime(T))
def mean(v): return st.mean(v) if v else float("nan")
def se(v): return st.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
def summ(v, hours=None):
    """n, mean, win, dead, $/fire after gas, $/day at the given hours"""
    if not v: return "  0"
    u = [usd(x) for x in v]; s = f"{len(v):3d} {mean(v):+6.1%} win {sum(x > 0 for x in v)/len(v):3.0%} dead {sum(x < -0.4 for x in v)/len(v):3.0%} ${mean(u):+5.2f}/fire"
    if hours: s += f" ${sum(u)/hours*24:+6.1f}/day"
    return s
