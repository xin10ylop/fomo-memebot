"""choose.py (reviewer I): choose the filter on one period alone, read it on the other. Candidates: no filter, the four bundle
caps, the causal template filter, and the template filter with each cap (10). Criterion, fixed before looking: the highest
$ a day on the choosing set; a tie (within $0.05 a day) goes to the candidate that removes fewer fires on the choosing set,
then to the looser one (no filter < higher cap < lower cap; no template < template). Then 24.34's pass criteria on the choice:
beats no-filter $/day on the fit, positive mean on each fit window, >= no-filter $/day on the recent set, win and dead no worse
than 10 and 5 points, >= 30 fit fires.   python3 data/derived/edge_check/I/choose.py > data/derived/edge_check/I/choose.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
V = c.variants(); ORDER = {n: i for i, n in enumerate(["none", "cap3.0", "cap2.0", "cap1.5", "cap1.0", "tmpl", "tmpl+cap3.0", "tmpl+cap2.0", "tmpl+cap1.5", "tmpl+cap1.0"])}
def table(pop, per, h):
    F = c.fires(pop, per); H = c.period_hours(per); out = {}
    for n, keep in V:
        k = [d for d in F if keep(d)]; out[n] = (c.stats(k, h, H), len(F) - len(k))
    return out
def pick(T):
    best = max(s["day"] for s, m in T.values())
    tied = [n for n, (s, m) in T.items() if s["day"] >= best - 0.05]
    return min(tied, key=lambda n: (T[n][1], ORDER[n]))
for pop in ("engine", "tables"):
    for h, rp in ((11, "rec"), (15, "rec"), (15, "rec+late")):
        Tf = table(pop, "fit", h); Tr = table(pop, rp, h)
        print(f"\n=== {pop}, exit h{h}, recent = {rp}")
        print(f"  {'filter':12s} {'fit $/day':>9s} {'(d)':>7s} {'fit mean':>8s} {'n':>3s}   {'rec $/day':>9s} {'(d)':>7s} {'rec mean':>8s} {'n':>3s}")
        for n, _ in V:
            sf, mf = Tf[n]; sr, mr = Tr[n]
            print(f"  {n:12s} {sf['day']:+9.2f} {sf['day'] - Tf['none'][0]['day']:+7.2f} {sf['mean']:+8.1%} {sf['n']:3d}   {sr['day']:+9.2f} {sr['day'] - Tr['none'][0]['day']:+7.2f} {sr['mean']:+8.1%} {sr['n']:3d}")
        for lab, A, B, an, bn in (("fit -> recent", Tf, Tr, "fit", rp), ("recent -> fit", Tr, Tf, rp, "fit")):
            n = pick(A); sa, sb = A[n][0], B[n][0]; na, nb = A["none"][0], B["none"][0]
            print(f"  chosen on {an}: {n:12s} {an} ${sa['day']:+.2f}/day ({sa['day'] - na['day']:+.2f}), mean {sa['mean']:+.1%} vs {na['mean']:+.1%};"
                  f"  read on {bn}: ${sb['day']:+.2f}/day ({sb['day'] - nb['day']:+.2f}), mean {sb['mean']:+.1%} vs {nb['mean']:+.1%}, {sb['n']} fires vs {nb['n']}")
        # 24.34 criteria for every candidate
        for n, keep in V:
            if n == "none": continue
            sf, sr = Tf[n][0], Tr[n][0]; bf, br = Tf["none"][0], Tr["none"][0]
            wins = [c.stats([d for d in c.fires(pop, "fit", w) if keep(d)], h, c.win_hours(w))["mean"] for w in c.FIT]
            ok = [sf["day"] > bf["day"], all(x > 0 for x in wins), sr["day"] >= br["day"] - 1e-9, sf["win"] >= bf["win"] - 0.10 and sr["win"] >= br["win"] - 0.10,
                  sf["dead"] <= bf["dead"] + 0.05 and sr["dead"] <= br["dead"] + 0.05, sf["n"] >= 30]
            if all(ok): print(f"  24.34 criteria: {n} PASSES all six (fit windows {', '.join(f'{x:+.1%}' for x in wins)})")
        print("  24.34 criteria: every candidate not listed above fails at least one")
