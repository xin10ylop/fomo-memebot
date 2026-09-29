#!/usr/bin/env python3
"""Creator profit on Pons V2 from a census file (pons_creator_census.py): per launch and per creator, with where the money
comes from (creator tax on every trade vs the creator side's own round trip) and who pays it (outside buyers).

    python3 src/analysis/pons_creator_profit.py data/derived/edge_check/P/census_sep28.json
"""
import json, sys, collections, statistics as st
C = json.load(open(sys.argv[1])); ETHUSD = C["eth_usd"]; L = C["launches"]; T = C["trades"]
ETH_Q = "0x" + "00" * 20
def unit(q):
    if q == ETH_Q: return 1e18, ETHUSD
    if q and q.startswith("0x5fc5360d"): return 1e6, 1.0                   # USDG, 6 decimals
    return None, None
rows = []; skipped = collections.Counter()
for x in L:
    dec, px = unit(x.get("quote"))
    if dec is None: skipped["quote not ETH/USDG" if x.get("quote") else f"other launch path {x.get('sel')}"] += 1; continue
    tr = sorted(T.get(x["curve"], []), key=lambda t: (t[0], t[1]))
    side = {x["creator"], x["from"]} | set(x["named"])
    usd = lambda v: v / dec * px
    tax = sum(t[7] for t in tr); fee = sum(t[6] for t in tr)
    buy_side = sum(t[4] for t in tr if t[2] == "B" and t[3] in side); sell_side = sum(t[5] for t in tr if t[2] == "S" and t[3] in side)
    tok_b = sum(t[5] for t in tr if t[2] == "B" and t[3] in side); tok_s = sum(t[4] for t in tr if t[2] == "S" and t[3] in side)
    buy_out = sum(t[4] for t in tr if t[2] == "B" and t[3] not in side); sell_out = sum(t[5] for t in tr if t[2] == "S" and t[3] not in side)
    last = tr[-1] if tr else None
    lastpx = ((last[4] / last[5]) if last[2] == "B" else (last[5] / last[4])) if last and last[5] and last[4] else 0.0   # quote per token (raw)
    unsold = max(0, tok_b - tok_s)
    launch_fee = 0.0005 * ETHUSD
    cons = usd(tax) + usd(sell_side) - usd(buy_side) - launch_fee
    marked = cons + usd(unsold * lastpx * 0.97)
    outsiders = {t[3] for t in tr if t[3] not in side}
    first_side_sell = next((t[0] for t in tr if t[2] == "S" and t[3] in side), None)
    rows.append({"creator": x["creator"], "from": x["from"], "curve": x["curve"], "named": len(x["named"]), "tax_bps": x.get("tax_bps"), "quote": "ETH" if x["quote"] == ETH_Q else "USDG",
                 "tax_usd": usd(tax), "side_buy_usd": usd(buy_side), "side_sell_usd": usd(sell_side), "side_trade_usd": usd(sell_side) - usd(buy_side), "profit_cons": cons, "profit_marked": marked,
                 "outside_in_usd": usd(buy_out), "outside_out_usd": usd(sell_out), "outsiders": len(outsiders), "volume_usd": usd(sum(t[4] for t in tr if t[2] == "B") + sum(t[5] for t in tr if t[2] == "S")),
                 "platform_fee_usd": usd(fee), "sold_blocks": (first_side_sell - x["bn"]) if first_side_sell else None, "unsold_share": (unsold / tok_b) if tok_b else None})
print(f"{sys.argv[1]}: {len(L)} launches; priced {len(rows)}; skipped {dict(skipped)}")
q = lambda v, a: sorted(v)[int(a * (len(v) - 1))]
pc = [r["profit_cons"] for r in rows]; pm = [r["profit_marked"] for r in rows]
print(f"\nPER LAUNCH (USD, unsold tokens at zero / at the last price):")
print(f"  total creator profit ${sum(pc):,.0f} / ${sum(pm):,.0f}; mean ${st.mean(pc):.2f} / ${st.mean(pm):.2f}; median ${st.median(pc):.2f}; p90 ${q(pc,.9):.0f}; p99 ${q(pc,.99):,.0f}; max ${max(pc):,.0f}")
print(f"  launches in profit {sum(1 for v in pc if v > 0)/len(pc):.0%}; over $100 {sum(1 for v in pc if v > 100)}; over $1,000 {sum(1 for v in pc if v > 1000)}; over $10,000 {sum(1 for v in pc if v > 10000)}")
print(f"  where it comes from: creator tax ${sum(r['tax_usd'] for r in rows):,.0f}; the creator side's own round trip ${sum(r['side_trade_usd'] for r in rows):,.0f}; launch fees ${-0.0005*ETHUSD*len(rows):,.0f}")
print(f"  who pays: outside buyers put in ${sum(r['outside_in_usd'] for r in rows):,.0f} and took out ${sum(r['outside_out_usd'] for r in rows):,.0f}; platform fees and snipe tax ${sum(r['platform_fee_usd'] for r in rows):,.0f}")
by = collections.defaultdict(list)
for r in rows: by[r["creator"]].append(r)
cr = sorted(((c, sum(r["profit_cons"] for r in v), len(v)) for c, v in by.items()), key=lambda z: -z[1])
tot = sum(z[1] for z in cr if z[1] > 0)
print(f"\nPER CREATOR: {len(cr)} creators; in profit {sum(1 for z in cr if z[1] > 0)}; top 10 take {sum(z[1] for z in cr[:10])/tot:.0%} of all positive profit, top 1% ({max(1,len(cr)//100)}) take {sum(z[1] for z in cr[:max(1,len(cr)//100)])/tot:.0%}")
print(f"  launches per creator: 1 launch {sum(1 for z in cr if z[2]==1)}, 2-9 {sum(1 for z in cr if 2<=z[2]<=9)}, 10+ {sum(1 for z in cr if z[2]>=10)}")
print(f"\nTOP 15 CREATORS (profit with unsold at zero):")
print(f"  {'creator':12s} {'launches':>8s} {'profit':>9s} {'from tax':>9s} {'own trades':>10s} {'named/launch':>12s} {'tax bps':>7s} {'their buy':>9s} {'outside in':>10s} {'buyers':>6s} {'sold after':>10s}")
for c, p, n in cr[:15]:
    v = by[c]
    print(f"  {c[:12]} {n:8d} {p:9,.0f} {sum(r['tax_usd'] for r in v):9,.0f} {sum(r['side_trade_usd'] for r in v):10,.0f} {st.median(r['named'] for r in v):12.0f} {st.median([r['tax_bps'] or 0 for r in v]):7.0f} {st.median(r['side_buy_usd'] for r in v):9,.0f} {sum(r['outside_in_usd'] for r in v):10,.0f} {st.median(r['outsiders'] for r in v):6.0f} {str(st.median([r['sold_blocks'] for r in v if r['sold_blocks'] is not None]) if any(r['sold_blocks'] is not None for r in v) else '-'):>10s}")
print(f"\nWHAT SEPARATES THE PROFITABLE LAUNCHES (median profit, share in profit, n):")
def split(name, key, buckets):
    for lo, hi in buckets:
        v = [r for r in rows if key(r) is not None and lo <= key(r) < hi]
        if v: print(f"  {name} [{lo}, {hi}): n={len(v):5d} mean ${st.mean(r['profit_cons'] for r in v):8.2f} median ${st.median(r['profit_cons'] for r in v):7.2f} in profit {sum(1 for r in v if r['profit_cons'] > 0)/len(v):4.0%}  tax share of profit {sum(r['tax_usd'] for r in v)/max(1e-9, sum(max(0, r['profit_cons']) for r in v)):.0%}")
split("named exempt wallets", lambda r: r["named"], [(0, 1), (1, 3), (3, 10), (10, 20), (20, 40)])
split("creator tax bps", lambda r: r["tax_bps"], [(0, 1), (1, 100), (100, 200), (200, 400), (400, 2001)])
split("creator side's buy $", lambda r: r["side_buy_usd"], [(0, 1), (1, 25), (25, 100), (100, 500), (500, 1e9)])
split("launches by this creator that day", lambda r: len(by[r["creator"]]), [(1, 2), (2, 10), (10, 100), (100, 100000)])
json.dump(rows, open(sys.argv[1].replace(".json", "_profit.json"), "w"))
