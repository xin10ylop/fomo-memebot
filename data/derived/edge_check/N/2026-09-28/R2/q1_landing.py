"""Q1: did the 2 ms step / 46 ms lead (live 12:27 Sep 28) land us earlier? Read from the chain on disk: every burst of our relay
in the crowd files (blocks 0..k+1, every transaction aimed at the curve with its index in the block) and each launch's E1 buyers
in order (launches_*.json). Burst-level measure: rival transactions ahead of our first shot in E1 (not only fills)."""
import json, gzip, glob, os, time, math, statistics as st
D = "/home/user/fomo-memebot/data/derived/live_vs_table"
RELAY = "0xe8e98c3514d5bd83fdd01360896f2382b861a720"; W = "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01"
SWITCH = 1790598420   # 2026-09-28 12:27 UTC
rows = []
for lf in sorted(glob.glob(f"{D}/launches_sep2[6-8]*.json")):
    n = os.path.basename(lf)[9:-5]
    cf = next((c for c in (f"{D}/crowd_raw_{n}.json.gz", f"{D}/crowd_raw_{n}.json") if os.path.exists(c)), None)
    if not cf: continue
    L = {l["cv"].lower(): l for l in json.load(open(lf))}
    R = json.load(gzip.open(cf, "rt")) if cf.endswith(".gz") else json.load(open(cf))
    for r in R:
        bl = r["blocks"]; k = r["k"]
        ours = [(j, t["ix"]) for j, b in enumerate(bl) for t in b if t["to"].lower() == RELAY]
        if not ours: continue
        l = L.get(r["cv"].lower(), {}); e1 = l.get("e1_block_buyers"); e1 = e1 if isinstance(e1, list) else None
        inc = sum(1 for j, _ in ours if j <= k); ine1 = [ix for j, ix in ours if j == k + 1]
        ahead = sum(1 for t in bl[k + 1] if t["to"].lower() != RELAY and t["ix"] < min(ine1)) if ine1 and len(bl) > k + 1 else None
        pos = (e1.index(W) + 1) if e1 and W in e1 else None
        rows.append(dict(t=r["T0"], cv=r["cv"][:10], k=k, in_creation=inc, in_e1=len(ine1), rivals_ahead=ahead, e1_pos=pos, e1_n=len(e1) if e1 else None, post=r["T0"] >= SWITCH))
rows.sort(key=lambda x: x["t"])
print("burst                    k  ours in creation s / in E1   rival txs ahead of our first E1 shot   our E1 buyer position (of)")
for x in rows:
    print(f"{time.strftime('%m-%d %H:%M:%S', time.gmtime(x['t']))} {x['cv']} {'NEW' if x['post'] else 'old'} {x['k']:2d}   {x['in_creation']:2d} / {x['in_e1']:2d}      {str(x['rivals_ahead']):>4s}      {str(x['e1_pos']):>4s} ({x['e1_n']})")
def fisher_one_sided(a, b, c, d):
    """P(X >= a) for a 2x2 table [[a, b], [c, d]] with fixed margins (hypergeometric)"""
    n1, n2, m = a + b, c + d, a + c; N = n1 + n2
    p = lambda x: math.comb(n1, x) * math.comb(n2, m - x) / math.comb(N, m)
    return sum(p(x) for x in range(a, min(n1, m) + 1))
for label, sel in (("old", lambda x: not x["post"]), ("new", lambda x: x["post"])):
    v = [x for x in rows if sel(x) and x["rivals_ahead"] is not None]
    print(f"{label}: bursts with shots in E1 {len(v)}, first in E1 (no rival tx ahead) {sum(x['rivals_ahead'] == 0 for x in v)}, rival txs ahead median {st.median(x['rivals_ahead'] for x in v)}")
o = [x for x in rows if not x["post"] and x["rivals_ahead"] is not None]; nw = [x for x in rows if x["post"] and x["rivals_ahead"] is not None]
a = sum(x["rivals_ahead"] == 0 for x in nw); c = sum(x["rivals_ahead"] == 0 for x in o)
print(f"Fisher one-sided p (new lands first more often than old), bursts: {fisher_one_sided(a, len(nw) - a, c, len(o) - c):.2f}")
# fills only, as the brief counts them (the reading's landed lines, Sep 26-28): old [2,2,first(E1+2),2,1], new [1,4,2,1,1]
print(f"Fisher one-sided p, fills (old 1 of 5 first in E1, new 3 of 5): {fisher_one_sided(3, 2, 1, 4):.2f};  as the brief counts (2 of 5 vs 4 of 5): {fisher_one_sided(4, 1, 2, 3):.2f}")
# sample size: two proportions, one-sided alpha 0.05, power 0.8
za, zb = 1.645, 0.842
for p0, p1 in ((0.4, 0.8), (0.4, 0.6), (0.3, 0.5)):
    pb = (p0 + p1) / 2; nn = (za * math.sqrt(2 * pb * (1 - pb)) + zb * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2 / (p1 - p0) ** 2
    print(f"fills per arm to tell {p0:.0%} from {p1:.0%} first (one-sided 5%, power 80%): {math.ceil(nn)}")
# against a fixed baseline (one-sample binomial): how many new-setting landings to reject p0 = 0.4 if the truth is 0.6 or 0.8
for p0, p1 in ((0.4, 0.6), (0.4, 0.8)):
    nn = ((za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))) / (p1 - p0)) ** 2
    print(f"new-setting landings to reject a fixed {p0:.0%} baseline if the truth is {p1:.0%}: {math.ceil(nn)}")
# what first place is worth over second on the week's fills (grids with both columns), usual view, slip 0.20
R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rows_k1reg.json")))
v = [(x["ret_first"]["11"], x["ret"]["11"], x["T0"]) for x in R if x["why"] == "FILL" and x["ret_first"].get("11") is not None]
for lab, lo, hi in (("Sep 21-23", 0, 1790208000), ("Sep 24-28", 1790208000, 2e9)):
    w = [(f, s) for f, s, t in v if lo <= t < hi]
    if w: print(f"first minus second at h11, fills {lab}: n={len(w)} mean first {st.mean(f for f, s in w):+.1%} second {st.mean(s for f, s in w):+.1%} gap {st.mean(f - s for f, s in w):+.1%} median gap {st.median(f - s for f, s in w):+.1%}")
# the burst's offset against the tick, from the shots that landed in the creation second: shots run from -LEAD to +22 ms around the
# estimated boundary, STEP apart, so n shots before the tick means the tick came at about n*STEP - LEAD ms from the estimate
# (negative: the tick came earlier than the estimate / our shots arrived later than planned). Old 3 ms / 80 ms (runbook 5y), new 2 / 46.
print("\nburst offset (tick minus estimate, ms) from the shots in the creation second")
for lab, post, step, lead in (("old 3/80", False, 3, 80), ("new 2/46", True, 2, 46)):
    v = [x for x in rows if x["post"] == post]
    offs = [x["in_creation"] * step - lead for x in v]
    print(f"  {lab}: {sorted(offs)}  median {st.median(offs):+.0f} ms; bursts with no shot in the creation second (all late) {sum(x['in_creation'] == 0 for x in v)} of {len(v)}; with every landed shot in the creation second {sum(x['in_e1'] == 0 for x in v)}")
