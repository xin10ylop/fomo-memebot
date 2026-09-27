"""twostage.py (edge_check/F), task 4: six two-stage exits, no more, against the best fixed hold on both periods.
  V1 take profit at +30% else sell at 300    V2 take profit at +60% else 300    V3 stop at -30% else 300
  V4 stop at -20% else sell at 15            V5 half at 9, half at 300          V6 half at 15, half at 300
The trigger reads the fire's mark (sell-everything value, model_eff) at the end of each block after the seat; the sell lands 2 blocks
after the trigger (the engine's lag), and a fixed exit at h lands at h+2 too. Partial exits sell half with its own impact and
fold the rest of the tape (common.paths partial). Benchmarks: the best fixed hold of each period in 1..600 (its own in-sample
optimum, exact block) and the variant's base hold at the same lag. Null test for the trigger variants (24.34 discipline): 1,000
permutations, each fire's exit block decided on another fire's path (same period) and read on its own path; how often the null gains
as much over the base hold as the real trigger does, and how often a null variant beats the best fixed hold on both periods.
Also: how the recent and fit dumps happen (blocks from the last mark above -10% to the first below -40%).
    python3 data/derived/edge_check/F/twostage.py > data/derived/edge_check/F/twostage.txt"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from load import *
import common as cm
LAG = 2; NPERM = 1000; rng = np.random.default_rng(11)
TRIG = {"V1 TP +30% else 300": ("tp", 0.30, 300), "V2 TP +60% else 300": ("tp", 0.60, 300), "V3 stop -30% else 300": ("sl", -0.30, 300), "V4 stop -20% else 15": ("sl", -0.20, 15)}
def exit_block(path, kind, lvl, h):
    seg = path[1: h + 1]; hit = np.where(seg >= lvl)[0] if kind == "tp" else np.where(seg <= lvl)[0]
    return (int(hit[0]) + 1 if len(hit) else h) + LAG
def run(M, kind, lvl, h, perm=None):
    T = M if perm is None else M[perm]
    return np.array([M[i, exit_block(T[i], kind, lvl, h)] for i in range(len(M))])
per = {s: P2[mask(s) & FIRE] for s in ("fit", "rec")}
best = {s: (int(np.argmax(per[s].mean(0)[1:601])) + 1) for s in per}
print(f"best fixed hold (exact block, in-sample): fit h {best['fit']} {per['fit'].mean(0)[best['fit']]:+.1%}; rec h {best['rec']} {per['rec'].mean(0)[best['rec']]:+.1%}")
print(f"fixed holds landing 2 late: h15 -> fit {per['fit'][:, 17].mean():+.1%} rec {per['rec'][:, 17].mean():+.1%};  h9 -> fit {per['fit'][:, 11].mean():+.1%} rec {per['rec'][:, 11].mean():+.1%};  h300 -> fit {per['fit'][:, 302].mean():+.1%} rec {per['rec'][:, 302].mean():+.1%}\n")
print(f"{'variant':24s} {'fit':>7s} {'rec':>7s}  {'base fit':>8s} {'base rec':>8s}  triggered fit/rec  beats best both?  null: P(gain>=real) fit / rec   null variants beating best on both")
wins_real = 0
for name, (kind, lvl, h) in TRIG.items():
    v = {s: run(per[s], kind, lvl, h) for s in per}; base = {s: per[s][:, h + LAG] for s in per}
    trig = {s: np.mean([exit_block(p, kind, lvl, h) < h + LAG for p in per[s]]) for s in per}
    gain = {s: v[s].mean() - base[s].mean() for s in per}; nb = {s: 0 for s in per}; nboth = 0
    for _ in range(NPERM):
        g = {}
        for s in per:
            nv = run(per[s], kind, lvl, h, rng.permutation(len(per[s]))); g[s] = nv.mean()
            nb[s] += (g[s] - base[s].mean()) >= gain[s]
        nboth += all(g[s] > per[s].mean(0)[best[s]] for s in per)
    both = all(v[s].mean() > per[s].mean(0)[best[s]] for s in per); wins_real += both
    print(f"{name:24s} {v['fit'].mean():+7.1%} {v['rec'].mean():+7.1%}  {base['fit'].mean():+8.1%} {base['rec'].mean():+8.1%}  {trig['fit']:4.0%} / {trig['rec']:4.0%}        {'yes' if both else 'no':3s}             {nb['fit']/NPERM:5.1%} / {nb['rec']/NPERM:5.1%}                   {nboth/NPERM:5.1%}")
# the partial exits, priced on the tapes with our own half-sale folded into the curve
R = cm.load_all(); meta_set = {m["cv"]: m["set"] for m in META}
for name, (h1, h2) in {"V5 half at 9, half at 300": (9, 300), "V6 half at 15, half at 300": (15, 300)}.items():
    v = {"fit": [], "rec": []}
    for r in R:
        if not cm.is_fire(r): continue
        p, g = cm.paths(cm.tape(r["cv"]), 1, hmax=h2 + LAG, partial=(h1 + LAG, 0.5)); v[r["set"]].append(p[h2 + LAG])
    both = all(np.mean(v[s]) > per[s].mean(0)[best[s]] for s in per); wins_real += both
    print(f"{name:24s} {np.mean(v['fit']):+7.1%} {np.mean(v['rec']):+7.1%}  (fixed {h1}: fit {per['fit'][:, h1+LAG].mean():+.1%} rec {per['rec'][:, h1+LAG].mean():+.1%}; fixed {h2}: fit {per['fit'][:, h2+LAG].mean():+.1%} rec {per['rec'][:, h2+LAG].mean():+.1%})  beats best both? {'yes' if both else 'no'}")
print(f"\nvariants tried: 6; variants beating the best fixed hold on both periods: {wins_real}")
print("\nhow the dumps happen (fires whose mark falls below -40% within 600 blocks): blocks from the last mark above -10% to the first below -40%")
for s in per:
    gaps = []
    for p in per[s]:
        below = np.where(p[1:601] <= -0.40)[0]
        if not len(below): continue
        j = int(below[0]) + 1; above = np.where(p[1:j] > -0.10)[0]
        gaps.append(j - (int(above[-1]) + 1) if len(above) else None)
    g = [x for x in gaps if x is not None]
    print(f"   {s}: {len(gaps)} fires fall below -40%; one block: {sum(x == 1 for x in g)}, 2-5 blocks: {sum(2 <= x <= 5 for x in g)}, more: {sum(x > 5 for x in g)}, never above -10% after the seat: {gaps.count(None)}; gaps {sorted(g)}")
