"""features.py (reviewer B): per launch (every launch of the 15 crowd files whose tape is cached), the rule's inputs and what
happened on the chain after the seat: fleets by block, shots, the seat block, the bundle, who sold in the 300 blocks after the
seat and when, the follow-on demand, the model's returns at 15/60/300 blocks (stake_scale.model_eff, $13, second place in the
seat block E1, exactly reach_table's pricing). Writes features.json.
    python3 data/derived/edge_check/B/features.py"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
_saved = list(sys.argv); sys.argv = ["x"]
exec(open("src/analysis/stake_scale.py").read().split("\nfor name, cf, hours in W:")[0])   # model_eff, E, GAS
sys.argv = _saved
import live_vs_table as lv
def load_tape(cv):
    L = c.tape(cv)
    if L is None: return None
    L["ts"] = {int(k): v for k, v in L["ts"].items()}; return L
def bundle_eth(L):
    X, Y = lv.X0, lv.Y0; b = 0.0; ts = L["ts"]; T0 = L["T0"]
    for i, r in enumerate(L["rows"]):
        if ts.get(r["bn"], 9e18) != T0: break
        if r["k"] == "B":
            if 0 < r["tk"] < Y:
                net = X * r["tk"] / (Y - r["tk"]); fee = 1 - net / r["eth"] if r["eth"] > 0 else 1; X, Y = lv.fold_buy(X, Y, r["tk"])
                if i > 0 and abs(fee - L["tier"]) <= 0.0008: b += r["eth"]
        else: X, Y = lv.fold_sell(X, Y, r["tk"])
    return b
def feat(r, grp):
    L = load_tape(r["cv"])
    if L is None or L["tier"] is None: return None
    b0, k, ts, T0 = r["b0"], r["k"], L["ts"], L["T0"]
    bE1 = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
    bE2 = next((n for n in range(b0 + 1, b0 + 31) if ts.get(n, 0) == T0 + 2), None)
    if bE1 is None: return None
    fb = c.fleets_by_block(r); cw, cf = c.cums(r)
    f_k2 = set(x[1] for rows in fb[: max(0, k - 1)] for x in rows) if k >= 2 else set()
    f_all = set(x[1] for rows in fb[: k + 2] for x in rows)
    shots_cs = sum(len(rows) for rows in fb[: k + 1]); shots_seat = len(fb[k + 1]) if len(fb) > k + 1 else 0
    rows = L["rows"]
    # identities: the bundle (creation-second buyers, creator, named), the fleets' recipients (seat-block buys joined to the crowd's shots)
    bundle = {x["who"] for x in rows if ts.get(x["bn"], 9e18) == T0 and x["k"] == "B"} | {r["creator"]} | set(r["named"])
    shot_fleet = {}
    if len(r["blocks"]) > k + 1:
        for t in r["blocks"][k + 1]:
            if t["to"] in c.US or t["fr"] in c.US or t["to_token"]: continue
            fid = t["fr"] if t["direct"] else t["to"]; shot_fleet[(b0 + k + 1, t["ix"])] = (fid, t["named_fr"] or t["named_data"])
    fleet_who = {}
    for x in rows:
        if x["bn"] == bE1 and x["k"] == "B":
            s = shot_fleet.get((x["bn"], x["ti"]))
            if s and not s[1] and x["who"] not in bundle: fleet_who[x["who"]] = s[0]
    seat_buys = [x for x in rows if x["bn"] == bE1 and x["k"] == "B" and x["who"] not in lv.OURS]
    e1sec_last = max((n for n in range(bE1, b0 + 31) if ts.get(n, 0) == T0 + 1), default=bE1)
    hold_to = bE1 + 300
    def cls(w):
        if w in lv.OURS: return "us"
        if w in bundle: return "bundle"
        if w in fleet_who: return "fleet"
        return "other"
    # tokens held by class after the seat second (for the share sold)
    held = collections.Counter(); sold_by = {h: collections.Counter() for h in (15, 60, 150, 300)}
    sell_eth = collections.Counter(); first_sell = {}; buy_eth_after = collections.Counter(); outsiders = set()
    for x in rows:
        cl = cls(x["who"])
        if x["k"] == "B" and x["bn"] <= e1sec_last: held[cl] += x["tk"]
        if x["bn"] < bE1 or x["bn"] > hold_to: continue
        if x["k"] == "S":
            sell_eth[cl] += x["eth"]; first_sell.setdefault(cl, x["bn"] - bE1)
            for h in sold_by:
                if x["bn"] <= bE1 + h: sold_by[h][cl] += x["tk"]
        elif x["bn"] > e1sec_last:
            buy_eth_after[cl] += x["eth"]
            if cl == "other": outsiders.add(x["who"])
    ret = {}
    for h in (15, 60, 300):
        try: ret[h] = model_eff(L, 13 / E, bE1, 1, h)[0]
        except Exception: ret[h] = None
    creation_buys = [x for x in rows if ts.get(x["bn"], 9e18) == T0 and x["k"] == "B"]
    creator_tk = sum(x["tk"] for x in creation_buys if x["who"] == r["creator"])
    return {"cv": r["cv"], "win": r["win"], "grp": grp, "T0": T0, "hour": (T0 // 3600) % 24, "b0": b0, "k": k, "bE1": bE1, "bE2": bE2,
            "tier": L["tier"], "named": len(r["named"]), "creator": r["creator"], "named_set": sorted(r["named"]), "fire": c.at(cf, k - 2) >= 2,
            "cf": cf, "cw": cw, "f_k2": sorted(f_k2), "f_all": sorted(f_all), "n_f_k2": len(f_k2), "n_f_all": len(f_all), "shots_cs": shots_cs, "shots_seat": shots_seat,
            "seat_n": len(seat_buys), "seat_eth": sum(x["eth"] for x in seat_buys), "fleet_who": fleet_who,
            "bundle_eth": bundle_eth(L), "creation_eth": sum(x["eth"] for x in creation_buys), "creator_share": creator_tk / lv.Y0,
            "held": dict(held), "sold": {h: dict(v) for h, v in sold_by.items()}, "sell_eth": dict(sell_eth), "first_sell": first_sell,
            "buy_eth_after": dict(buy_eth_after), "n_outsiders": len(outsiders), "ret": ret, "tape_to": L.get("to")}
if __name__ == "__main__":
    out = []; miss = 0
    for grp, files in (("fit", c.FIT), ("recent", c.RECENT)):
        for r in c.load(files):
            f = feat(r, grp)
            if f is None: miss += 1; continue
            out.append(f)
    json.dump(out, open(c.B + "features.json", "w"))
    print(len(out), "launches with tapes;", miss, "without;", sum(f["fire"] for f in out), "fires")
