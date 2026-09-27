"""checks.py (edge_check/C): the small numbers the report quotes that no other script prints: the reproduction of round 1's
means, the bundle-sell exit, the recent fires outside sep24paper, and the arithmetic of the expectation table and the
break-even fill rates.
    python3 data/derived/edge_check/C/checks.py > data/derived/edge_check/C/checks.txt"""
import sys, json
sys.path.insert(0, "data/derived/edge_check/C"); from common import *
P = json.load(open(C + "pop.json"))
fit = [x for x in P if x["set"] == "fit" and x["f_k2"] >= 2]; rec = [x for x in P if x["set"] == "rec" and x["f_k2"] >= 2]
rec18 = [x for x in rec if x["win"] not in GAPS]
print(f"reproduction: fit {len(fit)} fires h300 {mean([x['ret']['300'] for x in fit]):+.2%} h15 {mean([x['ret']['15'] for x in fit]):+.2%};"
      f" committed recent {len(rec18)} fires h300 {mean([x['ret']['300'] for x in rec18]):+.2%} h15 {mean([x['ret']['15'] for x in rec18]):+.2%};"
      f" with the gap fire {len(rec)} h300 {mean([x['ret']['300'] for x in rec]):+.2%} h15 {mean([x['ret']['15'] for x in rec]):+.2%}")
for name, s in (("fit", fit), ("recent", rec)):
    print(f"bundle-sell exit ({name}): sell 2 blocks after the named wallets' first sell after the seat, else 300: {mean([x['ret_nsx'] for x in s]):+.1%}"
          f"  (h300 {mean([x['ret']['300'] for x in s]):+.1%}); fires with such a sell before +298: {sum(1 for x in s if x['first_named_sell'] and x['first_named_sell'] < 298)}/{len(s)}")
oth = [x for x in rec if x["win"] != "sep24paper"]
print(f"recent fires outside sep24paper: {len(oth)}  h15 {mean([x['ret']['15'] for x in oth]):+.1%}  h60 {mean([x['ret']['60'] for x in oth]):+.1%}"
      f"  h150 {mean([x['ret']['150'] for x in oth]):+.1%}  h300 {mean([x['ret']['300'] for x in oth]):+.1%}")
last6 = [x for x in rec if x["T0"] >= 1790414100]; m6 = mean([x["ret"]["15"] for x in last6])
print(f"the six fires since Sep 26 09:15, h15 mean {m6:+.1%}: a week of 54 fires at full fill ${54*(STAKE*m6 - GAS):+.1f}, live mix (fill 1 in 2, second place) ${54*(0.5*STAKE*m6 - GAS):+.1f}")
r15 = mean([x["ret"]["15"] for x in rec]); t15 = mean([x["ret_third"]["15"] for x in rec])
print(f"break-even fill rate at h15, recent means: second place {GAS/(STAKE*r15):.0%} (mean {r15:+.1%}), third place {GAS/(STAKE*t15):.0%} (mean {t15:+.1%})")
import random
random.seed(3); f15 = [x["ret"]["15"] for x in fit]
p6 = sum(mean(random.choices(f15, k=len(last6))) <= m6 for _ in range(100000)) / 100000
print(f"{len(last6)} fires drawn from the fit's h15 returns average <= {m6:+.1%} in {p6:.1%} of 100,000 draws")
