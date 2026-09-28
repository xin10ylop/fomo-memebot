"""Q4: the winners the rule cannot take. Among the launches that reach the crowd gate and are refused at the usual view (engine count
at k-1 with the registration block < 2 fleets): how often the crowd appears in the tick's own block (engine count at k >= 2), what
they pay at second place, and whether any signal known before the tick picks them out. Each signal's threshold is chosen on one
half and read on the other (fit Sep 21-23, read Sep 24-28), as an ADDED fire on top of the live rule, at the 0.20 guard, $13."""
import sys, time, collections; sys.path.insert(0, "."); from common import *
exec(open(f"{ROOT}/src/analysis/crowd_rules.py").read().split("def view(")[0].split('OPEN_F =')[0])   # US and imports
from importlib import util
def cums2(r):
    """wallets, fleets and curve-aimed shots by block offset, the tables' exclusions (crowd_rules.cums) plus the shot count"""
    wallets, fleets = set(), set(); cw, cf, cs = [], [], []; n = 0
    for off, rows in enumerate(r["blocks"][: r["k"] + 1]):
        for t in rows:
            if t["to"] in US or t["to_token"] or t["fr"] in US: continue
            if t["direct"]:
                if not t["named_fr"]: fleets.add(t["fr"]); wallets.add(t["fr"]); n += 1
            elif not t["named_data"]:
                fleets.add(t["to"])
                if not t["named_fr"]: wallets.add(t["fr"]); n += 1
        cw.append(len(wallets)); cf.append(len(fleets)); cs.append(n)
    return cw, cf, cs
at = lambda c, j: c[j] if 0 <= j < len(c) else 0
C = crowd(); V = {v: load_view(v) for v in ("k2", "k1reg", "kreg")}
E = sorted([r for r in V["k1reg"].values() if eligible(r) and r["cv"] in C], key=lambda r: r["T0"])
rows = []; hist = collections.deque(maxlen=10); last_T = None
for r in E:
    c = C[r["cv"]]; cw, cf, cs = cums2(c); k = r["k"]; rk = V["kreg"][r["cv"]]
    x = {"cv": r["cv"], "T0": r["T0"], "p": period(r["T0"]), "fl_k1": r.get("fleets", 0), "fl_k": rk.get("fleets", 0), "fired_k1": bool(r.get("fired")), "ret": r["ret"]["11"], "g": r.get("guard_ratio"),
         "w_k1": at(cw, k - 1), "shots_k1": at(cs, k - 1), "f_k2": at(cf, k - 2), "k": k, "bundle": r["bundle"], "named": r["named"], "tier": r["tier"], "tk0": (r["tk0"] or 0) / 1e9,
         "hour": time.gmtime(r["T0"]).tm_hour, "heat10": (sum(hist) / len(hist)) if hist else 0.0, "gap_min": ((r["T0"] - last_T) / 60) if last_T else 999}
    x["usd"] = usd({"guard_ratio": x["g"], "ret": {"11": x["ret"]}})
    rows.append(x); hist.append(1 if x["fl_k"] >= 2 else 0); last_T = r["T0"]
ref = [x for x in rows if not x["fired_k1"] and x["ret"] is not None]
print("refused at the usual view (engine count at k-1 < 2), second place h11, 0.20 guard:")
for p in ("fit", "read"):
    a = [x for x in ref if x["p"] == p]; kc = [x for x in a if x["fl_k"] >= 2]; nk = [x for x in a if x["fl_k"] < 2]
    f = lambda s: f"n={len(s):3d} mean {st.mean([y['ret'] for y in s]):+6.1%} win {sum(y['ret'] > 0 for y in s) / len(s):3.0%} ${sum(y['usd'] for y in s):+7.2f}"
    print(f"  {p:4s} all {f(a)} | crowd only in block k {f(kc)} | no crowd by k {f(nk)} | P(block-k crowd) {len(kc) / len(a):.0%}")
feats = [("fl_k1", [1]), ("w_k1", [1, 2, 3, 5]), ("shots_k1", [1, 2, 3, 5, 10]), ("f_k2", [1]), ("k", [3, 4, 5, 6, 7, 8]), ("bundle", [0.5, 0.75, 1.0, 1.5, 2.0]), ("named", [5, 10, 15, 20]),
         ("tier", [0.025]), ("tk0", [0.02, 0.03, 0.05, 0.1]), ("heat10", [0.2, 0.3, 0.4, 0.5]), ("gap_min", [2, 5, 10, 20])]
def rule_rows(fe, th, sign, pp): return [x for x in ref if x["p"] == pp and ((x[fe] >= th) if sign > 0 else (x[fe] < th))]
print("\nadded fires on refused launches: signal chosen on one half (max $, n >= 4), read on the other; also P(block-k crowd) inside the rule")
res = []
for fe, ths in feats:
    for chose, readp in (("fit", "read"), ("read", "fit")):
        best = None
        for th in ths:
            for sign in (1, -1):
                s = rule_rows(fe, th, sign, chose)
                if len(s) < 4: continue
                v = sum(y["usd"] for y in s)
                if best is None or v > best[0]: best = (v, th, sign, len(s))
        if best is None: continue
        v, th, sign, n = best; s2 = rule_rows(fe, th, sign, readp)
        pk = lambda s: sum(1 for y in s if y["fl_k"] >= 2) / max(len(s), 1)
        res.append((fe, chose, th, sign, n, v, len(s2), sum(y["usd"] for y in s2), pk(rule_rows(fe, th, sign, chose)), pk(s2)))
for fe, chose, th, sign, n, v, n2, v2, pk1, pk2 in res:
    print(f"  {fe:9s} {'>=' if sign > 0 else '< '} {th:<6} chosen on {chose:4s}: n={n:3d} ${v:+7.2f} (P blk-k {pk1:.0%}) -> other half n={n2:3d} ${v2:+7.2f} (P blk-k {pk2:.0%})")
print("\nsignals whose chosen rule gains in BOTH directions (chosen on fit reads > 0 on read AND chosen on read reads > 0 on fit):")
byf = collections.defaultdict(list)
for x in res: byf[x[0]].append(x)
ok = [fe for fe, xs in byf.items() if len(xs) == 2 and all(x[7] > 0 for x in xs)]
print("  " + (", ".join(ok) if ok else "none"))
print("\na perfect oracle for the block-k crowd (fire on every refused launch whose engine count at k reaches 2), by guard:")
for p in ("fit", "read"):
    kc = [x for x in ref if x["p"] == p and x["fl_k"] >= 2]
    for slip in (0.07, 0.20, 0.30, 1.0):
        u = [usd({"guard_ratio": x["g"], "ret": {"11": x["ret"]}}, slip) for x in kc]; nf = sum(1 for x in kc if x["g"] is None or x["g"] >= 1 - slip)
        fills = [x["ret"] for x in kc if x["g"] is None or x["g"] >= 1 - slip]
        print(f"  {p:4s} slip {slip:4.2f}: {len(kc)} fires, {nf} fills mean {st.mean(fills) if fills else float('nan'):+6.1%}, ${sum(u):+7.2f} (${sum(u) / days(p):+.2f}/day)")
    big = sorted(kc, key=lambda x: -x["ret"])[:3]
    print("       largest: " + ", ".join(f"{time.strftime('%b %d %H:%M', time.gmtime(x['T0']))} {x['ret']:+.0%} g {x['g'] if x['g'] is None else round(x['g'], 2)}" for x in big))
