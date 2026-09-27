"""chain_change.py (edge_check/A): test 3, what changed on the chain for the launches the rule fires on, fit (73) vs Sep 24-27
(18). From the crowd files: fleets and rival shots by block, which relays; from the tapes (tapes.json.gz): the seat block's
crowd, the bundle's and the fleets' selling after the seat, the outsiders' buying after the seat second (follow-on demand).
Classes on the tape (the Buy/Sell event's trader = msg.sender on the curve): named = the launch's named wallets + creator;
fleet = any relay target or direct/relay sender that shot at the curve in blocks 0..k+1; early = anyone else who bought by
the seat block; outsider = everybody else.  python3 data/derived/edge_check/A/chain_change.py"""
import sys, json, gzip, statistics as st, collections, time
sys.path.insert(0, "data/derived/edge_check/A"); from common import *
T = json.load(gzip.open(A + "tapes.json.gz", "rt")); F = json.load(open(A + "fires.json")); raw = {r["cv"]: r for r in all_launches(FIT + REC)}
def shooters(r, upto):
    rel, snd, shots = set(), set(), 0
    for rows in r["blocks"][:upto + 1]:
        for t in rows:
            if t["to_token"] or t["to"] in US or t["fr"] in US or t["named_fr"] or t["named_data"]: continue
            shots += 1
            if t["direct"]: snd.add(t["fr"])
            else: rel.add(t["to"]); snd.add(t["fr"])
    return rel, snd, shots
for x in F:
    r = raw[x["cv"]]; L = T[x["cv"]]; k = r["k"]; b0 = x["b0"]; bE1 = x["bE1"]; named = set(r["named"]) | {r["creator"]}
    rel_k2, _, shots_k2 = shooters(r, k - 2); rel_all, snd_all, shots_k = shooters(r, k); rel_s, snd_s, shots_s = shooters(r, k + 1)
    fleet = rel_s | snd_s
    # which fleets at k-2 (the relay targets and direct senders that make the count)
    fl_k2 = set()
    for rows in r["blocks"][: k - 1]:
        for t in rows:
            if t["to_token"] or t["to"] in US or t["fr"] in US: continue
            if t["direct"] and not t["named_fr"]: fl_k2.add(t["fr"])
            elif not t["direct"] and not t["named_data"]: fl_k2.add(t["to"])
    rows = [e for e in L["rows"] if e["who"] not in US]; early = set()
    for e in rows:
        if e["bn"] <= bE1 and e["k"] == "B" and e["who"] not in named and e["who"] not in fleet: early.add(e["who"])
    cls = lambda w: "named" if w in named else "fleet" if w in fleet else "early" if w in early else "out"
    seat = [e for e in rows if e["bn"] == bE1 and e["k"] == "B"]
    bought = collections.Counter(); sold = collections.defaultdict(lambda: collections.Counter())
    for e in rows:
        if e["bn"] <= bE1 and e["k"] == "B": bought[cls(e["who"])] += e["tk"]
    ts = {int(a): b for a, b in L["ts"].items()}; seat_sec_end = max(n for n, t in ts.items() if t == L["T0"] + 1)
    out_eth = collections.Counter(); sell_eth = collections.Counter(); first_named_sell = None
    for e in rows:
        d = e["bn"] - bE1
        if d <= 0 or d > 300: continue
        c = cls(e["who"])
        if e["k"] == "B" and c == "out" and e["bn"] > seat_sec_end:
            out_eth["15" if d <= 15 else "60" if d <= 60 else "300"] += e["eth"]
        if e["k"] == "S":
            sell_eth[c] += e["eth"]
            for h in (15, 60, 300):
                if d <= h: sold[c][h] += e["tk"]
            if c == "named" and first_named_sell is None: first_named_sell = d
    x["creator_share"] = sum(e["tk"] for e in L["rows"] if e["k"] == "B" and e["who"] == r["creator"] and e["bn"] <= b0 + k) / 1e9
    x.update({"shots_k2": shots_k2, "shots_k": shots_k, "shots_seat": shots_s - shots_k, "fleets_k2": at(x["fleets"], k - 2), "fleets_k": at(x["fleets"], k),
              "fleets_seat": len(rel_s | {t["fr"] for rows_ in r["blocks"][:k + 2] for t in rows_ if t["direct"] and not t["named_fr"] and t["fr"] not in US and not t["to_token"]}),
              "fl_k2": sorted(fl_k2), "seat_buys": len(seat), "seat_eth": sum(e["eth"] for e in seat), "ahead_eth": seat[0]["eth"] if seat else 0.0,
              "bought_named": bought["named"], "bought_fleet": bought["fleet"], "bought_early": bought["early"],
              "named_sold_frac": {h: sold["named"][h] / bought["named"] if bought["named"] else None for h in (15, 60, 300)},
              "fleet_sold_frac": {h: (sold["fleet"][h] + sold["early"][h]) / (bought["fleet"] + bought["early"]) if bought["fleet"] + bought["early"] else None for h in (15, 60, 300)},
              "out_eth": dict(out_eth), "out_eth_total": sum(out_eth.values()), "sell_eth": dict(sell_eth), "first_named_sell": first_named_sell})
def q(v):
    v = [y for y in v if y is not None]
    return f"n {len(v):2d} mean {st.mean(v):7.3f} median {st.median(v):7.3f}" if v else "n 0"
fit = [x for x in F if x["set"] == "fit"]; rec = [x for x in F if x["set"] == "rec"]
print("=== per-fire features, fit (73) vs Sep 24-27 (18): mean / median")
feats = [("k (blocks after b0 in the creation second)", lambda x: x["k"]), ("fleets at k-2", lambda x: x["fleets_k2"]), ("fleets at k (end of creation second)", lambda x: x["fleets_k"]),
         ("fleets incl. the seat block", lambda x: x["fleets_seat"]), ("rival shots by k-2", lambda x: x["shots_k2"]), ("rival shots in the creation second", lambda x: x["shots_k"]), ("rival shots in the seat block", lambda x: x["shots_seat"]),
         ("buys in the seat block", lambda x: x["seat_buys"]), ("ETH bought in the seat block", lambda x: x["seat_eth"]), ("ETH of the buy ahead of us", lambda x: x["ahead_eth"]),
         ("bundle ETH (e1_multi)", lambda x: x["bundle_eth"]), ("tier", lambda x: x["tier"]), ("named wallets", lambda x: x["named_n"]),
         ("named tokens bought by the seat (M)", lambda x: x["bought_named"] / 1e6), ("fleet+early tokens bought by the seat (M)", lambda x: (x["bought_fleet"] + x["bought_early"]) / 1e6),
         ("share of the named's tokens sold by seat+15", lambda x: x["named_sold_frac"][15]), ("... by seat+60", lambda x: x["named_sold_frac"][60]), ("... by seat+300", lambda x: x["named_sold_frac"][300]),
         ("share of fleet+early tokens sold by seat+15", lambda x: x["fleet_sold_frac"][15]), ("... by seat+60", lambda x: x["fleet_sold_frac"][60]), ("... by seat+300", lambda x: x["fleet_sold_frac"][300]),
         ("block of the first named sell after the seat", lambda x: x["first_named_sell"]),
         ("outsider ETH bought after the seat second, to seat+15", lambda x: x["out_eth"].get("15", 0)), ("... seat+16..60", lambda x: x["out_eth"].get("60", 0)), ("... seat+61..300", lambda x: x["out_eth"].get("300", 0)),
         ("outsider ETH bought, total to seat+300", lambda x: x["out_eth_total"]), ("ETH sold by the named to seat+300", lambda x: x["sell_eth"].get("named", 0)),
         ("ETH sold by fleets+early to seat+300", lambda x: x["sell_eth"].get("fleet", 0) + x["sell_eth"].get("early", 0)), ("creator's own buy in the creation second, share of supply", lambda x: x["creator_share"])]
for n, f in feats:
    print(f"{n:52s} fit {q([f(x) for x in fit])}   recent {q([f(x) for x in rec])}")
json.dump(F, open(A + "fires_features.json", "w"), indent=0)
# which fleets: relay targets / direct senders counted at k-2
print("\n=== which fleets (the addresses counted at k-2): fires they appear in, and the mean return of those fires")
cf, cr = collections.Counter(), collections.Counter(); rf, rr = collections.defaultdict(list), collections.defaultdict(list)
for x in fit:
    for a in x["fl_k2"]: cf[a] += 1; rf[a].append(x["ret"]["300"])
for x in rec:
    for a in x["fl_k2"]: cr[a] += 1; rr[a].append(x["ret"]["300"])
for a in sorted(set(cf) | set(cr), key=lambda a: -(cf[a] + cr[a]))[:25]:
    print(f"  {a}  fit {cf[a]:3d} fires {st.mean(rf[a]) if rf[a] else float('nan'):+7.1%}   recent {cr[a]:2d} fires {st.mean(rr[a]) if rr[a] else float('nan'):+7.1%}")
new = [a for a in cr if a not in cf]
print(f"  addresses at k-2 in recent fires never seen at k-2 in a fit fire: {len(new)} of {len(cr)}; recent fires with at least one such: {sum(1 for x in rec if any(a in new for a in x['fl_k2']))} of {len(rec)}")
print(f"  recent fires whose k-2 fleets are all fit-era fleets: {sum(1 for x in rec if all(a in cf for a in x['fl_k2']))}, mean {st.mean([x['ret']['300'] for x in rec if all(a in cf for a in x['fl_k2'])]):+.1%}")
# fleets over the whole population: the share of launches each relay shoots at in the creation second
print("\n=== the busiest shooters over the whole population (share of qualifying launches shot at in blocks 0..k)")
pop = {"fit": all_launches(FIT), "rec": all_launches(REC)}; share = {}
for s, L in pop.items():
    c = collections.Counter()
    for r in L:
        rel, snd, _ = shooters(r, r["k"]); c.update(rel | {t["fr"] for rows in r["blocks"][:r["k"] + 1] for t in rows if t["direct"] and not t["named_fr"] and t["fr"] not in US and not t["to_token"]})
    share[s] = {a: n / len(L) for a, n in c.items()}
    print(f"  {s}: launches {len(L)}, mean distinct shooters (fleets) per launch in the creation second {sum(c.values())/len(L):.2f}")
for a in sorted(set(share["fit"]) | set(share["rec"]), key=lambda a: -(share["fit"].get(a, 0) + share["rec"].get(a, 0)))[:15]:
    print(f"  {a}  fit {share['fit'].get(a, 0):5.1%}  recent {share['rec'].get(a, 0):5.1%}")
# hour of day, tier, k, bundle: the fit's conditional means re-weighted to the recent mix
print("\n=== composition: the fit's mean in each bucket, re-weighted to the recent fires' mix")
def buckets(name, f):
    fb = {}
    for x in fit: fb.setdefault(f(x), []).append(x["ret"]["300"])
    rb = collections.Counter(f(x) for x in rec)
    exp = sum(st.mean(fb[b]) * n for b, n in rb.items() if b in fb) / sum(n for b, n in rb.items() if b in fb)
    print(f"  {name:28s} recent mix {dict(sorted(rb.items()))}  fit counts {dict(sorted((b, len(v)) for b, v in fb.items()))}  fit bucket means {dict(sorted((b, round(st.mean(v), 3)) for b, v in fb.items()))}  -> expected {exp:+.1%}")
buckets("hour (UTC, 6-h bins)", lambda x: x["hour"] // 6 * 6)
buckets("tier", lambda x: round(x["tier"], 3))
buckets("k (<=5, 6-7, 8+)", lambda x: 0 if x["k"] <= 5 else 6 if x["k"] <= 7 else 8)
buckets("bundle ETH (<0.5, <1, >=1)", lambda x: 0 if x["bundle_eth"] < 0.5 else 0.5 if x["bundle_eth"] < 1 else 1)
buckets("fleets at k-2 (2, 3+)", lambda x: min(x["fleets_k2"], 3))
# serial launchers
print("\n=== serial launchers: fires whose creator launched another qualifying launch in the same period")
for s, S in (("fit", fit), ("rec", rec)):
    cc = collections.Counter(r["creator"] for r in pop[s]); rep = [x for x in S if cc[x["creator"]] > 1]
    print(f"  {s}: {len(rep)} of {len(S)} fires by repeat creators" + (f", mean {st.mean([x['ret']['300'] for x in rep]):+.1%}" if rep else "") + f"; repeat creators' share of all launches {sum(1 for r in pop[s] if cc[r['creator']] > 1)/len(pop[s]):.0%}")
fitcr = {r["creator"] for r in pop["fit"]}
print(f"  recent fires whose creator also launched in the fit windows: {sum(1 for x in rec if x['creator'] in fitcr)} of {len(rec)}")

# broad shooters: an address's share of the period's qualifying launches shot at in the creation second (knowable live as a
# running count); a fire's k-2 fleets split by whether one of them is a broad shooter (>= 20% of launches in its period)
print("\n=== fires whose k-2 fleets include a broad shooter (>= 20% of the period's launches) vs not")
for s_, S in (("fit", fit), ("rec", rec)):
    br = {a for a, v in share[s_].items() if v >= 0.20}
    w = [x["ret"]["300"] for x in S if any(a in br for a in x["fl_k2"])]; wo = [x["ret"]["300"] for x in S if not any(a in br for a in x["fl_k2"])]
    ex = [x["ret"]["300"] for x in S if sum(1 for a in x["fl_k2"] if a not in br) >= 2]
    print(f"  {s_}: broad shooters {sorted(br)}; fires with one {len(w)} mean {st.mean(w) if w else float('nan'):+.1%}; without {len(wo)} mean {st.mean(wo) if wo else float('nan'):+.1%}; still >= 2 fleets without the broad ones: {len(ex)} mean {st.mean(ex) if ex else float('nan'):+.1%}")
new_ = [x["ret"]["300"] for x in rec if any(a not in cf for a in x["fl_k2"])]
print(f"  recent fires with an address never counted in a fit fire: {len(new_)} mean {st.mean(new_):+.1%}")
for x in rec:
    print(f"   {hms(x['T0'])} {x['cv'][:10]} h300 {x['ret']['300']:+6.1%} k {x['k']} fleets@k-2 {x['fleets_k2']} " + " ".join(f"{a[:8]}({'fit' if a in cf else 'NEW'},{share['rec'].get(a,0):.0%})" for a in x["fl_k2"]) + f"  named sold by +300 {x['named_sold_frac'][300] if x['named_sold_frac'][300] is not None else float('nan'):.0%} outsider ETH {x['out_eth_total']:.2f}")
print("\n=== composition by crowd size (rival shots; k-2 is known at the decision, the rest after it)")
buckets("rival shots by k-2 (<6, 6-19, 20+)", lambda x: 0 if x["shots_k2"] < 6 else 6 if x["shots_k2"] < 20 else 20)
buckets("rival shots creation sec (<25, 25-79, 80+)", lambda x: 0 if x["shots_k"] < 25 else 25 if x["shots_k"] < 80 else 80)
buckets("buys in the seat block (<=2, 3-5, 6+)", lambda x: 2 if x["seat_buys"] <= 2 else 5 if x["seat_buys"] <= 5 else 6)
buckets("fleets incl. seat block (<=4, 5-8, 9+)", lambda x: 4 if x["fleets_seat"] <= 4 else 8 if x["fleets_seat"] <= 8 else 9)
