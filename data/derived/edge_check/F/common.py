"""common.py (edge_check/F, hold sweep): loaders and the one yardstick for every reviewer-F script. Run from the repo root.

Population: the crowd files of the fit (sep1819, sep2021, sep2223, sep23day) and the recent windows (sep24paper .. sep27night),
plus round 1 A's two gap pulls (gapA Sep 26 17:38-22:38, gapB Sep 27 04:09-09:20), deduplicated by curve, first file wins
(sep25eve2 repeats 5 of sep25eve, sep26restart 1 of sep26pm). 563 fit + 160 recent + 12 gap = 735 launches.
A fire: crowd_rules.cums fleets >= 2 at block k-2 (reach_table.py). 73 fit fires, 18 recent (+1 in gapA = 19).

Tapes b0..b0+640: A/tapes.json.gz (the 91 fires, real stamps), A/tapes_gap{A,B} (real), C/tapes_extra (85 sep2223, real),
then B/tapes (472 real, 166 synthesised stamps), then D/tapes (synthesised). Synthesised stamps put b0..b0+k in T0 and b0+k+1
in T0+1, which is what the chain says by the definition of k, so the seat and the surcharge are the same (B/synth_check.py).
F/ext.json.gz (pull_ext.py) adds every Buy/Sell b0+641..b0+1240, so holds reach 1,200 blocks after the seat.

Pricing: stake_scale.model_eff imported by exec as reach_table.py does ($13 at ETH 2570, second place in E1 = n_ahead 1, the
surcharge by second, tier on buy and sell, the 3% cap, later buys folded by their ETH, sells by their tokens, the exit's own
impact). paths() below is model_eff unrolled over the hold: it returns model_eff(L, s, bE1, n_ahead, h)[0] for every h in
one pass; check_paths.py proves it equal to model_eff at every h 1..600 on the fires and on a sample of refused launches."""
import json, gzip, os, sys, time, math
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "src/analysis"))
_argv = list(sys.argv); sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])                    # cums, at, US
exec(open("src/analysis/stake_scale.py").read().split("\nfor name, cf, hours in W:")[0])   # model_eff, net_eth_of, E, GAS, lv, fold_*
sys.argv = _argv
import live_vs_table as lv
D = "data/derived/live_vs_table/"; EC = "data/derived/edge_check/"; F = EC + "F/"
FIT = ["sep1819", "sep2021", "sep2223", "sep23day"]
REC = ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night"]
GAPS = ["gapA", "gapB"]
STAKE = 13.0; HMAX = 1200
def _raw(w):
    p = (EC + "A/" if w in GAPS else D) + f"crowd_raw_{w}.json.gz"
    return json.load(gzip.open(p, "rt"))
def load_all():
    seen = set(); out = []
    for w in FIT + REC + GAPS:
        for r in _raw(w):
            if r["cv"] in seen: continue
            seen.add(r["cv"]); r["win"] = w; r["set"] = "fit" if w in FIT else "rec"; out.append(r)
    return out
def fleets_k2(r):
    cw, cf = cums(r); return at(cf, r["k"] - 2)
def is_fire(r): return fleets_k2(r) >= 2
_T = {}; _EXT = None
def _load():
    global _EXT
    if _T: return
    for f in ("A/tapes.json.gz", "A/tapes_gapA.json.gz", "A/tapes_gapB.json.gz", "A/tapes_chk27.json.gz", "C/tapes_extra.json.gz", "C/tapes_extra27.json.gz"):
        if os.path.exists(EC + f):
            for cv, L in json.load(gzip.open(EC + f, "rt")).items(): L["src"] = f; _T.setdefault(cv, L)
    _EXT = json.load(gzip.open(F + "ext.json.gz", "rt")) if os.path.exists(F + "ext.json.gz") else {}
def tape(cv, ext=True):
    """the tape with integer block stamps, b0..b0+640 from the caches, plus b0+641..b0+1240 from ext.json.gz when present"""
    _load(); L = _T.get(cv)
    if L is None:
        for d in ("B/tapes/", "D/tapes/"):
            p = EC + d + f"{cv}.json"
            if os.path.exists(p): L = json.load(open(p)); L["src"] = d; break
    if L is None: return None
    L = dict(L); L["ts"] = {int(k): v for k, v in L["ts"].items()}
    L["rows"] = [x for x in L["rows"] if x["bn"] <= L["b0"] + 640]; L["reach"] = L["b0"] + 640
    if ext and cv in _EXT:
        L["rows"] = sorted(L["rows"] + _EXT[cv]["rows"], key=lambda x: (x["bn"], x["li"])); L["reach"] = _EXT[cv]["hi"]
    return L
def seat_block(L):
    return next((n for n in range(L["b0"] + 1, L["b0"] + 30) if L["ts"].get(n, 0) == L["T0"] + 1), None)

def paths(L, n_ahead=1, stake=STAKE, hmax=HMAX, partial=None):
    """model_eff unrolled: returns (ret, g) with ret[h] = model_eff(L, stake/E, bE1, n_ahead, h)[0] for h = 0..hmax (None past the
    tape's reach). partial=(h1, frac): sell frac of the position after block bE1+h1 (tier fee, own impact), keep folding, and
    ret[h] for h > h1 is (ETH back at h1 + value of the rest at h) / stake - 1 (ret[h] for h <= h1 is the full mark)."""
    bE1 = seat_block(L)
    if bE1 is None: return None, None
    NET = net_eth_of(L)
    def fold_buy_eth(X, Y, r):
        n = NET.get((r["bn"], r["li"]))
        if n is None: return X, Y
        return X + n, Y - Y * n / (X + n)
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
    reach = L.get("reach", L["b0"] + 640); ret = [None] * (hmax + 1); j = 0; hold_tk = tk; banked = 0.0
    for h in range(0, hmax + 1):
        b = bE1 + h
        if b > reach: break
        while j < len(post) and post[j]["bn"] <= b:
            r = post[j]; j += 1
            if r["k"] == "B": X, Y = fold_buy_eth(X, Y, r)
            else: X, Y = fold_sell(X, Y, r["tk"])
        if partial and h == partial[0]:
            s = tk * partial[1]; out = X * s / (Y + s); banked = out * (1 - tier); X, Y = X - out, Y + s; hold_tk = tk - s
            ret[h] = (banked + X * hold_tk / (Y + hold_tk) * (1 - tier)) / g - 1
            continue
        ret[h] = (banked + X * hold_tk / (Y + hold_tk) * (1 - tier)) / g - 1
    return ret, g

def usd(ret, g=STAKE / 2570.0): return ret * g * E - GAS
def hms(t): return time.strftime("%b %d %H:%M", time.gmtime(t))
def day(t): return time.strftime("%b %d", time.gmtime(t))
def mean(v): return sum(v) / len(v) if v else float("nan")
def median(v):
    s = sorted(v); n = len(s)
    return float("nan") if not n else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)
def sd(v):
    if len(v) < 2: return float("nan")
    m = mean(v); return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
def se(v): return sd(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
