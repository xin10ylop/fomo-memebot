"""K1/q7_more.py: more fills. (a) E2 (the first block of the second after E1's, surcharge 0.19%) in place of E1 on the usual view's
fires; (b) E2 as a second try after the guard reverts E1; (c) E2 on launches the crowd gate refuses, gated on what the seat block
(E1, on the feed ~1 s before E2's tick) showed: its buys and their ETH; (d) a later block of E1's own second (E1+1..3, first place
and behind one); exits 11 blocks after the entry, $13, gas $0.33 a burst, second place unless noted. Thresholds chosen on one half,
read on the other. Taped launches only (Sep 21 09:40 - Sep 27 ~18:00)."""
import sys, os, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from k1 import *
R = load(); T = [r for r in R if r.get("p2")]
def cell(v): return f"n={len(v):3d} {mean(v):+6.1%} med {st.median(v) if v else float('nan'):+6.1%} win {sum(x>0 for x in v)/max(1,len(v)):3.0%} ${sum(x*STAKE-GAS for x in v):+7.2f}"
def ok(r, key, h=11): p = r.get(key); return p is not None and len(p) > h and p[h] is not None
D = decide(T, view="k-1", slip=1.0); fires = [d["r"] for d in D if d["why"] == "FILL"]
D7 = {d["r"]["cv"]: d["why"] for d in decide(T, view="k-1", slip=0.07)}
print("== (a) the usual view's fires (all, guard ignored): E1 vs E2 ==")
for key, lab in (("p1", "E1 first"), ("p2", "E1 second"), ("e2p1", "E2 first"), ("e2p2", "E2 second")):
    print(f"  {lab:10s} fit {cell([r[key][11] for r in fires if r['set']=='fit' and ok(r, key)])} | read {cell([r[key][11] for r in fires if r['set']=='read' and ok(r, key)])}")
print("\n== (b) E2 as a second try when the 7% guard reverts E1 (second place in E2) ==")
g = [r for r in fires if D7[r["cv"]] == "GUARD"]
for key, lab in (("e2p1", "E2 first"), ("e2p2", "E2 second"), ("p2", "(E1 second, had it filled)")):
    print(f"  {lab:26s} fit {cell([r[key][11] for r in g if r['set']=='fit' and ok(r, key)])} | read {cell([r[key][11] for r in g if r['set']=='read' and ok(r, key)])}")
print("\n== (c) E2 on the launches refused at the crowd gate (pre-gate filters passed), gated on the seat block ==")
G = [d["r"] for d in decide(T, view="k-1", slip=1.0, fire_fn=lambda r: True) if d["why"] == "FILL" and d["r"]["f_k1r"] < 2 and ok(d["r"], "e2p2")]
print(f"  every refused launch, E2 second: fit {cell([r['e2p2'][11] for r in G if r['set']=='fit'])} | read {cell([r['e2p2'][11] for r in G if r['set']=='read'])}")
feats = {"E1 buys": lambda r: len(r["e1_buys"]), "E1 buy ETH": lambda r: sum(x[0] for x in r["e1_buys"]), "fleets incl. E1 block": lambda r: r["f_kp1r"]}
for fn, f in feats.items():
    vals = sorted(set(f(r) for r in G)); qs = sorted(set(vals[int(i * (len(vals) - 1) / 15)] for i in range(16)))
    sc = []
    for q in qs:
        s = {p: [r["e2p2"][11] for r in G if r["set"] == p and f(r) >= q] for p in ("fit", "read")}
        sc.append((q, sum(x * STAKE - GAS for x in s["fit"]), sum(x * STAKE - GAS for x in s["read"]), s))
    bf = max(sc, key=lambda x: x[1]); br = max(sc, key=lambda x: x[2])
    print(f"  {fn:22s} >= {bf[0]:<7.4g} chosen on fit: fit {cell(bf[3]['fit'])} -> read {cell(bf[3]['read'])}")
    print(f"  {'':22s} >= {br[0]:<7.4g} chosen on read: read {cell(br[3]['read'])} -> fit {cell(br[3]['fit'])}")
print("\n== (c2) the same for the usual view's fires: E2 gated on the seat block (as a replacement for E1) ==")
for fn, f in feats.items():
    vals = sorted(set(f(r) for r in fires)); qs = sorted(set(vals[int(i * (len(vals) - 1) / 15)] for i in range(16)))
    sc = []
    for q in qs:
        s = {p: [r["e2p2"][11] for r in fires if r["set"] == p and ok(r, "e2p2") and f(r) >= q] for p in ("fit", "read")}
        sc.append((q, sum(x * STAKE - GAS for x in s["fit"]), sum(x * STAKE - GAS for x in s["read"]), s))
    bf = max(sc, key=lambda x: x[1]); br = max(sc, key=lambda x: x[2])
    print(f"  {fn:22s} >= {bf[0]:<7.4g} chosen on fit: fit {cell(bf[3]['fit'])} -> read {cell(bf[3]['read'])} | >= {br[0]:<7.4g} chosen on read: read {cell(br[3]['read'])} -> fit {cell(br[3]['fit'])}")
print("\n== (d) a later block of E1's second (a second seat), the usual view's fires ==")
for j in (1, 2, 3):
    for key, lab in ((f"e1p{j}", f"E1+{j} first"), (f"e1b{j}", f"E1+{j} behind one")):
        print(f"  {lab:16s} fit {cell([r[key][11] for r in fires if r['set']=='fit' and ok(r, key)])} | read {cell([r[key][11] for r in fires if r['set']=='read' and ok(r, key)])}")
print("\n(e) launches outside the tables' rule (bundle < 0.3 ETH, 1% tier): none are in the population files, crowd files or tapes on disk -> not testable here.")
