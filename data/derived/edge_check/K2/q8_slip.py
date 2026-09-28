"""K2/q8_slip.py: the one recommendation, BURST_SLIP, tested end to end. (1) the replay's convention (every burst lands second in
E1): finer sweep, chosen on fit and read on read and the reverse, by day, the gain's bootstrap and without its largest fill;
(2) the landing mix of the live bursts (Sep 26-28: first 3, second 3, last 1, first in E1+2 after a sequencer hold 1, of 8 that
landed) on the taped fires, the guard checked where the burst lands, so the looser guard pays for the deep and late landings it
lets through; (3) the worst case (every burst lands last or late)."""
import os, sys, json, gzip, random, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from sim import *
import price_tapes as PT
SLIPS = (0.05, 0.07, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 1.0)
print("== (1) the replay's convention: second place, all 129 usual-view fires ==")
R = {s: run(slip=s) for s in SLIPS}
for s in SLIPS:
    a, b = summ(R[s], "fit"), summ(R[s], "read")
    print(f"  slip {s:4.2f}: fit {a['fills']:3d}/{a['fired']} ${a['usd']:+7.2f} ({a['usd_day']:+6.2f}/d) | read {b['fills']:3d}/{b['fired']} ${b['usd']:+7.2f} ({b['usd_day']:+6.2f}/d)")
for per, other in (("fit", "read"), ("read", "fit")):
    best = max(SLIPS, key=lambda s: summ(R[s], per)["usd"])
    print(f"  chosen on {per}: slip {best:.2f}; on {other} ${summ(R[best], other)['usd']:+.2f} against ${summ(R[0.07], other)['usd']:+.2f} at 0.07")
base = {r["x"]["cv"]: r for r in R[0.07]}
for s in (0.15, 0.20):
    new = [r for r in R[s] if r.get("fill") and not base[r["x"]["cv"]].get("fill")]
    print(f"\n  slip {s:.2f} vs 0.07: {len(new)} bursts fill instead of reverting")
    for per in ("fit", "read"):
        v = [r["ret"] for r in new if period(r["x"]) == per]; lo, hi = boot_ci(v)
        top = sorted(v)[-1] if v else 0
        print(f"    {per}: n {len(v)} mean {mean(v):+.1%} (95% {lo:+.1%}..{hi:+.1%}), median {sorted(v)[len(v)//2]:+.1%}, win {sum(a>0 for a in v)/len(v):.0%}; gain ${sum(a*13 for a in v):+.2f} ({sum(a*13 for a in v)/HOURS[per]*24:+.2f}/d); without the largest ({top:+.0%}) ${sum(a*13 for a in v)-top*13:+.2f}")
    byday = collections.defaultdict(float)
    for r in new: byday[r["x"]["day"]] += r["ret"] * 13
    print("    gain by day: " + ", ".join(f"{d} {v:+.2f}" for d, v in sorted(byday.items(), key=lambda z: time.strptime(z[0] + ' 2026', '%b %d %Y'))))
# (2) the landing mix
F = [r["x"] for r in run(guard=False) if r.get("fired") and r["x"]["cv"] in PT.TAPES]
def outcome(x, scen, slip):
    L = PT.TAPES[x["cv"]]; ts = L["ts"]; bE1 = L["b0"] + x["k"] + 1
    blk, na = {"first": (bE1, 0), "second": (bE1, 1), "third": (bE1, 2), "last": (bE1, 10 ** 6), "late2": (bE1 + 2, 0), "late5": (bE1 + 5, 0)}[scen]
    if ts.get(blk, 0) != L["T0"] + 1: return -0.33
    vals, tk, g = PT.path(L, 13.0, blk, na, (11,))
    if x["tk_build"] and tk < (1 - slip) * x["tk_build"]: return -0.33
    return vals[11] * 13 - 0.33
cache = {(x["cv"], sc, s): outcome(x, sc, s) for x in F for sc in ("first", "second", "third", "last", "late2", "late5") for s in SLIPS}
MIX = {"live mix (first 3/8, second 3/8, last 1/8, E1+2 1/8)": {"first": 3/8, "second": 3/8, "last": 1/8, "late2": 1/8},
       "deeper mix (first 1/4, second 1/4, third 1/4, last 1/8, E1+5 1/8)": {"first": .25, "second": .25, "third": .25, "last": .125, "late5": .125},
       "worst: last 1/2, E1+2 1/4, E1+5 1/4": {"last": .5, "late2": .25, "late5": .25}}
for lab, mix in MIX.items():
    print(f"\n== (2) {lab}: expected $ per fire and per day (taped fires; the day rate uses the period's fires a day at the usual view) ==")
    res = {}
    for s in SLIPS:
        c = []
        for per in ("fit", "read"):
            sub = [x for x in F if period(x) == per]; pf = mean([sum(w * cache[(x["cv"], sc, s)] for sc, w in mix.items()) for x in sub])
            res[(s, per)] = pf; c.append(f"{per} ${pf:+.3f}/fire ${pf * summ(R[0.07], per)['fires_day']:+6.2f}/d")
        print(f"  slip {s:4.2f}: " + " | ".join(c))
    for per, other in (("fit", "read"), ("read", "fit")):
        best = max(SLIPS, key=lambda s: res[(s, per)])
        print(f"  chosen on {per}: {best:.2f}; on {other}: ${res[(best, other)]:+.3f}/fire vs ${res[(0.07, other)]:+.3f} at 0.07 ({(res[(best, other)] - res[(0.07, other)]) * summ(R[0.07], other)['fires_day']:+.2f}/d); 0.15 on {other}: {(res[(0.15, other)] - res[(0.07, other)]) * summ(R[0.07], other)['fires_day']:+.2f}/d")
