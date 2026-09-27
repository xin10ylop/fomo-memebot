"""kit.py (reviewer D): the evaluation harness shared by the analysis scripts. A policy maps a launch's features to an exit
(blocks after E1) or None (no fire). Money: $13 stake, second place in E1, the path of features.py (= stake_scale.model_eff),
gas $0.33 per fire. $/day on the fit 96 h and the recent 60 h (reach_table.py's hours), per fit window on crowd_rules' hours."""
import sys, os, json, gzip, math, random, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
FE = json.load(gzip.open(c.DD + "features.json.gz", "rt"))
for f in FE: f["day"] = c.day(f["T0"])
FIT = [f for f in FE if f["grp"] == "fit"]; REC = [f for f in FE if f["grp"] == "recent"]
def rets(L, pol):
    out = []
    for f in L:
        h = pol(f)
        if h is None: continue
        out.append(f["path"][min(h, 600)])
    return out
def dpd(v, hours): return sum(c.usd(x) for x in v) / hours * 24
def evaluate(pol, L=None):
    """{'fit': (n, mean, win, dead, $/day), 'recent': ..., per fit window $/day}"""
    res = {}
    for g, S in (("fit", FIT), ("recent", REC)):
        v = rets(S, pol); res[g] = (len(v), c.mean(v), sum(x > 0 for x in v) / len(v) if v else float("nan"), sum(x < -0.4 for x in v) / len(v) if v else float("nan"), dpd(v, c.HOURS[g]), v)
    res["wins"] = {w: dpd(rets([f for f in FIT if f["win"] == w], pol), h) for w, h in c.FIT_W_HOURS.items()}
    return res
def line(name, res):
    a, b = res["fit"], res["recent"]
    return (f"{name:46s} fit {a[0]:3d} {a[1]:+6.1%} w{a[2]:4.0%} d{a[3]:4.0%} ${a[4]:+6.1f}/d | recent {b[0]:3d} {b[1]:+6.1%} w{b[2]:4.0%} d{b[3]:4.0%} ${b[4]:+6.1f}/d"
            + " | windows " + " ".join(f"{x:+.0f}" for x in res["wins"].values()))
def gate(f): return f["fire"]
