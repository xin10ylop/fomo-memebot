"""dims.py: the brief's candidate dimensions one at a time, read from search_results.json (run search.py first): FIT pooled,
VAL pooled and the criteria string (a letter = met) for each.
    cd /home/user/fomo-memebot && python3 <B>/dims.py"""
import sys, os, json; HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "search_results.json")))
ix = {(r["cand"], r["hold"]): r for r in R}
def line(c, h="behind1_15_h300"):
    r = ix[(c, h)]; f, v = r["fit"], r["val"]
    fs = f"FIT n={f['n']:3d} {f['mean']:+6.1%} med {f['median']:+6.1%} win {f['win']:3.0%} dead {f['dead']:3.0%} ${f['usd_burst']:+5.2f}/b ${f['usd_day']:6.1f}/d" if f["n"] else "FIT n=0"
    vs = f"VAL n={v['n']:3d} {v['mean']:+6.1%} ${v['usd_total']:+6.1f}" if v["n"] else "VAL n=0"
    print(f"  {c[:44]:44s} {h.replace('behind1_15_',''):18s} {fs} | {vs} | {''.join(k if ok else '-' for k, ok in r['crit'].items())}")
print("1. threshold / unit / view (hold 300)")
for c in ["fleets>=1@k-2", "fleets>=2@k-2", "fleets>=3@k-2", "fleets>=4@k-2", "wallets>=1@k-2", "wallets>=2@k-2", "wallets>=3@k-2", "wallets>=5@k-2", "wallets>=10@k-2",
          "fleets>=1@k-3", "fleets>=2@k-3", "fleets>=2@k-2 & fleets>=1@k-3", "fleets>=2@k-2 & wallets>=2@k-3", "fleets>=2@k-2 & wallets>=5@k-2", "fleets>=2@k-2 | wallets>=2@k-2",
          "fleets>=2@k-2 | wallets>=5@k-2", "fleets>=2@k-2 | fleets>=1@k-3", "fleets>=1@k-2 & wallets>=5@k-2"]: line(c)
print("2. the hold, baseline gate")
for h in ["behind1_15_h15", "behind1_15_h30", "behind1_15_h60", "behind1_15_h150", "behind1_15_h300", "behind1_15_h600", "behind1_15_tp50_h600", "behind1_15_stop20_h600", "behind1_15_tp50_stop20_h600"]: line("fleets>=2@k-2", h)
print("3. features as AND-filters on the baseline gate (hold 300), a selection")
for c in ["bundle_eth>=0.628", "bundle_eth>=0.836", "bundle_eth<0.628", "named>=5", "named<5", "tier==2%", "tier>2%", "k>=5", "k<=6", "arr1>=3", "arr2>=3", "maxw@k-2>=3", "maxshots@k-2>=3", "shots@k-2>=5", "direct fleets@k-2==0", "relay fleets@k-2>=2"]: line("BASE & " + c)
print("3b. features as OR-branches (fire also when fleets@k-2 < 2 and ...), hold 300, a selection")
for c in ["bundle_eth>=0.836", "bundle_eth>=1.0", "bundle_eth>=1.5", "named<4", "k<=4", "w@k-2>=2", "w@k-2>=5", "maxshots@k-2>=3", "tier==2%", "only h18-23"]: line("BASE | (f@k-2<2 & " + c + ")"); line("BASE | (f@k-2==1 & " + c + ")")
print("5. hours of the day (AND on the baseline gate, hold 300)")
for c in ["not h00-05", "not h06-11", "not h12-17", "not h18-23", "only h12-17", "only h18-23", "TRADE_HOURS 12-05", "not creator repeat"]: line("BASE & " + c)
