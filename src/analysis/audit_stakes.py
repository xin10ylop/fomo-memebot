"""How big can a trade get before our own buy eats the return, on the four new days and under the filtered rule.
This sets STAKE_MAX for later; at $25 the stake never binds so the number matters only once the bankroll grows."""
import sys, statistics as st, datetime
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX
data = RH.load(); data.update(RH.load_new())
sel = []
for k in sorted(data):
    for cv, (L, f) in data[k].items():
        d = datetime.datetime.fromtimestamp(L["ts"], datetime.timezone.utc)
        if d.strftime("%Y-%m-%d") < "2026-09-12": continue
        if not (f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)): continue
        if not (f["bundle_n"] >= 5 and 0.3 <= f["bundle_eth"] <= 1.2 and f["tk0"] >= 0.03): continue
        sel.append(L)
print(f"the filtered rule on Sep 12-16: {len(sel)} launches\n{'stake':>7s} {'n':>5s} {'mean':>8s} {'median':>8s} {'win':>5s} {'$ per trade':>12s} {'$ total':>9s}")
for stake in (25, 50, 100, 150, 200, 300, 500):
    rois = []
    for L in sel:
        x = RH.replay(L, stake / PX, hold=5.0, tp=0.5)
        if x[1] <= 1e-6 or x[4] == "reverted": continue
        rois.append(((x[0] * PX - 0.10) / (x[1] * PX), x[1] * PX))
    r = [a for a, b in rois]; cost = st.mean(b for a, b in rois)
    print(f"{stake:7d} {len(r):5d} {100*st.mean(r):+7.1f}% {100*st.median(r):+7.1f}% {100*sum(1 for x in r if x>0)/len(r):4.0f}% "
          f"{st.mean(a*b for a, b in rois):+11.2f} {sum(a*b for a, b in rois):+9.0f}   (average money actually put in ${cost:.0f})")
