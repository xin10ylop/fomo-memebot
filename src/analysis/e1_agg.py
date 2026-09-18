"""aggregate e1m_*.json: both seats by day, position and hold; who occupies the E1 block; hours."""
import json, glob, time, statistics as st, collections, sys
files = sorted(glob.glob(sys.argv[1] + "/e1m_*.json" if len(sys.argv) > 1 else "e1m_*.json"))
days = []
for f in files:
    d = json.load(open(f)); L = d["launches"]
    if not L: continue
    days.append((d["t_lo"], d["t_hi"], L, d["creations"]))
days.sort()
def row(L, key):
    v = [l["res"][key] for l in L if key in l["res"]]; roi = [x[0] for x in v]; usd = [x[0] * x[1] for x in v]
    return len(v), st.mean(roi), st.median(roi), sum(x > 0 for x in roi) / len(roi), sum(x < -0.2 for x in roi) / len(roi), st.mean(usd)
print("=== both legal outside seats with real second boundaries, per day (tier 2-3%, >=3 named, bundle >=0.3 ETH, hold 15 blocks = 1.5 s, $250 capped at 3% of supply)")
print(f"{'day (UTC)':22s} {'n':>4s} {'/day':>5s} | {'E1 first':>9s} {'med':>6s} {'win':>4s} | {'E1 last':>8s} {'med':>6s} {'win':>4s} | {'E1 +1blk':>8s} | {'E2 first':>9s} {'med':>6s} | {'E2 last':>8s} {'med':>6s} | {'$/day E1 first':>14s} {'E1 last':>8s}")
allL = []
for t_lo, t_hi, L, n_cre in days:
    allL += L; day = (t_hi - t_lo) / 86400
    a = row(L, "E1_first_h15_250"); b = row(L, "E1_last_h15_250"); c = row(L, "E1_late1_h15_250"); d2 = row(L, "E2_first_h15_250"); e = row(L, "E2_last_h15_250")
    print(f"{time.strftime('%b %d %H:%M', time.gmtime(t_lo)):22s} {len(L):4d} {len(L)/day:5.0f} | {a[1]:+9.1%} {a[2]:+6.1%} {a[3]:4.0%} | {b[1]:+8.1%} {b[2]:+6.1%} {b[3]:4.0%} | {c[1]:+8.1%} | {d2[1]:+9.1%} {d2[2]:+6.1%} | {e[1]:+8.1%} {e[2]:+6.1%} | {a[5]*len(L)/day:+14.0f} {b[5]*len(L)/day:+8.0f}")
print(f"\n=== all days pooled: {len(allL)} launches over {sum((h-l) for l,h,_,_ in days)/86400:.1f} days")
print(f"{'variant':26s} {'n':>4s} {'mean':>7s} {'median':>7s} {'win':>4s} {'dead':>5s} {'$/trade':>8s}")
for key in ("E1_first_h15_250", "E1_first_h30_250", "E1_first_h60_250", "E1_first_h60tp50_250", "E1_last_h15_250", "E1_last_h30_250", "E1_last_h60_250", "E1_last_h60tp50_250", "E1_late1_h15_250", "E1_late1_h30_250",
            "E2_first_h15_250", "E2_first_h30_250", "E2_first_h60_250", "E2_last_h15_250", "E2_last_h30_250", "E2_last_h60_250", "E1_first_h15_10", "E1_last_h15_10"):
    n, m, md, w, dd, usd = row(allL, key); print(f"{key:26s} {n:4d} {m:+7.1%} {md:+7.1%} {w:4.0%} {dd:5.0%} {usd:+8.2f}")
# the E1 block's occupants
occ = collections.Counter(); n_empty = 0; n_buys = []
for l in allL:
    b = l["e1_block_buyers"]; n_buys.append(len(b)); n_empty += not b
    for w in set(b): occ[w] += 1
print(f"\n=== the first block of the next second: launches with nobody else in it {n_empty}/{len(allL)} ({n_empty/len(allL):.0%}); other buys per launch mean {st.mean(n_buys):.1f}, median {st.median(n_buys):.0f}")
print("   most frequent occupants (buyer address in the Buy event, launches present / all launches):")
for w, c in occ.most_common(8): print(f"     {w}  {c:4d} / {len(allL)}  ({c/len(allL):.0%})")
top = [w for w, c in occ.most_common(3)]
covered = sum(1 for l in allL if any(w in top for w in l["e1_block_buyers"]))
print(f"   launches where at least one of the top-3 occupants is in the block: {covered}/{len(allL)} ({covered/len(allL):.0%})")
# same-second blocks and the E2 block
print(f"   blocks sharing the creation's second after the creation block: median {st.median(l['same_second_blocks'] for l in allL):.0f}; E2-block other buys mean {st.mean(len(l['e2_block_buyers']) for l in allL):.1f}, empty {sum(1 for l in allL if not l['e2_block_buyers'])/len(allL):.0%}")
# hours
byh = collections.defaultdict(list)
for l in allL: byh[l["hour"]].append(l["res"]["E1_first_h15_250"][0])
print("\n=== E1 first, by hour UTC: n / mean")
print("  " + "  ".join(f"{h:02d}:{len(v)}/{st.mean(v):+.0%}" for h, v in sorted(byh.items())))
