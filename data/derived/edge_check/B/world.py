"""world.py (reviewer B), test 5 from the cached tapes: the fee each buy and sell really paid by second after the creation
(implied from the curve folded in tape order: 1 - net/eth for buys, 1 - eth_out/gross for sells), minus the launch's tier;
the sequencer's cadence (blocks per whole second in seconds +1 and +2 after the creation, from the stamps); by period.
    python3 data/derived/edge_check/B/world.py"""
import sys, os, json, collections, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
import live_vs_table as lv
LIVE = 1790414640          # Sep 26 09:24 UTC: our first live burst; the fleets could see our relay from here
def periods(T0):
    return "fit" if T0 < 1790200000 else ("recent, before our first burst" if T0 < LIVE else "recent, after our first burst")
fee = collections.defaultdict(lambda: collections.defaultdict(list)); sfee = collections.defaultdict(lambda: collections.defaultdict(list))
cad = collections.defaultdict(list); ks = collections.defaultdict(list); n = collections.Counter()
seen = set()
for grp, files in (("fit", c.FIT), ("recent", c.RECENT)):
    for r in c.load(files):
        L = c.tape(r["cv"])
        if L is None or L["tier"] is None or r["cv"] in seen: continue
        seen.add(r["cv"]); ts = {int(k): v for k, v in L["ts"].items()}; T0 = L["T0"]; p = periods(T0); n[p] += 1; tier = L["tier"]
        for s in (1, 2):
            bl = [b for b, t in ts.items() if t == T0 + s]
            if bl and max(ts) > max(bl): cad[p].append(len(bl))
        ks[p].append(r["k"])
        X, Y = lv.X0, lv.Y0
        for x in L["rows"]:
            sec = ts.get(x["bn"], None); sec = (sec - T0) if sec is not None else 3
            sec = min(sec, 3)
            if x["k"] == "B":
                if 0 < x["tk"] < Y and x["eth"] > 0:
                    net = X * x["tk"] / (Y - x["tk"]); fee[p][sec].append(1 - net / x["eth"] - tier); X, Y = lv.fold_buy(X, Y, x["tk"])
            else:
                gross = X * x["tk"] / (Y + x["tk"])
                if gross > 0: sfee[p][min(sec, 3)].append(1 - x["eth"] / gross - tier)
                X, Y = lv.fold_sell(X, Y, x["tk"])
def q(v, lo, hi): return sum(lo <= x <= hi for x in v) / len(v) if v else float("nan")
print("launches with a tape:", dict(n))
for p in fee:
    print(f"\n== {p}")
    for s in range(4):
        v = fee[p][s]
        if not v: continue
        tgt = lv.SUR.get(s, 0.0)
        print(f"  buys  second {s}{'+' if s == 3 else ' '}: n={len(v):5d}  median fee-tier {st.median(v):+.4f}  share within 0.001 of the schedule's {tgt:.4f}: {q(v, tgt - 0.001, tgt + 0.001):.2f}" + (f"  (at 0, the bundle's exemption: {q(v, -0.001, 0.001):.2f})" if s == 0 else ""))
    for s in range(4):
        v = sfee[p][s]
        if v: print(f"  sells second {s}{'+' if s == 3 else ' '}: n={len(v):5d}  median fee-tier {st.median(v):+.4f}  share within 0.001 of 0: {q(v, -0.001, 0.001):.2f}")
    print(f"  cadence: blocks in a whole second (+1, +2): mean {st.mean(cad[p]):.2f}, share with 10: {sum(x == 10 for x in cad[p])/len(cad[p]):.2f}, distribution {sorted(collections.Counter(cad[p]).items())}")
    print(f"  k (blocks after b0 in the creation second): mean {st.mean(ks[p]):.2f}, distribution {sorted(collections.Counter(ks[p]).items())}")
