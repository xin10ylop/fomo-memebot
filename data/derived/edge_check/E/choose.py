"""choose.py (edge_check/E): choose the hold on one set, read it on another. The choice is the h in 1..600 with the highest mean
return of the fires on the choosing set (second place, $13; $ a fire is the same ranking at $13, the cap never binds); its
plateau is every h whose mean is within one standard error (sd/sqrt(n) of the fires at the optimum) of the optimum's mean on
the choosing set, printed as ranges. Pairs: fit -> recent, recent -> fit, Sep 18-21 -> Sep 22-27, and leave-one-window-out
on the fit (choose on three windows, read on the fourth). Every choice is also read at h+2 and h+4 (the engine's sell lands
2-4 blocks after the hold). The reading set's mean averaged over the choosing set's plateau is printed too.
    python3 data/derived/edge_check/E/choose.py > data/derived/edge_check/E/choose.txt"""
import sys, os, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
P = json.load(gzip.open(c.EE + "paths.json.gz", "rt")); DAYS = [f"Sep {d}" for d in range(18, 28)]
def fires(sel): return [x["p1"] for x in P if x["fire"] and sel(x)]
def curve(F, hmax=600): return {h: c.mean([p[h] for p in F]) for h in range(1, hmax + 1)}
def opt(F, lo=1, hmax=600):
    cv = curve(F, hmax); h = max(range(lo, hmax + 1), key=lambda h: cv[h]); s = c.se([p[h] for p in F]); return h, cv[h], s, cv
def ranges(hs):
    hs = sorted(hs); out = []
    for h in hs:
        if out and h == out[-1][1] + 1: out[-1][1] = h
        else: out.append([h, h])
    return out
def plateau(F, hmax=600):
    h, m, s, cv = opt(F, 1, hmax); on = [g for g in range(1, hmax + 1) if cv[g] >= m - s]
    rs = ranges(on); core = next(r for r in rs if r[0] <= h <= r[1]); return h, m, s, cv, rs, core, on
def fmt_r(rs): return ", ".join(f"{a}-{b}" if a != b else f"{a}" for a, b in rs)
SETS = {"fit": lambda x: x["set"] == "fit", "rec": lambda x: x["set"] == "rec", "Sep18-21": lambda x: x["day"] in DAYS[:4], "Sep22-27": lambda x: x["day"] in DAYS[4:]}
for w in c.FIT: SETS[w] = (lambda w: lambda x: x["win"] == w)(w)
for w in c.FIT: SETS["fit-" + w] = (lambda w: lambda x: x["set"] == "fit" and x["win"] != w)(w)
def report(choose, read):
    Fc, Fr = fires(SETS[choose]), fires(SETS[read]); h, m, s, cv, rs, core, on = plateau(Fc); cr = curve(Fr)
    print(f"choose on {choose} ({len(Fc)} fires): h* = {h}, mean {m:+.1%} (se {s:.1%}); plateau (mean >= {m-s:+.1%}): {fmt_r(rs)} "
          f"[{len(on)} of 600 holds; the run around h*: {core[0]}-{core[1]}]")
    print(f"   read on {read} ({len(Fr)} fires): at h* {cr[h]:+.1%}, at h*+2 {cr[h+2]:+.1%}, at h*+4 {cr[h+4]:+.1%};"
          f" averaged over the plateau {c.mean([cr[g] for g in on]):+.1%}, over the run around h* {c.mean([cr[g] for g in range(core[0], core[1]+1)]):+.1%};"
          f" the choosing set at h*+2 {cv[h+2]:+.1%}, h*+4 {cv[h+4]:+.1%}; the reading set's own optimum h {max(cr, key=cr.get)} {max(cr.values()):+.1%}")
    return h
print("=== 2. choose on one set, read on the other (h in 1..600)")
report("fit", "rec"); report("rec", "fit"); report("Sep18-21", "Sep22-27")
print("\n=== the same with the search limited to h >= 5 and to h in 1..60 (the short end alone)")
for a, b in (("fit", "rec"), ("rec", "fit"), ("Sep18-21", "Sep22-27")):
    Fc, Fr = fires(SETS[a]), fires(SETS[b]); cr = curve(Fr)
    for lo, hm in ((5, 600), (1, 60)):
        h, m, s, cv = opt(Fc, lo, hm); on = [g for g in range(lo, hm + 1) if cv[g] >= m - s]
        print(f"  {a:8s} h in {lo}..{hm}: h* {h:3d} {m:+.1%} (se {s:.1%}) plateau {fmt_r(ranges(on))}; read on {b} {cr[h]:+.1%} (h+2 {cr[h+2]:+.1%}, h+4 {cr[h+4]:+.1%})")
print("\n=== 3b. leave one fit window out: choose on the other three, read on the one left out (h in 1..600)")
for w in c.FIT: report("fit-" + w, w)
print("\n=== the pooled 92 fires (fit + recent), for reference")
Fa = fires(lambda x: True); h, m, s, cv, rs, core, on = plateau(Fa)
print(f"pooled: h* = {h}, mean {m:+.1%} (se {s:.1%}); plateau {fmt_r(rs)}; at 15 {cv[15]:+.1%}, 300 {cv[300]:+.1%}")
print("\n=== each set's curve maximum in 1..1200 (the extended tapes)")
for k in ("fit", "rec", "Sep18-21", "Sep22-27"):
    F = fires(SETS[k]); h, m, s, cv = opt(F, 1, 1200); print(f"  {k:9s} h* {h:4d} {m:+.1%} (se {s:.1%}); best in 601..1200: h {max(range(601,1201), key=cv.get)} {max(cv[g] for g in range(601,1201)):+.1%}")
