"""story.py (edge_check/C): question 5, what the whole story shows. (a) the real fills' money, from sep17_20_fills.json; (b) where
the fit's 300-block premium came from, window by window, for the rule's fires and for every launch; (c) the rule's lift over the
refused at 15 and 300 blocks, window by window and day by day; (d) the gate as a proxy, window by window: the post-seat crowd
(outsiders' distinct buyers in E1+1..15) and the late demand (outsider ETH in E1+16..60) of fires against refused, and the
bundle's dumps.
    python3 data/derived/edge_check/C/story.py > data/derived/edge_check/C/story.txt"""
import sys, json
sys.path.insert(0, "data/derived/edge_check/C"); from common import *
F = json.load(open(D + "sep17_20_fills.json"))
net = [x["net"] for x in F if x.get("net") is not None]
print(f"(a) the real fills Sep 17-20: {len(F)} launches, net {sum(net):+.5f} ETH = ${sum(net)*E:+.2f} at {E:.0f} before gas;"
      f" single fills {sum(1 for x in F if x['fills'] == 1)}, net ${sum(x['net'] for x in F if x['fills'] == 1 and x.get('net') is not None)*E:+.2f};"
      f" multi-fills ${sum(x['net'] for x in F if x['fills'] > 1 and x.get('net') is not None)*E:+.2f}")
s1 = [x for x in F if x["fills"] == 1 and x["ahead"] > 0]
print(f"    single fills with somebody ahead (the discovery's 12): net ${sum(x['net'] for x in s1)*E:+.2f} before gas, ${sum(x['net'] for x in s1)*E - 0.33*len(s1):+.2f} after $0.33 a burst;"
      f" held {min(x['hold'] for x in s1)}-{max(x['hold'] for x in s1)} blocks")
P = [x for x in json.load(open(C + "pop.json")) if x["ret"] is not None]
for x in P: x["ret"] = {int(h): v for h, v in x["ret"].items()}
fire = lambda x: x["f_k2"] >= 2
wins = FIT + ["rec"]
def grp(w): return [x for x in P if (x["win"] == w if w != "rec" else x["set"] == "rec")]
print("\n(b)+(c) by window: the rule's fires and the refused at h15 and h300; premium = h300 - h15; lift = fires - refused")
for w in wins:
    g = grp(w); f = [x for x in g if fire(x)]; r = [x for x in g if not fire(x)]
    f15, f300 = mean([x["ret"][15] for x in f]), mean([x["ret"][300] for x in f]); r15, r300 = mean([x["ret"][15] for x in r]), mean([x["ret"][300] for x in r])
    print(f"  {w:8s} launches {len(g):3d} fires {len(f):3d}   fires h15 {f15:+6.1%} h300 {f300:+6.1%} premium {f300-f15:+6.1%}   refused h15 {r15:+6.1%} h300 {r300:+6.1%} premium {r300-r15:+6.1%}"
          f"   lift h15 {f15-r15:+6.1%} h300 {f300-r300:+6.1%}")
fit_f = [x for x in P if x["set"] == "fit" and fire(x)]
tot = sum(x["ret"][300] - x["ret"][15] for x in fit_f)
for w in FIT:
    part = sum(x["ret"][300] - x["ret"][15] for x in fit_f if x["win"] == w)
    print(f"  share of the fit's summed h300-h15 premium from {w}: {part/tot:+.0%}")
ex = [x for x in fit_f if x["win"] != "sep2223"]
print(f"  fit without sep2223: {len(ex)} fires h15 {mean([x['ret'][15] for x in ex]):+.1%} h300 {mean([x['ret'][300] for x in ex]):+.1%}")
print("\n    day by day, lift (fires - refused)")
for d in sorted({day(x["T0"]) for x in P}):
    g = [x for x in P if day(x["T0"]) == d]; f = [x for x in g if fire(x)]; r = [x for x in g if not fire(x)]
    if not f: continue
    print(f"  {d} fires {len(f):2d} refused {len(r):3d}  lift h15 {mean([x['ret'][15] for x in f]) - mean([x['ret'][15] for x in r]):+6.1%}   lift h300 {mean([x['ret'][300] for x in f]) - mean([x['ret'][300] for x in r]):+6.1%}")
print("\n(d) the gate as a proxy, by window: post-seat crowd (outsiders' distinct buyers E1+1..15, mean), late demand (outsider ETH E1+16..60, median), dumps (bundle sold > 10% by +300)")
import statistics as st
for w in wins:
    g = grp(w); f = [x for x in g if fire(x)]; r = [x for x in g if not fire(x)]
    print(f"  {w:8s} a15 wallets fires {mean([x['a15_w'] for x in f]):4.1f} refused {mean([x['a15_w'] for x in r]):4.1f}   late ETH median fires {st.median([x['a16_60_eth'] for x in f]):5.2f} refused {st.median([x['a16_60_eth'] for x in r]):5.2f}"
          f"   dumps fires {sum(x['named_sold300'] > 0.1 for x in f)/len(f):4.0%} refused {sum(x['named_sold300'] > 0.1 for x in r)/len(r):4.0%}")
