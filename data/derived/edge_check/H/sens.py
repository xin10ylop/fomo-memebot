"""sens.py (edge_check/H): sensitivities. (a) the template filter over the grid shares >= {2,3,5} x template size >= {3,5,8}
(causal) and reviewer B's hindsight template (connected components over ANY shared named wallet, all launches of both periods,
size >= 5), each alone and with the 3.0 ETH cap, $/day against no filter, both periods, both populations, h11 and h15;
(b) the recent h11 with the tape-less fires' unknown h11 replaced by their h15; (c) the cap's effect by day.
    python3 data/derived/edge_check/H/sens.py > data/derived/edge_check/H/sens.txt"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
P = load(); TG = json.load(open(H + "template_flags.json")); RH = spans(P, REC)
par = {}
def find(a):
    while par.setdefault(a, a) != a: par[a] = par[par[a]]; a = par[a]
    return a
for x in P:
    for w in x["named"]: par[find(w)] = find(x["named"][0])
comp = collections.Counter(find(x["named"][0]) for x in P if x["named"])
BFLAG = {x["cv"]: bool(x["named"]) and comp[find(x["named"][0])] >= 5 for x in P}
def R(x, h, sub=False):
    v = x["r11"] if h == 11 else x["r15"]
    return x["r15"] if (v is None and sub) else v
def day(F, h, s, sub=False):
    v = [(R(x, h, sub), x["g"]) for x in F if R(x, h, sub) is not None]
    return len(v), mean([r for r, _ in v]), sum(usd(r, g) for r, g in v) / (FIT_HOURS if s == "fit" else RH) * 24
print("(a) template filters: fires, mean, $/day (fit 96 h | recent 62.65 h); 'none' first")
for key, lab in (("fire_eng", "engine"), ("fire_tab", "tables")):
    for h in (11, 15):
        print(f"  {lab} h{h}")
        flt = [("none", lambda x: True), ("cap3.0", lambda x: x["bundle"] <= 3.0)]
        for g in sorted(TG): flt.append((f"tmpl{g}", lambda x, g=g: not TG[g][x["cv"]]["flag"])); flt.append((f"tmpl{g}+cap3.0", lambda x, g=g: not TG[g][x["cv"]]["flag"] and x["bundle"] <= 3.0))
        flt += [("B-hindsight", lambda x: not BFLAG[x["cv"]]), ("B-hindsight+cap3.0", lambda x: not BFLAG[x["cv"]] and x["bundle"] <= 3.0)]
        base = {s: day([x for x in P if x["set"] == s and x[key]], h, s) for s in ("fit", "rec")}
        for n, f in flt:
            o = []
            for s in ("fit", "rec"):
                k, m, d = day([x for x in P if x["set"] == s and x[key] and f(x)], h, s); o.append(f"{s} {k:3d} {m:+6.1%} ${d:+6.1f} ({d - base[s][2]:+5.1f})")
            print(f"    {n:20s} " + " | ".join(o))
print("\n  B-hindsight flags (fires): " + ", ".join(f"{s}-{k[5:]} {sum(BFLAG[x['cv']] for x in P if x['set']==s and x[k])}/{sum(1 for x in P if x['set']==s and x[k])}" for s in ("fit", "rec") for k in ("fire_tab", "fire_eng")))
print("\n(b) recent h11 with the unknown h11 replaced by h15 (engine: 0x85a1e161, 0x3341b8c1; tables also 0x7b2eac5e, 0x4fed869a)")
for key in ("fire_eng", "fire_tab"):
    for n, f in (("none", lambda x: True), ("cap3.0", lambda x: x["bundle"] <= 3.0), ("tmpl3_5", lambda x: not TG["3_5"][x["cv"]]["flag"])):
        k, m, d = day([x for x in P if x["set"] == "rec" and x[key] and f(x)], 11, "rec", sub=True)
        print(f"  {key[5:]} {n:8s} {k:3d} {m:+6.1%} ${d:+6.1f}/day")
print("\n(c) the 3.0 ETH cap by day, engine fires, h11: fires kept/all, $ kept vs all (the days where it acts)")
for d0 in sorted(set(time.strftime("%b %d", time.gmtime(x["T0"])) for x in P)):
    F = [x for x in P if x["fire_eng"] and time.strftime("%b %d", time.gmtime(x["T0"])) == d0 and x["r11"] is not None]
    K = [x for x in F if x["bundle"] <= 3.0]
    if F: print(f"  {d0}: {len(K)}/{len(F)}  ${sum(usd(x['r11'], x['g']) for x in K):+6.2f} vs ${sum(usd(x['r11'], x['g']) for x in F):+6.2f}" + ("  <- acts" if len(K) < len(F) else ""))
