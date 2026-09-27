"""alternatives.py (edge_check/A): test 4, what the rule does not see, fit vs Sep 24-27. (a) the hold (15/30/60/150/300/600)
and a -20% stop on the rule's own fires (reviewer A's model on tapes.json.gz); (b) other gates on the whole population priced
by hold_grid's stored columns (behind1_15_*): the tick's-shot view (0.76), k-1, k-3, fleets >= 1 and >= 3, wallets >= 2.
    python3 data/derived/edge_check/A/alternatives.py"""
import sys, json, math, statistics as st
sys.path.insert(0, "data/derived/edge_check/A"); from common import *
F = json.load(open(A + "fires.json"))
def d(v): return f"{len(v):3d} mean {st.mean(v):+6.1%} med {st.median(v):+6.1%} win {sum(y > 0 for y in v)/len(v):3.0%} dead {sum(y < -0.4 for y in v)/len(v):3.0%}" if v else "  0"
print("(a) the rule's fires, second place, $13, by exit")
for col in ("15", "30", "60", "150", "300", "600", "stop_300", "stop_600"):
    print(f"   {col:9s} fit {d([x['ret'][col] for x in F if x['set'] == 'fit'])}   recent {d([x['ret'][col] for x in F if x['set'] == 'rec'])}")
print("   first place instead of second, h300: fit %s   recent %s" % (d([x["ret_first"]["300"] for x in F if x["set"] == "fit"]), d([x["ret_first"]["300"] for x in F if x["set"] == "rec"])))
H = {}
for w in FIT + REC: H.update({x["cv"]: x for x in json.load(open(D + HG[w]))})
def view(k, frac): return max(-1, min(k, math.floor(frac * (k + 1)) - 1))
gates = [("fleets>=2 @k-2 (the rule)", lambda r, cf, cw: at(cf, r["k"] - 2) >= 2), ("fleets>=2 @k-1", lambda r, cf, cw: at(cf, r["k"] - 1) >= 2),
         ("fleets>=2 @k-3", lambda r, cf, cw: at(cf, r["k"] - 3) >= 2), ("fleets>=2 @tick's shot (0.76)", lambda r, cf, cw: at(cf, view(r["k"], 0.76)) >= 2),
         ("fleets>=1 @k-2", lambda r, cf, cw: at(cf, r["k"] - 2) >= 1), ("fleets>=3 @k-2", lambda r, cf, cw: at(cf, r["k"] - 2) >= 3),
         ("wallets>=2 @k-2", lambda r, cf, cw: at(cw, r["k"] - 2) >= 2), ("wallets>=3 @k-2", lambda r, cf, cw: at(cw, r["k"] - 2) >= 3),
         ("no gate (every launch)", lambda r, cf, cw: True)]
print("\n(b) gates on the whole population, hold_grid's behind1_15 columns ($15, second place)")
for col in ("h300", "h60", "h15", "stop20_h600"):
    print(f"  column behind1_15_{col}")
    for name, g in gates:
        out = {}
        for s, ws in (("fit", FIT), ("rec", REC)):
            out[s] = [H[r["cv"]][f"behind1_15_{col}"] for r in all_launches(ws) if g(r, fleets_by_block(r), fleets_by_block(r, "wallets"))]
        print(f"   {name:32s} fit {d(out['fit'])}   recent {d(out['rec'])}")
print("\n(c) paired: h15 minus h300 on the same fires (reviewer A's model, $13)")
for s in ("fit", "rec"):
    dd = [x["ret"]["15"] - x["ret"]["300"] for x in F if x["set"] == s]; se = st.stdev(dd) / math.sqrt(len(dd))
    print(f"   {s:4s} mean {st.mean(dd):+.1%} se {se:.3f} t {st.mean(dd)/se:+.2f}")
dd = [x["ret"]["15"] - x["ret"]["300"] for x in F]; se = st.stdev(dd) / math.sqrt(len(dd)); print(f"   all 91 mean {st.mean(dd):+.1%} se {se:.3f} t {st.mean(dd)/se:+.2f}")
print("\n(d) $/day at $13 after $0.33 gas on the rule's fires (fit 96 h, recent 60 h as the brief counts them)")
for col in ("15", "60", "150", "300", "600", "stop_300"):
    f = sum(x["ret"][col] * 13 - 0.33 for x in F if x["set"] == "fit") / 96 * 24; r = sum(x["ret"][col] * 13 - 0.33 for x in F if x["set"] == "rec") / 60 * 24
    print(f"   {col:9s} fit ${f:+6.1f}/day   recent ${r:+6.1f}/day")
