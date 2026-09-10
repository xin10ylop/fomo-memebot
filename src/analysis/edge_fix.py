"""two honest checks on the gauge, then the levers we can still pull on the launches we keep.
1) the tiers vs flat sizing at the same average exposure (is the gauge a selector or just a throttle?)
2) the gauge's tiers chosen on FIT only, applied to TEST and NEW (was 0.15/0.25/0.35 fitted on everything?)
3) dump reaction: exit as soon as a sell of >= x% of supply lands inside the hold (we land one block after seeing it)
4) exit variants on the NEW windows once more with the gauge on top"""
import sys, statistics as st, collections, random
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH, sniper_exact as SE
PX = RH.PX; Y0 = SE.Y0
data = RH.load(); new = RH.load_new(); data.update(new); NEWK = set(new)
def follow_eth(L, t_in, t_out):
    return sum(r[2] for r in L["rows"] if r[1] == "B" and t_in <= r[0] < t_out)
def build(hold=5.0, tp=0.5, stop_sell_frac=None):
    byk = {}
    for k in sorted(data):
        half = "NEW" if k in NEWK else ("FIT" if k in RH.FIT else "TEST"); recs = []
        for cv, (L, f) in data[k].items():
            r = RH.replay(L, 300 / PX, hold=hold, tp=tp, stop_sell_frac=stop_sell_frac)
            if r[4] == "reverted": continue
            kept = f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)
            by = {}
            for stk in RH.STAKES:
                x = RH.replay(L, stk / PX, hold=hold, tp=tp, stop_sell_frac=stop_sell_frac); by[stk] = (x[0] * PX - 1.0, x[1] * PX, L["ts"] + x[2], L["ts"] + x[3])
            r5 = RH.replay(L, 300 / PX, hold=5.0, tp=0.5)                  # the gauge is always the plain rule's follow-on ETH
            recs.append(dict(t_in=L["ts"] + r[2], t_score=L["ts"] + r5[3] + 20.0, roi=r[0] / r[1], feth=follow_eth(L, r5[2], r5[3]), kept=kept, by=by, k=k, half=half))
        recs.sort(key=lambda x: x["t_in"])
        for i, x in enumerate(recs):
            prev = [y["feth"] for y in recs[:i] if y["t_score"] <= x["t_in"]][-20:]
            x["gauge"] = st.mean(prev) if len(prev) >= 10 else None
        byk[k] = recs
    return byk
def path(recs, rule, start=300.0, frac=0.15):
    bank = start; busy = -1e9; taken = []; stopped = False; expo = []
    for x in recs:
        if not x["kept"] or x["t_in"] < busy: continue
        if bank < 0.5 * start: stopped = True
        if stopped: continue
        mult = rule(x)
        if mult <= 0: continue
        stake = min(max(bank * frac * mult, 25.0), min(300.0, bank)); near = min(RH.STAKES, key=lambda s_: abs(s_ - stake)); rr = x["by"][near]
        dep = min(stake, rr[1]) if rr[1] > 1e-6 else 0.0; bank += dep * (rr[0] / rr[1]) if rr[1] > 1e-6 else rr[0]; busy = rr[3]; taken.append(rr[0] / rr[1] if rr[1] > 1e-6 else 0.0); expo.append(stake / max(bank, 1))
    return bank - start, taken, stopped, expo
def run(byk, rule, frac=0.15, label=""):
    tot = collections.Counter(); ntr = collections.Counter(); stops = collections.Counter(); worst = {}; ex = collections.defaultdict(list); rois = collections.defaultdict(list)
    for k in sorted(byk):
        recs = byk[k]
        if sum(1 for x in recs if x["kept"]) < 10: continue
        g, taken, stopped, expo = path(recs, rule, frac=frac); half = recs[0]["half"]; tot[half] += g; ntr[half] += len(taken); stops[half] += stopped; worst[half] = min(worst.get(half, 9e9), g); ex[half] += expo; rois[half] += taken
    print(f"   {label:70s} FIT {tot['FIT']:7,.0f} ({ntr['FIT']:3d} tr, worst {worst.get('FIT',0):6,.0f}, ROI {100*st.mean(rois['FIT']):+5.1f}%) | TEST {tot['TEST']:7,.0f} ({ntr['TEST']:3d}, worst {worst.get('TEST',0):6,.0f}, ROI {100*st.mean(rois['TEST']):+5.1f}%) | NEW {tot['NEW']:7,.0f} ({ntr['NEW']:3d}, worst {worst.get('NEW',0):6,.0f}, ROI {100*st.mean(rois['NEW']):+5.1f}%) | stops {sum(stops.values())}")
    return tot, rois
TIERS = lambda x: 1.0 if x["gauge"] is None else (0.0 if x["gauge"] < 0.15 else (0.5 if x["gauge"] < 0.25 else (1.0 if x["gauge"] < 0.35 else 1.5)))
byk = build()
print("=== 1) selector or throttle? the tiers against flat sizing (own path from $300, $25 floor, $300 cap, one at a time)")
run(byk, lambda x: 1.0, 0.15, "flat 15%")
run(byk, lambda x: 1.0, 0.20, "flat 20%")
run(byk, lambda x: 1.0, 0.225, "flat 22.5%")
run(byk, TIERS, 0.15, "tiers on 15% (<0.15 off, <0.25 half, <0.35 full, else x1.5)")
run(byk, lambda x: 1.0 if x["gauge"] is None else (0.5 if x["gauge"] < 0.25 else 1.0), 0.225, "gauge halves 22.5% below 0.25 ETH")
run(byk, lambda x: 1.0 if x["gauge"] is None else (0.5 if x["gauge"] < 0.25 else (1.0 if x["gauge"] < 0.35 else 1.5)), 0.20, "tiers on 20%")
print("\n=== 2) the gauge's bins on FIT alone (the thresholds were round numbers picked after seeing all windows); quartiles of the FIT gauge")
fitg = sorted(x["gauge"] for k in byk for x in byk[k] if x["half"] == "FIT" and x["kept"] and x["gauge"] is not None)
q = [fitg[int(len(fitg) * p)] for p in (0.25, 0.5, 0.75)]
print(f"   FIT gauge quartiles: {q[0]:.3f} {q[1]:.3f} {q[2]:.3f}")
Q = lambda x: 1.0 if x["gauge"] is None else (0.5 if x["gauge"] < q[0] else (1.0 if x["gauge"] < q[2] else 1.5))
run(byk, Q, 0.15, f"tiers at FIT quartiles: <{q[0]:.2f} half, <{q[2]:.2f} full, else x1.5")
print("\n=== 3) dump reaction: sell as soon as a sell of >= x% of supply lands inside the hold (we land slip=0.3 s later), ROI per trade on the kept launches")
for ssf in (None, 0.005, 0.01, 0.02, 0.03, 0.05):
    b = build(stop_sell_frac=ssf)
    run(b, lambda x: 1.0, 0.15, f"stop on sell >= {ssf}" if ssf else "no dump reaction (the rule)")
print("\n=== 4) exits with the gauge on top, NEW windows in view")
for hold, tp in ((5.0, 0.5), (7.0, 0.5), (7.0, None), (4.0, 0.5), (5.0, 0.3), (5.0, None)):
    b = build(hold=hold, tp=tp)
    run(b, TIERS, 0.15, f"hold {hold:.0f} TP {tp} with tiers")
