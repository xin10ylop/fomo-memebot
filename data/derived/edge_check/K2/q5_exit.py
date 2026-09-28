"""K2/q5_exit.py: exit rules against the fixed exit at E1+11, on second place's path (every block 0..60 after the fill, taped fires of
the usual view, the guard ignored so the sample is every burst). A rule reads the curve at the end of block h and its sell lands L
blocks later (L = 2 the base, 3-4 checked: the engine's sell lands 2-4 blocks after the setting); the value taken is the path at h+L,
never at h. Parameters chosen on one period, read on the other."""
import os, sys, json, gzip, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from sim import *
P = json.load(gzip.open(os.path.join(HERE, "prices.json.gz"), "rt")); PR = P["rows"]
def fires(view):
    return [r["x"] for r in run(view=view, guard=False) if r.get("fired") and r["x"]["cv"] in PR]
def fixed(H):
    return lambda p, L: p["p2"][H]
def tp(th, base=11, first=1):
    def f(p, L):
        v = p["p2"]
        for h in range(first, base - L + 1):
            if v[h] >= th: return v[h + L]
        return v[base]
    return f
def stop(th, base=11, first=1):
    def f(p, L):
        v = p["p2"]
        for h in range(first, base - L + 1):
            if v[h] <= -th: return v[h + L]
        return v[base]
    return f
def seat_sell(base=11, cap=None):
    """sell when a seat-block buyer is seen selling (block h), else at base; with cap, hold past base until that sell (at most cap)"""
    def f(p, L):
        v = p["p2"]; fs = p["seat_first_sell"]; end = cap or base
        if fs is not None and fs + L <= end: return v[max(fs + L, 0)] if (cap or fs + L <= base) else v[base]
        return v[end] if cap else v[base]
    return f
def early_read(hr, th, base=11, late=None):
    """at the end of block hr: below th -> sell (lands hr+L); else hold to base (or to late if above th)"""
    def f(p, L):
        v = p["p2"]
        if v[hr] < th: return v[hr + L]
        return v[late] if late else v[base]
    return f
def trail(dd, base=11, arm=0.10, cap=30):
    def f(p, L):
        v = p["p2"]; pk = -9
        for h in range(1, cap - L + 1):
            pk = max(pk, v[h])
            if pk >= arm and v[h] <= pk - dd: return v[h + L]
            if pk < arm and h >= base - L: return v[base]
        return v[cap]
    return f
RULES = [("fixed 11 (live)", fixed(11)), ("fixed 9", fixed(9)), ("fixed 13", fixed(13)), ("fixed 15", fixed(15))]
RULES += [(f"tp +{int(t*100)}% else 11", tp(t)) for t in (0.10, 0.20, 0.30, 0.50, 0.75, 1.0)]
RULES += [(f"stop -{int(s*100)}% else 11", stop(s)) for s in (0.05, 0.10, 0.15, 0.20, 0.30)]
RULES += [("seat buyers' first sell, else 11", seat_sell()), ("seat buyers' first sell, hold up to 20", seat_sell(cap=20)), ("seat buyers' first sell, hold up to 30", seat_sell(cap=30))]
RULES += [(f"read at E1+{hr}: < {th:+.0%} sell, else 11", early_read(hr, th)) for hr in (2, 3, 5) for th in (-0.10, -0.05, 0.0)]
RULES += [(f"read at E1+{hr}: < {th:+.0%} sell, else hold to 15", early_read(hr, th, late=15)) for hr in (3, 5) for th in (0.0,)]
RULES += [(f"trail {int(d*100)}% after +10%, else 11 (cap 30)", trail(d)) for d in (0.10, 0.20, 0.30)]
for view in ("k1r", "k0r"):
    F = fires(view)
    for L in (2, 3, 4):
        print(f"\n==== {view} fires with a tape (fit {sum(period(x)=='fit' for x in F)}, read {sum(period(x)=='read' for x in F)}); the rule's sell lands {L} blocks after its read; mean second-place return, [fit | read] ====")
        base = {per: [fixed(11)(PR[x['cv']], L) for x in F if period(x) == per] for per in ("fit", "read")}
        for lab, f in RULES:
            c = []
            for per in ("fit", "read"):
                v = [f(PR[x["cv"]], L) for x in F if period(x) == per]; d = [a - b for a, b in zip(v, base[per])]
                lo, hi = boot_ci(d)
                c.append(f"{mean(v):+6.1%} (d {mean(d):+5.1%}, 95% {lo:+5.1%}..{hi:+5.1%}, better on {sum(z > 1e-9 for z in d):2d} worse {sum(z < -1e-9 for z in d):2d})")
            print(f"  {lab:44s} " + " | ".join(c))
        if view == "k0r": break
