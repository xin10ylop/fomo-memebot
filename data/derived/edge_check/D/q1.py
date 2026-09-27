"""q1.py (reviewer D), brief question 1: the discovery against the rule.
Part A, the real fills (winners_anatomy.json joined with sep17_20_fills.json, 43 launches, Sep 17-20): what the 12 winners
(actual > +5%) had against the 31 others, including the pre-tick crowd (winners_anatomy's own wallet count at block k-2, and the
rule's fleet count where the launch is in a crowd file), and the price path of every fill by hold.
Part B, the population (all 723 launches, features.json): the crowd after the seat as the discovery defined it, as an oracle:
how often the rule's fires get it, how often the refused do, and what it is worth at 15 and 300 blocks, fit against recent.
    python3 data/derived/edge_check/D/q1.py > data/derived/edge_check/D/q1.txt"""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c, kit as K
W = json.load(open(c.LV + "winners_anatomy.json")); F = {x["cv"]: x for x in json.load(open(c.LV + "sep17_20_fills.json"))}
FE = {f["cv"]: f for f in K.FE}
def m(v): v = [x for x in v if x is not None]; return (st.mean(v), len(v)) if v else (float("nan"), 0)
for w in W:
    fl = F[w["cv"]]; k = len(w["attackers"]) - 1; w["k"] = k
    w["att_k2"] = w["attackers"][k - 2] if k >= 2 else 0; w["att_k"] = w["attackers"][k]
    f = FE.get(w["cv"]); w["fleets_k2"] = f["k2"]["f"] if f else None; w["rule"] = (f["fire"] if f else None)
    w["single"] = fl["fills"] == 1; w["hold"] = fl["hold"]; w["ahead"] = fl["ahead"]; w["landed"] = fl["landed"]
Wn = [w for w in W if w["actual"] > 0.05]; Lo = [w for w in W if w["actual"] <= 0.05]
print(f"PART A. The real fills, Sep 17-20: {len(W)} launches, {len(Wn)} winners (actual > +5%), {len(Lo)} others")
rows = [("actual return", lambda w: w["actual"]), ("first-in-block model (h15)", lambda w: w["first"]), ("buys ahead of us", lambda w: w["ahead"]),
        ("buys behind us in the seat block", lambda w: w["seat_behind_n"]), ("ETH behind us in the seat block", lambda w: w["seat_behind_eth"]),
        ("buys in the next 15 blocks", lambda w: w["after_n"]), ("wallets in the next 15 blocks", lambda w: w["after_wallets"]), ("ETH in the next 15 blocks", lambda w: w["after_eth"]),
        ("pre-tick wallets at block k-2 (anatomy's count)", lambda w: w["att_k2"]), ("pre-tick wallets by block k (whole second)", lambda w: w["att_k"]),
        ("share with >= 2 pre-tick wallets at k-2", lambda w: 1.0 * (w["att_k2"] >= 2)), ("rule's fleets at k-2 (in a crowd file)", lambda w: w["fleets_k2"]),
        ("named wallets", lambda w: w["named"]), ("hold (blocks)", lambda w: w["hold"])]
for h in ("15", "30", "60", "150", "600"): rows.append((f"curve price +{h} blocks vs our entry", (lambda h: lambda w: w["marks"].get(h))(h)))
print(f"{'':50s} {'winners':>14s} {'others':>14s}")
for name, fn in rows:
    a, na = m([fn(w) for w in Wn]); b, nb = m([fn(w) for w in Lo]); print(f"{name:50s} {a:10.3f} ({na:2d}) {b:10.3f} ({nb:2d})")
print("\nby the pre-tick count (the rule's reading) on the same 43 fills:")
for lab, sel in (("wallets at k-2 >= 2", lambda w: w["att_k2"] >= 2), ("wallets at k-2 < 2", lambda w: w["att_k2"] < 2),
                 ("rule fires (fleets>=2 @k-2, crowd file)", lambda w: w["rule"] is True), ("rule refuses (crowd file)", lambda w: w["rule"] is False)):
    S = [w for w in W if sel(w)]
    if not S: continue
    print(f"  {lab:42s} n {len(S):2d}  actual {m([w['actual'] for w in S])[0]:+6.1%}  win {sum(w['actual']>0.05 for w in S)/len(S):3.0%}  "
          f"behind-in-seat {m([w['seat_behind_n'] for w in S])[0]:.1f}  wallets next 15 {m([w['after_wallets'] for w in S])[0]:.1f}  price+60 {m([w['marks'].get('60') for w in S])[0]:+.0%}  +600 {m([w['marks'].get('600') for w in S])[0]:+.0%}")
print("\nthe crowd after the seat (behind-in-seat >= 3 or wallets in 15 blocks >= 4) on the fills:")
for lab, sel in (("crowd after", lambda w: w["seat_behind_n"] >= 3 or w["after_wallets"] >= 4), ("no crowd after", lambda w: not (w["seat_behind_n"] >= 3 or w["after_wallets"] >= 4))):
    S = [w for w in W if sel(w)]
    print(f"  {lab:16s} n {len(S):2d}  actual {m([w['actual'] for w in S])[0]:+6.1%}  win {sum(w['actual']>0.05 for w in S)/len(S):3.0%}  pre-tick wallets k-2 >= 2: {sum(w['att_k2']>=2 for w in S)}/{len(S)}")
# Part B
print("\nPART B. The population (features.json): the crowd after the seat, second place in E1, as an oracle")
def ca(f): return f["behind_n"] >= 3 or f["ow15"] >= 4
for g, S in (("fit", K.FIT), ("recent", K.REC)):
    fi = [f for f in S if f["fire"]]; re = [f for f in S if not f["fire"]]
    print(f" {g}: P(crowd after | fire) {sum(map(ca, fi))/len(fi):.0%} ({sum(map(ca, fi))}/{len(fi)})   P(crowd after | refused) {sum(map(ca, re))/len(re):.0%} ({sum(map(ca, re))}/{len(re)})")
    for lab, T in (("fires with crowd after", [f for f in fi if ca(f)]), ("fires without", [f for f in fi if not ca(f)]), ("refused with crowd after", [f for f in re if ca(f)]), ("refused without", [f for f in re if not ca(f)])):
        if T: print(f"   {lab:26s} n {len(T):3d}  h0 {c.mean([f['path'][0] for f in T]):+6.1%}  h15 {c.mean([f['path'][15] for f in T]):+6.1%}  h60 {c.mean([f['path'][60] for f in T]):+6.1%}  h150 {c.mean([f['path'][150] for f in T]):+6.1%}  h300 {c.mean([f['path'][300] for f in T]):+6.1%}")
    print(f"   fires: behind-in-seat mean {c.mean([f['behind_n'] for f in fi]):.1f}, outsider wallets next 15 {c.mean([f['ow15'] for f in fi]):.1f}, outsider ETH next 15 {c.mean([f['oeth15'] for f in fi]):.2f};"
          f" refused: {c.mean([f['behind_n'] for f in re]):.1f}, {c.mean([f['ow15'] for f in re]):.1f}, {c.mean([f['oeth15'] for f in re]):.2f}")
