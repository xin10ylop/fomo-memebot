#!/usr/bin/env python3
"""What predicts genuine demand for a Pons V2 launch. Demand = outside buyers who are neither the creator side nor
auto-buying bots (wallets that bought BOT_N or more different launches that day), their money in the six hours after launch,
whether the curve filled (4.2 ETH net for ETH launches), and the creator tax an honest (never-selling) creator would earn.
Operators (10+ launches that day) are reported apart. Features are split day by day so a pattern has to hold on both.

    python3 src/analysis/pons_demand.py data/derived/edge_check/P/census_sep28.json [more census files]
"""
import json, sys, collections, statistics as st, time
BOT_N = 20; ETH_Q = "0x" + "00" * 20
def load(path):
    C = json.load(open(path)); F = json.load(open(path.replace(".json", "_features.json"))); T = C["trades"]; E = C["eth_usd"]
    Ls = [x for x in C["launches"] if x.get("sel") == "f85f8e41" and x["curve"] in F and (x.get("quote") == ETH_Q or (x.get("quote") or "").startswith("0x5fc5360d"))]
    per_creator = collections.Counter(x["creator"] for x in C["launches"])
    buys_by_wallet = collections.defaultdict(set)
    for x in Ls:
        side = {x["creator"], x["from"]} | set(x["named"])
        for t in T.get(x["curve"], []):
            if t[2] == "B" and t[3] not in side: buys_by_wallet[t[3]].add(x["curve"])
    bots = {w for w, s in buys_by_wallet.items() if len(s) >= BOT_N}
    seen_names = {}; rows = []
    for x in sorted(Ls, key=lambda x: x["bn"]):
        f = F[x["curve"]]; dec, px = (1e18, E) if x["quote"] == ETH_Q else (1e6, 1.0)
        side = {x["creator"], x["from"]} | set(x["named"]); tr = sorted(T.get(x["curve"], []), key=lambda t: (t[0], t[1]))
        org = [t for t in tr if t[2] == "B" and t[3] not in side and t[3] not in bots]; botb = [t for t in tr if t[2] == "B" and t[3] in bots]
        net = sum(t[4] - t[6] - t[7] for t in tr if t[2] == "B") - sum(t[5] for t in tr if t[2] == "S")
        key_n = f["name"].strip().lower(); key_s = f["symbol"].strip().lower()
        copy = any(k in seen_names and seen_names[k] != x["creator"] for k in (("n", key_n), ("s", key_s)))
        for k in (("n", key_n), ("s", key_s)): seen_names.setdefault(k, x["creator"])
        dev = sum(t[4] for t in tr if t[2] == "B" and t[3] in side) / dec * px
        hour = time.gmtime(C_T0[path] + (x["bn"] - C["blocks"][0]) / 10.0).tm_hour if False else None
        rows.append({"day": path, "operator": per_creator[x["creator"]] >= 10, "serial": per_creator[x["creator"]] >= 2, "org_buyers": len({t[3] for t in org}), "org_usd": sum(t[4] for t in org) / dec * px,
                     "bot_buyers": len({t[3] for t in botb}), "filled": x["quote"] == ETH_Q and net / 1e18 >= 4.2, "tax_usd": sum(t[7] for t in tr) / dec * px, "dev_usd": dev,
                     "x": f["x"], "x_post": f["x_post"], "telegram": f["telegram"], "website": f["website"], "desc": f["description_len"] > 0, "image": bool(f["image"]),
                     "n_socials": sum(1 for k in ("x", "telegram", "website", "discord") if f[k]), "copycat": copy, "tax_bps": x.get("tax_bps") or 0, "named": len(x["named"]),
                     "quote": "ETH" if x["quote"] == ETH_Q else "USDG", "name_len": len(f["name"]), "sym_eq_name": key_n.replace(" ", "") == key_s, "bn": x["bn"]})
    lo, hi = min(r["bn"] for r in rows), max(r["bn"] for r in rows)
    for r in rows: r["hour"] = int(24 * (r["bn"] - lo) / max(1, hi - lo))       # hour of the day (the window is one UTC day)
    return rows, len(bots)
C_T0 = {}
days = []
for p in sys.argv[1:]:
    rows, nb = load(p); days.append((p.split("census_")[-1].replace(".json", ""), rows)); print(f"{p}: {len(rows)} launches, {nb} bot wallets (bought {BOT_N}+ launches)")
def real(r): return r["org_buyers"] >= 20
def line(name, pick):
    parts = []
    for d, rows in days:
        v = [r for r in rows if not r["operator"] and pick(r)]
        if not v: parts.append(f"{d}: -"); continue
        parts.append(f"{d}: n={len(v):4d} real {sum(1 for r in v if real(r))/len(v):5.1%} filled {sum(1 for r in v if r['filled'])/len(v):5.1%} org$ med {st.median(r['org_usd'] for r in v):6.0f} mean {st.mean(r['org_usd'] for r in v):7.0f} tax$ mean {st.mean(r['tax_usd'] for r in v):6.1f}")
    print(f"  {name:34s} " + " | ".join(parts))
print(f"\nNon-operator launches ('real' = 20+ genuine outside buyers in 6 h; 'filled' = the curve reached 4.2 ETH; org$ = genuine buyers' money; tax$ = what an honest creator earns):")
line("ALL", lambda r: True)
print(" socials and presentation:")
for k, lab in (("x", "X profile link"), ("x_post", "links an X post"), ("telegram", "Telegram"), ("website", "website"), ("desc", "has a description"), ("image", "has an image")):
    line(f"{lab}: yes", lambda r, k=k: r[k]); line(f"{lab}: no", lambda r, k=k: not r[k])
line("0 social links", lambda r: r["n_socials"] == 0); line("1 social link", lambda r: r["n_socials"] == 1); line("2+ social links", lambda r: r["n_socials"] >= 2)
print(" originality:")
line("copycat name/symbol (seen earlier today)", lambda r: r["copycat"]); line("original name/symbol", lambda r: not r["copycat"])
print(" launch settings:")
for lo, hi in ((0, 1), (1, 50), (50, 200), (200, 1000), (1000, 1e9)): line(f"dev buy ${lo}-{hi if hi < 1e9 else 'up'}", lambda r, lo=lo, hi=hi: lo <= r["dev_usd"] < hi)
for lo, hi in ((0, 1), (1, 200), (200, 300), (300, 2001)): line(f"creator tax {lo}-{hi} bps", lambda r, lo=lo, hi=hi: lo <= r["tax_bps"] < hi)
line("exempt wallets named: 0", lambda r: r["named"] == 0); line("exempt wallets named: 1-9", lambda r: 1 <= r["named"] <= 9); line("exempt wallets named: 10+", lambda r: r["named"] >= 10)
line("quote ETH", lambda r: r["quote"] == "ETH"); line("quote USDG", lambda r: r["quote"] == "USDG")
line("first launch of this creator today", lambda r: not r["serial"]); line("2-9 launches by this creator today", lambda r: r["serial"])
print(" timing (UTC):")
for a, b in ((0, 6), (6, 12), (12, 18), (18, 24)): line(f"launched {a:02d}-{b:02d} UTC", lambda r, a=a, b=b: a <= r["hour"] < b)
print("\nOperators (10+ launches a day), for contrast:")
for d, rows in days:
    v = [r for r in rows if r["operator"]]
    if v: print(f"  {d}: n={len(v)} real {sum(1 for r in v if real(r))/len(v):.1%} org$ mean {st.mean(r['org_usd'] for r in v):.0f} bot buyers median {st.median(r['bot_buyers'] for r in v)}")
