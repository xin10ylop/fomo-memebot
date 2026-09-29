#!/usr/bin/env python3
"""The first-seat economics of every ETH-paired v4 launch in a v4_launch_pull.py dataset.

Seat model (the Pons discipline, adapted to a no-tax venue): the launch is seen in its Initialize block b0; our buy lands in
b0+1 at the head of the block (seat "b1-first": the pool state after every swap of b0) or at its tail (seat "b1-last": after
every swap of b0+1), or one second late (seat "late": after every swap through b0+10). Our buy and our sell are priced against
the pool's active liquidity at that moment (single-range concentrated-liquidity math, so our own size moves the price), with
the pool's fee on both legs; the crowd's price path in between is the observed one. Gas $0.05 a round trip. Returns net.

    python3 src/analysis/v4_seat.py data/derived/edge_check/O/v4_24h.json [stake_usd=25] [eth_usd=2650]
"""
import json, sys, collections, statistics as st
D = json.load(open(sys.argv[1])); STAKE = float(sys.argv[2]) if len(sys.argv) > 2 else 25.0; ETHUSD = float(sys.argv[3]) if len(sys.argv) > 3 else 2650.0
X_IN = STAKE / ETHUSD * 1e18; GAS = 0.05; ZERO = "0" * 40; Q = 2 ** 96; HOLDS = (5, 11, 30, 100, 300, 600, 1200)
pools = D["pools"]; swaps = D["swaps"]; dop = set(D.get("doppler_assets", []))

def buy(eth_is_c0, sp, L, x):
    """ETH x (raw, after fee) into a pool at sqrtP sp (Q96), active liquidity L: (tokens out, new sqrtP)"""
    s = sp / Q
    if L <= 0 or s <= 0: return 0.0, sp
    if eth_is_c0:                                   # token0 in: 1/s' = 1/s + x/L; token1 out = L (s - s')
        s2 = 1.0 / (1.0 / s + x / L); return L * (s - s2), s2 * Q
    s2 = s + x / L; return L * (1.0 / s - 1.0 / s2), s2 * Q   # token1 in: s' = s + x/L; token0 out = L (1/s - 1/s')

def sell(eth_is_c0, sp, L, t):
    """tokens t (raw) into the pool: ETH out (raw, before fee)"""
    s = sp / Q
    if L <= 0 or s <= 0: return 0.0
    if eth_is_c0:                                   # token1 in: s' = s + t/L; token0 out = L (1/s - 1/s')
        s2 = s + t / L; return L * (1.0 / s - 1.0 / s2)
    s2 = 1.0 / (1.0 / s + t / L); return L * (s - s2)          # token0 in: 1/s' = 1/s + t/L; token1 out = L (s - s')

def state_after(sw, bn_last, pool):
    """(sqrtP, liquidity) after every swap in blocks <= bn_last; before any swap: the initial price and the first swap's liquidity"""
    prev = [x for x in sw if x[0] <= bn_last]
    if prev: return prev[-1][5], prev[-1][6]
    return pool["sqrtP0"], (sw[0][6] if sw else 0)

rows = []
for pid, p in pools.items():
    if ZERO not in (p["c0"], p["c1"]): continue
    sw = sorted(swaps.get(pid, []), key=lambda x: (x[0], x[1])); b0 = p["bn"]
    if not sw: rows.append({"pid": pid, "dead": True, "p": p}); continue
    eth_c0 = p["c0"] == ZERO; fee = (sw[0][7] if sw[0][7] is not None else p["fee"]) / 1e6
    if fee > 0.2: continue                                            # dynamic-fee flags or taxes above 20%: not this venue class
    launch = [x for x in sw if x[0] == b0]; b1 = [x for x in sw if x[0] == b0 + 1]
    eth_in_launch = sum((x[3] if eth_c0 else x[4]) for x in launch if (x[3] if eth_c0 else x[4]) < 0) * -1 / 1e18   # v4 deltas: negative = the swapper paid
    r = {"pid": pid, "dead": False, "fam": f"{p['hook'][:8]}|{p['fee']}|{p['ts']}|{'dop' if (p['c0'] in dop or p['c1'] in dop) else ''}", "fee": fee, "n_launch": len(launch), "eth_launch": eth_in_launch,
         "n_b1": len(b1), "n_b1_10": len([x for x in sw if b0 < x[0] <= b0 + 10]), "n_60s": len([x for x in sw if x[0] <= b0 + 600]), "senders_b1_10": len({x[2] for x in sw if b0 < x[0] <= b0 + 10}), "seats": {}}
    for seat, entry_last in (("b1-first", b0), ("b1-last", b0 + 1), ("late", b0 + 10)):
        sp, L = state_after(sw, entry_last, p)
        if L <= 0: continue
        tok, sp_after = buy(eth_c0, sp, L, X_IN * (1 - fee))
        if tok <= 0: continue
        impact_in = 1 - ((sp / sp_after) ** 2 if eth_c0 else (sp_after / sp) ** -2) if sp_after else None
        out = {}
        for h in HOLDS:
            sp2, L2 = state_after(sw, entry_last + h, p)
            eth_out = sell(eth_c0, sp2, L2, tok) * (1 - fee)
            out[h] = (eth_out - X_IN) / X_IN - GAS / STAKE
        r["seats"][seat] = {"ret": out, "impact_in": impact_in}
    rows.append(r)

live = [r for r in rows if not r["dead"]]; dead = [r for r in rows if r["dead"]]
print(f"{len(pools)} pools; ETH-paired {len(rows)} ({len(dead)} with no swap in 20 min); stake ${STAKE:.0f}")
def show(name, xs, seat="b1-first"):
    xs = [x for x in xs if seat in x["seats"]]
    if len(xs) < 5: print(f"  {name:44s} n={len(xs)}"); return
    line = f"  {name:44s} n={len(xs):4d}"
    for h in (11, 30, 100, 300, 1200):
        v = [x["seats"][seat]["ret"][h] for x in xs]
        line += f" | h{h}: {st.mean(v):+6.1%} med {st.median(v):+5.1%} w{sum(1 for a in v if a > 0) / len(v):.0%}"
    print(line)
    return xs
print("\nall ETH-paired launches with a swap, by seat:")
for seat in ("b1-first", "b1-last", "late"): show(f"seat {seat}", live, seat)
fams = collections.Counter(r["fam"] for r in live)
print("\nby pool family (hook|fee|tickspacing|doppler), seat b1-first:")
for f, n in fams.most_common(10): show(f, [r for r in live if r["fam"] == f])
print("\nby what is visible at the launch block, seat b1-first:")
show("creator/launch-block buy >= 0.05 ETH", [r for r in live if r["eth_launch"] >= 0.05])
show("launch-block buy 0.01-0.05 ETH", [r for r in live if 0.01 <= r["eth_launch"] < 0.05])
show("launch-block buy < 0.01 ETH", [r for r in live if r["eth_launch"] < 0.01])
show(">= 3 swaps in the launch block", [r for r in live if r["n_launch"] >= 3])
print("\ncompetition: swaps and distinct senders in blocks b0+1..b0+10:")
print(f"  swaps in b0+1: {dict(sorted(collections.Counter(min(r['n_b1'], 5) for r in live).items()))} (5 = five or more)")
print(f"  senders in b0+1..10: {dict(sorted(collections.Counter(min(r['senders_b1_10'], 5) for r in live).items()))}")
imp = [r["seats"]["b1-first"]["impact_in"] for r in live if "b1-first" in r["seats"] and r["seats"]["b1-first"]["impact_in"] is not None]
if imp: print(f"  our own entry impact at ${STAKE:.0f}: median {st.median(imp):.1%}, p90 {sorted(imp)[int(0.9 * (len(imp) - 1))]:.1%}")
json.dump(rows, open(sys.argv[1].replace(".json", f"_seat{int(STAKE)}.json"), "w"))
