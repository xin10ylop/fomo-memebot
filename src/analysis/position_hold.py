"""position_hold.py: on the gated launches, the seat by position (first, behind 1, 2, 3, everybody) and hold (15..600).
    python3 src/analysis/position_hold.py crowd_signal.json [min_attackers=2]   -> decides how dense the burst must be."""
import json, sys, statistics as st
sys.path.insert(0, "src/analysis"); import live_vs_table as lv
from hold_grid import model_path, HOLDS
C = json.load(open(sys.argv[1])); MIN_A = int(sys.argv[2]) if len(sys.argv) > 2 else 2; E = 2570.0
at = lambda r: r["attackers_by_block"][min(5, len(r["attackers_by_block"]) - 1)] if r["attackers_by_block"] else 0
gated = [r for r in C if at(r) >= MIN_A]; rows = []
for r in gated:
    cv = r["cv"]; b0 = r["b0"]; L = lv.launch(cv, b0 + r["k"] + 1)
    if L is None or L["tier"] is None: continue
    ev = lv.call("eth_getLogs", [{"fromBlock": hex(b0 + 121), "toBlock": hex(b0 + 620), "address": cv, "topics": [[lv.BUY, lv.SELL]]}])
    L["rows"] = sorted(L["rows"] + [lv.row_of(e) for e in ev], key=lambda x: (x["bn"], x["li"])); ts = L["ts"]; T0 = L["T0"]
    bE1 = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
    if bE1 is None: continue
    nb = sum(1 for x in L["rows"] if x["bn"] == bE1 and x["k"] == "B" and x["who"] not in lv.OURS); row = {"cv": cv, "block_buys": nb}
    for pos, nah in (("first", 0), ("behind1", 1), ("behind2", 2), ("behind3", 3), ("last", 99)):
        if nah not in (0, 99) and nb < nah: continue
        o = model_path(L, 15.0 / E, bE1, nah, HOLDS)
        for h in HOLDS: row[f"{pos}_h{h}"] = o[h]
    rows.append(row)
json.dump(rows, open(sys.argv[1].replace(".json", "_position_hold.json"), "w"), indent=0)
print(f"{len(rows)} gated launches ({sys.argv[1]}), $15, before gas: mean / win")
print(f"{'position':9s} " + " ".join(f"{'h%d' % h:>13s}" for h in HOLDS) + "   n")
for pos in ("first", "behind1", "behind2", "behind3", "last"):
    v = [r for r in rows if f"{pos}_h15" in r]
    print(f"{pos:9s} " + " ".join(f"{st.mean(r[f'{pos}_h{h}'] for r in v):+7.1%}/{sum(r[f'{pos}_h{h}']>0 for r in v)/len(v):3.0%}" for h in HOLDS) + f"   {len(v)}")
