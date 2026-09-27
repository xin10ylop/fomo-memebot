"""tmpl_gap.py (verifier VI): the causal template filter's split (flagged vs not) at h11/h15/h300 per period and population,
next to B's non-causal split; and B's component size for every capped fire.   python3 data/derived/edge_check/VI/tmpl_gap.py"""
import sys, os, statistics as st, collections
sys.path.insert(0, "/home/user/fomo-memebot/data/derived/edge_check/I"); import common as c
P = c.load(); F = c.flags()
par = {}
def find(x):
    while par.setdefault(x, x) != x: par[x] = par[par[x]]; x = par[x]
    return x
for d in P:
    L = sorted(d["named"])
    for x in L: par[find(x)] = find(L[0])
size = collections.Counter(find(sorted(d["named"])[0]) for d in P if d["per"] in ("fit", "rec"))
def m(fs, h):
    v = [d["r"][h] for d in fs if d["r"][h] is not None]; return f"{st.mean(v):+6.1%} (n{len(v)})" if v else "   n/a"
for pop, key in (("engine", "fire_e"), ("tables", "fire_t")):
    for per in ("fit", "rec"):
        fs = [d for d in P if d[key] and d["per"] == per]
        fl = [d for d in fs if F[d["cv"]]]; nf = [d for d in fs if not F[d["cv"]]]
        bb = [d for d in fs if size[find(sorted(d["named"])[0])] >= 5]; bo = [d for d in fs if d not in bb]
        print(f"{pop} {per}: causal flagged vs not: " + "  ".join(f"h{h} {m(fl,h)} vs {m(nf,h)}" for h in (11, 15, 300)))
        print(f"{' '*len(pop)} {per}: B non-causal in vs out:   " + "  ".join(f"h{h} {m(bb,h)} vs {m(bo,h)}" for h in (11, 15, 300)))
print("\nB's component size for every launch above 3 ETH that fires (either count):")
for d in P:
    if d["bundle"] > 3.0 and (d["fire_e"] or d["fire_t"]):
        print(f"  {c.hms(d['T0'])} {d['cv'][:10]} bundle {d['bundle']:.3f} B-component size {size[find(sorted(d['named'])[0])]}  causal flag {F[d['cv']]}")
