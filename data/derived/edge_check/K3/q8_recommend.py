"""q8_recommend.py (K3): the one change, BURST_SLIP 0.07 -> 0.20, stress-tested: by day, by view, by hold, without the largest winners,
bootstrap of the gain, landing-position mixes (tapes), and the sequential test's expected length.
    python3 data/derived/edge_check/K3/q8_recommend.py > data/derived/edge_check/K3/q8_recommend.txt"""
import sys, os, random; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
X = load_dump(); NEW = 0.20
def outcome(x, slip, h=11, view="k-1", reg=1):
    d = engine(x, slip=slip, view=view, reg=reg)
    return (ret(x, h) * 13 - GAS) if d == "fill" else (-GAS if d == "guard" else 0.0), d
print("1. by day, usual view, h11: bursts / fills / $ at 7% and at 20%; gain")
days = sorted(set(x["day"] for x in X), key=lambda d: int(d.split()[1]))
for d in days:
    xs = [x for x in X if x["day"] == d]; a = [outcome(x, 0.07) for x in xs]; b = [outcome(x, NEW) for x in xs]
    fa = [x for x, o in zip(xs, a) if o[1] == "fill"]; fb = [x for x, o in zip(xs, b) if o[1] == "fill"]
    print(f"  {d}: bursts {sum(o[1] in ('fill','guard') for o in a):3d}  7%: fills {len(fa):3d} ${sum(o[0] for o in a):+7.2f}   20%: fills {len(fb):3d} mean {mean([ret(x) for x in fb]):+6.1%} ${sum(o[0] for o in b):+7.2f}   gain ${sum(o[0] for o in b)-sum(o[0] for o in a):+6.2f}")
print("\n2. the gain (20% minus 7%) by period, view and hold")
for view, reg in (("k-2", 0), ("k-1", 1), ("k", 1)):
    for h in (9, 11, 13, 15):
        cells = []
        for p in ("A", "B"):
            xs = [x for x in X if period(x) == p]; g = sum(outcome(x, NEW, h, view, reg)[0] - outcome(x, 0.07, h, view, reg)[0] for x in xs)
            cells.append(f"{p} ${g:+7.2f}")
        print(f"  view {view} reg{reg} h{h:<2d}: " + "  ".join(cells))
print("\n3. the switched bursts (reverted at 7%, filled at 20%): each pays ret*13 (the gas is spent either way)")
for p in ("A", "B", "Sep 26-28"):
    xs = [x for x in X if (period(x) == p if p != "Sep 26-28" else x["day"] in ("Sep 26", "Sep 27", "Sep 28")) and engine(x, slip=0.07) == "guard" and engine(x, slip=NEW) == "fill"]
    g = [ret(x) * 13 for x in xs]; s = sorted(g, reverse=True)
    lo, hi = boot_ci(g, stat=sum) if len(g) > 1 else (float('nan'), float('nan'))
    print(f"  {p}: {fmt([ret(x) for x in xs], sum(g))}  bootstrap 95% of the $ gain [{lo:+.2f}, {hi:+.2f}], P(gain > 0) {boot_p_pos(g):.3f}; without the largest {s[0] if s else 0:+.2f}: ${sum(s[1:]):+.2f}; without the two largest ${sum(s[2:]):+.2f}")
print("\n4. landing-position mixes (tapes; fires at the usual view): $ per period at 7% and 20%")
fired = [x for x in X if engine(x, slip=None) == "fill" and tape(x["cv"])]
POS = {"first": 0, "second": 1, "third": 2, "fifth": 4, "last": 10 ** 6}
for x in fired:
    L = tape(x["cv"]); x["pos"] = {nm: (lambda p: (p["tk"], p["v"][11]))(path(L, n, hmax=15)) for nm, n in POS.items()}
MIX = {"live Sep 26-28 (first 1/2, second 1/3, last 1/6)": {"first": 1/2, "second": 1/3, "last": 1/6}, "even (first, second, third, last 1/4 each)": {"first": .25, "second": .25, "third": .25, "last": .25},
       "deep (second .2, third .3, fifth .2, last .3)": {"second": .2, "third": .3, "fifth": .2, "last": .3}, "always last": {"last": 1.0}}
for nm, w in MIX.items():
    cells = []
    for p in ("A", "B"):
        xs = [x for x in fired if period(x) == p]
        def usd(s): return sum(wt * sum(((x["pos"][q][1] * 13 - GAS) if x["pos"][q][0] >= (1 - s) * x["tk_build"] else -GAS) for x in xs) for q, wt in w.items())
        cells.append(f"{p} (n={len(xs)}): 7% ${usd(0.07):+7.2f}  20% ${usd(NEW):+7.2f}  gain ${usd(NEW)-usd(0.07):+6.2f}")
    print(f"  {nm:50s} " + "   ".join(cells))
print("\n5. $ a day on the Sep 24-28 supply (B, 4.40 days), usual view: 7% vs 20%")
xs = [x for x in X if period(x) == "B"]; a = sum(outcome(x, 0.07)[0] for x in xs); b = sum(outcome(x, NEW)[0] for x in xs)
fb = [x for x in xs if engine(x, slip=NEW) == "fill"]; fa = [x for x in xs if engine(x, slip=0.07) == "fill"]
print(f"  7%: {len(fa)} fills ({len(fa)/DAYS_B:.1f}/day) ${a:+.2f} (${a/DAYS_B:+.2f}/day);  20%: {len(fb)} fills ({len(fb)/DAYS_B:.1f}/day) mean {mean([ret(x) for x in fb]):+.1%} ${b:+.2f} (${b/DAYS_B:+.2f}/day); gain ${(b-a)/DAYS_B:+.2f}/day")
print("\n6. the sequential test (H0 +2.5%, H1 +19%, sd 0.34, bounds +-2.94): expected fills to a boundary at a true mean mu")
m0, m1, s = 0.025, 0.19, 0.34
for mu in (0.0, 0.025, 0.079, 0.1075, 0.126, 0.14, 0.19, 0.20):
    d = (mu * (m1 - m0) - (m1 ** 2 - m0 ** 2) / 2) / s ** 2
    print(f"  mu {mu:+.1%}: drift {d:+.4f} a fill -> " + (f"~{2.94/abs(d):.0f} fills to the {'upper' if d > 0 else 'lower'} bound" if abs(d) > 1e-4 else "no drift (never decides in expectation)"))
