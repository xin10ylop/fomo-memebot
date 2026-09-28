"""K1/q3_gate.py: the crowd gate. ATTACK_MIN 1-4 at each view (k-2 without the registration block = floor, k-1 with it = usual,
k with it = ceiling; plus k-2 with and k-1 without); then other signals at the usual view as a second condition or a replacement:
wallets, curve-aimed transactions, growth k-2 -> k-1, fleets at k vs k-1, bundle ETH, named wallets, k, hour. Each threshold is
chosen on one half and read on the other. Exit 11, $13, gas $0.33; guard 7% (live) and 20% (q1)."""
import sys, os, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from k1 import *
R = load()
def at(c, j): return c[j] if 0 <= j < len(c) else 0
for slip in (0.07, 0.20):
    print(f"== guard {slip:.2f}: ATTACK_MIN by view   (fit | read)")
    for v in ("k-2", "k-2r", "k-1n", "k-1", "k"):
        for a in (1, 2, 3, 4):
            D = decide(R, view=v, amin=a, slip=slip); print(f"  {v:5s} >= {a}: fit {fmt(summ(D, 'fit'))} | read {fmt(summ(D, 'read'))}")
    print()
# alternative / extra conditions at the usual view, fleets >= 2 kept unless 'replace'
def feats(r):
    k = r["k"]; return {"wallets@k-1": at(r["cw"], k - 1), "txs@k-1": sum(r["ntx"][: k]), "growth k-2->k-1": r["f_k1r"] - r["f_k2n"], "fleets k minus k-1": r["f_k0r"] - r["f_k1r"],
                        "fleets@k-1": r["f_k1r"], "bundle ETH": r["bundle"], "named wallets": r["n_named"], "k (blocks in 2nd 0)": k, "hour UTC": r["hour"], "tier bps": r["tier_bps"],
                        "creator supply %": (r["tk0"] or 0) / 1e7}
FN = list(feats(R[0]).keys())
for slip in (0.07, 0.20):
    base = decide(R, view="k-1", slip=slip); B = {p: summ(base, p)["usd"] for p in ("fit", "read")}
    print(f"== guard {slip:.2f}: an extra condition on top of fleets>=2 @k-1 (live: fit ${B['fit']:+.2f}, read ${B['read']:+.2f}); threshold chosen on one half, read on the other")
    for fn in FN:
        vals = sorted(set(feats(r)[fn] for r in R))
        qs = sorted(set(vals[int(i * (len(vals) - 1) / 12)] for i in range(13)))
        best = {}
        for side in (">=", "<="):
            for q in qs:
                cond = (lambda r, q=q, side=side: (feats(r)[fn] >= q) if side == ">=" else (feats(r)[fn] <= q))
                D = decide(R, view="k-1", slip=slip, fire_fn=lambda r, c=cond: r["f_k1r"] >= 2 and c(r))
                s = {p: summ(D, p) for p in ("fit", "read")}
                for p in ("fit", "read"):
                    if p not in best or s[p]["usd"] > best[p][0]: best[p] = (s[p]["usd"], side, q, s)
        f_, r_ = best["fit"], best["read"]
        print(f"  {fn:22s} chosen on fit: {f_[1]}{f_[2]:<6g} fit ${f_[0]:+7.2f} -> read ${f_[3]['read']['usd']:+7.2f} ({f_[3]['read']['fills']} fills, live ${B['read']:+.2f}) | "
              f"chosen on read: {r_[1]}{r_[2]:<6g} read ${r_[0]:+7.2f} -> fit ${r_[3]['fit']['usd']:+7.2f} ({r_[3]['fit']['fills']} fills, live ${B['fit']:+.2f})")
    print()
