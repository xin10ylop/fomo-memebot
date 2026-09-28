"""common.py (edge_check/K3): the dump (build_dump.py), the edge review's tapes, one pricing path and the statistics every K3 script uses.
Pricing = stake_scale.model_eff / hold_grid.model_path's rules (creation-second rows folded by tokens, rows ahead of us in the entry
block folded, surcharge by second, tier on buy and sell, 3% cap, buys after ours folded by their ETH, sells by tokens, the exit's own
impact), in one pass returning the exit value after every block entry+h, h = 0..HMAX. check_pricing.py proves it equals the grids /
G's r2 on the shared launches. Periods: A = Sep 21 09:40 - Sep 23 23:59 (fit), B = Sep 24 00:00 - Sep 28 09:40 (read), or the reverse."""
import os, sys, json, gzip, math, random, calendar, time
K3 = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(K3, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src/analysis"))
from live_vs_table import fold_buy, fold_sell, X0, Y0, OURS, SUR, CAP
EC = os.path.join(ROOT, "data/derived/edge_check"); E = 2570.0; GAS = 0.33; STAKE = 13.0; HMAX = 120
SPLIT = calendar.timegm(time.strptime("2026-09-24", "%Y-%m-%d"))
def load_dump(): return json.load(gzip.open(os.path.join(K3, "week_dump.json.gz"), "rt"))
def period(x): return "A" if x["T0"] < SPLIT else "B"
_TP = {}
for d in ("B/tapes", "D/tapes"):
    for f in os.listdir(os.path.join(EC, d)): _TP.setdefault(f[:-5].lower(), os.path.join(EC, d, f))
_TC = {}
def tape(cv):
    if cv in _TC: return _TC[cv]
    p = _TP.get(cv)
    if not p: _TC[cv] = None; return None
    L = json.load(open(p)); L["ts"] = {int(k): v for k, v in L["ts"].items()}; L["rows"] = [r for r in L["rows"] if r["who"] not in OURS]
    L["hi"] = L["b0"] + 640; _TC[cv] = L; return L
def second_block(L, s):
    return next((n for n in range(L["b0"] + 1, L["b0"] + 60) if L["ts"].get(n, 0) == L["T0"] + s), None)
def net_eth(L):
    if "_net" in L: return L["_net"]
    X, Y = X0, Y0; net = {}
    for r in L["rows"]:
        if r["k"] == "B":
            if 0 < r["tk"] < Y: net[(r["bn"], r["li"])] = X * r["tk"] / (Y - r["tk"]); X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
    L["_net"] = net; return net
def path(L, n_ahead=1, stake=STAKE, entry_block=None, hmax=HMAX, sec=1, view_block=None, extra_ahead_eth=0.0):
    """exit value after every block entry+h (h = 0..hmax), our buy behind n_ahead buys of the entry block (default: the first block of
    second `sec` after the creation's). Returns dict(v=[...], tk=tokens, g=ETH paid, bE=entry block, px_in, X/Y path not kept).
    view_block: if given, the tokens a buy would get on the curve as of the end of that block (the engine's build sizing) are in 'tk_view'."""
    bE = entry_block or second_block(L, sec)
    if bE is None: return None
    NET = net_eth(L); rows = L["rows"]; tier = L["tier"]; ts = L["ts"]; T0 = L["T0"]; X, Y = X0, Y0; i = 0
    while i < len(rows) and ts.get(rows[i]["bn"], 9e18) == T0:
        r = rows[i]
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
        i += 1
    rest = rows[i:]; seen = 0; pre = []; post = []
    for r in rest:
        if r["bn"] < bE: pre.append(r)
        elif r["bn"] == bE:
            if r["k"] == "B" and seen < n_ahead: pre.append(r); seen += 1
            elif r["k"] == "B": post.append(r)
            else: (pre if seen < n_ahead else post).append(r)
        else: post.append(r)
    for r in pre:
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = fold_buy(X, Y, r["tk"])
        else: X, Y = fold_sell(X, Y, r["tk"])
    sur = SUR.get(ts.get(bE, T0) - T0, 0.0); g = stake / E; net = g * (1 - tier - sur); tk = Y * net / (X + net)
    if tk > CAP * Y0: tk = CAP * Y0; net = X * tk / (Y - tk); g = net / (1 - tier - sur)
    X, Y = X + net, Y - tk; vals = []; j = 0; p_in = X / Y; px = []
    for h in range(hmax + 1):
        if bE + h > L["hi"]: vals.append(None); px.append(None); continue
        while j < len(post) and post[j]["bn"] <= bE + h:
            r = post[j]; j += 1
            if r["k"] == "B":
                n = NET.get((r["bn"], r["li"]))
                if n is not None: X, Y = X + n, Y - Y * n / (X + n)
            else: X, Y = fold_sell(X, Y, r["tk"])
        vals.append((X * tk / (Y + tk) * (1 - tier)) / g - 1); px.append(X / Y / p_in - 1)
    return {"v": vals, "px": px, "tk": tk, "g": g, "bE": bE, "n_ahead_real": seen}
def mean(v): v = [x for x in v if x is not None]; return sum(v) / len(v) if v else float("nan")
def median(v):
    s = sorted(x for x in v if x is not None); n = len(s)
    return float("nan") if not n else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)
def sd(v):
    v = [x for x in v if x is not None]
    if len(v) < 2: return float("nan")
    m = mean(v); return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
def se(v): return sd(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
def win(v): return sum(1 for x in v if x > 0) / len(v) if v else float("nan")
def boot_ci(v, n=4000, seed=7, stat=None):
    stat = stat or mean; rnd = random.Random(seed); v = list(v)
    if len(v) < 2: return (float("nan"), float("nan"))
    b = sorted(stat([rnd.choice(v) for _ in v]) for _ in range(n)); return b[int(0.025 * n)], b[int(0.975 * n)]
def boot_p_pos(v, n=4000, seed=7):
    """share of bootstrap draws whose SUM (dollar total) is positive"""
    rnd = random.Random(seed); v = list(v)
    if not v: return float("nan")
    return sum(1 for _ in range(n) if sum(rnd.choice(v) for _ in v) > 0) / n
def fmt(v, usd=None):
    if not v: return "n=0"
    s = f"n={len(v):3d} mean {mean(v):+6.1%} med {median(v):+6.1%} win {win(v):3.0%}"
    if usd is not None: s += f" ${usd:+7.2f}"
    return s
# the engine's chain on a dump row, parametrised
def fleets_at(x, view, reg=1):
    k = x["k"]; off = {"k-3": k - 3, "k-2": k - 2, "k-1": k - 1, "k": k}[view]; fb = x[f"fl_reg{reg}"]
    return fb[off] if 0 <= off < len(fb) else 0
def ret(x, h=11, pos="behind1", stake=13):
    return x["ret"].get(f"{pos}_{stake}_h{h}")
DAYS_B = 4 + 9.67 / 24                                          # Sep 24 00:00 - Sep 28 09:40
DAYS_A = (calendar.timegm(time.strptime("2026-09-24", "%Y-%m-%d")) - calendar.timegm(time.strptime("2026-09-21 09:40", "%Y-%m-%d %H:%M"))) / 86400
