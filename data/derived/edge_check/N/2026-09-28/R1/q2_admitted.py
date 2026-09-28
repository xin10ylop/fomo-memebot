"""Q2: the guard-admitted class (the seat block's tokens 7-20% under the build's sizing at second place). Today's fires since 12:27
at the three views, the class on the week by period, and the class's own sequential test on the live fills."""
import sys, time; sys.path.insert(0, "."); from common import *
V = {v: load_view(v) for v in ("k2", "k1reg", "kreg")}
print("fires since 12:27 at any view (the replay prices second place; g = seat tokens / build tokens):")
cvs = sorted({cv for v in V.values() for cv, r in v.items() if r.get("fired") and r["T0"] >= SWITCH}, key=lambda c: V["k1reg"][c]["T0"])
for cv in cvs:
    r = V["k1reg"][cv]; g = r.get("guard_ratio"); cls = "7% fill" if g is None or g >= 0.93 else ("ADMITTED" if g >= 0.80 else "revert at 20%")
    print(f"  {time.strftime('%H:%M', time.gmtime(r['T0']))} {cv[:10]} views {' '.join(v for v in V if V[v][cv].get('fired'))}  g {g if g is None else round(g, 3)}  {cls}  h11 {r['ret']['11']:+.1%}")
print("\nthe admitted class on the week, usual view (fires with 0.80 <= g < 0.93), h11 at second place:")
for p in ("fit", "read"):
    for lo, hi, lab in ((0.93, 9, "g >= 0.93 (fills at 7%)"), (0.80, 0.93, "0.80-0.93 (admitted)"), (0.85, 0.93, "  of which 0.85-0.93"), (0.80, 0.85, "  of which 0.80-0.85"), (0, 0.80, "g < 0.80 (reverts at 20%)")):
        xs = [r for r in V["k1reg"].values() if r.get("fired") and period(r["T0"]) == p and r.get("guard_ratio") is not None and lo <= r["guard_ratio"] < hi and r["ret"]["11"] is not None]
        v = [r["ret"]["11"] for r in xs]
        print(f"  {p:4s} {lab:28s} n={len(v):3d} mean {st.mean(v) if v else float('nan'):+6.1%} median {st.median(v) if v else float('nan'):+6.1%} win {sum(x > 0 for x in v) / max(len(v), 1):3.0%}  ${sum(x * STAKE - GAS for x in v):+7.2f}")
# the admitted class's sequential test (H0 +2.5%, H1 +19%, sd 0.34, bounds +-2.94) on the live admitted fills: today's 15:36 only
def llr(xs, m0=0.025, m1=0.19, sd=0.34): return sum(((x - m0) ** 2 - (x - m1) ** 2) / (2 * sd * sd) for x in xs)
live = [-0.071]
print(f"\nlive admitted fills so far: {len(live)} ({', '.join(f'{x:+.1%}' for x in live)}); class LLR {llr(live):+.2f} (bounds +-2.94)")
print(f"one more fill at -7% moves it by {llr([-0.07]):+.2f}; at the read mean of the class the upper bound needs about {2.94 / llr([0.20]):.0f} fills")
print("the rollback rule (5y 1): back to 0.15 if most of the first ten admitted fills land last in the seat block or later; today 1 of 10 (index 4 of 5+ buys, not last)")
