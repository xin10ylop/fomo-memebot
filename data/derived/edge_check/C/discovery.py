"""discovery.py (edge_check/C): question 1, part one. What the real winners of Sep 17-20 had, re-derived from the two artefacts
the discovery came from (winners_anatomy.json, sep17_20_fills.json), then joined to the fit's crowd pull (crowd_raw_sep1819)
to ask whether the rule that was built on the discovery (fleets >= 2 at k-2) would have picked those winners, and whether the
pre-tick crowd predicts the post-seat crowd on them.
    python3 data/derived/edge_check/C/discovery.py > data/derived/edge_check/C/discovery.txt"""
import sys, json, statistics as st
sys.path.insert(0, "data/derived/edge_check/C"); from common import *
F = json.load(open(D + "sep17_20_fills.json")); W = json.load(open(D + "winners_anatomy.json"))
def m(v): v = [x for x in v if x is not None]; return (st.mean(v), st.median(v), len(v)) if v else (float("nan"),) * 3
print("=== 1. the fills (sep17_20_fills.json): single fills by who was ahead in the seat block")
for name, f in (("nobody ahead", lambda x: x["ahead"] == 0), ("somebody ahead", lambda x: x["ahead"] > 0), ("all", lambda x: True)):
    s = [x for x in F if x["fills"] == 1 and x["actual"] is not None and f(x)]
    print(f"  {name:15s} n {len(s):2d}  first-in-block {st.mean(x['first'] for x in s):+.1%}  at our position h15 {st.mean(x['landed'] for x in s):+.1%}"
          f"  actual {st.mean(x['actual'] for x in s):+.1%}  win {sum(x['actual'] > 0 for x in s)/len(s):.0%}  mean hold {st.mean(x['hold'] for x in s):.0f} blocks")
print("\n=== 2. winners (actual > +5%) against the rest (winners_anatomy.json, all 43 filled launches, multi-fills included)")
Wn = [x for x in W if x["actual"] > 0.05]; Lo = [x for x in W if x["actual"] <= 0.05]
print(f"  winners {len(Wn)}, rest {len(Lo)}   (mean / median)")
feats = [("buys behind us in the seat block", lambda x: x["seat_behind_n"]), ("ETH behind us in the seat block", lambda x: x["seat_behind_eth"]),
         ("buys in the next 15 blocks", lambda x: x["after_n"]), ("distinct wallets, next 15 blocks", lambda x: x["after_wallets"]), ("ETH, next 15 blocks", lambda x: x["after_eth"]),
         ("price +15 blocks vs our entry", lambda x: x["marks"].get("15")), ("price +60", lambda x: x["marks"].get("60")), ("price +150", lambda x: x["marks"].get("150")),
         ("price +600", lambda x: x["marks"].get("600")), ("first-in-block model (h15)", lambda x: x["first"]), ("actual", lambda x: x["actual"]), ("fills (multi-fill count)", lambda x: x["fills"]),
         ("wallets firing by the last creation block (anatomy's unit)", lambda x: x["attackers"][-1]), ("wallets firing by block k-2 (anatomy's unit)", lambda x: x["attackers"][len(x["attackers"]) - 3] if len(x["attackers"]) >= 3 else 0),
         ("named wallets", lambda x: x["named"]), ("somebody ahead of us (ahead > 0)", lambda x: 1.0 if x["ahead"] > 0 else 0.0)]
for name, f in feats:
    a = m([f(x) for x in Wn]); b = m([f(x) for x in Lo])
    print(f"  {name:58s} winners {a[0]:8.3f} / {a[1]:8.3f}   rest {b[0]:8.3f} / {b[1]:8.3f}")
print("  share of the rest whose price at +600 was above our entry:", f"{sum((x['marks'].get('600') or 0) > 0 for x in Lo)}/{len(Lo)}",
      "  winners:", f"{sum((x['marks'].get('600') or 0) > 0 for x in Wn)}/{len(Wn)}")
print("  single fills only:")
for name, s in (("winners", [x for x in Wn if x["fills"] == 1]), ("rest", [x for x in Lo if x["fills"] == 1])):
    print(f"    {name:8s} n {len(s):2d}  seat-behind {st.mean(x['seat_behind_n'] for x in s):.1f}  next-15 buys {st.mean(x['after_n'] for x in s):.1f} from {st.mean(x['after_wallets'] for x in s):.1f} wallets"
          f"  +15 {st.mean(x['marks']['15'] for x in s):+.0%}  +60 {st.mean(x['marks']['60'] for x in s):+.0%}  +150 {st.mean(x['marks']['150'] for x in s):+.0%}  +600 {st.mean(x['marks']['600'] for x in s):+.0%}")
print("\n=== 3. the same launches in the fit's crowd pull (crowd_raw_sep1819): the rule's pre-tick count, the engine's unit")
Rw = {r["cv"]: r for r in load_all() if r["win"] == "sep1819"}
rows = []
for x in W:
    r = Rw.get(x["cv"])
    if r is None: continue
    cw, cf = cums(r); k = r["k"]; rows.append((x, at(cf, k - 2), at(cw, k - 2), cf[-1] if cf else 0, k))
print(f"  {len(rows)} of {len(W)} filled launches are in the fit's population (the rest were outside the tables' filters or before Sep 18 13:27)")
for name, f in (("rule fires (fleets >= 2 at k-2)", lambda t: t[1] >= 2), ("rule refuses", lambda t: t[1] < 2)):
    s = [t for t in rows if f(t)]
    if not s: print(f"  {name}: 0"); continue
    xs = [t[0] for t in s]
    print(f"  {name:32s} n {len(s):2d}  winners {sum(x['actual'] > 0.05 for x in xs):2d}  actual {st.mean(x['actual'] for x in xs):+.1%}  first {st.mean(x['first'] for x in xs):+.1%}"
          f"  seat-behind {st.mean(x['seat_behind_n'] for x in xs):.1f}  next-15 wallets {st.mean(x['after_wallets'] for x in xs):.1f}  +60 {st.mean(x['marks']['60'] for x in xs):+.0%}  +600 {st.mean(x['marks']['600'] for x in xs):+.0%}")
print("  per launch: when, cv, actual, winner, fleets k-2, wallets k-2, fleets end of second, k, seat-behind, next-15 wallets")
for x, f2, w2, fe, k in sorted(rows, key=lambda t: t[0]["when"]):
    print(f"   {x['when']} {x['cv'][:10]} {x['actual']:+6.1%} {'W' if x['actual'] > 0.05 else '.'}  f{f2} w{w2} fend{fe} k{k}  sb {x['seat_behind_n']:2d}  a15w {x['after_wallets']:2d}")
# rank correlation of the pre-tick count with the post-seat crowd on these launches
def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
        for t in range(i, j + 1): r[o[t]] = (i + j) / 2
        i = j + 1
    return r
def spear(a, b):
    ra, rb = rank(a), rank(b); ma, mb = st.mean(ra), st.mean(rb)
    num = sum((p - ma) * (q - mb) for p, q in zip(ra, rb)); den = (sum((p - ma) ** 2 for p in ra) * sum((q - mb) ** 2 for q in rb)) ** 0.5
    return num / den if den else float("nan")
if rows:
    print(f"  Spearman, fleets at k-2 vs next-15 wallets: {spear([t[1] for t in rows], [t[0]['after_wallets'] for t in rows]):+.2f};"
          f" vs seat-behind buys: {spear([t[1] for t in rows], [t[0]['seat_behind_n'] for t in rows]):+.2f};  next-15 wallets vs actual: {spear([t[0]['after_wallets'] for t in rows], [t[0]['actual'] for t in rows]):+.2f}"
          f";  fleets at k-2 vs actual: {spear([t[1] for t in rows], [t[0]['actual'] for t in rows]):+.2f}  (n {len(rows)})")
