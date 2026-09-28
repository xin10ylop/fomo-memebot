"""Q1: where the live bursts landed, before and after the 12:27 settings (step 3 -> 2 ms, lead 80 -> 46 ms, 0.07 -> 0.20, new box).
From the chain's own rows (crowd_raw: every tx aimed at the curve in blocks 0..k+1, in chain order): our relay's shots in the
creation second (reverted), our first shot's position in E1 among the txs aimed at the curve, and head to head against every rival
target present in the same E1 block (did our first shot precede that rival's first?)."""
import sys, time, math; sys.path.insert(0, "."); from common import *
C = crowd(); rows = []
for cv, r in C.items():
    bl = r["blocks"]; k = r["k"]
    ours = [(off, i) for off in range(len(bl)) for i, t in enumerate(bl[off]) if t["to"] in US or t["fr"] in US]
    if not ours or r["T0"] < calendar.timegm(time.strptime("2026-09-26 00:00", "%Y-%m-%d %H:%M")): continue
    e1 = k + 1; cs = sum(1 for o, i in ours if o <= k); inE1 = [i for o, i in ours if o == e1]
    pos = min(inE1) if inE1 else None
    riv = {}
    if e1 < len(bl):
        for i, t in enumerate(bl[e1]):
            if t["to"] in US or t["fr"] in US or t["named_fr"]: continue
            key = t["to"] if not t["direct"] else t["fr"]
            riv.setdefault(key, i)
    h2h = [(key[:8], pos is not None and pos < i) for key, i in riv.items()] if pos is not None else []
    rows.append((r["T0"], cv, k, len(ours), cs, len(inE1), pos, h2h))
rows.sort()
print(f"{'when':12s} {'launch':10s} {'k':>2s} {'shots':>5s} {'in CS':>5s} {'in E1':>5s} {'E1 pos':>6s}  head-to-head vs rivals in E1 (True = we were ahead)")
agg = {"pre": [0, 0, 0, 0, 0], "post": [0, 0, 0, 0, 0]}
for T0, cv, k, n, cs, ne1, pos, h2h in rows:
    p = "post" if T0 >= SWITCH else "pre"
    a = agg[p]; a[0] += 1; a[1] += (pos == 0); a[2] += sum(1 for _, w in h2h if w); a[3] += len(h2h); a[4] += cs / max(n, 1)
    print(f"{time.strftime('%m-%d %H:%M', time.gmtime(T0))} {cv[:10]} {k:2d} {n:5d} {cs:5d} {ne1:5d} {str(pos):>6s}  {p:4s} " + " ".join(f"{a_}:{'W' if w else 'L'}" for a_, w in h2h))
print("\n(bursts held by the sequencer past E1, 22:09 Sep 27 and 14:55 Sep 28, have no row in blocks <= k+1 and are not listed)")
for p, a in agg.items():
    print(f"{p:5s}: {a[0]} bursts in E1, first at position 0 in {a[1]}, head-to-head won {a[2]} of {a[3]} ({a[2] / max(a[3], 1):.0%}), mean share of shots landing in the creation second {a[4] / max(a[0], 1):.0%}")
# how many would settle it: two-proportion, 80% power, alpha 0.05 two-sided, for the observed head-to-head rates
def need(p1, p2, za=1.96, zb=0.84):
    pb = (p1 + p2) / 2
    return math.ceil((za * math.sqrt(2 * pb * (1 - pb)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / (p1 - p2) ** 2) if p1 != p2 else float("inf")
pa = agg["pre"][2] / agg["pre"][3]; pb_ = agg["post"][2] / agg["post"][3]
print(f"head-to-head rate pre {pa:.2f} post {pb_:.2f}: to tell them apart at 80% power needs about {need(pa, pb_)} head-to-head pairs a side")
# Fisher exact on first-position bursts
from math import comb
def fisher(a, b, c, d):
    n = a + b + c + d; r1 = a + b; c1 = a + c; p0 = comb(r1, a) * comb(n - r1, c1 - a) / comb(n, c1); tot = 0
    for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1):
        p = comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1)
        if p <= p0 + 1e-12: tot += p
    return tot
pre, post = agg["pre"], agg["post"]
print(f"first in E1: pre {pre[1]}/{pre[0]}, post {post[1]}/{post[0]}: Fisher p = {fisher(pre[1], pre[0] - pre[1], post[1], post[0] - post[1]):.2f}")
print(f"head-to-head: pre {pre[2]}/{pre[3]}, post {post[2]}/{post[3]}: Fisher p = {fisher(pre[2], pre[3] - pre[2], post[2], post[3] - post[2]):.2f}")
for p1, p2 in ((0.4, 0.7), (0.5, 0.75)):
    print(f"bursts needed per side to tell P(first) {p1:.0%} from {p2:.0%} at 80% power: {need(p1, p2)}")
# the bursts whose gate opened only after the tick (no shot in the creation second) cannot test the step: every shot left late
ag2 = {"pre": [0, 0, 0, 0], "post": [0, 0, 0, 0]}
for T0, cv, k, n, cs, ne1, pos, h2h in rows:
    if cs == 0: continue
    a = ag2["post" if T0 >= SWITCH else "pre"]; a[0] += 1; a[1] += (pos == 0); a[2] += sum(1 for _, w in h2h if w); a[3] += len(h2h)
for p, a in ag2.items(): print(f"on-time gate only, {p}: first {a[1]}/{a[0]}, head-to-head {a[2]}/{a[3]} ({a[2] / a[3]:.0%})")
pre, post = ag2["pre"], ag2["post"]
print(f"  Fisher p first = {fisher(pre[1], pre[0] - pre[1], post[1], post[0] - post[1]):.2f}; head-to-head = {fisher(pre[2], pre[3] - pre[2], post[2], post[3] - post[2]):.2f}")
