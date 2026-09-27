"""bundle.py (edge_check/H): what the bundle cap removes. (a) every fire (engine or tables) with bundle >= 1.5 ETH, one line each;
(b) all launches (fires and refused) by bundle bin: n, h11/h15 mean, share flat at the fee floor (h11 == h15 == h15 of the first
place, the curve untouched after the seat); (c) a fine sweep of the cap 1.0..5.0 ETH on the engine's fires, h11 and h15, both periods.
    python3 data/derived/edge_check/H/bundle.py > data/derived/edge_check/H/bundle.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
P = load(); TF = json.load(open(H + "template_flags.json"))["3_5"]
f11 = lambda x: "   n/a" if x["r11"] is None else f"{x['r11']:+6.1%}"
print("(a) fires (tables or engine) with bundle >= 1.5 ETH")
for x in P:
    if (x["fire_tab"] or x["fire_eng"]) and x["bundle"] >= 1.5:
        print(f"  {hms(x['T0'])} {x['set']:3s} {x['win']:10s} {x['cv'][:10]} bundle {x['bundle']:.3f} named {len(x['named']):2d} fleets tab {x['f_tab']} eng {x['f_eng']}"
              f"{' ENGINE' if x['fire_eng'] else ' tables'}  h11 {f11(x)} h15 {x['r15']:+6.1%}  template-flag {TF[x['cv']]['flag']}")
print("\n(b) all launches by bundle ETH (fires and refused); flat = h11 and h15 equal and below -8% (nobody traded after the seat)")
bins = [(0, 0.5), (0.5, 0.75), (0.75, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 99)]
for s in ("fit", "rec"):
    for lo, hi in bins:
        S = [x for x in P if x["set"] == s and lo <= x["bundle"] < hi]; S11 = [x for x in S if x["r11"] is not None]
        flat = [x for x in S11 if abs(x["r11"] - x["r15"]) < 1e-9 and x["r15"] < -0.08]
        fe = [x for x in S if x["fire_eng"]]; ft = [x for x in S if x["fire_tab"]]
        print(f"  {s:3s} bundle {lo:4.2f}-{hi:5.2f}: {len(S):3d} launches, h11 {mean([x['r11'] for x in S11]):+6.1%} h15 {mean([x['r15'] for x in S]):+6.1%}, flat {len(flat)}/{len(S11)};"
              f" engine fires {len(fe):2d} (h15 {mean([x['r15'] for x in fe]):+6.1%}), tables fires {len(ft):2d} (h15 {mean([x['r15'] for x in ft]):+6.1%})")
print("\n(c) fine sweep of BUNDLE_MAX_ETH on the engine's fires ($/day: fit 96 h, recent 62.65 h)")
RH = spans(P, REC)
for h in (11, 15):
    print(f"  exit block {h}")
    for c in [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0, 4.1, 4.15, 4.2, 4.25, 5.0, 99]:
        out = []
        for s, hrs in (("fit", FIT_HOURS), ("rec", RH)):
            F = [x for x in P if x["set"] == s and x["fire_eng"] and x["bundle"] <= c and (x["r11"] if h == 11 else x["r15"]) is not None]
            v = [x["r11"] if h == 11 else x["r15"] for x in F]
            out.append(f"{s} {len(v):2d} {mean(v):+6.1%} ${sum(usd(r, x['g']) for r, x in zip(v, F)) / hrs * 24:+6.1f}/day")
        print(f"    cap {c:5.2f}: " + " | ".join(out))
