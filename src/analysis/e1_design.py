"""design questions on the five days: contested vs alone, the minOut-as-position-filter, predictors of bot presence, stake, hours."""
import json, glob, statistics as st, collections, time, sys
L = []
for f in sorted(glob.glob((sys.argv[1] + "/" if len(sys.argv) > 1 else "") + "e1m_*.json")):
    d = json.load(open(f)); L += [dict(l, day=time.strftime("%b %d", time.gmtime(d["t_lo"]))) for l in d["launches"]]
def m(xs): return f"{st.mean(xs):+6.1%} med {st.median(xs):+6.1%} win {sum(x>0 for x in xs)/len(xs):3.0%} n {len(xs):3d}" if xs else "n/a"
F = lambda l: l["res"]["E1_first_h15_250"][0]; LA = lambda l: l["res"]["E1_last_h15_250"][0]
con = [l for l in L if l["e1_block_buyers"]]; unc = [l for l in L if not l["e1_block_buyers"]]
print("=== alone in the block vs contested, five days pooled")
print(f"  alone ({len(unc)}/{len(L)} = {len(unc)/len(L):.0%}):      first {m([F(l) for l in unc])}")
print(f"  contested, first:               {m([F(l) for l in con])}")
print(f"  contested, last:                {m([LA(l) for l in con])}")
print("  by day: alone share / alone value / contested-first / contested-last")
for day in sorted(set(l["day"] for l in L), key=lambda d: [l["day"] for l in L].index(d)):
    u = [l for l in L if l["day"] == day and not l["e1_block_buyers"]]; c = [l for l in L if l["day"] == day and l["e1_block_buyers"]]
    print(f"    {day}: {len(u)/(len(u)+len(c)):4.0%} / {st.mean(F(l) for l in u) if u else 0:+6.1%} / {st.mean(F(l) for l in c):+6.1%} / {st.mean(LA(l) for l in c):+6.1%}")
# the minOut rule as a position filter: a fill behind the crowd yields fewer tokens; if the drop exceeds the tolerance the buy reverts (gas)
print("\n=== minOut tolerance as a position filter (a 'last' landing fills only if the crowd ahead moved the price less than the tolerance)")
X0, Y0 = 1.68, 1e9
for tol in (0.02, 0.03, 0.05, 0.10, 0.25):
    ev_last = []; fills = 0
    for l in con:
        X1 = X0 + 0.035 * 0.99 + l["bundle_eth"] * (1 - l["tier"]); ratio = (X1 / (X1 + l["e1_block_eth"])) ** 2
        if ratio >= 1 - tol: ev_last.append(LA(l)); fills += 1
        else: ev_last.append(-0.0004)
    print(f"  tolerance {tol:4.0%}: behind the crowd -> fills {fills/len(con):4.0%} of the time, mean {st.mean(ev_last):+6.1%}  (vs {st.mean(LA(l) for l in con):+6.1%} filling always)")
# EV vs win share with the 3% rule
X = lambda l: (X0 + 0.035 * 0.99 + l["bundle_eth"] * (1 - l["tier"]))
last3 = [LA(l) if (X(l) / (X(l) + l["e1_block_eth"])) ** 2 >= 0.97 else -0.0004 for l in con]
u = st.mean(F(l) for l in unc); f = st.mean(F(l) for l in con); g = st.mean(last3); pu = len(unc) / len(L); n_day = len(L) / 5
print(f"\n=== expected value per trade by the share of contested blocks we win (3% minOut, alone always ours at {u:+.1%})")
for p in (0.0, 0.25, 0.5, 0.75, 1.0):
    ev = pu * u + (1 - pu) * (p * f + (1 - p) * g); print(f"  win {p:4.0%} -> {ev:+6.1%} a trade, {ev * 250 * n_day:+8,.0f} $/day at $250")
# what predicts bot presence?
print("\n=== who gets a crowd: share of launches with other buys in the block, by feature")
def by(key, fn, bins):
    print(f"  {key}:")
    for lo, hi in bins:
        g_ = [l for l in L if lo <= fn(l) < hi]
        if g_: print(f"    [{lo}, {hi}): n {len(g_):3d}  contested {sum(1 for l in g_ if l['e1_block_buyers'])/len(g_):4.0%}  first {st.mean(F(l) for l in g_):+6.1%}  last {st.mean(LA(l) for l in g_):+6.1%}")
by("bundle ETH", lambda l: l["bundle_eth"], [(0.3, 0.5), (0.5, 0.8), (0.8, 1.2), (1.2, 2.0), (2.0, 99)])
by("tier", lambda l: round(l["tier"], 4), [(0.02, 0.0225), (0.0225, 0.0275), (0.0275, 0.0301)])
by("blocks left in the creation second after the creation block", lambda l: l["same_second_blocks"], [(0, 3), (3, 6), (6, 12)])
by("hour UTC", lambda l: l["hour"], [(0, 4), (4, 8), (8, 12), (12, 16), (16, 20), (20, 24)])
# number of others in the block vs first value (the more bots behind us, the better)
print("\n=== first value by the number of other buys in the block")
byn = collections.defaultdict(list)
for l in L: byn[min(len(l["e1_block_buyers"]), 6)].append(F(l))
for k, v in sorted(byn.items()): print(f"  {k}{'+' if k == 6 else ''} others: n {len(v):3d}  first {st.mean(v):+6.1%}  med {st.median(v):+6.1%}")
# stake capacity: $10 vs $250 at first
print(f"\n=== stake: first at $10 {st.mean(l['res']['E1_first_h15_10'][0] for l in L):+.1%} vs $250 (3% cap) {st.mean(F(l) for l in L):+.1%}; capped launches (stake < $250): {sum(1 for l in L if l['res']['E1_first_h15_250'][1] < 249)/len(L):.0%}, mean stake ${st.mean(l['res']['E1_first_h15_250'][1] for l in L):.0f}")
