"""K1/q2_filters.py: which pre-gate filters earn their keep. Each filter switched off alone (every other setting live), view k-1 with
registration, exit 11, $13; the launches it lets through are priced by the same chain (crowd gate, guard). Shown at the live guard
(7%) and at a 20% guard (q1's candidate), fit (Sep 21 09:40 - Sep 23) and read (Sep 24 - Sep 28 09:40)."""
import sys, os, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from k1 import *
R = load()
print("population: tier range already 100-200 bps on all 632 (the tables' rule), bundle >= 0.3 ETH on all 632, creator buy > 2 ETH on 0:")
print("  so the tier, bundle-floor and creator-buy-cap filters remove nothing here and cannot be tested on disk.\n")
for slip in (0.07, 0.20):
    base = decide(R, view="k-1", slip=slip); bs = {p: summ(base, p) for p in ("fit", "read")}
    print(f"== guard {slip:.2f}: live settings  fit {fmt(bs['fit'])} | read {fmt(bs['read'])}")
    for f, lab in (("supply", "creator supply >= 1%"), ("repeat", "creator's first launch of the day"), ("nb", "bundle >= 3 buyers"), ("cap", "bundle <= 3.0 ETH")):
        D = decide(R, view="k-1", slip=slip, F={f: False}); b0 = {d["r"]["cv"]: d for d in base}
        new = [d for d in D if d["why"] in ("FILL", "GUARD") and b0[d["r"]["cv"]]["why"] not in ("FILL", "GUARD")]
        lost = [d for d in D if d["why"] not in ("FILL", "GUARD") and b0[d["r"]["cv"]]["why"] in ("FILL", "GUARD")]   # (busy-gate knock-ons)
        line = []
        for p in ("fit", "read"):
            s = summ(D, p); nn = [d for d in new if d["r"]["set"] == p]; nf = [d["ret"] for d in nn if d["why"] == "FILL"]
            line.append(f"{p}: +{len(nn)} fires, {len(nf)} fills {mean(nf):+6.1%} (med {st.median(nf) if nf else float('nan'):+6.1%}), filter's value ${bs[p]['usd'] - s['usd']:+6.2f}")
        allrm = [r for r in R if (f == "supply" and r["tk0"] and r["tk0"] < 0.01 * Y0) or (f == "repeat" and r["repeat"]) or (f == "nb" and r["nb"] < 3) or (f == "cap" and r["bundle"] > 3.0)]
        v = {p: [r2(x, 11) for x in allrm if x["set"] == p and r2(x, 11) is not None] for p in ("fit", "read")}
        print(f"  off: {lab:34s} removes {len(allrm):3d} (all, 2nd place h11: fit {len(v['fit'])} {mean(v['fit']):+6.1%}, read {len(v['read'])} {mean(v['read']):+6.1%}) | " + " | ".join(line) + (f" | knock-on lost {len(lost)}" if lost else ""))
    print()
# the creator-supply filter at other floors: the population's creator buys cluster at 0.1%, 0.29%, 0.5%, 1%, 1.5%, 2%, 3%, 5%
print("== the creator-supply floor swept (guard 0.07 | guard 0.20), $ fit / $ read ==")
import copy
for fl in (0.0, 0.001, 0.002, 0.005, 0.01, 0.015, 0.02, 0.03):
    out = []
    for slip in (0.07, 0.20):
        RR = [dict(r, tk0=(r["tk0"] if r["tk0"] >= fl * Y0 else 0.5 * 0.01 * Y0)) if r["tk0"] else r for r in R]   # below the floor -> mark as < 1% for decide()
        if fl < 0.01: RR = [dict(r, tk0=(max(r["tk0"], 0.01 * Y0) if r["tk0"] >= fl * Y0 else 0.5 * 0.01 * Y0)) if r["tk0"] else r for r in R]
        D = decide(RR, view="k-1", slip=slip); a, b = summ(D, "fit"), summ(D, "read"); out.append(f"fired {a['fired']:3d}/{b['fired']:3d} fills {a['fills']:3d}/{b['fills']:3d} ${a['usd']:+7.2f}/${b['usd']:+7.2f}")
    print(f"  floor {fl:5.3f}: guard .07 {out[0]} | guard .20 {out[1]}")
