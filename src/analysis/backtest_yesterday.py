"""yesterday, replayed with the rule as the engine runs it now: hours 12-06 UTC, no first-of-a-dead-stretch trade, E2 0.3 s in,
hold 5 + TP 50%, $25 stakes (the live cap) and the $300 cap, one position at a time, from the live wallet's $92."""
import sys, statistics as st, collections, datetime
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX
data = RH.load_new(); WINS = [("2026-09-10", "12-18"), ("2026-09-10", "18-24"), ("2026-09-11", "0-6")]
recs = []
for k in WINS:
    if k not in data: print("missing window", k); continue
    for cv, (L, f) in data[k].items():
        kept = f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)
        by = {}
        for stk in RH.STAKES:
            x = RH.replay(L, stk / PX, hold=5.0, tp=0.5); by[stk] = (x[0] * PX - 1.0, x[1] * PX, L["ts"] + x[2], L["ts"] + x[3], x[4])
        recs.append(dict(k=k, t=by[25][2], t_score=by[25][3] + 20, kept=kept and by[25][4] != "reverted", roi=by[25][0] / by[25][1] if by[25][1] > 1e-6 else 0.0, by=by, hour=f["hour"], bundle=f["bundle_n"], beth=f["bundle_eth"]))
recs.sort(key=lambda x: x["t"])
for i, x in enumerate(recs):
    x["prev1h"] = sum(1 for y in recs[:i] if y["kept"] and x["t"] - 3600 <= y["t_score"] <= x["t"])
    x["hour_ok"] = not (6 <= int(x["hour"]) < 12)
kept = [x for x in recs if x["kept"]]
print(f"=== yesterday: {len(recs)} bundled launches in the three windows, {len(kept)} pass the rule")
print(f"{'window':18s} {'kept':>4s} {'ROI':>7s} {'median':>7s} {'<-40%':>5s} {'net $25 stakes':>14s}")
for k in WINS:
    xs = [x for x in kept if x["k"] == k]
    if xs: print(f"{k[0][5:]} {k[1]:6s}     {len(xs):4d} {100*st.mean(x['roi'] for x in xs):+6.1f}% {100*st.median(x['roi'] for x in xs):+6.1f}% {100*sum(1 for x in xs if x['roi'] < -0.4)/len(xs):4.0f}% {sum(x['by'][25][0] for x in xs):+13.0f}")
print("\n--- by hour (UTC), kept launches")
byh = collections.defaultdict(list)
for x in kept: byh[int(x["hour"])].append(x["roi"])
for h in sorted(byh): print(f"   {h:02d}:00  n {len(byh[h]):3d}  mean {100*st.mean(byh[h]):+6.1f}%  <-40% {sum(1 for r in byh[h] if r < -0.4)}")
def path(rule, start, frac, cap):
    bank = start; busy = -1e9; taken = []; peak = start; dd = 0
    for x in recs:
        if not x["kept"] or not rule(x) or x["t"] < busy: continue
        stake = min(max(bank * frac, 25.0), min(cap, bank)); near = min(RH.STAKES, key=lambda s_: abs(s_ - stake)); rr = x["by"][near]
        if rr[4] == "reverted": continue
        dep = min(stake, rr[1]) if rr[1] > 1e-6 else 0.0; bank += dep * (rr[0] / rr[1]) if rr[1] > 1e-6 else rr[0]; busy = rr[3]; taken.append(rr[0] / rr[1] if rr[1] > 1e-6 else 0.0); peak = max(peak, bank); dd = max(dd, 1 - bank / peak)
    return bank, taken, dd
print("\n--- own path from $92, one position at a time")
for label, rule in (("rule as before (any hour, any stretch)", lambda x: True), ("engine 4.7: hours 12-06 and a rule-passing launch in the previous hour", lambda x: x["hour_ok"] and x["prev1h"] >= 1)):
    for cap in (25, 300):
        bank, taken, dd = path(rule, 92.0, 0.15, cap)
        print(f"   {label:70s} cap ${cap:3d}: {len(taken):3d} trades, mean {100*st.mean(taken):+5.1f}%, losers <-40%: {sum(1 for r in taken if r < -0.4)}, end ${bank:,.0f} ({bank-92:+,.0f}), worst drawdown {100*dd:.0f}%")
skipped = [x for x in kept if not (x["hour_ok"] and x["prev1h"] >= 1)]
if skipped: print(f"\n--- the new gates would have skipped {len(skipped)} rule-passing launches yesterday: mean {100*st.mean(x['roi'] for x in skipped):+.1f}%, " + ", ".join(f"{datetime.datetime.utcfromtimestamp(x['t']).strftime('%H:%M')} {100*x['roi']:+.0f}%" for x in skipped[:12]))
