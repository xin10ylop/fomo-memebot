"""VH verification 2: the ENGINE's own bundle_eth rule (sniper_engine.fold_buy: named wallets + creator buys within 9 blocks of b0,
closed at the first outsider buy in the creation window) on the cached tapes, on the gate's k-2 view and on the whole creation
second; does a 3.0 ETH cap drop the same engine fires as H's e1_multi-rule bundle?"""
import sys
sys.path.insert(0, "/home/user/fomo-memebot/data/derived/edge_check/VH/rerun"); from common import *; from common import _tapes
TP = _tapes(); P = load(); raws = {}
for w in FIT + REC:
    for r in raw(w): raws.setdefault(r["cv"], r)
def eng_bundle(L, r, last_off):
    named = set(r["named"]); cr = r.get("creator"); b0 = L["b0"]; b = 0.0; closed = False
    for row in sorted(L["rows"], key=lambda q: (q["bn"], q["li"])):
        off = row["bn"] - b0
        if off > min(9, last_off): break
        if row["k"] != "B": continue
        who = row.get("who")
        if who in named or who == cr:
            if not closed: b += row["eth"]
        else:
            closed = True
    return b
rows = []
for x in P:
    if x["cv"] not in TP: continue
    L = TP[x["cv"]]; r = raws[x["cv"]]
    x["eb_full"] = eng_bundle(L, r, r["k"]); x["eb_k2"] = eng_bundle(L, r, r["k"] - 2)
for s in ("fit", "rec"):
    for key in ("fire_eng", "fire_tab"):
        F = [x for x in P if x["set"] == s and x[key] and "eb_k2" in x]
        H_ = {x["cv"] for x in F if x["bundle"] > 3.0}; Ef = {x["cv"] for x in F if x["eb_full"] > 3.0}; Ek = {x["cv"] for x in F if x["eb_k2"] > 3.0}
        print(f"{s} {key}: fires with tape {len(F)}; cap3.0 drops: e1_multi-rule {len(H_)}, engine-rule whole {len(Ef)}, engine-rule k-2 {len(Ek)}; same set: {H_ == Ef == Ek}")
        near = sorted(F, key=lambda x: -x["eb_k2"])[:12]
        for x in near: print(f"    {x['cv'][:10]} e1 {x['bundle']:.3f} eng-whole {x['eb_full']:.3f} eng-k2 {x['eb_k2']:.3f} k {x['k']}")
# over all launches with a tape: how does the engine rule relate to e1_multi on the >3 ETH ones
big = [x for x in P if "eb_k2" in x and (x["bundle"] > 3.0 or x["eb_full"] > 3.0)]
print("\nall tape launches with e1 bundle > 3 or engine-rule > 3:")
for x in big: print(f"  {hms(x['T0'])} {x['cv'][:10]} k {x['k']} e1 {x['bundle']:.3f} eng-whole {x['eb_full']:.3f} eng-k2 {x['eb_k2']:.3f} fire_eng {x['fire_eng']}")
