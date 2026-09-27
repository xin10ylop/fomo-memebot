"""pop.py (reviewer B), tests 3 and 4 on every launch of the population (fires and refused): the seat's h15/h300 return for
all launches by period, the rule's lift over the refused, the rule's variants (views k-1, the tick's shot 0.76, k-2, k-3;
fleets >= 3; wallets), the bundle's dump rate, the outsiders' demand, the named-wallet templates.
    python3 data/derived/edge_check/B/pop.py"""
import sys, os, json, collections, statistics as st, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
F = json.load(open(c.B + "features.json")); LIVE = 1790414640
def per(f): return f["grp"] if f["grp"] == "fit" else ("recent-pre" if f["T0"] < LIVE else "recent-post")
def R(f, h=300): return f["ret"][str(h)]
def share(f, cl="bundle", h=300):
    held = f["held"].get(cl, 0); s = f["sold"][str(h)].get(cl, 0); return min(1.0, s / held) if held > 0 else 0.0
def line(lab, S, h=300):
    if not S: return f"{lab:28s}   0"
    v = [R(f, h) for f in S]; return f"{lab:28s} {len(v):4d}  mean {st.mean(v):+6.1%}  median {st.median(v):+6.1%}  win {sum(x>0 for x in v)/len(v):3.0%}  dead {sum(x<-0.4 for x in v)/len(v):3.0%}"
G = {"fit": [f for f in F if f["grp"] == "fit"], "recent": [f for f in F if f["grp"] == "recent"]}
print("launches with a tape:", {g: len(S) for g, S in G.items()})
for g, S in G.items():
    fr = [f for f in S if f["fire"]]
    print(f"  population filter on the {g} fires: tier {min(f['tier'] for f in fr):.3f}-{max(f['tier'] for f in fr):.3f}, bundle < 0.3 ETH: {sum(f['bundle_eth'] < 0.3 for f in fr)}, named < 3: {sum(f['named'] < 3 for f in fr)}")
for g, S in G.items():
    print(f"\n== {g}")
    fires = [f for f in S if f["fire"]]; ref = [f for f in S if not f["fire"]]
    for h in (15, 300):
        print(f"  h{h}: " + line("all launches", S, h)); print(f"  h{h}: " + line("fires (fleets>=2 @k-2)", fires, h)); print(f"  h{h}: " + line("refused", ref, h))
        print(f"  h{h}: lift fires - refused {st.mean(R(f, h) for f in fires) - st.mean(R(f, h) for f in ref):+.1%}")
    print("  rule variants (h300):")
    for lab, fn in (("fleets>=1 @k-2", lambda f: c.at(f["cf"], f["k"] - 2) >= 1), ("fleets>=2 @k-3", lambda f: c.at(f["cf"], f["k"] - 3) >= 2),
                    ("fleets>=2 @k-2", lambda f: c.at(f["cf"], f["k"] - 2) >= 2), ("fleets>=2 @tick 0.76", lambda f: c.at(f["cf"], c.view(f["k"], 0.76)) >= 2),
                    ("fleets>=2 @k-1", lambda f: c.at(f["cf"], f["k"] - 1) >= 2), ("fleets>=3 @k-2", lambda f: c.at(f["cf"], f["k"] - 2) >= 3),
                    ("wallets>=2 @k-2", lambda f: c.at(f["cw"], f["k"] - 2) >= 2), ("wallets>=3 @k-2", lambda f: c.at(f["cw"], f["k"] - 2) >= 3)):
        print("    " + line(lab, [f for f in S if fn(f)]))
    for lab, T in (("all launches", S), ("fires", fires), ("refused", ref)):
        d = [f for f in T if share(f) > 0.1]
        print(f"  bundle sold >10% of its tokens by E1+300: {lab:13s} {len(d)}/{len(T)} = {len(d)/max(1,len(T)):.0%}; h300 with {st.mean(R(f) for f in d) if d else float('nan'):+.1%}, without {st.mean(R(f) for f in T if share(f) <= 0.1):+.1%}; first sell median {st.median([f['first_sell']['bundle'] for f in d]) if d else float('nan')} blocks after E1")
    for lab, T in (("all launches", S), ("fires", fires)):
        o = [f["buy_eth_after"].get("other", 0.0) for f in T]
        print(f"  outsiders' ETH after the seat second, {lab:13s}: mean {st.mean(o):.3f} median {st.median(o):.3f}; distinct outside buyers median {st.median(f['n_outsiders'] for f in T):.0f}")
print("\n== by period with the live split (h300):")
for p in ("fit", "recent-pre", "recent-post"):
    S = [f for f in F if per(f) == p]; fires = [f for f in S if f["fire"]]
    print("  " + line(p + " all", S) + " | " + line("fires", fires).strip() + f" | bundle dump {sum(share(f) > 0.1 for f in S)/len(S):.0%}")
# templates: launches linked by a shared named wallet (connected components over both periods)
par = {}
def find(x):
    while par.setdefault(x, x) != x: par[x] = par[par[x]]; x = par[x]
    return x
pop = c.load(c.FIT) + c.load(c.RECENT)
for r in pop:
    for w in r["named"]: par[find(w)] = find(r["named"][0])
comp = collections.defaultdict(list)
for f in F:
    if f["named_set"]: comp[find(f["named_set"][0])].append(f)
print("\n== named-wallet templates (launches linked by a shared named wallet)")
for g in ("fit", "recent"):
    fires = [f for f in F if f["grp"] == g and f["fire"]]
    big = [f for f in fires if len(comp[find(f["named_set"][0])]) >= 5]
    print(f"  {g} fires in a template of >= 5 launches: {len(big)}/{len(fires)}, h300 {st.mean(R(f) for f in big) if big else float('nan'):+.1%}; outside templates {st.mean(R(f) for f in fires if f not in big):+.1%}")
for key, L in sorted(comp.items(), key=lambda kv: -len(kv[1]))[:8]:
    fit = [f for f in L if f["grp"] == "fit"]; rec = [f for f in L if f["grp"] == "recent"]
    print(f"  template {key[:10]}: {len(fit)} fit launches h300 {st.mean(R(f) for f in fit) if fit else float('nan'):+.1%} (dump {sum(share(f) > 0.1 for f in fit)}), fires {sum(f['fire'] for f in fit)};"
          f" {len(rec)} recent h300 {st.mean(R(f) for f in rec) if rec else float('nan'):+.1%} (dump {sum(share(f) > 0.1 for f in rec)}), fires {sum(f['fire'] for f in rec)}; bundle first sell (blocks after E1) fit {sorted(f['first_sell'].get('bundle', -1) for f in fit)[-6:]} recent {sorted(f['first_sell'].get('bundle', -1) for f in rec)}")
