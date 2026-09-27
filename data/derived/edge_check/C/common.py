"""common.py (edge_check/C): loaders and the one yardstick used by every reviewer-C script. Run from the repo root.
Launch population: the crowd files of the fit (sep1819, sep2021, sep2223, sep23day) and the recent windows (sep24paper ..
sep27night), plus round 1 A's two gap pulls (gapA Sep 26 17:38-22:38, gapB Sep 27 04:09-09:20), deduplicated by curve.
The fleet count is crowd_rules.cums (the engine's unit and exclusions); a fire is fleets >= 2 at block k-2 (reach_table).
Pricing is stake_scale.model_eff (second place in the E1 block, the surcharge by second, the 3% cap, later buys folded by ETH),
$13 at ETH 2570, gas $0.33 a burst."""
import json, gzip, os, sys, time, math
sys.path.insert(0, "src/analysis")
_argv = list(sys.argv); sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])                    # cums, at, US
exec(open("src/analysis/stake_scale.py").read().split("\nfor name, cf, hours in W:")[0])   # model_eff, net_eth_of, E, GAS, lv
sys.argv = _argv
D = "data/derived/live_vs_table/"; A = "data/derived/edge_check/A/"; B = "data/derived/edge_check/B/"; C = "data/derived/edge_check/C/"
FIT = ["sep1819", "sep2021", "sep2223", "sep23day"]
REC = ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night"]
GAPS = ["gapA", "gapB"]
STAKE = 13.0
def _raw(w):
    p = (A if w in GAPS or w.startswith("chk") else D) + f"crowd_raw_{w}.json.gz"
    if w.startswith("extra"): p = C + f"crowd_raw_{w}.json.gz"
    return json.load(gzip.open(p, "rt"))
def load_all(extra=()):
    seen = set(); out = []
    for w in FIT + REC + GAPS + list(extra):
        try: R = _raw(w)
        except FileNotFoundError: continue
        for r in R:
            if r["cv"] in seen: continue
            seen.add(r["cv"]); r["win"] = w; r["set"] = "fit" if w in FIT else "rec"; out.append(r)
    return out
_T = {}
def _load_tapes():
    if _T: return
    for f in ("tapes.json.gz", "tapes_gapA.json.gz", "tapes_gapB.json.gz", "tapes_chk27.json.gz"):
        if os.path.exists(A + f):
            for cv, L in json.load(gzip.open(A + f, "rt")).items(): _T.setdefault(cv, L)
    for f in os.listdir(C):
        if f.startswith("tapes_") and f.endswith(".json.gz"):
            for cv, L in json.load(gzip.open(C + f, "rt")).items(): _T.setdefault(cv, L)
def have_tape(cv):
    _load_tapes(); return cv in _T or os.path.exists(B + f"tapes/{cv}.json")
def tape(cv):
    """the tape with integer block stamps; A's and C's caches (real stamps) first, then B's per-launch files (some synthesised)"""
    _load_tapes(); L = _T.get(cv)
    if L is None:
        p = B + f"tapes/{cv}.json"
        if not os.path.exists(p): return None
        L = json.load(open(p))
    L = dict(L); L["ts"] = {int(k): v for k, v in L["ts"].items()}; return L
def seat_block(L):
    return next((n for n in range(L["b0"] + 1, L["b0"] + 30) if L["ts"].get(n, 0) == L["T0"] + 1), None)
def price(L, hold, n_ahead=1, stake=STAKE):
    bE1 = seat_block(L)
    if bE1 is None: return None
    return model_eff(L, stake / E, bE1, n_ahead, hold)[0]
def fleets_k2(r):
    cw, cf = cums(r); return at(cf, r["k"] - 2), at(cw, r["k"] - 2)
def is_fire(r): return fleets_k2(r)[0] >= 2
def usd(ret): return ret * STAKE - GAS
def hms(t): return time.strftime("%b %d %H:%M", time.gmtime(t))
def day(t): return time.strftime("%b %d", time.gmtime(t))
def mean(v): return sum(v) / len(v) if v else float("nan")
def sd(v):
    if len(v) < 2: return float("nan")
    m = mean(v); return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
def se(v): return sd(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
