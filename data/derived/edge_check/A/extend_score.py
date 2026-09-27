"""extend_score.py (edge_check/A): score the stretches pulled by extend_window.py (tags given on the command line) with the
same fleet counter and the same model as the rest of this folder: every qualifying launch priced at second place, $13,
h15 and h300; the fires (fleets >= 2 at k-2) listed; then the recent set updated with them and the fit comparison redone.
    python3 data/derived/edge_check/A/extend_score.py gapA gapB [chk27]"""
import sys, json, gzip, math, random, statistics as st, io, contextlib
sys.path.insert(0, "data/derived/edge_check/A"); sys.path.insert(0, "src/analysis")
from common import *
tags = [t for t in sys.argv[1:] if not t.startswith("chk")]; chks = [t for t in sys.argv[1:] if t.startswith("chk")]
with contextlib.redirect_stdout(io.StringIO()): import price as P       # (price.py resets sys.argv)
def d(v): return f"n {len(v):3d} mean {st.mean(v):+6.1%} median {st.median(v):+6.1%} win {sum(y > 0 for y in v)/len(v):3.0%} dead {sum(y < -0.4 for y in v)/len(v):3.0%}" if v else "n   0"
new_fires = []; new_ref = []; committed = {r["cv"] for w in REC for r in load_raw(w)}
for tag in tags + chks:
    meta = json.load(open(A + f"launches_{tag}.json")); R = json.load(gzip.open(A + f"crowd_raw_{tag}.json.gz", "rt")); TP = json.load(gzip.open(A + f"tapes_{tag}.json.gz", "rt"))
    print(f"=== {tag}: {hms(meta['t_lo'])} - {hms(meta['t_hi'])} UTC ({(meta['t_hi']-meta['t_lo'])/3600:.2f} h), creations {meta['creations']}, unresolved {meta['unresolved']}, qualifying {len(meta['launches'])}, crowds {len(R)}, tapes {len(TP)}")
    for r in sorted(R, key=lambda r: r["T0"]):
        L = TP.get(r["cv"])
        if L is None or L.get("tier") is None: print("   no tape", r["cv"]); continue
        bE1, ts = P.seat_block(L)
        if bE1 is None: print("   no seat block", r["cv"]); continue
        m = P.my_model(L); cf = fleets_by_block(r); fire = at(cf, r["k"] - 2) >= 2
        print(f"   {hms(r['T0'])} {r['cv'][:10]} k {r['k']} fleets {cf} {'FIRE' if fire else '    '} h15 {m[15]:+7.1%} h300 {m[300]:+7.1%}")
        if r["cv"] in committed and tag in tags: print("      (already in a committed window: not counted again)"); continue
        if tag in tags: (new_fires if fire else new_ref).append({"T0": r["T0"], "cv": r["cv"], "h15": m[15], "h300": m[300]})
if chks:
    committed = {r["cv"] for w in REC for r in load_raw(w)}
    for tag in chks:
        R = json.load(gzip.open(A + f"crowd_raw_{tag}.json.gz", "rt")); mine = {r["cv"] for r in R}
        base = [r for r in load_raw("sep27night")]; bc = {r["cv"] for r in base}
        print(f"\n=== completeness check {tag} against the committed sep27night: mine {len(mine)}, committed {len(bc)}, in both {len(mine & bc)}, only mine {len(mine - bc)}, only committed {len(bc - mine)}")
        for r in base:
            if r["cv"] not in mine: print(f"   only in the committed file: {hms(r['T0'])} {r['cv'][:10]} (T0 {r['T0']}, the window ends at {json.load(open(A + f'launches_{tag}.json'))['t_hi']})")
        for r in R:
            if r["cv"] not in bc: print(f"   missing from the committed file: {hms(r['T0'])} {r['cv'][:10]} fleets@k-2 {at(fleets_by_block(r), r['k'] - 2)}")
if tags:
    print(f"\nnew stretches: fires {d([x['h300'] for x in new_fires])}; refused {d([x['h300'] for x in new_ref])}")
    print(f"               fires at h15 {d([x['h15'] for x in new_fires])}")
    F = json.load(open(A + "fires.json")); fit = [x["ret"]["300"] for x in F if x["set"] == "fit"]; rec = [x["ret"]["300"] for x in F if x["set"] == "rec"]
    allrec = rec + [x["h300"] for x in new_fires]; random.seed(20260927)
    boot = sum(st.fmean(random.choices(fit, k=len(allrec))) <= st.mean(allrec) for _ in range(100000)) / 100000
    pool = fit + allrec; obs = st.mean(fit) - st.mean(allrec); cnt = 0
    for _ in range(100000):
        random.shuffle(pool)
        if st.fmean(pool[:len(fit)]) - st.fmean(pool[len(fit):]) >= obs: cnt += 1
    allr = sorted((x, i < len(fit)) for i, x in enumerate(fit + allrec)); Ra = sum(i + 1 for i, (x, isa) in enumerate(allr) if isa)
    U = Ra - len(fit) * (len(fit) + 1) / 2; mu = len(fit) * len(allrec) / 2; sd = math.sqrt(len(fit) * len(allrec) * (len(fit) + len(allrec) + 1) / 12); z = (U - mu) / sd
    sdp = st.stdev(fit + allrec); llr = sum((x ** 2 - (x - st.mean(fit)) ** 2) / (2 * sdp ** 2) for x in allrec)
    print(f"recent updated: {d(allrec)}\n   bootstrap P(18+ draws from the fit <= this mean) {boot:.4f}; permutation p {cnt/100000:.4f}; Mann-Whitney z {z:.2f} p {0.5*math.erfc(z/math.sqrt(2)):.4f}; SPRT LLR {llr:+.2f}")
    # the gate's lift with the new stretches: refused = the committed recent refused (hold_grid behind1_15_h300) + the new refused (this model)
    Hh = {}
    for w in REC: Hh.update({x["cv"]: x for x in json.load(open(D + HG[w]))})
    ref = [Hh[r["cv"]]["behind1_15_h300"] for r in all_launches(REC) if not is_fire(r)] + [x["h300"] for x in new_ref]
    print(f"   lift with the new stretches: fired {st.mean(allrec):+.1%} ({len(allrec)}) - refused {st.mean(ref):+.1%} ({len(ref)}) = {st.mean(allrec) - st.mean(ref):+.1%}")
    step = st.mean(fit) ** 2 / (2 * sdp ** 2); hrs_new = sum((json.load(open(A + f"launches_{t}.json"))["t_hi"] - json.load(open(A + f"launches_{t}.json"))["t_lo"]) / 3600 for t in tags)
    r_all = len(allrec) / (60 + hrs_new) * 24; r_new = max(len(new_fires), 1e-9) / hrs_new * 24
    lo_n = (2.94 + llr) / step; hi_n = (2.94 - llr) / step
    print(f"   sequential test: drift {step:.3f} per fire; about {lo_n:.0f} more fires to the lower boundary if the true mean is 0, {hi_n:.0f} to the upper if it is the fit's")
    print(f"   fire rate: {len(allrec)} fires in {60 + hrs_new:.1f} h = {r_all:.1f}/day -> {lo_n / r_all:.1f} / {hi_n / r_all:.1f} days; the last {hrs_new:.1f} h alone: {len(new_fires)} fire(s) = {r_new:.1f}/day -> {lo_n / r_new:.1f} / {hi_n / r_new:.1f} days")
