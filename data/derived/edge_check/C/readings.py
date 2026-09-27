"""readings.py (edge_check/C): question 1, part two, and question 2. Which reading of the discovery survives, on the fit windows
and on the recent ones, all on one yardstick (C/pop.json: model_eff, second place in E1, $13, gas $0.33 a burst).
Readings: no gate; the rule (fleets >= 2 at k-2); the post-seat crowd as an oracle (not tradable); whether the rule's gate is a
proxy for the post-seat crowd; the hold 15/60/150/300; the combination (the gate, then a hold decided at E1+12 by the post-seat
crowd: tradable). Then the 15-block rule against the 300-block rule by window and day by day, the position, the dumps.
    python3 data/derived/edge_check/C/readings.py > data/derived/edge_check/C/readings.txt"""
import sys, json, statistics as st, random, math
sys.path.insert(0, "data/derived/edge_check/C"); from common import *
P = [x for x in json.load(open(C + "pop.json")) if x["ret"] is not None]
for x in P:
    for key in ("ret", "ret_first", "ret_third"): x[key] = {int(h): v for h, v in x[key].items()}
FITH = 96.0; FIRES_H_NOW = 0.32
def S(name): return [x for x in P if x["set"] == name]
def line(lbl, rs, per_day=None):
    if not rs: return f"  {lbl:44s}   0"
    m = mean(rs); u = mean([usd(v) for v in rs]); t = m / se(rs) if len(rs) > 2 and se(rs) > 0 else float("nan")
    s = f"  {lbl:44s} {len(rs):4d}  mean {m:+6.1%}  med {st.median(rs):+6.1%}  win {sum(v > 0 for v in rs)/len(rs):4.0%}  dead {sum(v < -0.4 for v in rs)/len(rs):3.0%}  se {se(rs):5.1%}  t {t:+5.2f}  $/fire {u:+5.2f}"
    if per_day: s += f"  $/day {u*per_day:+6.1f}"
    return s
fire = lambda x: x["f_k2"] >= 2
print("=== A. every reading at every hold (second place, $13; $/day at the period's own fire rate: fit 73 fires / 96 h; recent 0.32 fires an hour)")
for per in ("fit", "rec"):
    pop = S(per); fires = [x for x in pop if fire(x)]; fpd = (len(fires) / FITH * 24) if per == "fit" else FIRES_H_NOW * 24
    print(f"--- {per}: {len(pop)} launches, {len(fires)} fires")
    for h in (15, 30, 60, 150, 300, 600):
        print(line(f"all launches, h{h}", [x["ret"][h] for x in pop]))
        print(line(f"the rule's fires, h{h}", [x["ret"][h] for x in fires], fpd))
        ref = [x["ret"][h] for x in pop if not fire(x)]
        print(line(f"refused, h{h}", ref) + f"   lift {mean([x['ret'][h] for x in fires]) - mean(ref):+.1%}")
print("\n=== B. the post-seat crowd (the discovery's variable), outsiders only; is it still what pays? (oracle, not tradable)")
for per in ("fit", "rec"):
    pop = S(per)
    for lbl, f in (("a15 wallets >= 4", lambda x: x["a15_w"] >= 4), ("a15 wallets <= 1", lambda x: x["a15_w"] <= 1), ("seat buys behind >= 3", lambda x: x["sb_n"] >= 3), ("seat buys behind 0", lambda x: x["sb_n"] == 0)):
        s = [x for x in pop if f(x)]
        print(f"  {per:3s} {lbl:24s} n {len(s):3d} ({len(s)/len(pop):3.0%})  h15 {mean([x['ret'][15] for x in s]):+6.1%}  h60 {mean([x['ret'][60] for x in s]):+6.1%}  h300 {mean([x['ret'][300] for x in s]):+6.1%}"
              f"   of which rule fires {sum(fire(x) for x in s):3d}")
print("\n=== C. is the pre-tick gate a proxy for the post-seat crowd? (means, fires vs refused)")
for per in ("fit", "rec"):
    pop = S(per); fr = [x for x in pop if fire(x)]; rf = [x for x in pop if not fire(x)]
    for key in ("sb_n", "sb_eth", "a15_w", "a15_eth", "a16_60_eth", "a16_60_w", "named_sold300"):
        a = [x[key] for x in fr]; b = [x[key] for x in rf]
        print(f"  {per:3s} {key:14s} fires mean {mean(a):7.3f} med {st.median(a):7.3f}   refused mean {mean(b):7.3f} med {st.median(b):7.3f}   ratio of means {mean(a)/mean(b) if mean(b) else float('nan'):5.2f}")
    fk = [x for x in pop if x["a15_w"] >= 4]
    print(f"  {per:3s} P(a15 wallets >= 4 | fire) {sum(x['a15_w'] >= 4 for x in fr)/len(fr):.0%}   P(... | refused) {sum(x['a15_w'] >= 4 for x in rf)/len(rf):.0%}")
print("\n=== D. the combination, tradable: the rule's gate, then at E1+12 hold to H if the outsiders' distinct buyers in E1+1..E1+12 >= N, else sell at E1+15")
def combo(xs, N, H, key="a12_w"): return [x["ret"][H] if x[key] >= N else x["ret"][15] for x in xs]
for per in ("fit", "rec"):
    fires = [x for x in S(per) if fire(x)]
    for H in (60, 150, 300):
        cells = []
        for N in (1, 2, 3, 4, 5, 6, 8):
            v = combo(fires, N, H); cells.append(f"N{N} {mean(v):+6.1%}")
        print(f"  {per:3s} H{H:3d}: " + "  ".join(cells) + f"   (h15 {mean([x['ret'][15] for x in fires]):+.1%}, h{H} {mean([x['ret'][H] for x in fires]):+.1%})")
# fit the (N, H) on the fit, read on recent; and the reverse
def best(xs):
    return max(((mean(combo(xs, N, H)), N, H) for N in range(1, 11) for H in (60, 150, 300)))
fit_f = [x for x in S("fit") if fire(x)]; rec_f = [x for x in S("rec") if fire(x)]
bf = best(fit_f); br = best(rec_f)
print(f"  fitted on fit: N {bf[1]} H {bf[2]} fit {bf[0]:+.1%}  -> recent {mean(combo(rec_f, bf[1], bf[2])):+.1%}  (recent h15 {mean([x['ret'][15] for x in rec_f]):+.1%}, h300 {mean([x['ret'][300] for x in rec_f]):+.1%})")
print(f"  fitted on recent: N {br[1]} H {br[2]} recent {br[0]:+.1%}  -> fit {mean(combo(fit_f, br[1], br[2])):+.1%}  (fit h15 {mean([x['ret'][15] for x in fit_f]):+.1%}, h300 {mean([x['ret'][300] for x in fit_f]):+.1%})")
# null test: permute a12_w among the fires within each set, refit on fit, count how often the fit gain over the better fixed hold and the recent gain over h15 are both >= the real ones
random.seed(7)
def gain(xs, N, H): return mean(combo(xs, N, H))
real_fit = bf[0] - max(mean([x['ret'][h] for x in fit_f]) for h in (15, 60, 150, 300)); real_rec = gain(rec_f, bf[1], bf[2]) - mean([x['ret'][15] for x in rec_f])
passes = 0; NPERM = 2000
for i in range(NPERM):
    pf = [x["a12_w"] for x in fit_f]; random.shuffle(pf); pr = [x["a12_w"] for x in rec_f]; random.shuffle(pr)
    FF = [dict(x, a12_w=v) for x, v in zip(fit_f, pf)]; RR = [dict(x, a12_w=v) for x, v in zip(rec_f, pr)]
    b = best(FF); gf = b[0] - max(mean([x['ret'][h] for x in fit_f]) for h in (15, 60, 150, 300)); gr = gain(RR, b[1], b[2]) - mean([x['ret'][15] for x in rec_f])
    if gf >= real_fit and gr >= real_rec: passes += 1
print(f"  null test: real gain over the best fixed hold on fit {real_fit:+.1%}, over h15 on recent {real_rec:+.1%};  permuted feature does at least as well on both in {passes}/{NPERM} = {passes/NPERM:.1%}")
print("\n=== E. the rule at 15 against 300 blocks, by window, by position (first / second / third in the seat block)")
for per in ("fit", "rec"):
    for w in (FIT if per == "fit" else REC + GAPS):
        fs = [x for x in P if x["win"] == w and fire(x)]
        if not fs: continue
        print(f"  {w:12s} {len(fs):3d} fires  h15 {mean([x['ret'][15] for x in fs]):+6.1%}  h60 {mean([x['ret'][60] for x in fs]):+6.1%}  h150 {mean([x['ret'][150] for x in fs]):+6.1%}  h300 {mean([x['ret'][300] for x in fs]):+6.1%}")
for per in ("fit", "rec"):
    fs = [x for x in S(per) if fire(x)]
    for pos, key in (("first", "ret_first"), ("third", "ret_third")):
        print(f"  {per:3s} {pos:6s} h15 {mean([x[key][15] for x in fs]):+6.1%}  h300 {mean([x[key][300] for x in fs]):+6.1%}   (second: h15 {mean([x['ret'][15] for x in fs]):+6.1%}  h300 {mean([x['ret'][300] for x in fs]):+6.1%})")
print("\n=== F. day by day, Sep 18-27 (UTC day of the creation), the rule's fires, h15 and h300, $ at $13 after gas")
days = sorted({day(x["T0"]) for x in P})
cum15 = cum300 = 0.0
for d in days:
    fs = [x for x in P if day(x["T0"]) == d and fire(x)]; n = len([x for x in P if day(x["T0"]) == d])
    if not fs: print(f"  {d}  launches {n:3d}  fires 0"); continue
    u15 = sum(usd(x["ret"][15]) for x in fs); u300 = sum(usd(x["ret"][300]) for x in fs); cum15 += u15; cum300 += u300
    print(f"  {d}  launches {n:3d}  fires {len(fs):2d}   h15 {mean([x['ret'][15] for x in fs]):+6.1%} win {sum(x['ret'][15] > 0 for x in fs)/len(fs):4.0%} ${u15:+6.2f} (cum {cum15:+7.2f})"
          f"   h300 {mean([x['ret'][300] for x in fs]):+6.1%} win {sum(x['ret'][300] > 0 for x in fs)/len(fs):4.0%} ${u300:+6.2f} (cum {cum300:+7.2f})")
print("\n=== G. the dumps and the thin demand: the rule's fires split by the bundle's selling by E1+300 (> 10% of its tokens) and by outsider ETH in E1+16..60")
for per in ("fit", "rec"):
    fs = [x for x in S(per) if fire(x)]
    for lbl, f in (("bundle dumped (>10% by +300)", lambda x: x["named_sold300"] > 0.10), ("bundle held", lambda x: x["named_sold300"] <= 0.10),
                   ("outsider ETH +16..60 < 0.2", lambda x: x["a16_60_eth"] < 0.2), ("outsider ETH +16..60 >= 0.2", lambda x: x["a16_60_eth"] >= 0.2)):
        s = [x for x in fs if f(x)]
        if s: print(f"  {per:3s} {lbl:32s} {len(s):3d} ({len(s)/len(fs):3.0%})  h15 {mean([x['ret'][15] for x in s]):+6.1%}  h60 {mean([x['ret'][60] for x in s]):+6.1%}  h300 {mean([x['ret'][300] for x in s]):+6.1%}")
print("\n=== H. paired h15 - h300 on the rule's fires")
for per in ("fit", "rec", "all"):
    fs = [x for x in P if fire(x) and (per == "all" or x["set"] == per)]
    d = [x["ret"][15] - x["ret"][300] for x in fs]
    print(f"  {per:3s} n {len(fs):3d}  mean h15-h300 {mean(d):+.1%}  se {se(d):.1%}  t {mean(d)/se(d):+.2f}")
