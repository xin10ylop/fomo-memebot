"""features.py (edge_check/C): one record per launch of the fit and recent populations (735 launches: 563 fit, 172 recent incl.
round 1 A's two gap pulls), offline from the cached tapes. Returns at second place in E1 (model_eff, $13) for holds 15, 30, 60,
150, 300, 600; at first and third place for 15 and 300; the post-seat crowd (buys behind second place in the seat block, buys /
distinct buyers / ETH in the 15 blocks after the seat, outsiders only: not the named wallets or the creator); the bundle's
sells; the pre-tick crowd (fleets and wallets by k-2, shots by k-2, relay vs direct fleets); the creator's and the named
template's prior launches (causal: only launches created earlier in this population).
    python3 data/derived/edge_check/C/features.py      -> C/pop.json"""
import sys, json, collections
sys.path.insert(0, "data/derived/edge_check/C"); from common import *
HOLDS = (15, 30, 60, 150, 300, 600)
R = sorted(load_all(), key=lambda r: r["T0"])
prior_creator = collections.Counter(); prior_named = collections.Counter(); out = []; missing = 0
for r in R:
    L = tape(r["cv"])
    named = {w.lower() for w in r["named"]} | {r["creator"].lower()}
    rec = {"cv": r["cv"], "win": r["win"], "set": r["set"], "T0": r["T0"], "k": r["k"], "creator": r["creator"]}
    cw, cf = cums(r); k = r["k"]
    rec.update({"f_k2": at(cf, k - 2), "w_k2": at(cw, k - 2), "f_k3": at(cf, k - 3), "f_k1": at(cf, k - 1), "f_end": cf[-1] if cf else 0, "w_end": cw[-1] if cw else 0})
    shots = 0; relay_f = set(); direct_f = set()
    for rows in r["blocks"][: max(0, k - 1)]:
        for t in rows:
            if t["to"] in US or t["to_token"] or t["fr"] in US: continue
            if t["direct"]:
                if not t["named_fr"]: direct_f.add(t["fr"]); shots += 1
            elif not t["named_data"]: relay_f.add(t["to"]); shots += 1
    rec.update({"shots_k2": shots, "relay_k2": len(relay_f), "direct_k2": len(direct_f)})
    # causal history: earlier launches by the same creator / sharing a named wallet
    rec["creator_prior"] = prior_creator[r["creator"].lower()]
    rec["named_prior"] = max((prior_named[w] for w in r["named"]), default=0)
    prior_creator[r["creator"].lower()] += 1
    for w in set(x.lower() for x in r["named"]): prior_named[w] += 1
    if L is None or seat_block(L) is None: missing += 1; rec["ret"] = None; out.append(rec); continue
    bE1 = seat_block(L); rows = [x for x in L["rows"] if x["who"] not in OURS]; T0 = L["T0"]
    rec["tier"] = L["tier"]; rec["bE1"] = bE1; rec["b0"] = L["b0"]
    rec["ret"] = {h: price(L, h, 1) for h in HOLDS}
    rec["ret_first"] = {h: price(L, h, 0) for h in (15, 300)}
    rec["ret_third"] = {h: price(L, h, 2) for h in (15, 300)}
    creation = [x for x in rows if L["ts"].get(x["bn"], 0) == T0]
    rec["bundle_eth"] = sum(x["eth"] for x in creation if x["k"] == "B"); rec["bundle_buys"] = sum(1 for x in creation if x["k"] == "B")
    rec["bundle_sells_creation"] = sum(1 for x in creation if x["k"] == "S")
    seat = [x for x in rows if x["bn"] == bE1 and x["k"] == "B"]
    rec["seat_buys"] = len(seat); rec["sb_n"] = max(0, len(seat) - 1); rec["sb_eth"] = sum(x["eth"] for x in seat[1:])
    a15 = [x for x in rows if bE1 < x["bn"] <= bE1 + 15 and x["k"] == "B" and x["who"] not in named]
    rec["a15_n"] = len(a15); rec["a15_w"] = len({x["who"] for x in a15}); rec["a15_eth"] = sum(x["eth"] for x in a15)
    a12 = [x for x in rows if bE1 < x["bn"] <= bE1 + 12 and x["k"] == "B" and x["who"] not in named]
    rec["a12_w"] = len({x["who"] for x in a12}); rec["a12_eth"] = sum(x["eth"] for x in a12)
    a3 = [x for x in rows if bE1 < x["bn"] <= bE1 + 3 and x["k"] == "B" and x["who"] not in named]
    rec["a3_w"] = len({x["who"] for x in a3}); rec["a3_eth"] = sum(x["eth"] for x in a3)
    a60 = [x for x in rows if bE1 + 15 < x["bn"] <= bE1 + 60 and x["k"] == "B" and x["who"] not in named]
    rec["a16_60_eth"] = sum(x["eth"] for x in a60); rec["a16_60_w"] = len({x["who"] for x in a60})
    # the bundle's (named + creator) tokens bought, and share sold by E1+15 and E1+300
    nb = sum(x["tk"] for x in rows if x["k"] == "B" and x["who"] in named)
    ns15 = sum(x["tk"] for x in rows if x["k"] == "S" and x["who"] in named and x["bn"] <= bE1 + 15)
    ns300 = sum(x["tk"] for x in rows if x["k"] == "S" and x["who"] in named and x["bn"] <= bE1 + 300)
    rec["named_sold15"] = ns15 / nb if nb else 0.0; rec["named_sold300"] = ns300 / nb if nb else 0.0
    # exit on the bundle's first sell after the seat (sold 2 blocks later: the feed and the send), else at 300
    fs = next((x["bn"] for x in rows if x["k"] == "S" and x["who"] in named and x["bn"] > bE1), None)
    rec["first_named_sell"] = (fs - bE1) if fs else None
    rec["ret_nsx"] = price(L, min(300, fs - bE1 + 2), 1) if fs and fs - bE1 + 2 < 300 else rec["ret"][300]
    rec["ret_nsx15"] = price(L, max(15, min(300, fs - bE1 + 2)), 1) if fs and fs - bE1 + 2 < 300 else rec["ret"][300]
    out.append(rec)
json.dump(out, open(C + "pop.json", "w"))
print("launches", len(out), "fit", sum(x["set"] == "fit" for x in out), "recent", sum(x["set"] == "rec" for x in out), "unpriced", missing)
