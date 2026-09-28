"""K1/q4_position.py: return by landing position in the seat block (first, second, third, fourth, last: G's curve on the tapes, exit
11) and by the size of the buy ahead (the first E1 buy's ETH), on the launches the engine fires at the usual view (guard ignored:
every fire, so the position is the only variable). Fit | read, counts shown; untaped fires (Sep 27 evening on) are not in here."""
import sys, os, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from k1 import *
R = load()
D = decide(R, view="k-1", slip=1.0); F = [d["r"] for d in D if d["why"] == "FILL" and d["r"].get("p1")]
def cell(v): return f"n={len(v):3d} {mean(v):+6.1%} med {st.median(v) if v else float('nan'):+6.1%} win {sum(x>0 for x in v)/max(1,len(v)):3.0%}"
print("== by position, exit 11, fires at k-1 (taped) ==")
for p, lab in (("p1", "first"), ("p2", "second"), ("p3", "third"), ("p4", "fourth"), ("plast", "last in E1")):
    print(f"  {lab:10s} fit {cell([r[p][11] for r in F if r['set']=='fit'])} | read {cell([r[p][11] for r in F if r['set']=='read'])}")
print("\n== second place by the first E1 buy's size (the buy ahead of us), exit 11 ==")
for lo, hi in ((0, 0.015), (0.015, 0.05), (0.05, 0.14), (0.14, 0.25), (0.25, 10)):
    s = [r for r in F if r["e1_buys"] and lo <= r["e1_buys"][0][0] < hi]
    print(f"  ahead {lo:5.3f}-{hi:5.3f} ETH: fit {cell([r['p2'][11] for r in s if r['set']=='fit'])} | read {cell([r['p2'][11] for r in s if r['set']=='read'])}   first place here: fit {mean([r['p1'][11] for r in s if r['set']=='fit']):+6.1%} read {mean([r['p1'][11] for r in s if r['set']=='read']):+6.1%}")
s = [r for r in F if not r["e1_buys"]]; print(f"  nobody in E1 (we would be alone): fit {cell([r['p1'][11] for r in s if r['set']=='fit'])} | read {cell([r['p1'][11] for r in s if r['set']=='read'])}")
print("\n== by the number of other buys in the seat block (the crowd that lands with us), second place, exit 11 ==")
for lo, hi in ((0, 1), (1, 2), (2, 4), (4, 7), (7, 99)):
    s = [r for r in F if lo <= len(r["e1_buys"]) < hi]
    print(f"  {lo}-{hi-1} buys: fit {cell([r['p2'][11] for r in s if r['set']=='fit'])} | read {cell([r['p2'][11] for r in s if r['set']=='read'])}")
print("\n== the whole taped population (every qualifying launch, fired or not), by position, exit 11 ==")
A = [r for r in R if r.get("p1")]
for p in ("p1", "p2", "p3", "plast"):
    print(f"  {p:6s} fit {cell([r[p][11] for r in A if r['set']=='fit'])} | read {cell([r[p][11] for r in A if r['set']=='read'])}")
