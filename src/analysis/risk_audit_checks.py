"""answers to the auditor's five open points, on the replay: (a) the later buyers' tolerance as measured from their calldata instead of a flat
10%; (b) the exit variants on all three halves with stop odds; (c) the gate read on the entry's own clock (rival before 2.3 s) and on a widened
second-two band; (d) off-grid fee tiers among the kept launches"""
import sys, os, hashlib, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import risk_harness as RH
data = RH.load(); new = RH.load_new(); data.update(new); NEWK = set(new)
BASE = {"skip_fn": RH.G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0)}
# (a) measured tolerances of direct buyers (Sep 9, 79 sampled): 59% send minOut = 0; the protected 41% by decile: 0.1, 1.0, 2.6, 5, 10, 20, 20, 25, 30, 42 %
DEC = [0.001, 0.010, 0.026, 0.050, 0.100, 0.200, 0.200, 0.250, 0.300, 0.419]
def tol_factory(p_none, router_tol=None):
    def tol(r):
        h = int(hashlib.md5(repr(r).encode()).hexdigest()[:8], 16) / 0xffffffff        # a deterministic draw per event row
        if router_tol is not None and h > 0.5:                                          # half the buys come through a router (measured 67%; 50% used): their tolerance is unknown
            return router_tol
        u = (h * 7919) % 1.0
        if u < p_none:
            return None
        return DEC[int((u - p_none) / (1 - p_none) * 10) % 10]
    return tol
print("=== (a) later buyers' tolerance: flat assumptions vs the measured mix (direct buyers: 59% unprotected, the rest by decile); routers unknown")
for label, tol in (("flat 10% (the tables)", 0.10), ("flat 5% (the auditor's worst case)", 0.05), ("flat 25%", 0.25), ("no reverts at all", None),
                   ("measured mix, routers like direct buyers", tol_factory(0.59)), ("measured mix, every router buyer at 5%", tol_factory(0.59, 0.05)), ("measured mix, every router buyer unprotected", tol_factory(0.59, None))):
    RH.summarize(RH.evaluate(dict(BASE, tol=tol), data), label)
print("\n=== (b) exits, same gate, 15%/$25, all halves")
for label, cfg in (("hold 5 + TP 50% (adopted)", dict(BASE)), ("hold 5, no TP", dict(BASE, take_profit=None)), ("hold 6 + TP 50%", dict(BASE, hold=6.0)), ("hold 7 + TP 50%", dict(BASE, hold=7.0)),
                   ("hold 7, no TP (the section-22 exit)", dict(BASE, hold=7.0, take_profit=None)), ("hold 7 no TP, 20%/$50", dict(BASE, hold=7.0, take_profit=None, sizing=0.2, clamp=(50.0, 300.0)))):
    RH.summarize(RH.evaluate(cfg, data), label)
print("\n=== (c) the gate on the entry's own clock: skip if the first second-two outsider is stamped before 2.3 s (no creation phase), and a widened rival band")
def G_T23(f): return f["rival_t"] is not None and f["rival_t"] < 2.3
def rival_wide(L):
    tier = L["tier"]; return next((r[0] for r in L["rows"][1:] if r[1] == "B" and r[0] <= 3.0 and 0.0010 <= r[5] - tier <= 0.0050), None)
for label, cfg in (("rival stamped before 2.3 s", dict(BASE, skip_fn=G_T23)), ("rival_lag < 0.3 (adopted)", dict(BASE)),
                   ("rival stamped before 2.0 s", dict(BASE, skip_fn=lambda f: f["rival_t"] is not None and f["rival_t"] < 2.0)),
                   ("any rival ever in the seat (look-ahead bound)", dict(BASE, skip_fn=RH.G_RIVAL))):
    RH.summarize(RH.evaluate(cfg, data), label)
wide = {}
for k, keep in data.items():
    for cv, (L, f) in keep.items():
        wide[id(f)] = rival_wide(L)
RH.summarize(RH.evaluate(dict(BASE, skip_fn=lambda f: wide.get(id(f)) is not None and wide[id(f)] - (2.0 - f["pos_create"]) < 0.3), data), "rival_lag < 0.3 with the band widened to 0.10-0.50%")
print("\n=== (d) off-grid fee tiers among the kept launches (a tier off the 0.5% grid can hide a second-two rival)")
grid = lambda t: abs(t * 200 - round(t * 200)) < 0.02
off = collections.Counter(); tot = collections.Counter()
for k, keep in data.items():
    h = "NEW" if k in NEWK else ("FIT" if k in RH.FIT else "TEST")
    for cv, (L, f) in keep.items():
        if f["out1_n"] > 0 or RH.G_WAIT(0.3)(f): continue
        tot[h] += 1; off[h] += not grid(L["tier"])
print({h: f"{off[h]} of {tot[h]} ({100*off[h]/max(1,tot[h]):.1f}%)" for h in ("FIT", "TEST", "NEW")})
RH.summarize(RH.evaluate(dict(BASE, skip_fn=lambda f: RH.G_WAIT(0.3)(f) or not grid(f["tier"])), data), "adopted rule, off-grid tiers skipped")
