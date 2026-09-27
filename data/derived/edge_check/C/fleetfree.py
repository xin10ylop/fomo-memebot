"""fleetfree.py (edge_check/C): question 3. Rules that do not name or count fleets, fitted on one period and read on the other,
with 24.34's null-test discipline (permute the feature, count passes). Features knowable before the tick (from the crowd pull
and the creation second of the tape): wallets shooting by k-2, shots by k-2, relay fleets vs direct senders by k-2, the
bundle's ETH / buys / sells in the creation second, the creator's and the named template's prior launches (causal), the tier,
k. For each feature, direction and threshold (the fit's quantiles), holds 15 and 300: the fitted rule is the one with the best
$/day on the fitting period among those with enough fires (fit >= 30, recent >= 8); read on the other period. $/day is
(sum of $ over the fires / launches in the period) x 64.8 launches a day (the recent supply, 2.7 an hour), so both periods
are priced at today's supply. A pass: $/day on the reading period >= the rule's (fleets >= 2 at k-2) at the same hold, and
the fired mean above the refused mean there. Also: the rule restricted by the creator/template history.
    python3 data/derived/edge_check/C/fleetfree.py > data/derived/edge_check/C/fleetfree.txt"""
import sys, json, random
sys.path.insert(0, "data/derived/edge_check/C"); from common import *
P = [x for x in json.load(open(C + "pop.json")) if x["ret"] is not None]
for x in P: x["ret"] = {int(h): v for h, v in x["ret"].items()}
LPD = 2.7 * 24
FEATS = ["w_k2", "shots_k2", "relay_k2", "direct_k2", "bundle_eth", "bundle_buys", "bundle_sells_creation", "creator_prior", "named_prior", "tier", "k"]
per = {"fit": [x for x in P if x["set"] == "fit"], "rec": [x for x in P if x["set"] == "rec"]}
def score(pop, sel, h):
    f = [x for x, s in zip(pop, sel) if s]; r = [x for x, s in zip(pop, sel) if not s]
    if not f: return 0, float("nan"), float("nan"), 0.0
    u = sum(usd(x["ret"][h]) for x in f) / len(pop) * LPD
    return len(f), mean([x["ret"][h] for x in f]), mean([x["ret"][h] for x in f]) - (mean([x["ret"][h] for x in r]) if r else 0), u
def cands(pop, key):
    vals = sorted(x[key] for x in pop); qs = sorted({vals[int(q * (len(vals) - 1))] for q in [i / 20 for i in range(1, 20)]})
    for t in qs:
        yield (">=", t, [x[key] >= t for x in pop])
        yield ("<=", t, [x[key] <= t for x in pop])
def fit_read(key, h, src, dst, vals_src=None, vals_dst=None, minf=None):
    ps, pd = per[src], per[dst]
    vs = vals_src if vals_src is not None else [x[key] for x in ps]; vd = vals_dst if vals_dst is not None else [x[key] for x in pd]
    Ps = [dict(x, **{key: v}) for x, v in zip(ps, vs)] if vals_src is not None else ps
    Pd = [dict(x, **{key: v}) for x, v in zip(pd, vd)] if vals_dst is not None else pd
    minf = minf or (30 if src == "fit" else 8); best = None
    for op, t, sel in cands(Ps, key):
        n, m, lift, u = score(Ps, sel, h)
        if n < minf: continue
        if best is None or u > best[0]: best = (u, op, t, n, m, lift)
    if best is None: return None
    u, op, t, n, m, lift = best
    seld = [(x[key] >= t) if op == ">=" else (x[key] <= t) for x in Pd]
    return (op, t, n, m, lift, u) + score(Pd, seld, h)
rule = {}
for h in (15, 300):
    for p in ("fit", "rec"):
        rule[(p, h)] = score(per[p], [x["f_k2"] >= 2 for x in per[p]], h)
print("the rule (fleets >= 2 at k-2) at today's supply:")
for (p, h), (n, m, lift, u) in sorted(rule.items()):
    print(f"  {p:3s} h{h:3d}  fires {n:3d}  mean {m:+6.1%}  lift {lift:+6.1%}  $/day {u:+6.1f}")
random.seed(5); NPERM = 300; summary = []
for src, dst in (("fit", "rec"), ("rec", "fit")):
    print(f"\n=== fitted on {src}, read on {dst}")
    for h in (15, 300):
        base = rule[(dst, h)]
        for key in FEATS:
            r = fit_read(key, h, src, dst)
            if r is None: continue
            op, t, n, m, lift, u, n2, m2, lift2, u2 = r
            ok = u2 >= base[3] and lift2 > 0
            # null: permute the feature within each period, refit, read; count passes
            passes = 0
            for _ in range(NPERM):
                vs = [x[key] for x in per[src]]; random.shuffle(vs); vd = [x[key] for x in per[dst]]; random.shuffle(vd)
                q = fit_read(key, h, src, dst, vs, vd)
                if q and q[9] >= base[3] and q[8] > 0: passes += 1
            summary.append((src, h, key, ok, passes / NPERM))
            print(f"  h{h:3d} {key:22s} {op} {t:<8.4g} {src}: {n:3d} fires {m:+6.1%} lift {lift:+6.1%} ${u:+6.1f}/d  | {dst}: {n2:3d} fires {m2:+6.1%} lift {lift2:+6.1%} ${u2:+6.1f}/d"
                  f"  (rule {base[3]:+.1f})  {'PASS' if ok else 'fail'}  null pass rate {passes/NPERM:.0%}")
print("\nsummary: passes by direction and hold (real) against the permuted features' mean pass rate")
for src in ("fit", "rec"):
    for h in (15, 300):
        s = [x for x in summary if x[0] == src and x[1] == h]
        print(f"  fitted on {src}, h{h}: real passes {sum(x[3] for x in s)}/{len(s)}  permuted mean pass rate {mean([x[4] for x in s]):.0%}")
print("\n=== the rule restricted by history (the creator's or the named template's prior launches in this population, causal)")
for h in (15, 300):
    for lbl, f in (("rule", lambda x: x["f_k2"] >= 2), ("rule, template prior <= 2", lambda x: x["f_k2"] >= 2 and x["named_prior"] <= 2),
                   ("rule, template prior 0", lambda x: x["f_k2"] >= 2 and x["named_prior"] == 0), ("rule, template prior >= 3", lambda x: x["f_k2"] >= 2 and x["named_prior"] >= 3),
                   ("rule, creator prior 0", lambda x: x["f_k2"] >= 2 and x["creator_prior"] == 0)):
        cells = []
        for p in ("fit", "rec"):
            n, m, lift, u = score(per[p], [f(x) for x in per[p]], h); cells.append(f"{p} {n:3d} fires {m:+6.1%} ${u:+6.1f}/d")
        print(f"  h{h:3d} {lbl:28s} " + "   ".join(cells))
