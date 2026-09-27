"""price.py (edge_check/H): the bundle cap, the causal template filter and both, on the engine's and the tables' fires, at exit
block 11 (setting 9 as it lands) and 15; per period, per fit window; the null test (2,000 random drops of the same number of fires
per period, seed 11); the choice on the fit read on the recent set and the reverse.
    python3 data/derived/edge_check/H/price.py > data/derived/edge_check/H/price.txt
Stats per cell: fires, mean, win (> 0), dead (< -40%), $ a fire after $0.33 gas, $ a day. $ a day = the fires' $ / hours * 24 with
hours: fit 96 (the brief; the T0 spans give 95.96), each fit window its T0 span, recent the union of the windows' T0 spans (62.65 h,
check.txt) and, in brackets, the union of the scan windows t_lo..t_hi (76.23 h). h11 on the recent set: the tape-less fires whose
h11 is unknown are left out and counted (n/a)."""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
P = load(); TF = json.load(open(H + "template_flags.json"))
REC_T0H = spans(P, REC); REC_SCANH = 76.23          # check.py (d)
HOURS = {"fit": FIT_HOURS, "rec": REC_T0H, **{w: spans(P, [w]) for w in FIT}}
CAPS = (1.0, 1.5, 2.0, 3.0)
def variants(tkey="3_5"):
    V = [("none", lambda x: True)]
    for c in CAPS: V.append((f"cap{c:.1f}", lambda x, c=c: x["bundle"] <= c))
    V.append(("tmpl", lambda x: not TF[tkey][x["cv"]]["flag"]))
    for c in CAPS: V.append((f"tmpl+cap{c:.1f}", lambda x, c=c: x["bundle"] <= c and not TF[tkey][x["cv"]]["flag"]))
    return V
V = variants()
def ret(x, h): return x["r11"] if h == 11 else x["r15"]
def fires(pop, s, key, h, wins=None):
    S = [x for x in P if x["set"] == s and x[key] and (wins is None or x["win"] in wins)]
    return [x for x in S if ret(x, h) is not None], sum(ret(x, h) is None for x in S)
def stats(F, h, hours):
    v = [ret(x, h) for x in F]; d = [usd(ret(x, h), x["g"]) for x in F]
    if not v: return dict(n=0, mean=float("nan"), win=float("nan"), dead=float("nan"), pf=float("nan"), day=0.0, tot=0.0)
    return dict(n=len(v), mean=mean(v), win=sum(r > 0 for r in v) / len(v), dead=sum(r < -0.4 for r in v) / len(v), pf=mean(d), day=sum(d) / hours * 24, tot=sum(d))
def cell(s, extra=""): return f"{s['n']:3d} {s['mean']:+6.1%} {s['win']:4.0%} {s['dead']:3.0%} ${s['pf']:+5.2f} ${s['day']:+6.1f}{extra}" if s["n"] else f"{0:3d} {'-':>6s}"
rng = random.Random(11); NDRAW = 2000
def null(Ff, Fr, keepf, keepr, h):
    """share of random drops (same number per period) whose kept mean is >= the filter's kept mean on fit, on recent, on both"""
    vf = [ret(x, h) for x in Ff]; vr = [ret(x, h) for x in Fr]
    mf = mean([ret(x, h) for x in keepf]); mr = mean([ret(x, h) for x in keepr]); kf, kr = len(keepf), len(keepr)
    a = b = ab = 0
    for _ in range(NDRAW):
        sf = mean(rng.sample(vf, kf)) if kf else float("nan"); sr = mean(rng.sample(vr, kr)) if kr else float("nan")
        okf = sf >= mf - 1e-12; okr = sr >= mr - 1e-12; a += okf; b += okr; ab += okf and okr
    return a / NDRAW, b / NDRAW, ab / NDRAW
RES = {}
for key, lab in (("fire_eng", "ENGINE (fleet_variants fleets_k2 engine=True >= 2)"), ("fire_tab", "TABLES (crowd_rules fleets >= 2 at k-2)")):
    for h in (11, 15):
        Ff, mf = fires(P, "fit", key, h); Fr, mr = fires(P, "rec", key, h)
        print(f"\n=== {lab}, exit block {h}: fit {len(Ff)} fires, recent {len(Fr)} fires" + (f" (+{mr} with h{h} unknown, left out)" if mr else ""))
        print(f"{'variant':14s} | {'fit: n   mean  win dead  $/fire  $/day':40s} | {'recent: n  mean  win dead  $/fire  $/day (scan-h $/day)':52s} | drop f/r | null P(rand>=) fit rec BOTH | dropped fires' mean fit / rec")
        for vn, fn in V:
            kf = [x for x in Ff if fn(x)]; kr = [x for x in Fr if fn(x)]
            sf = stats(kf, h, HOURS["fit"]); sr = stats(kr, h, HOURS["rec"]); df = [x for x in Ff if not fn(x)]; dr = [x for x in Fr if not fn(x)]
            pn = null(Ff, Fr, kf, kr, h) if vn != "none" else (float("nan"),) * 3
            RES[(key, h, vn)] = dict(fit=sf, rec=sr, null=pn, drop=(len(df), len(dr)), wins={w: stats([x for x in kf if x["win"] == w], h, HOURS[w]) for w in FIT})
            print(f"{vn:14s} | {cell(sf):40s} | {cell(sr, ' ($%+5.1f)' % (sr['tot'] / REC_SCANH * 24)):52s} | {len(df):3d}/{len(dr):2d} | "
                  + ("      -    -    -  " if vn == "none" else f"   {pn[0]:4.0%} {pn[1]:4.0%} {pn[2]:5.1%}") +
                  f"  | {mean([ret(x, h) for x in df]):+6.1%} / {mean([ret(x, h) for x in dr]):+6.1%}")
        print(f"  per fit window ($/day on the window's T0 span: " + ", ".join(f"{w} {HOURS[w]:.2f} h" for w in FIT) + ")")
        print(f"  {'variant':14s} | " + " | ".join(f"{w + ': n mean win dead $/fire $/day':38s}" for w in FIT))
        for vn, fn in V:
            print(f"  {vn:14s} | " + " | ".join(f"{cell(RES[(key, h, vn)]['wins'][w]):38s}" for w in FIT))
        # choice on one period, read on the other ($/day at full fill is the objective; ties to the fewer drops)
        for a, b in (("fit", "rec"), ("rec", "fit")):
            best = max(V, key=lambda v: (round(RES[(key, h, v[0])][a]["day"], 6), -sum(RES[(key, h, v[0])]["drop"])))[0]
            A = RES[(key, h, best)]; N0 = RES[(key, h, "none")]
            print(f"  CHOOSE on {a}: {best:14s} {a} ${A[a]['day']:+.1f}/day vs none ${N0[a]['day']:+.1f} (mean {A[a]['mean']:+.1%} vs {N0[a]['mean']:+.1%}); "
                  f"READ on {b}: ${A[b]['day']:+.1f}/day vs none ${N0[b]['day']:+.1f} (mean {A[b]['mean']:+.1%} vs {N0[b]['mean']:+.1%}, n {A[b]['n']} vs {N0[b]['n']})"
                  + ("" if best == "none" else f"; null P both {A['null'][2]:.1%}"))
json.dump({"|".join(map(str, k)): v for k, v in RES.items()}, open(H + "price.json", "w"), default=str)
