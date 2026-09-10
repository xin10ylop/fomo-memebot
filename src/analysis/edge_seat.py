"""the crowding lever, as a rule the operator can run from the engine's readout: pick the E1 seat (first in second one, +6.18% surcharge,
every bundled launch is tradable because we land before any outsider) when the share of bundled launches with an outsider in second one
over the previous 60 launches exceeds a threshold, else the E2 rule. E1 'front' lands first (lat 0); 'block' lands one block behind (lat 0.1).
Own path from $300 (15%, $25 floor, $300 cap, one at a time, stop -50%), summed per half; and ROI per trade."""
import sys, statistics as st, collections
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH, sniper_exact as SE
PX = RH.PX
data = RH.load(); new = RH.load_new(); data.update(new); NEWK = set(new)
def rep(L, stk, entry, lat):
    if entry == "E1":
        x = RH.replay(L, stk / PX, hold=5.0, tp=0.5, entry="E1", lat=lat, slip=0.3, min_out_slip=None if lat == 0 else 0.25)
    else:
        x = RH.replay(L, stk / PX, hold=5.0, tp=0.5)
    return (x[0] * PX - 1.0, x[1] * PX, L["ts"] + x[2], L["ts"] + x[3], x[4])
byk = {}
for k in sorted(data):
    half = "NEW" if k in NEWK else ("FIT" if k in RH.FIT else "TEST"); recs = []
    for cv, (L, f) in data[k].items():
        kept = f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)
        by = {"E2": {}, "E1f": {}, "E1b": {}}
        for stk in RH.STAKES:
            by["E2"][stk] = rep(L, stk, "E2", 0.3); by["E1f"][stk] = rep(L, stk, "E1", 0.0); by["E1b"][stk] = rep(L, stk, "E1", 0.1)
        recs.append(dict(t=L["ts"], kept=kept, out1=f["out1_n"] > 0, by=by, half=half, k=k))
    recs.sort(key=lambda x: x["t"])
    for i, x in enumerate(recs):
        prev = [y["out1"] for y in recs[max(0, i - 60):i]]
        x["occ"] = st.mean(prev) if len(prev) >= 20 else None
    byk[k] = recs
def path(recs, choose, start=300.0, frac=0.15):
    bank = start; busy = -1e9; taken = []; stopped = False
    for x in recs:
        seat = choose(x)
        if seat is None: continue
        if seat == "E2" and not x["kept"]: continue
        rr0 = x["by"][seat][300]
        if rr0[4] == "reverted" or rr0[2] < busy: continue
        if bank < 0.5 * start: stopped = True
        if stopped: continue
        stake = min(max(bank * frac, 25.0), min(300.0, bank)); near = min(RH.STAKES, key=lambda s_: abs(s_ - stake)); rr = x["by"][seat][near]
        dep = min(stake, rr[1]) if rr[1] > 1e-6 else 0.0; bank += dep * (rr[0] / rr[1]) if rr[1] > 1e-6 else rr[0]; busy = rr[3]; taken.append((seat, rr[0] / rr[1] if rr[1] > 1e-6 else 0.0))
    return bank - start, taken, stopped
def run(choose, label):
    tot = collections.Counter(); n = collections.Counter(); e1 = collections.Counter(); worst = {}; stops = 0; rois = collections.defaultdict(list); per = []
    for k in sorted(byk):
        recs = byk[k]
        if sum(1 for x in recs if x["kept"]) < 10: continue
        g, taken, stopped = path(recs, choose); h = recs[0]["half"]; tot[h] += g; n[h] += len(taken); e1[h] += sum(1 for s_, r in taken if s_ != "E2"); stops += stopped; worst[h] = min(worst.get(h, 9e9), g); rois[h] += [r for s_, r in taken]; per.append((k, g))
    print(f"   {label:58s} " + " | ".join(f"{h} {tot[h]:7,.0f} ({n[h]:3d} tr, {e1[h]:3d} at E1, ROI {100*st.mean(rois[h]):+5.1f}%, worst {worst.get(h, 0):6,.0f})" for h in ("FIT", "TEST", "NEW")) + f" | stops {stops}")
    return per
print("=== seat choice per launch from the previous 60 bundled launches' second-one occupancy (known at send time)")
run(lambda x: "E2", "E2 always (the rule)")
run(lambda x: "E1f", "E1 front always")
run(lambda x: "E1b", "E1 one block behind always")
for thr in (0.35, 0.45, 0.55, 0.65):
    per = run(lambda x, thr=thr: "E2" if x["occ"] is None or x["occ"] <= thr else "E1f", f"E1 front when occupancy of last 60 > {int(100*thr)}%, else E2")
    if thr in (0.45, 0.55):
        print("      per window: " + ", ".join(f"{k[0][5:]}/{k[1]} {g:+,.0f}" for k, g in per))
    run(lambda x, thr=thr: "E2" if x["occ"] is None or x["occ"] <= thr else "E1b", f"E1 one block behind when occupancy > {int(100*thr)}%, else E2")
print("\n=== the same by half, ROI per trade of E1 front on ALL bundled launches vs E2 on the kept ones, per window")
for k in sorted(byk):
    recs = byk[k]
    if sum(1 for x in recs if x["kept"]) < 10: continue
    e2 = [x["by"]["E2"][300] for x in recs if x["kept"] and x["by"]["E2"][300][4] != "reverted"]; e1 = [x["by"]["E1f"][300] for x in recs if x["by"]["E1f"][300][4] != "reverted"]; occ = st.mean(x["out1"] for x in recs)
    print(f"   {k[0][5:]} {k[1]:5s} occupancy {100*occ:3.0f}%  E2 kept n {len(e2):3d} ROI {100*st.mean(r[0]/r[1] for r in e2 if r[1] > 1e-6):+5.1f}%   E1 front n {len(e1):3d} ROI {100*st.mean(r[0]/r[1] for r in e1 if r[1] > 1e-6):+5.1f}%")
