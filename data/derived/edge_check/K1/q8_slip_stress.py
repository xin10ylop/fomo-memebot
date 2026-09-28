"""K1/q8_slip_stress.py: the one change K1 recommends (BURST_SLIP 0.07 -> 0.20), attacked. (1) the landing position: if every burst
lands at position p (first, second, third, last in E1), which launches fill under each slip (the tokens at p against 1-slip of the
tokens sized at the build) and what they return; (2) the gain by day and without its best launches; (3) a bootstrap of the gain on
the read half; (4) what the change adds per day on the Sep 24-28 supply at $13; (5) the sequential test's arithmetic."""
import sys, os, json, math, random, statistics as st, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from k1 import *
R = load(); TK = json.load(open(os.path.join(HERE, "tokens.json")))
print("== (1) by assumed landing position, fires at k-1 with tapes; $ at $13 after gas (every fired burst pays $0.33) ==")
D = decide(R, view="k-1", slip=1.0); F = [d["r"] for d in D if d["why"] == "FILL" and d["r"]["cv"] in TK and d["r"].get("p1")]
POS = (("first", "first", "p1"), ("second", "seat1", "p2"), ("third", "seat2", "p3"), ("last", "last", "plast"))
for lab, tkk, rk in POS:
    line = []
    for part in ("fit", "read"):
        s = [r for r in F if r["set"] == part]; cells = []
        for slip in (0.07, 0.15, 0.20):
            fl = [r for r in s if TK[r["cv"]][tkk] >= (1 - slip) * TK[r["cv"]]["build"]]
            usd = sum(r[rk][11] * STAKE for r in fl) - GAS * len(s); cells.append(f"{slip:.2f}: {len(fl):2d}/{len(s)} fill {mean([r[rk][11] for r in fl]):+6.1%} ${usd:+7.2f}")
        line.append(f"{part} " + "  ".join(cells))
    print(f"  land {lab:6s} | " + " | ".join(line))
mix = {"first": 0.25, "second": 0.45, "third": 0.15, "last": 0.15}
for part in ("fit", "read"):
    s = [r for r in F if r["set"] == part]; out = []
    for slip in (0.07, 0.15, 0.20):
        u = 0.0
        for lab, tkk, rk in POS:
            u += mix[lab] * (sum(r[rk][11] * STAKE for r in s if TK[r["cv"]][tkk] >= (1 - slip) * TK[r["cv"]]["build"]) - GAS * len(s))
        out.append(f"{slip:.2f} ${u:+7.2f}")
    print(f"  landing mix {mix}: {part} " + "  ".join(out))
print("\n== (2) the gain (slip 0.20 minus 0.07, second place) by day, usual view ==")
A = {d["r"]["cv"]: d for d in decide(R, view="k-1", slip=0.07)}; Bd = {d["r"]["cv"]: d for d in decide(R, view="k-1", slip=0.20)}
gain = collections.defaultdict(list)
for cv, b in Bd.items():
    a = A[cv]
    if a["why"] != b["why"] or abs(a["usd"] - b["usd"]) > 1e-9: gain[b["r"]["day"]].append((b["usd"] - a["usd"], cv, b["r"]))
for dy in sorted(gain, key=lambda d: time.strptime(d + " 2026", "%b %d %Y")):
    v = gain[dy]; print(f"  {dy}: {len(v):2d} bursts change, gain ${sum(x[0] for x in v):+6.2f}; first E1 buyers: {collections.Counter((x[2].get('e1_buys') or [[0, 'untaped']])[0][1][:10] for x in v).most_common(3)}")
for part in ("fit", "read"):
    v = sorted([x[0] for dy in gain for x in gain[dy] if x[2]["set"] == part], reverse=True)
    print(f"  {part}: {len(v)} bursts, gain ${sum(v):+.2f}; without the best 1 ${sum(v[1:]):+.2f}, best 3 ${sum(v[3:]):+.2f}; median gain per burst ${st.median(v):+.2f}; positive {sum(x > 0 for x in v)}/{len(v)}")
print("\n== (3) bootstrap of the read half's gain (resampling the changed bursts), 10,000 draws ==")
for part in ("fit", "read"):
    v = [x[0] for dy in gain for x in gain[dy] if x[2]["set"] == part]; rnd = random.Random(7)
    bs = sorted(sum(rnd.choice(v) for _ in v) for _ in range(10000)); print(f"  {part}: gain ${sum(v):+.2f}, 90% interval ${bs[500]:+.2f} to ${bs[9500]:+.2f}, P(gain <= 0) = {sum(b <= 0 for b in bs) / 1e4:.3f}")
print("\n== (4) dollars a day at $13 on the Sep 24-28 supply (read half, 105.7 h) ==")
for slip in (0.07, 0.15, 0.20):
    s = summ(decide(R, view="k-1", slip=slip), "read"); print(f"  slip {slip:.2f}: {fmt(s)}")
s26 = [d for d in decide(R, view="k-1", slip=0.20) if d["r"]["T0"] >= 1790380800]; s7 = [d for d in decide(R, view="k-1", slip=0.07) if d["r"]["T0"] >= 1790380800]
print(f"  Sep 26-28 only (57.7 h): slip 0.07 ${sum(d['usd'] for d in s7 if d['why'] in ('FILL','GUARD')):+.2f}, slip 0.20 ${sum(d['usd'] for d in s26 if d['why'] in ('FILL','GUARD')):+.2f}")
for v in ("k-2", "k"):
    a, b = summ(decide(R, view=v, slip=0.07), "read"), summ(decide(R, view=v, slip=0.20), "read"); print(f"  view {v}: read slip 0.07 ${a['usd']:+.2f} ({a['fills']} fills) -> 0.20 ${b['usd']:+.2f} ({b['fills']} fills, {b['mean']:+.1%})")
print("\n== (5) the sequential test (H0 +2.5%, H1 +19%, sd 0.34, bounds +-2.944) ==")
m0, m1, sd = 0.025, 0.19, 0.34; A_ = math.log(19)
def drift(m): return (m1 - m0) / sd ** 2 * (m - (m0 + m1) / 2)
for m in (0.025, 0.079, 0.10, 0.13, 0.16, 0.19):
    d = drift(m); print(f"  true mean per fill {m:+.1%}: drift per fill {d:+.3f} -> fills to reach {'+' if d > 0 else '-'}2.94 about {A_ / abs(d):.0f}" if abs(d) > 1e-6 else f"  true mean {m:+.1%}: no drift")
for part in ("fit", "read"):
    for slip in (0.07, 0.20):
        s = summ(decide(R, view="k-1", slip=slip), part); print(f"  {part} slip {slip:.2f}: per-fill mean {s['mean']:+.1%} sd {s['sd']:.2f} on {s['fills']} fills")
