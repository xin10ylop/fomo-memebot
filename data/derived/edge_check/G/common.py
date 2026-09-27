"""common.py (edge_check/G): loaders and the one yardstick used by every reviewer-G script. Run from the repo root.
Population: the crowd files of the fit (sep1819, sep2021, sep2223, sep23day: 563 launches) and the recent windows (sep24paper ..
sep27night: 160 launches) plus round 1 A's two gap pulls (gapA Sep 26 17:38-22:38, gapB Sep 27 04:09-09:20), de-duplicated by
curve, first file wins. "rec18" = the eleven recent windows only (18 fires); "rec" = with the gaps (172 launches, 19 fires).
Fire = fleets >= 2 at block k-2 (crowd_rules.cums/at, exactly as reach_table.py).
Tapes: A/tapes*.json.gz and C/tapes_extra.json.gz (real stamps) first, then B/tapes, D/tapes (stamps synthesised from k, checked
by B/synth_check.py), all to b0+640; G/tapes_ext.json.gz adds b0+641..b0+1250 (G/pull_ext.py).
Pricing: stake_scale.model_eff imported by exec as reach_table.py does ($13 at 2570 $/ETH, second place in E1, surcharge by
second, tier on buy and sell, 3% cap, later buys folded by ETH, sells by tokens, the exit's own impact); curve() below is a
one-pass rewrite of model_eff that returns the exit value after every block E1+h, h = 0..HMAX, and check_curve.py proves it
equals model_eff."""
import json, gzip, os, sys, time, math
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "src/analysis"))
_argv = list(sys.argv); sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])                    # cums, at, US
exec(open("src/analysis/stake_scale.py").read().split("\nfor name, cf, hours in W:")[0])   # model_eff, net_eth_of, E, GAS, lv, fold_*
sys.argv = _argv
import live_vs_table as lv
LV = "data/derived/live_vs_table/"; EC = "data/derived/edge_check/"; G = EC + "G/"
FIT = ["sep1819", "sep2021", "sep2223", "sep23day"]
REC = ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night"]
GAPS = ["gapA", "gapB"]
STAKE = 13.0; HMAX = 1200; TAPE_HI = 640; EXT_HI = 1250
def _raw(w):
    p = (EC + "A/" if w in GAPS else LV) + f"crowd_raw_{w}.json.gz"
    return json.load(gzip.open(p, "rt"))
def load_all():
    seen = set(); out = []
    for w in FIT + REC + GAPS:
        for r in _raw(w):
            if r["cv"] in seen: continue
            seen.add(r["cv"]); r["win"] = w; r["set"] = "fit" if w in FIT else "rec"; r["rec18"] = w in REC; out.append(r)
    return out
def fleets_k2(r):
    cw, cf = cums(r); return at(cf, r["k"] - 2)
def is_fire(r): return fleets_k2(r) >= 2
_T = {}
def _load():
    if _T: return
    for f in ("A/tapes.json.gz", "A/tapes_gapA.json.gz", "A/tapes_gapB.json.gz", "A/tapes_chk27.json.gz", "C/tapes_extra.json.gz"):
        for cv, L in json.load(gzip.open(EC + f, "rt")).items(): L["src"] = f.split(".")[0]; _T.setdefault(cv, L)
    for d in ("B/tapes/", "D/tapes/"):
        for f in os.listdir(EC + d):
            cv = f[:-5]
            if cv not in _T: L = json.load(open(EC + d + f)); L["src"] = d.rstrip("/"); _T[cv] = L
_EXT = None
def tape(cv, ext=True):
    """the tape b0..b0+640 with integer stamps; with ext, the events b0+641..b0+1250 appended (hi = b0+1250)"""
    global _EXT
    _load(); L = _T.get(cv)
    if L is None: return None
    L = dict(L); L["ts"] = {int(k): v for k, v in L["ts"].items()}; L["hi"] = L["b0"] + TAPE_HI
    if ext:
        if _EXT is None: _EXT = json.load(gzip.open(G + "tapes_ext.json.gz", "rt")) if os.path.exists(G + "tapes_ext.json.gz") else {}
        x = _EXT.get(cv)
        if x is not None:
            L["rows"] = sorted([r for r in L["rows"] if r["bn"] <= L["b0"] + TAPE_HI] + x, key=lambda r: (r["bn"], r["li"])); L["hi"] = L["b0"] + EXT_HI
    return L
def seat_block(L):
    return next((n for n in range(L["b0"] + 1, L["b0"] + 30) if L["ts"].get(n, 0) == L["T0"] + 1), None)
def curve(L, n_ahead=1, stake=STAKE, hmax=HMAX, entry_block=None):
    """model_eff(L, stake/E, E1, n_ahead, h)[0] for every h = 0..hmax in one pass; None past the tape's reach. Returns (vals, g)"""
    bE1 = entry_block or seat_block(L)
    if bE1 is None: return None, None
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
    X, Y = X + net, Y - tk; vals = []; j = 0
    for h in range(hmax + 1):
        if bE1 + h > L["hi"]: vals.append(None); continue
        while j < len(post) and post[j]["bn"] <= bE1 + h:
            r = post[j]; j += 1
            if r["k"] == "B":
                n = NET.get((r["bn"], r["li"]))
                if n is not None: X, Y = X + n, Y - Y * n / (X + n)
            else: X, Y = fold_sell(X, Y, r["tk"])
        vals.append((X * tk / (Y + tk) * (1 - tier)) / g - 1)
    return vals, g
def partial(L, h1, h2, frac=0.5, n_ahead=1, stake=STAKE):
    """sell frac of the tokens at the end of block E1+h1 and the rest at E1+h2, the first sale's impact on the curve included"""
    bE1 = seat_block(L); NET = net_eth_of(L)
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
    X, Y = X + net, Y - tk; back = 0.0; left = tk; j = 0
    for hx, part in ((h1, tk * frac), (h2, left - tk * frac)):
        while j < len(post) and post[j]["bn"] <= bE1 + hx:
            r = post[j]; j += 1
            if r["k"] == "B":
                n = NET.get((r["bn"], r["li"]))
                if n is not None: X, Y = X + n, Y - Y * n / (X + n)
            else: X, Y = fold_sell(X, Y, r["tk"])
        out = X * part / (Y + part); back += out * (1 - tier); X, Y = X - out, Y + part
    return back / g - 1
def usd(ret, g): return ret * g * E - GAS
def day(t): return time.strftime("%b %d", time.gmtime(t))
def hms(t): return time.strftime("%b %d %H:%M", time.gmtime(t))
def mean(v): return sum(v) / len(v) if v else float("nan")
def median(v):
    s = sorted(v); n = len(s)
    return float("nan") if not n else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)
def sd(v):
    if len(v) < 2: return float("nan")
    m = mean(v); return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
def se(v): return sd(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
