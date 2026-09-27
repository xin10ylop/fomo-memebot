"""template.py (reviewer B): the launches of the named-wallet template that holds 6 of the 18 recent fires (linked by a shared
named wallet, as pop.py), one line each. python3 data/derived/edge_check/B/template.py"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
F = {f["cv"]: f for f in json.load(open(c.B + "features.json"))}
par = {}
def find(x):
    while par.setdefault(x, x) != x: par[x] = par[par[x]]; x = par[x]
    return x
pop = c.load(c.FIT) + c.load(c.RECENT)
for r in pop:
    for w in r["named"]: par[find(w)] = find(r["named"][0])
key = find(F[[cv for cv in F if cv.startswith("0x80c0efae")][0]]["named_set"][0])
for r in sorted(pop, key=lambda r: r["T0"]):
    if not r["named"] or find(r["named"][0]) != key: continue
    f = F.get(r["cv"])
    if not f: print(f"  {c.hhmm(r['T0'])} {r['cv'][:10]} no tape"); continue
    held = f["held"].get("bundle", 0); sh = min(1, f["sold"]["300"].get("bundle", 0) / held) if held else 0
    print(f"  {c.hhmm(f['T0'])} {f['cv'][:10]} {f['grp']:6s} fire {str(f['fire']):5s} fleets@k-2 {f['n_f_k2']} h15 {f['ret']['15']:+6.1%} h300 {f['ret']['300']:+6.1%}  bundle sold {sh:.0%} by E1+300, first at E1+{f['first_sell'].get('bundle', '-')}")
ids = {r["cv"] for r in pop if r["named"] and find(r["named"][0]) == key}
import statistics as st
for g in ("fit", "recent"):
    v = [f["ret"]["300"] for f in F.values() if f["fire"] and f["grp"] == g and f["cv"] not in ids]; w = [f["ret"]["300"] for f in F.values() if f["fire"] and f["grp"] == g and f["cv"] in ids]
    print(f"{g}: fires of this template {len(w)} mean {st.mean(w):+.1%}; the other fires {len(v)} mean {st.mean(v):+.1%}")
