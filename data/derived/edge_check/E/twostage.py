"""twostage.py (edge_check/E): two-stage exits under the same discipline as the fixed holds. Eight variants, fixed before
looking and not tuned: take-profit +25% / +50% with a 300-block hold, +25% with a 60-block hold; stop -20% with a 300- and
a 60-block hold; half at 9 and half at 60 / 150 / 300 blocks. The engine sees its position's value at the end of a block,
decides, and its sell lands d = 2, 3 or 4 blocks later (every number is the mean over the three delays, as for the fixed
settings); triggers are read on the block-end value. The partial exits fold our own first sale into the curve (the later
buyers fold by their ETH, as model_eff does). Benchmarks: each period's best fixed setting (chosen in-sample on the landing
average: fit 334, recent 8) and the candidate setting 9. Null test: for the triggered variants the trigger is read on the path
of another fire (paths permuted across fires within each period, 1,000 permutations, seed 11) and applied to the fire's own
path: how often the permuted variant beats setting 9 on both periods, and where the real variant's margin falls.
    python3 data/derived/edge_check/E/twostage.py > data/derived/edge_check/E/twostage.txt"""
import sys, os, json, gzip
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
P = json.load(gzip.open(c.EE + "paths.json.gz", "rt")); F = {s: [x for x in P if x["fire"] and x["set"] == s] for s in ("fit", "rec")}
D = (2, 3, 4)
def partial(L, h1, h2, d, frac=0.5):
    """sell frac of the tokens at the end of block E1+h1+d, the rest at E1+h2+d; our first sale folded into the curve"""
    bE1 = c.seat_block(L); NET = c.net_eth_of(L); rows = [r for r in L["rows"] if r["who"] not in c.OURS]; tier = L["tier"]; ts = L["ts"]; T0 = L["T0"]
    X, Y = c.X0, c.Y0; i = 0
    while i < len(rows) and ts.get(rows[i]["bn"], 9e18) == T0:
        r = rows[i]
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = c.fold_buy(X, Y, r["tk"])
        else: X, Y = c.fold_sell(X, Y, r["tk"])
        i += 1
    seen = 0; pre = []; post = []
    for r in rows[i:]:
        if r["bn"] < bE1: pre.append(r)
        elif r["bn"] == bE1:
            if r["k"] == "B" and seen < 1: pre.append(r); seen += 1
            elif r["k"] == "B": post.append(r)
            else: (pre if seen < 1 else post).append(r)
        else: post.append(r)
    for r in pre:
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = c.fold_buy(X, Y, r["tk"])
        else: X, Y = c.fold_sell(X, Y, r["tk"])
    sur = c.SUR.get(ts.get(bE1, T0) - T0, 0.0); g = c.STAKE / c.E; net = g * (1 - tier - sur); tk = Y * net / (X + net)
    if tk > c.CAP * c.Y0: tk = c.CAP * c.Y0; net = X * tk / (Y - tk); g = net / (1 - tier - sur)
    X, Y = X + net, Y - tk; back = 0.0; j = 0
    for hb, part in ((h1 + d, tk * frac), (h2 + d, tk * (1 - frac))):
        while j < len(post) and post[j]["bn"] <= bE1 + hb:
            r = post[j]
            if r["k"] == "B":
                n = NET.get((r["bn"], r["li"]))
                if n is not None: X, Y = X + n, Y - Y * n / (X + n)
            else: X, Y = c.fold_sell(X, Y, r["tk"])
            j += 1
        back += X * part / (Y + part) * (1 - tier); X, Y = c.fold_sell(X, Y, part)
    return back / g - 1
def fixed(p, s): return np.mean([p[s + d] for d in D])
def trig(pt, pr, kind, lvl, H):
    """trigger read on path pt, value taken on path pr (pt is pr unless permuted)"""
    out = []
    for d in D:
        t = next((u for u in range(1, H + 1) if (pt[u] >= lvl if kind == "tp" else pt[u] <= lvl)), H); out.append(pr[t + d])
    return np.mean(out)
TRIG = [("take-profit +25%, hold 300", "tp", 0.25, 300), ("take-profit +50%, hold 300", "tp", 0.50, 300), ("take-profit +25%, hold 60", "tp", 0.25, 60),
        ("stop -20%, hold 300", "st", -0.20, 300), ("stop -20%, hold 60", "st", -0.20, 60)]
PART = [("half at 9, half at 60", 9, 60), ("half at 9, half at 150", 9, 150), ("half at 9, half at 300", 9, 300)]
res = {}
for s in ("fit", "rec"):
    ps = [x["p1"] for x in F[s]]; res[s] = {"best fixed": None, "setting 9": [fixed(p, 9) for p in ps], "setting 15": [fixed(p, 15) for p in ps]}
    best = max(range(1, 597), key=lambda h: np.mean([fixed(p, h) for p in ps])); res[s]["best fixed"] = [fixed(p, best) for p in ps]; res[s]["_best"] = best
    for name, kind, lvl, H in TRIG: res[s][name] = [trig(p, p, kind, lvl, H) for p in ps]
    for name, h1, h2 in PART:
        v = []
        for x in F[s]:
            L = c.tape(x["cv"]); v.append(np.mean([partial(L, h1, h2, d) for d in D]))
        res[s][name] = v
    # the half-and-half without our own impact, as a check on the fold: the mean of the two fixed exits
    for name, h1, h2 in PART: res[s][name + " (no own impact)"] = [0.5 * fixed(p, h1) + 0.5 * fixed(p, h2) for p in ps]
print(f"best fixed setting on the landing average: fit {res['fit']['_best']}, recent {res['rec']['_best']} (in-sample on each period)")
print(f"{'exit':44s} {'fit mean':>9s} {'win':>4s} {'dead':>5s} {'sd':>5s} {'rec mean':>9s} {'win':>4s} {'dead':>5s} {'sd':>5s}  {'vs best fixed (fit, rec)':>26s}  {'vs setting 9 (fit, rec)':>26s}")
names = ["best fixed", "setting 9", "setting 15"] + [t[0] for t in TRIG] + [p[0] for p in PART] + [p[0] + " (no own impact)" for p in PART]
for n in names:
    row = f"{n:44s}"
    for s in ("fit", "rec"):
        v = np.array(res[s][n]); row += f" {v.mean():+9.1%} {np.mean(v > 0):4.0%} {np.mean(v < -0.4):5.0%} {v.std(ddof=1):5.2f}"
    db = [np.mean(np.array(res[s][n]) - np.array(res[s]["best fixed"])) for s in ("fit", "rec")]; d9 = [np.mean(np.array(res[s][n]) - np.array(res[s]["setting 9"])) for s in ("fit", "rec")]
    row += f"  {db[0]:+7.1%} {db[1]:+7.1%} {'PASS' if min(db) > 0 else 'fail':>6s}      {d9[0]:+7.1%} {d9[1]:+7.1%} {'PASS' if min(d9) > 0 else 'fail':>6s}"
    print(row)
print("\nnull test (triggered variants): the trigger read on another fire's path, 1,000 permutations within each period")
rng = np.random.default_rng(11); NP = 1000
wins_any = 0; perm_wins = {t[0]: 0 for t in TRIG}; perm_marg = {t[0]: {"fit": [], "rec": []} for t in TRIG}
for k in range(NP):
    any_win = False
    perms = {s: rng.permutation(len(F[s])) for s in ("fit", "rec")}
    for name, kind, lvl, H in TRIG:
        m = {}
        for s in ("fit", "rec"):
            ps = [x["p1"] for x in F[s]]; v = [trig(ps[perms[s][i]], ps[i], kind, lvl, H) for i in range(len(ps))]
            m[s] = np.mean(v) - np.mean(res[s]["setting 9"]); perm_marg[name][s].append(m[s])
        if min(m.values()) > 0: perm_wins[name] += 1; any_win = True
    wins_any += any_win
for name, kind, lvl, H in TRIG:
    real = {s: np.mean(res[s][name]) - np.mean(res[s]["setting 9"]) for s in ("fit", "rec")}
    print(f"  {name:30s} permuted beats setting 9 on both periods in {perm_wins[name]/NP:5.1%}; real margin fit {real['fit']:+.1%} (permuted >= real in {np.mean(np.array(perm_marg[name]['fit']) >= real['fit']):.0%}), rec {real['rec']:+.1%} (permuted >= real in {np.mean(np.array(perm_marg[name]['rec']) >= real['rec']):.0%})")
print(f"  at least one of the five permuted variants beats setting 9 on both periods in {wins_any/NP:.1%} of permutations")
print("\nhow the stops fire: among fires whose path reaches -20% within 300 blocks, the drop in the block that crosses (trigger block value minus the previous block's)")
for s in ("fit", "rec"):
    drops = []; after = []
    for x in F[s]:
        p = x["p1"]; t = next((u for u in range(1, 301) if p[u] <= -0.2), None)
        if t: drops.append(p[t] - p[t - 1]); after.append(np.mean([p[t + d] for d in D]))
    if drops: print(f"  {s}: {len(drops)} fires cross -20%; median one-block drop at the crossing {np.median(drops):+.1%}; value where the stop's sell lands (t+2..4) median {np.median(after):+.1%}")
