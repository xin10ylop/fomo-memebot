"""the E1 seat priced honestly: stop odds by resample (all bundled launches of a window, shuffled, 1000 paths) for the front and the
one-block-behind landing at 10% and 15% sizing, hold 5 + TP 50% and hold 7 no TP; the tail; per-window own path for E1 front."""
import sys, statistics as st, collections, random
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH, sniper_exact as SE
PX = RH.PX
data = RH.load(); new = RH.load_new(); data.update(new); NEWK = set(new)
def rep(L, stk, lat, hold, tp):
    x = RH.replay(L, stk / PX, hold=hold, tp=tp, entry="E1", lat=lat, slip=0.3, min_out_slip=None if lat == 0 else 0.25)
    return (x[0] * PX - 1.0, x[1] * PX, L["ts"] + x[2], L["ts"] + x[3], x[4])
def build(lat, hold, tp):
    byk = {}
    for k in sorted(data):
        half = "NEW" if k in NEWK else ("FIT" if k in RH.FIT else "TEST"); recs = []
        for cv, (L, f) in data[k].items():
            by = {stk: rep(L, stk, lat, hold, tp) for stk in RH.STAKES}
            if by[300][4] == "reverted": continue
            recs.append(dict(t=L["ts"], by=by, half=half, k=k, roi=by[300][0] / by[300][1]))
        recs.sort(key=lambda x: x["t"]); byk[k] = recs
    return byk
def own(recs, frac):
    bank = 300.0; busy = -1e9; n = 0; stopped = False
    for x in recs:
        rr0 = x["by"][300]
        if rr0[2] < busy: continue
        if bank < 150.0: stopped = True
        if stopped: continue
        stake = min(max(bank * frac, 25.0), min(300.0, bank)); near = min(RH.STAKES, key=lambda s_: abs(s_ - stake)); rr = x["by"][near]
        dep = min(stake, rr[1]) if rr[1] > 1e-6 else 0.0; bank += dep * (rr[0] / rr[1]) if rr[1] > 1e-6 else rr[0]; busy = rr[3]; n += 1
    return bank - 300.0, n, stopped
def resample(recs, frac, paths=1000):
    random.seed(7); stops = 0; ends = []
    for _ in range(paths):
        random.shuffle(recs); bank = 300.0; stopped = False
        for x in recs:
            if bank < 150.0: stopped = True; break
            stake = min(max(bank * frac, 25.0), min(300.0, bank)); near = min(RH.STAKES, key=lambda s_: abs(s_ - stake)); rr = x["by"][near]
            bank += (min(stake, rr[1]) * (rr[0] / rr[1]) if rr[1] > 1e-6 else rr[0])
        ends.append(bank); stops += stopped
    ends.sort(); return stops / paths, ends[len(ends) // 2] - 300
print("=== E1 on every bundled launch: ROI per trade, tail (< -40%), own path from $300, stop odds by resample; per half")
for lat, lname in ((0.0, "front"), (0.1, "one block behind")):
    for hold, tp in ((5.0, 0.5), (7.0, None)):
        byk = build(lat, hold, tp)
        for frac in (0.10, 0.15):
            agg = collections.defaultdict(lambda: dict(roi=[], tail=[], own=0.0, n=0, stops=0, pstop=[], pmax=0.0, wins=0, nwin=0))
            for k in sorted(byk):
                recs = byk[k]
                if len(recs) < 10: continue
                h = recs[0]["half"]; a = agg[h]; a["roi"] += [x["roi"] for x in recs]; g, n, stopped = own(recs, frac); a["own"] += g; a["n"] += n; a["stops"] += stopped; a["wins"] += g > 0; a["nwin"] += 1
                p, med = resample(list(recs), frac); a["pstop"].append(p); a["pmax"] = max(a["pmax"], p)
            print(f"   E1 {lname:16s} hold {hold:.0f} TP {str(tp):4s} sizing {int(100*frac):2d}%  " + " | ".join(f"{h} ROI {100*st.mean(a['roi']):+5.1f}% tail {100*sum(1 for r in a['roi'] if r < -0.4)/len(a['roi']):4.1f}% own {a['own']:7,.0f} ({a['n']:4d} tr, +win {a['wins']}/{a['nwin']}, own stops {a['stops']}) P(stop) {100*st.mean(a['pstop']):4.1f}% max {100*a['pmax']:4.1f}%" for h, a in sorted(agg.items())), flush=True)
print("\n=== per window, E1 front, hold 5 + TP 50%, 15%: own path and resampled stop odds; next to E2 kept")
byk = build(0.0, 5.0, 0.5)
e2 = {}
for k in sorted(data):
    rs = []
    for cv, (L, f) in data[k].items():
        if f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f):
            x = RH.replay(L, 300 / PX, hold=5.0, tp=0.5)
            if x[4] != "reverted": rs.append(x[0] / x[1])
    e2[k] = rs
for k in sorted(byk):
    recs = byk[k]
    if len(recs) < 10: continue
    g, n, stopped = own(recs, 0.15); p, med = resample(list(recs), 0.15)
    print(f"   {k[0][5:]} {k[1]:5s} E1 front n {len(recs):4d} ROI {100*st.mean(x['roi'] for x in recs):+5.1f}% tail {100*sum(1 for x in recs if x['roi'] < -0.4)/len(recs):4.1f}%  own {g:+7,.0f} ({n:3d} tr{', STOPPED' if stopped else ''}) P(stop) {100*p:4.1f}% median end {med:+7,.0f}   | E2 kept n {len(e2[k]):3d} ROI {100*st.mean(e2[k]):+5.1f}%" if e2[k] else "")
