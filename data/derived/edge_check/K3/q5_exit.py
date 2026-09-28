"""q5_exit.py (K3): exit rules against the fixed hold, second place, $13, on the engine's fills (usual view) with tapes. Every rule reads the
curve as the feed shows it at block E1+h and its sell lands LAG blocks later (LAG 2, and 3 as a check); a rule that never triggers sells
where the live setting lands (E1+11). Parameters chosen on one period, read on the other. Two fill sets: the live 7% guard (55 with tapes)
and the 25% guard (101 with tapes).
    python3 data/derived/edge_check/K3/q5_exit.py > data/derived/edge_check/K3/q5_exit.txt"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
X = load_dump(); BASE = 11
def prep(xs):
    for x in xs:
        if "V" in x: continue
        L = tape(x["cv"]); p = path(L, 1, hmax=60); x["V"] = p["v"]; bE = p["bE"]
        buyers = {r["who"] for r in L["rows"] if r["bn"] == bE and r["k"] == "B"}
        x["seat_sell"] = next((r["bn"] - bE for r in L["rows"] if bE < r["bn"] <= bE + 60 and r["k"] == "S" and r["who"] in buyers), None)
        x["any_sell"] = next((r["bn"] - bE for r in L["rows"] if bE < r["bn"] <= bE + 60 and r["k"] == "S"), None)
    return xs
def exit_val(x, rule, lag):
    V = x["V"]; kind, a = rule
    if kind == "hold": return V[a]
    for h in range(1, BASE - lag + 1):                       # the rule can act until the fixed sell would be sent
        v = V[h]
        if kind == "tp" and v >= a: return V[h + lag]
        if kind == "stop" and v <= -a: return V[h + lag]
        if kind == "seatsell" and x["seat_sell"] is not None and h >= x["seat_sell"]: return V[h + lag]
        if kind == "read" and h == a[0]: return V[h + lag] if v < a[1] else V[BASE]
        if kind == "extend" and h == BASE - lag:              # at the sell's send: if the value is still >= a[1], hold to E1+a[0]
            return V[a[0]] if v >= a[1] else V[BASE]
    return V[BASE]
RULES = [("hold", h) for h in (3, 5, 7, 9, 10, 11, 12, 13, 15, 20, 30)] + [("tp", t) for t in (0.1, 0.2, 0.3, 0.5, 0.8)] + [("stop", s) for s in (0.05, 0.1, 0.15, 0.2, 0.3)] + \
        [("seatsell", 0)] + [("read", (h, t)) for h in (1, 2, 3, 5) for t in (-0.12, -0.08, -0.04, 0.0)] + [("extend", (hh, t)) for hh in (15, 20, 30) for t in (0.2, 0.5)]
for slip in (0.07, 0.25):
    fills = prep([x for x in X if engine(x, slip=slip) == "fill" and tape(x["cv"])])
    A = [x for x in fills if period(x) == "A"]; B = [x for x in fills if period(x) == "B"]
    print(f"\n=== fills at guard {slip:.0%}: A {len(A)}, B {len(B)} (with tapes); fixed E1+11: A {mean([x['V'][11] for x in A]):+.1%}, B {mean([x['V'][11] for x in B]):+.1%}")
    print(f"    seat-block buyer's first sell by E1+11: A {sum(1 for x in A if x['seat_sell'] and x['seat_sell']<=11)}/{len(A)}, B {sum(1 for x in B if x['seat_sell'] and x['seat_sell']<=11)}/{len(B)}")
    for lag in (2, 3):
        res = {r: (mean([exit_val(x, r, lag) for x in A]), mean([exit_val(x, r, lag) for x in B])) for r in RULES}
        print(f"  lag {lag}:")
        for r in RULES:
            a, b = res[r]; print(f"    {str(r):22s} A {a:+6.1%} ({a-res[('hold',11)][0]:+5.1%})   B {b:+6.1%} ({b-res[('hold',11)][1]:+5.1%})")
        for fit, i in (("A", 0), ("B", 1)):
            best = max((r for r in RULES if r[0] != "hold"), key=lambda r: res[r][i]); j = 1 - i
            print(f"    best rule chosen on {fit}: {best} -> on {'B' if fit=='A' else 'A'} {res[best][j]:+.1%} vs fixed E1+11 {res[('hold',11)][j]:+.1%}")
