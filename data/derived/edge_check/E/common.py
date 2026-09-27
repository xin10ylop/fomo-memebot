"""common.py (edge_check/E): the population, the tapes and the one yardstick used by every reviewer-E script.
Run the scripts from the repository root (they chdir there themselves).

Population: the crowd files of the fit (sep1819, sep2021, sep2223, sep23day: 563 launches) and the recent windows (the eleven
committed files sep24paper .. sep27night: 160 launches, plus round 1 A's gap pulls gapA and gapB: 172 in all), de-duplicated by
curve, first file wins. A fire: fleets >= 2 at block k-2 (crowd_rules.cums / at, exactly as reach_table.py).
Pricing: stake_scale.model_eff imported by exec (as reach_table.py does): second place in the E1 block (n_ahead=1), $13 at
2570 $/ETH, the second's surcharge, the tier on buy and sell, the 3% cap, later buys folded by their ETH, the exit's own
impact; gas $0.33 a burst. `path()` below is model_eff made incremental over the hold (one pass per launch instead of one
per hold); check_path.py proves it equal to model_eff on every launch.
Tapes: b0..b0+640 from round 1 A's caches (real stamps), C's caches (real stamps), then B/tapes and D/tapes; blocks
b0+641..b0+1240 from this folder's pull_ext.py (tapes_ext.json.gz)."""
import json, gzip, os, sys, time, math
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "src/analysis"))
_argv = list(sys.argv); sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])                    # cums, at, US, view
exec(open("src/analysis/stake_scale.py").read().split("\nfor name, cf, hours in W:")[0])   # model_eff, net_eth_of, E, GAS, lv, fold_*
sys.argv = _argv
import live_vs_table as lv
LVD = "data/derived/live_vs_table/"; ED = "data/derived/edge_check/"; A = ED + "A/"; B = ED + "B/"; C = ED + "C/"; DD = ED + "D/"; EE = ED + "E/"
FIT = ["sep1819", "sep2021", "sep2223", "sep23day"]
REC = ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night"]
GAPS = ["gapA", "gapB"]
FIT_HOURS = {"sep1819": 23.1, "sep2021": 34.8, "sep2223": 29.3, "sep23day": 8.8}
STAKE = 13.0; HMAX = 1200; EXT_HI = 1240
def _raw(w):
    p = (A if w in GAPS else LVD) + f"crowd_raw_{w}.json.gz"
    return json.load(gzip.open(p, "rt"))
def load_all():
    seen = set(); out = []
    for w in FIT + REC + GAPS:
        for r in _raw(w):
            if r["cv"] in seen: continue
            seen.add(r["cv"]); r["win"] = w; r["set"] = "fit" if w in FIT else "rec"; r["committed"] = w not in GAPS
            r["day"] = time.strftime("%b %d", time.gmtime(r["T0"])); out.append(r)
    return out
def is_fire(r):
    cw, cf = cums(r); return at(cf, r["k"] - 2) >= 2
_T = {}
def _load_tapes():
    if _T: return
    for f in ("tapes.json.gz", "tapes_gapA.json.gz", "tapes_gapB.json.gz", "tapes_chk27.json.gz"):
        if os.path.exists(A + f):
            for cv, L in json.load(gzip.open(A + f, "rt")).items(): _T.setdefault(cv, (L, "A"))
    for f in ("tapes_extra.json.gz",):
        for cv, L in json.load(gzip.open(C + f, "rt")).items(): _T.setdefault(cv, (L, "C"))
_X = None
def _load_ext():
    global _X
    if _X is None:
        p = EE + "tapes_ext.json.gz"; _X = json.load(gzip.open(p, "rt")) if os.path.exists(p) else {}
    return _X
def tape(cv, ext=True):
    """the tape b0..b0+640 (hi = its last block), extended to b0+1240 when pull_ext.py has the launch; src says which cache"""
    _load_tapes(); L, src = _T.get(cv, (None, None))
    if L is None:
        for s, p in (("B", B + f"tapes/{cv}.json"), ("D", DD + f"tapes/{cv}.json")):
            if os.path.exists(p): L = json.load(open(p)); src = s; break
    if L is None: return None
    L = dict(L); L["ts"] = {int(k): v for k, v in L["ts"].items()}; L["src"] = src
    L["hi"] = L.get("hi") or L.get("to") or L["b0"] + 640
    L["rows"] = [r for r in L["rows"] if r["bn"] <= L["b0"] + 640]
    if ext:
        X = _load_ext().get(cv)
        if X is not None:
            L["rows"] = sorted(L["rows"] + [r for r in X["rows"] if r["bn"] > L["b0"] + 640], key=lambda r: (r["bn"], r["li"])); L["hi"] = X["hi"]
    return L
def seat_block(L):
    return next((n for n in range(L["b0"] + 1, L["b0"] + 30) if L["ts"].get(n, 0) == L["T0"] + 1), None)
def path(L, n_ahead=1, stake=STAKE, hmax=HMAX):
    """model_eff(L, stake/E, E1, n_ahead, h)[0] for every h = 0..hmax in one pass (identical folds, identical order), and the
    effective stake g in ETH. Holds past the tape's reach (E1 + h > hi) are None."""
    bE1 = seat_block(L)
    if bE1 is None or L["tier"] is None: return None, None
    NET = net_eth_of(L)
    rows = [r for r in L["rows"] if r["who"] not in OURS]; tier = L["tier"]; ts = L["ts"]; T0 = L["T0"]; X, Y = X0, Y0; i = 0
    while i < len(rows) and ts.get(rows[i]["bn"], 9e18) == T0:
        r = rows[i]
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
        i += 1
    rest = rows[i:]; seen = 0; pre = []; post = []
    for r in rest:
        if r["bn"] < bE1: pre.append(r)
        elif r["bn"] == bE1:
            if r["k"] == "B" and seen < n_ahead: pre.append(r); seen += 1
            elif r["k"] == "B": post.append(r)
            else: (pre if seen < n_ahead else post).append(r)
        else: post.append(r)
    for r in pre:
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
    sur = SUR.get(ts.get(bE1, T0) - T0, 0.0); g = stake / E; net = g * (1 - tier - sur); tk = Y * net / (X + net)
    if tk > CAP * Y0: tk = CAP * Y0; net = X * tk / (Y - tk); g = net / (1 - tier - sur)
    X, Y = X + net, Y - tk
    out = []; j = 0
    for h in range(hmax + 1):
        xb = bE1 + h
        if xb > L["hi"]: out.append(None); continue
        while j < len(post) and post[j]["bn"] <= xb:
            r = post[j]
            if r["k"] == "B":
                n = NET.get((r["bn"], r["li"]))
                if n is not None: X, Y = X + n, Y - Y * n / (X + n)
            else: X, Y = fold_sell(X, Y, r["tk"])
            j += 1
        out.append((X * tk / (Y + tk) * (1 - tier)) / g - 1)
    return out, g
def usd(ret, g=STAKE / 2570.0): return ret * g * E - GAS
def mean(v): return sum(v) / len(v) if v else float("nan")
def sd(v):
    if len(v) < 2: return float("nan")
    m = mean(v); return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
def se(v): return sd(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
def median(v):
    s = sorted(v); n = len(s)
    return float("nan") if not n else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)
def hms(t): return time.strftime("%b %d %H:%M", time.gmtime(t))
