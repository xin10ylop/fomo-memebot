"""curves.py (edge_check/E): the rule's fires at every hold h = 1..1200 (second place, $13, gas $0.33), and the refused launches
at the same h, for the fit set, each fit window, the recent set (172 launches, 19 fires; and the 160/18 committed files), day by
day Sep 18-27, and Sep 18-21 / Sep 22-27. Writes curves.csv (every group, every h) and prints the report's tables.
    python3 data/derived/edge_check/E/curves.py > data/derived/edge_check/E/curves.txt"""
import sys, os, json, gzip, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
P = json.load(gzip.open(c.EE + "paths.json.gz", "rt")); HM = 1200
DAYS = [f"Sep {d}" for d in range(18, 28)]
GROUPS = [("fit", lambda x: x["set"] == "fit")] + [(w, (lambda w: lambda x: x["win"] == w)(w)) for w in c.FIT] + \
         [("rec", lambda x: x["set"] == "rec"), ("rec18", lambda x: x["set"] == "rec" and x["committed"]),
          ("Sep18-21", lambda x: x["day"] in DAYS[:4]), ("Sep22-27", lambda x: x["day"] in DAYS[4:])] + \
         [(d, (lambda d: lambda x: x["day"] == d)(d)) for d in DAYS]
def stats(rows, h):
    v = [x["p1"][h] for x in rows if x["p1"][h] is not None]
    if not v: return None
    u = [x["p1"][h] * x["g"] * c.E - c.GAS for x in rows if x["p1"][h] is not None]
    return {"n": len(v), "mean": c.mean(v), "median": c.median(v), "win": sum(a > 0 for a in v) / len(v), "dead": sum(a < -0.4 for a in v) / len(v),
            "sd": c.sd(v), "se": c.se(v), "usd": c.mean(u)}
def curve(sel):
    f = [x for x in P if x["fire"] and sel(x)]; rf = [x for x in P if not x["fire"] and sel(x)]; out = {}
    for h in range(1, HM + 1):
        s = stats(f, h); r = stats(rf, h)
        if s is None: continue
        s["n_ref"] = r["n"] if r else 0; s["ref"] = r["mean"] if r else float("nan"); s["lift"] = s["mean"] - s["ref"]; out[h] = s
    return out
if __name__ == "__main__":
    CV = {g: curve(sel) for g, sel in GROUPS}
    with open(c.EE + "curves.csv", "w", newline="") as fh:
        w = csv.writer(fh); keys = ["n", "mean", "median", "win", "dead", "sd", "se", "usd", "n_ref", "ref", "lift"]; w.writerow(["group", "h"] + keys)
        for g, cv in CV.items():
            for h, s in cv.items(): w.writerow([g, h] + [round(s[k], 6) if isinstance(s[k], float) else s[k] for k in keys])
    TAB = [1] + list(range(5, 61, 5)) + list(range(80, 301, 20)) + list(range(350, 601, 50)) + list(range(700, 1201, 100))
    for g in ("fit", "rec"):
        cv = CV[g]; print(f"\n=== {g}: {cv[1]['n']} fires, {cv[1]['n_ref']} refused (second place, $13, sell at the end of block E1+h)")
        print(f"{'h':>5s} {'mean':>7s} {'median':>7s} {'win':>5s} {'dead':>5s} {'sd':>6s} {'se':>6s} {'$/fire':>7s} {'refused':>8s} {'lift':>7s}")
        for h in TAB:
            s = cv.get(h)
            if s: print(f"{h:5d} {s['mean']:+7.1%} {s['median']:+7.1%} {s['win']:5.0%} {s['dead']:5.0%} {s['sd']:6.3f} {s['se']:6.3f} {s['usd']:+7.2f} {s['ref']:+8.1%} {s['lift']:+7.1%}")
    print("\n=== every group, fires' mean return (n fires / n refused), same holds")
    print(f"{'group':>9s} {'n':>8s} " + " ".join(f"{h:>6d}" for h in TAB))
    for g, cv in CV.items():
        print(f"{g:>9s} {cv[1]['n']:3d}/{cv[1]['n_ref']:<4d} " + " ".join(f"{cv[h]['mean']:+6.1%}" if h in cv else "     -" for h in TAB))
    print("\n=== every group, lift over the refused at the same holds")
    for g, cv in CV.items():
        print(f"{g:>9s} {cv[1]['n']:3d}/{cv[1]['n_ref']:<4d} " + " ".join(f"{cv[h]['lift']:+6.1%}" if h in cv else "     -" for h in TAB))
    print("\n=== every group, $ a fire after gas")
    for g, cv in CV.items():
        print(f"{g:>9s} {cv[1]['n']:3d}/{cv[1]['n_ref']:<4d} " + " ".join(f"{cv[h]['usd']:+6.2f}" if h in cv else "     -" for h in TAB))
    print("\n=== every group, win rate / dead rate / sd at h = 15, 60, 150, 300, 600, 1200")
    for g, cv in CV.items():
        print(f"{g:>9s} " + "  ".join(f"h{h}: {cv[h]['win']:3.0%}/{cv[h]['dead']:3.0%}/{cv[h]['sd']:.2f}" for h in (15, 60, 150, 300, 600, 1200) if h in cv))
