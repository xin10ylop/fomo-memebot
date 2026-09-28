"""K1/check.py: (1) decide() reproduces engine_replay's three views (fired, guard, fills, $); (2) the tape pricing (G's curve, second
place) agrees with the grid's behind1_13_h11; (3) coverage of tapes and G curves by set."""
import sys, os, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from k1 import *
R = load()
for v in ("k-2", "k-1", "k"):
    D = decide(R, view=v); s = summ(D, "all"); print(f"view {v:4s}: {fmt(s)}")
    for p in ("fit", "read"): print(f"      {p:5s}: {fmt(summ(D, p))}")
D = decide(R, view="k-1"); mism = [(d['r']['cv'][:10], d['why'], d['r']['replay_why']) for d in D if d['why'].split()[0] != (d['r']['replay_why'] or '').split()[0]]
print("disposition class mismatches vs replay (k-1 reg):", len(mism), mism[:5])
diff = [abs(r["p2"][11] - r["behind1_13_h11"]) for r in R if r.get("p2") and r["p2"][11] is not None and r.get("behind1_13_h11") is not None]
print(f"tape p2[11] vs grid behind1_13_h11: n={len(diff)} median |diff| {st.median(diff):.4f} p95 {sorted(diff)[int(.95*len(diff))]:.4f} max {max(diff):.4f}")
diff = [abs(r["p1"][11] - r["first_13_h11"]) for r in R if r.get("p1") and r["p1"][11] is not None and r.get("first_13_h11") is not None]
print(f"tape p1[11] vs grid first_13_h11: n={len(diff)} median |diff| {st.median(diff):.4f} p95 {sorted(diff)[int(.95*len(diff))]:.4f} max {max(diff):.4f}")
c = collections.Counter((r["set"], bool(r.get("tape")), r["src"]) for r in R); print("coverage (set, tape, return source):", sorted(c.items()))
c = collections.Counter((r["set"], bool(r.get("tape"))) for r in D and [d["r"] for d in D if d["why"] in ("FILL", "GUARD")]); print("fired, by tape:", sorted(c.items()))
