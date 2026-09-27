"""features.py (reviewer D): one row per launch (all 723: 563 fit, 160 recent) with
 - the pre-tick crowd at every block of the creation second: fleets (the rule's unit), wallets, shots, direct senders, relays
 - the discovery's post-seat crowd (winners_anatomy.py's readings, at our modelled position, second in the seat block E1):
   buys behind us in the seat block, buys / ETH / distinct wallets in the 15 blocks after it (all, and outsiders = not the bundle)
 - the bundle (creation-second buyers + creator + named wallets): its ETH, its sells after the seat (block and share)
 - the price path: the value of a $13 position bought second in E1, sold after every block E1+h for h = 0..600, computed in one pass
   exactly as stake_scale.model_eff (checked against model_eff at h15 / h300 on every launch, printed)
    python3 data/derived/edge_check/D/features.py      -> D/features.json.gz"""
import sys, os, json, gzip, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
lv = c.lv; HMAX = 600
def path(L, entry, stake_eth, n_ahead=1):
    """model_eff's arithmetic, one pass: returns (list of returns after block entry+h for h=0..HMAX, g)"""
    NET = c.net_eth_of(L); rows = [r for r in L["rows"] if r["who"] not in lv.OURS]; tier = L["tier"]; ts = L["ts"]; T0 = L["T0"]; X, Y = lv.X0, lv.Y0; i = 0
    while i < len(rows) and ts.get(rows[i]["bn"], 9e18) == T0:
        r = rows[i]
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = lv.fold_buy(X, Y, r["tk"])
        else: X, Y = lv.fold_sell(X, Y, r["tk"])
        i += 1
    seen = 0; pre = []; post = []
    for r in rows[i:]:
        if r["bn"] < entry: pre.append(r)
        elif r["bn"] == entry:
            if r["k"] == "B" and seen < n_ahead: pre.append(r); seen += 1
            elif r["k"] == "B": post.append(r)
            else: (pre if seen < n_ahead else post).append(r)
        else: post.append(r)
    for r in pre:
        if r["k"] == "B":
            if 0 < r["tk"] < Y: X, Y = lv.fold_buy(X, Y, r["tk"])
        else: X, Y = lv.fold_sell(X, Y, r["tk"])
    sur = lv.SUR.get(ts.get(entry, T0) - T0, 0.0); g = stake_eth; net = g * (1 - tier - sur); tk = Y * net / (X + net)
    if tk > lv.CAP * lv.Y0: tk = lv.CAP * lv.Y0; net = X * tk / (Y - tk); g = net / (1 - tier - sur)
    X, Y = X + net, Y - tk; out = []; j = 0
    for h in range(HMAX + 1):
        while j < len(post) and post[j]["bn"] <= entry + h:
            r = post[j]; j += 1
            if r["k"] == "B":
                n = NET.get((r["bn"], r["li"]))
                if n is not None: X, Y = X + n, Y - Y * n / (X + n)
            else: X, Y = lv.fold_sell(X, Y, r["tk"])
        out.append((X * tk / (Y + tk) * (1 - tier)) / g - 1)
    return out, g
def counts(r):
    """per block offset 0..k: cumulative fleets, wallets, shots, direct senders, relays (the engine's exclusions)"""
    F, W, D, Rl = set(), set(), set(), set(); shots = 0; out = []
    for rows in r["blocks"][: r["k"] + 1]:
        for t in rows:
            if t["to"] in c.US or t["to_token"] or t["fr"] in c.US: continue
            if t["direct"]:
                if t["named_fr"]: continue
                F.add(t["fr"]); W.add(t["fr"]); D.add(t["fr"]); shots += 1
            elif not t["named_data"]:
                F.add(t["to"]); Rl.add(t["to"]); shots += 1
                if not t["named_fr"]: W.add(t["fr"])
        out.append({"f": len(F), "w": len(W), "s": shots, "d": len(D), "r": len(Rl), "fs": sorted(F)})
    return out
def feat(r):
    L = c.tape(r["cv"]); b0, k = r["b0"], r["k"]; ts, T0 = L["ts"], L["T0"]; bE1 = c.seat_block(L, b0)
    rows = [x for x in L["rows"] if x["who"] not in lv.OURS]
    bundle = {x["who"] for x in rows if ts.get(x["bn"], 9e18) == T0 and x["k"] == "B"} | {r["creator"]} | set(r["named"])
    seat = [x for x in rows if x["bn"] == bE1 and x["k"] == "B"]
    nxt = [x for x in rows if bE1 < x["bn"] <= bE1 + 15 and x["k"] == "B"]; out15 = [x for x in nxt if x["who"] not in bundle]
    held = sum(x["tk"] for x in rows if x["who"] in bundle and x["k"] == "B" and x["bn"] < bE1)
    bsell = [(x["bn"] - bE1, x["tk"]) for x in rows if x["who"] in bundle and x["k"] == "S" and x["bn"] >= bE1]
    cum = 0.0; bs = []
    for d, tk in bsell: cum += tk; bs.append((d, cum / held if held else 0.0))
    p, g = path(L, bE1, 13 / c.E)
    cn = counts(r); a = lambda j: cn[j] if 0 <= j < len(cn) else {"f": 0, "w": 0, "s": 0, "d": 0, "r": 0, "fs": []}
    return {"cv": r["cv"], "win": r["win"], "grp": r["grp"], "T0": T0, "k": k, "tier": L["tier"], "creator": r["creator"], "named": sorted(r["named"]),
            "fire": c.fire(r), "k2": a(k - 2), "k1": a(k - 1), "k3": a(k - 3), "k0": a(k),
            "seat_n": len(seat), "seat_eth": sum(x["eth"] for x in seat), "behind_n": max(0, len(seat) - 1), "behind_eth": sum(x["eth"] for x in seat[1:]),
            "n15": len(nxt), "eth15": sum(x["eth"] for x in nxt), "w15": len({x["who"] for x in nxt}),
            "on15": len(out15), "oeth15": sum(x["eth"] for x in out15), "ow15": len({x["who"] for x in out15}),
            "bundle_eth": sum(x["eth"] for x in rows if ts.get(x["bn"], 9e18) == T0 and x["k"] == "B"), "bsell": bs, "path": [round(v, 6) for v in p], "g": g}
if __name__ == "__main__":
    R = c.all_records(); out = []; dm = 0.0
    for n, r in enumerate(R):
        f = feat(r); out.append(f)
        if n % 7 == 0:
            L = c.tape(r["cv"]); e = c.seat_block(L, r["b0"])
            for h in (15, 300): dm = max(dm, abs(c.model_eff(L, 13 / c.E, e, 1, h)[0] - f["path"][h]))
    json.dump(out, gzip.open(c.DD + "features.json.gz", "wt"))
    print(len(out), "launches;", sum(f["fire"] for f in out), "fires; max |path - model_eff| at h15/h300 on every 7th launch:", f"{dm:.6f}")
