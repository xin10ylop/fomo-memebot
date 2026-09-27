"""sweep.py (edge_check/G): task 1. The rule's fires at every hold h = 1..1200 (second place, $13, gas $0.33), for the fit set, each
fit window, the recent set (19 fires with the gaps; rec18 = the eleven windows), Sep 18-21 / Sep 22-27, and each UTC day Sep 18-27:
n, mean, median, win, dead (< -40%), sd, se, $ a fire after gas, the refused launches' mean at the same h and the fires' lift over
them (refused priced at every block). Writes sweep_all.csv (every h, every set) and prints the report's tables.
    python3 data/derived/edge_check/G/sweep.py > data/derived/edge_check/G/sweep.txt"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
C = json.load(gzip.open(G + "curves.json.gz", "rt"))
SEP22 = 1790035200  # 2026-09-22 00:00 UTC
assert time.strftime("%Y-%m-%d %H:%M", time.gmtime(SEP22)) == "2026-09-22 00:00"
def sets():
    S = {"fit": lambda x: x["set"] == "fit", "rec": lambda x: x["set"] == "rec", "rec18": lambda x: x["rec18"],
         "Sep18-21": lambda x: x["T0"] < SEP22, "Sep22-27": lambda x: x["T0"] >= SEP22, "Sep22-23": lambda x: x["T0"] >= SEP22 and x["set"] == "fit"}
    for w in FIT: S[w] = (lambda w: lambda x: x["win"] == w)(w)
    for d in range(18, 28): S[f"Sep {d}"] = (lambda d: lambda x: day(x["T0"]) == f"Sep {d}")(d)
    return S
def stats(v, gs, ref):
    u = [usd(a, g) for a, g in zip(v, gs)]
    return {"n": len(v), "mean": mean(v), "median": median(v), "win": sum(a > 0 for a in v) / len(v), "dead": sum(a < -0.4 for a in v) / len(v),
            "sd": sd(v), "se": se(v), "usd": mean(u), "nref": len(ref), "ref": mean(ref) if ref else float("nan"), "lift": mean(v) - mean(ref) if ref else float("nan")}
def table(pred, key="r2"):
    F = [x for x in C if x["fire"] and pred(x)]; Rf = [x for x in C if not x["fire"] and pred(x)]; out = {}
    for h in range(1, HMAX + 1):
        pairs = [(x[key][h], x["g"]) for x in F if x[key][h] is not None]; ref = [x[key][h] for x in Rf if x[key][h] is not None]
        if len(pairs) < len(F) or not pairs: continue           # a hold is reported only where every fire's tape reaches it
        out[h] = stats([p[0] for p in pairs], [p[1] for p in pairs], ref)
    return out
if __name__ == "__main__":
    S = sets(); T = {name: table(p) for name, p in S.items()}
    with open(G + "sweep_all.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["set", "h", "n", "mean", "median", "win", "dead", "sd", "se", "usd_fire", "n_refused", "refused_mean", "lift"])
        for name, t in T.items():
            for h, s in t.items(): w.writerow([name, h] + [round(s[k], 6) if isinstance(s[k], float) else s[k] for k in ("n", "mean", "median", "win", "dead", "sd", "se", "usd", "nref", "ref", "lift")])
    HS = [1] + list(range(5, 61, 5)) + list(range(80, 301, 20)) + list(range(350, 601, 50)) + [700, 800, 900, 1000, 1100, 1200]
    for name in ("fit", "rec", "rec18"):
        t = T[name]; F = [x for x in C if x["fire"] and S[name](x)]; nref = t[1]["nref"]
        print(f"\n=== {name}: {len(F)} fires, {nref} refused; second place, $13, gas $0.33")
        print(f"{'h':>5s} {'mean':>7s} {'median':>7s} {'win':>4s} {'dead':>4s} {'sd':>5s} {'se':>5s} {'$/fire':>7s} {'refused':>7s} {'lift pts':>8s}")
        for h in HS:
            if h not in t: print(f"{h:5d}  (tapes do not reach)"); continue
            s = t[h]; print(f"{h:5d} {s['mean']:+7.1%} {s['median']:+7.1%} {s['win']:4.0%} {s['dead']:4.0%} {s['sd']:5.2f} {s['se']:5.3f} {s['usd']:+7.2f} {s['ref']:+7.1%} {s['lift']*100:+7.1f}")
    HC = [1, 5, 10, 12, 15, 20, 25, 30, 40, 60, 100, 150, 200, 300, 400, 500, 600, 1200]
    for group in (["fit"] + FIT + ["Sep18-21", "Sep22-27", "rec18", "rec"], [f"Sep {d}" for d in range(18, 28)]):
        print("\nmean by set (n fires / n refused); the lift over the refused in brackets")
        print(f"{'set':>10s} {'n':>7s} " + " ".join(f"{h:>13d}" for h in HC))
        for name in group:
            t = T[name]
            if not t: print(f"{name:>10s}  no fires"); continue
            n = t[1]["n"]; nr = t[1]["nref"]
            print(f"{name:>10s} {n:3d}/{nr:3d} " + " ".join(f"{t[h]['mean']:+6.1%}({t[h]['lift']*100:+5.1f})" if h in t else f"{'-':>13s}" for h in HC))
    print("\nwin / dead / $ a fire by window and day at h = 15, 60, 300, 600")
    for name in ["fit"] + FIT + ["rec"] + [f"Sep {d}" for d in range(18, 28)]:
        t = T[name]
        if not t: continue
        print(f"{name:>10s} " + "  ".join(f"h{h}: win {t[h]['win']:3.0%} dead {t[h]['dead']:3.0%} med {t[h]['median']:+6.1%} ${t[h]['usd']:+5.2f}" for h in (15, 60, 300, 600) if h in t))
