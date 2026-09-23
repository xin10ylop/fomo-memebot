"""gate_hold_eval.py: the gate x hold evaluation of one window: crowd_signal.json and hold_grid.json joined.
    python3 src/analysis/gate_hold_eval.py crowd_signal.json hold_grid.json [min_attackers=2] [stake=13] [gas=0.33]"""
import json, sys, statistics as st
C = {r["cv"]: r for r in json.load(open(sys.argv[1]))}; H = {r["cv"]: r for r in json.load(open(sys.argv[2]))}
MIN_A = int(sys.argv[3]) if len(sys.argv) > 3 else 2; STAKE = float(sys.argv[4]) if len(sys.argv) > 4 else 13.0; GAS = float(sys.argv[5]) if len(sys.argv) > 5 else 0.33
at = lambda r: r["attackers_by_block"][min(5, len(r["attackers_by_block"]) - 1)] if r["attackers_by_block"] else 0
both = [cv for cv in C if cv in H]; print(f"{len(both)} launches scored in both files")
for name, cond in (("all", lambda r: True), (f"gate: {MIN_A}+ attackers by block 5", lambda r: at(r) >= MIN_A), (f"skipped: fewer than {MIN_A}", lambda r: at(r) < MIN_A)):
    rows = [H[cv] for cv in both if cond(C[cv])]
    if not rows: continue
    print(f"  {name:34s} n={len(rows)}")
    for pos in ("first", "behind1"):
        print(f"     {pos:8s} " + "  ".join(f"h{h} {st.mean(r[f'{pos}_15_h{h}'] for r in rows):+6.1%}/{sum(r[f'{pos}_15_h{h}']>0 for r in rows)/len(rows):3.0%}" for h in (15, 60, 150, 300, 600)))
    for h in (15, 300):
        v = [r[f"behind1_15_h{h}"] * STAKE - GAS for r in rows]
        print(f"     ${STAKE:.0f} behind one, hold {h}: ${st.mean(v):+.2f} a burst after gas (SE ${st.pstdev(v)/len(v)**0.5:.2f}), dead {sum(r[f'behind1_15_h{h}']<-0.4 for r in rows)/len(rows):.0%}")
