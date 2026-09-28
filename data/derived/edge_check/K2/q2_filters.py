"""K2/q2_filters.py: each pre-gate filter switched off alone; the launches it alone was removing, taken through the rest of the chain
(fleets at the usual view, guard, second place h11, $13, gas on every burst). Also the marginal launches' return with no guard, so
the filter's worth does not hide behind the guard. Fit Sep 21-23 / read Sep 24-28."""
import os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from sim import *
FILT = [("creator supply < 1%", dict(supply=False)), ("creator buy > 2 ETH", dict(crebuy=False)), ("creator repeat", dict(repeat=False)),
        ("bundle count < 3", dict(nbmin=0)), ("bundle cap > 3.0 ETH", dict(bmax=0)), ("tier 100-200 bps", dict(tier=None)), ("bundle floor 0.3 ETH", dict(bmin=0))]
for slip in (0.07, 0.15):
    print(f"\n==== guard slip {slip:.2f} ====")
    base = run(slip=slip); bf = {r["x"]["cv"]: r for r in base}
    for per in ("fit", "read"):
        s = summ(base, per); print(f"  base [{per}]: fired {s['fired']} fills {s['fills']} ${s['usd']:+.2f} ({s['usd_day']:+.2f}/d)")
    for lab, kw in FILT:
        res = run(slip=slip, **kw)
        removed = sum(1 for r in base if r["why"] and r["why"].startswith("PRE") and lab.split()[0] in r["why"]) 
        cells = []
        for per in ("fit", "read"):
            add = [r for r in res if period(r["x"]) == per and r.get("fired") and not bf[r["x"]["cv"]].get("fired")]
            lost = [r for r in res if period(r["x"]) == per and not r.get("fired") and bf[r["x"]["cv"]].get("fired")]
            fl = [r["ret"] for r in add if r.get("fill")]; noguard = [r["x"]["behind1_13_h11"] for r in add]
            d = summ(res, per)["usd"] - summ(base, per)["usd"]
            cells.append(f"{per}: +{len(add)} fires (-{len(lost)}), {len(fl)} fills mean {mean(fl):+6.1%}, all fires at 2nd {mean(noguard):+6.1%}, d$ {d:+7.2f} ({d/HOURS[per]*24:+5.2f}/d)")
        print(f"  off: {lab:22s} | " + " | ".join(cells))
# how many launches each filter touches (alone or with others), by period
print("\n==== launches each filter flags (any, not only first) ====")
for per in ("fit", "read"):
    rs = [x for x in T if period(x) == per]
    print(f"  {per}: n {len(rs)}; supply<1% {sum(1 for x in rs if x['tk0'] is not None and x['tk0'] < 0.01*Y0)}, creator buy>2 {sum(1 for x in rs if (x['init_buy_eth'] or 0) > 2)}, repeat {sum(1 for x in rs if x['repeat']>0)}, bundle count<3 {sum(1 for x in rs if x['nb']<3)}, cap {sum(1 for x in rs if x['bundle']>3)}, tier out {sum(1 for x in rs if not 100<=x['tb']<=200)}, floor {sum(1 for x in rs if x['bundle']<0.3)}")
# the creator-supply filter at other thresholds (the launches between), all else live, slip 7% and 15%
print("\n==== creator-supply threshold swept (tk0 share of supply) ====")
for thr in (0.0, 0.002, 0.005, 0.01, 0.02, 0.03, 0.05):
    ex = (lambda t: (lambda x: "PRE supply thr" if (x["tk0"] is not None and x["tk0"] < t * Y0) else None))(thr)
    c = []
    for slip in (0.07, 0.15):
        res = run(supply=False, extra=ex, slip=slip); a, b = summ(res, "fit"), summ(res, "read")
        c.append(f"slip {slip:.2f}: fit {a['fired']:3d} fires ${a['usd']:+7.2f} | read {b['fired']:3d} fires ${b['usd']:+7.2f} ({b['usd_day']:+5.2f}/d)")
    print(f"  tk0 >= {thr:5.3f}: " + "  ||  ".join(c))
