"""templates.py (reviewer I): the named-wallet templates and what the causal filter flags.
A template = launches whose named sets share >= 3 wallets with the template's wallet union (built in T0 order); the filter
flags a launch when a template of >= 5 launches with a strictly earlier T0 shares >= 3 wallets with its named set.
Prints the final templates of >= 5 launches (every launch: time, window, fires, bundle, named count, returns h11/h15/h300,
flagged or not at that time), then the flag counts by period.  Also B's linkage (any one shared wallet) for comparison.
    python3 data/derived/edge_check/I/templates.py > data/derived/edge_check/I/templates.txt"""
import sys, os, collections, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
P = c.load(); flag, info = c.template_flags(P)
# final templates (same growth rule, all launches)
comps = []
for d in P:
    hit = [x for x in comps if len(d["named"] & x[0]) >= 3]
    w = set(d["named"]); m = [d]
    for x in hit: w |= x[0]; m += x[1]; comps.remove(x)
    comps.append([w, m])
comps.sort(key=lambda x: -len(x[1]))
def rr(d, h): v = d["r"][h]; return "   n/a" if v is None else f"{v:+6.1%}"
print("final templates of >= 5 launches (link: >= 3 shared named wallets with the template's union)")
for w, m in comps:
    if len(m) < 5: break
    m.sort(key=lambda d: d["T0"])
    print(f"\n== template of {len(m)} launches, {len(w)} wallets; bundles {sorted(set(round(d['bundle'], 3) for d in m))}")
    for d in m:
        print(f"  {c.hms(d['T0'])} {d['cv'][:10]} {d['win']:12s} fire tables {'Y' if d['fire_t'] else '.'} engine {'Y' if d['fire_e'] else '.'}  bundle {d['bundle']:.3f}  named {len(d['named']):2d}  "
              f"h11 {rr(d, 11)} h15 {rr(d, 15)} h300 {rr(d, 300)}  flagged {'YES' if flag[d['cv']] else 'no'}")
print("\nflagged by the causal filter (tables fires / engine fires / all launches):")
for per in ("fit", "rec", "late"):
    S = [d for d in P if d["per"] == per]
    print(f"  {per:4s}: tables {sum(flag[d['cv']] for d in S if d['fire_t'])}/{sum(d['fire_t'] for d in S)}  engine {sum(flag[d['cv']] for d in S if d['fire_e'])}/{sum(d['fire_e'] for d in S)}  launches {sum(flag[d['cv']] for d in S)}/{len(S)}")
# B's linkage: connected components over a shared named wallet, non-causal, all launches (B's pop.py rule), h300
par = {}
def find(x):
    while par.setdefault(x, x) != x: par[x] = par[par[x]]; x = par[x]
    return x
for d in P:
    L = sorted(d["named"])
    for x in L: par[find(x)] = find(L[0])
size = collections.Counter(find(sorted(d["named"])[0]) for d in P if d["per"] in ("fit", "rec"))
fam = [d for d in P if abs(d["bundle"] - 4.233) < 0.001]
print("\nthe 4.233 ETH launches: named wallets shared between each pair (a named-wallet template cannot link them):")
for a in fam: print(f"  {c.hms(a['T0'])} {a['cv'][:10]} named {len(a['named']):2d}  shared with each: {[len(a['named'] & b['named']) for b in fam]}  flagged {flag[a['cv']]}")
print("\nB's rule for comparison (any shared wallet links; component size over fit + rec; non-causal), h300:")
for per in ("fit", "rec"):
    F = [d for d in P if d["per"] == per and d["fire_t"]]; big = [d for d in F if size[find(sorted(d["named"])[0])] >= 5]
    out = [d for d in F if d not in big]
    print(f"  {per}: fires in a template of >= 5: {len(big)}/{len(F)} h300 {st.mean(d['r'][300] for d in big):+.1%}; outside {st.mean(d['r'][300] for d in out):+.1%}"
          f"  | h11 {st.mean(d['r'][11] for d in big):+.1%} vs {st.mean(d['r'][11] for d in out):+.1%}  | h15 {st.mean(d['r'][15] for d in big):+.1%} vs {st.mean(d['r'][15] for d in out):+.1%}")
    Fe = [d for d in P if d["per"] == per and d["fire_e"]]; bige = [d for d in Fe if size[find(sorted(d["named"])[0])] >= 5]; oute = [d for d in Fe if d not in bige]
    print(f"     engine's fires: in {len(bige)}/{len(Fe)}  h11 {st.mean(d['r'][11] for d in bige):+.1%} vs {st.mean(d['r'][11] for d in oute):+.1%}; h15 {st.mean(d['r'][15] for d in bige):+.1%} vs {st.mean(d['r'][15] for d in oute):+.1%}; h300 {st.mean(d['r'][300] for d in bige):+.1%} vs {st.mean(d['r'][300] for d in oute):+.1%}")
