"""gated_seat.py: the seat priced only on the launches the crowd signal would let us fire at, at the positions we can get.

    python3 src/analysis/gated_seat.py [min_attackers=2] [block=5]

Launches of data/derived/live_vs_table/crowd_signal.json with at least `min_attackers` distinct wallets already firing at the
curve by creation-second block `block`; for each, the tape from the chain and e1_multi's model at $15 and $100: first in the
seat block, behind 1, behind 2, behind 3, behind everybody; holds 15 and 25 blocks; plus the seat block's own price move from
the buys ahead (whether a 25% guard lets a fill through at each position). Gas: 35 shots at the measured $0.33."""
import json, sys, statistics as st, time
sys.path.insert(0, "src/analysis"); from live_vs_table import launch, model, fold_buy, X0, Y0, OURS
MIN_A = int(sys.argv[1]) if len(sys.argv) > 1 else 2; BLK = int(sys.argv[2]) if len(sys.argv) > 2 else 5; E = 2570.0; GAS = 0.33
SRC = sys.argv[3] if len(sys.argv) > 3 else "data/derived/live_vs_table/crowd_signal.json"; DST = sys.argv[4] if len(sys.argv) > 4 else "data/derived/live_vs_table/gated_seat.json"
C = json.load(open(SRC))
at = lambda r: r["attackers_by_block"][min(BLK, len(r["attackers_by_block"]) - 1)] if r["attackers_by_block"] else 0
gated = [r for r in C if at(r) >= MIN_A]; rest = [r for r in C if at(r) < MIN_A]
print(f"{len(C)} launches; gate 'attackers >= {MIN_A} by block {BLK}': {len(gated)} fire, {len(rest)} skipped (skipped: first {st.mean(r['first'] for r in rest):+.1%}, win {sum(r['first']>0 for r in rest)/len(rest):.0%})")
rows = []
for r in gated:
    L = launch(r["cv"], r["b0"] + r["k"] + 1)
    if L is None or L["tier"] is None: print("  skip", r["cv"][:10], "no tape"); continue
    ts = L["ts"]; T0 = L["T0"]; bE1 = next((n for n in range(L["b0"] + 1, L["b0"] + 30) if ts.get(n, 0) == T0 + 1), None)
    if bE1 is None: continue
    tape = [x for x in L["rows"] if x["who"] not in OURS]; blockbuys = [x for x in tape if x["bn"] == bE1 and x["k"] == "B"]
    # the price move inside the seat block from the buys ahead of position p: fold the creation second, then the pre-seat trades, then the first p buys
    X, Y = X0, Y0
    for x in tape:
        if x["bn"] >= bE1: break
        if x["k"] == "B":
            if 0 < x["tk"] < Y: X, Y = fold_buy(X, Y, x["tk"])
        else: X, Y = X - X * x["tk"] / (Y + x["tk"]), Y + x["tk"]
    p0 = X / Y; moves = []
    for x in blockbuys:
        if 0 < x["tk"] < Y: X, Y = fold_buy(X, Y, x["tk"])
        moves.append(X / Y / p0 - 1)
    row = {"cv": r["cv"], "hour": r["hour"], "attackers": at(r), "n_block": len(blockbuys), "moves": moves}
    for stake in (15.0, 100.0):
        g = stake / E
        for hold in (15, 25):
            row[f"first_{int(stake)}_{hold}"] = model(L, g, bE1, 0, hold=hold)
            for p in (1, 2, 3): row[f"behind{p}_{int(stake)}_{hold}"] = model(L, g, bE1, p, hold=hold) if len(blockbuys) >= p else None
            row[f"last_{int(stake)}_{hold}"] = model(L, g, bE1, 99, hold=hold)
    rows.append(row); print(f"  {time.strftime('%b %d %H:%M', time.gmtime(T0))} {r['cv'][:10]} attackers {at(r)} block buys {len(blockbuys)} first15 {row['first_15_15']:+.0%} b1 {row['behind1_15_15'] if row['behind1_15_15'] is None else round(100*row['behind1_15_15'])} b2 {row['behind2_15_15'] if row['behind2_15_15'] is None else round(100*row['behind2_15_15'])} last {row['last_15_15']:+.0%}  move ahead of pos2 {moves[0]*100 if moves else 0:+.0f}%", flush=True)
json.dump(rows, open(DST, "w"), indent=0)
def col(k):
    v = [x[k] for x in rows if x.get(k) is not None]; return f"n={len(v):2d} mean {st.mean(v):+6.1%} med {st.median(v):+6.1%} win {sum(x>0 for x in v)/len(v):3.0%}" if v else "-"
print(f"\n=== gated launches, model by position (hold 15 blocks / 25 blocks), before gas")
for stake in (15, 100):
    for k in ("first", "behind1", "behind2", "behind3", "last"):
        print(f"  ${stake:3d} {k:8s} h15 {col(f'{k}_{stake}_15')}   h25 {col(f'{k}_{stake}_25')}")
# what a 25% guard lets through: the fill at position p needs the move from the p buys ahead to be < 25%
for p in (1, 2, 3):
    ok = [x for x in rows if len(x["moves"]) >= p and x["moves"][p - 1] < 0.25]; print(f"  position behind {p}: fill possible on {len(ok)}/{sum(len(x['moves'])>=p for x in rows)} launches (price moved < 25% ahead of us)")
# expectation per burst: at position behind-1 when the guard allows, no fill otherwise; gas always
for stake in (15, 100):
    ev = []
    for x in rows:
        m = x.get(f"behind1_{stake}_15")
        if m is None: m = x[f"first_{stake}_15"]                                    # nobody in the block: we are first
        fill = (not x["moves"]) or x["moves"][0] < 0.25
        ev.append((m * stake if fill else 0.0) - GAS)
    print(f"  ${stake}: per gated burst, landing 2nd (or first when the block is empty), 25% guard, gas ${GAS}: mean ${st.mean(ev):+.2f}, {len(ev)} bursts over {len(C)} launches ({sum(1 for _ in C)} launches = 1 day): ${st.mean(ev)*len(ev):+.0f}/day; skipped launches would have cost {len(rest)} x ${GAS} gas = ${len(rest)*GAS:.0f}")
