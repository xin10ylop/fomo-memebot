"""q7_more_fills.py (K3): more fills a day. (1) E2 (first block of the second after E1's, surcharge 0.19%) at first / second / third place,
exit 11 blocks after the E2 entry, on the gate's fires, the guard's reverts and the gate's refusals; (2) E2 entered on a read of the seat
block E1 (its buys and ETH, visible on the feed ~0.9 s before E2 opens), threshold chosen on one period and read on the other; (3) a second
seat on a filled launch (E2 after our E1 fill); (4) the value of landing one place earlier in E1 (what a finer burst step could be worth).
    python3 data/derived/edge_check/K3/q7_more_fills.py > data/derived/edge_check/K3/q7_more_fills.txt"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
X = load_dump()
pop = [x for x in X if passes_filters(x) and tape(x["cv"])]
for x in pop:
    L = tape(x["cv"]); x["E2"] = {}
    for n in (0, 1, 2):
        p = path(L, n, sec=2, hmax=15); x["E2"][n] = p["v"][11] if p else None
    x["E1"] = {n: path(L, n, hmax=15)["v"][11] for n in (0, 1)}
    x["disp7"] = engine(x, slip=0.07); x["disp25"] = engine(x, slip=0.25)
    bE2 = second_block(L, 2); x["e2_nbuy"] = sum(1 for r in L["rows"] if r["bn"] == bE2 and r["k"] == "B")
print(f"launches passing the filters with tapes: {len(pop)} (A {sum(period(x)=='A' for x in pop)}, B {sum(period(x)=='B' for x in pop)})")
print("\n1. E2 return (h11 from the E2 entry, $13) by class; E1 second place alongside")
for lab, sel in (("7% fills", lambda x: x["disp7"] == "fill"), ("7% guard reverts", lambda x: x["disp7"] == "guard"), ("gate refused", lambda x: x["disp7"] == "gate"), ("all", lambda x: True)):
    for p in ("A", "B"):
        xs = [x for x in pop if sel(x) and period(x) == p and x["E2"][0] is not None]
        print(f"  {lab:17s} {p} n={len(xs):3d}: E2 first {mean([x['E2'][0] for x in xs]):+6.1%} (win {win([x['E2'][0] for x in xs]):3.0%})  second {mean([x['E2'][1] for x in xs]):+6.1%}  third {mean([x['E2'][2] for x in xs]):+6.1%} | E1 second {mean([x['E1'][1] for x in xs]):+6.1%}  | E2 block buys median {median([x['e2_nbuy'] for x in xs])}")
print("\n2. E2 on a read of E1 (buys in the seat block >= N, or E1 ETH >= t), on the launches the E1 chain did NOT fill (7% guard), E2 at second place (pessimistic) and first;")
print("   $ at $13 (ret*13 - 0.33); threshold chosen on one period, read on the other")
cand = [("e1_nbuy", t) for t in (2, 3, 4, 5, 6, 8, 10)] + [("e1_eth", t) for t in (0.05, 0.1, 0.2, 0.3, 0.5, 0.8)]
nof = [x for x in pop if x["disp7"] != "fill" and x["E2"][1] is not None]
def usd(xs, pos): return sum(x["E2"][pos] * 13 - GAS for x in xs)
for pos in (1, 0):
    res = {}
    for c in cand:
        for p in ("A", "B"):
            xs = [x for x in nof if period(x) == p and x[c[0]] >= c[1]]; res[(c, p)] = (len(xs), mean([x["E2"][pos] for x in xs]), usd(xs, pos))
    print(f"  E2 {'second' if pos else 'first'} place:")
    for c in cand: print(f"    {c[0]} >= {c[1]:<5g}: A n={res[(c,'A')][0]:3d} {res[(c,'A')][1]:+6.1%} ${res[(c,'A')][2]:+7.2f}   B n={res[(c,'B')][0]:3d} {res[(c,'B')][1]:+6.1%} ${res[(c,'B')][2]:+7.2f}")
    for fit, read in (("A", "B"), ("B", "A")):
        best = max(cand, key=lambda c: res[(c, fit)][2]); print(f"    chosen on {fit}: {best} -> {read}: n={res[(best, read)][0]} {res[(best, read)][1]:+.1%} ${res[(best, read)][2]:+.2f}")
print("\n3. a second seat: E2 first / second place on the launches the E1 chain filled (our E1 buy of $13 moves the E2 price by < 1%, ignored)")
for p in ("A", "B"):
    xs = [x for x in pop if x["disp7"] == "fill" and period(x) == p]
    print(f"  {p} n={len(xs)}: E2 first {fmt([x['E2'][0] for x in xs], usd(xs, 0))} | second {fmt([x['E2'][1] for x in xs], usd(xs, 1))}")
print("\n4. one place earlier in E1 (what a finer step could buy if it moved the landing): fires at the usual view, guard off")
for p in ("A", "B"):
    xs = [x for x in pop if engine(x, slip=None) == "fill" and period(x) == p]
    print(f"  {p} n={len(xs)}: first {mean([x['E1'][0] for x in xs]):+.1%} vs second {mean([x['E1'][1] for x in xs]):+.1%}: {mean([x['E1'][0]-x['E1'][1] for x in xs]):+.1%} a fire")
