"""stop odds of the sizing choices, plan-consistent resample (shuffle ALL kept trades of a window, each keeps its own gauge tier),
per half; and the split of the gains drop into fewer trades (crowding) vs less return per trade (demand)."""
import sys, statistics as st, collections, random
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH, sniper_exact as SE
sys.path.insert(0, '.'); 
PX = RH.PX
data = RH.load(); new = RH.load_new(); data.update(new); NEWK = set(new)
def follow_eth(L, t_in, t_out):
    return sum(r[2] for r in L["rows"] if r[1] == "B" and t_in <= r[0] < t_out)
byk = {}; share = collections.defaultdict(lambda: [0, 0])
for k in sorted(data):
    half = "NEW" if k in NEWK else ("FIT" if k in RH.FIT else "TEST"); recs = []
    for cv, (L, f) in data[k].items():
        r = RH.replay(L, 300 / PX, hold=5.0, tp=0.5)
        if r[4] == "reverted": continue
        kept = f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f); share[half][0] += kept; share[half][1] += 1
        by = {}
        for stk in RH.STAKES:
            x = RH.replay(L, stk / PX, hold=5.0, tp=0.5); by[stk] = (x[0] * PX - 1.0, x[1] * PX, L["ts"] + x[2], L["ts"] + x[3])
        recs.append(dict(t_in=L["ts"] + r[2], t_score=L["ts"] + r[3] + 20.0, roi=r[0] / r[1], feth=follow_eth(L, r[2], r[3]), kept=kept, by=by, k=k, half=half))
    recs.sort(key=lambda x: x["t_in"])
    for i, x in enumerate(recs):
        prev = [y["feth"] for y in recs[:i] if y["t_score"] <= x["t_in"]][-20:]
        x["gauge"] = st.mean(prev) if len(prev) >= 10 else None
    byk[k] = recs
print("=== clean launches (no outsider in second one, none before our send) as a share of bundled launches, and windows' mean")
for h in ("FIT", "TEST", "NEW"):
    print(f"   {h}: kept {share[h][0]} of {share[h][1]} bundled = {100*share[h][0]/share[h][1]:.0f}%")
nwin = collections.Counter(recs[0]["half"] for recs in byk.values() if len(recs))
kept_per_win = {h: share[h][0] / nwin[h] for h in nwin}
print("   kept per window: " + ", ".join(f"{h} {kept_per_win[h]:.0f}" for h in ("FIT", "TEST", "NEW")))
import math
roi = {h: st.mean(x["roi"] for k in byk for x in byk[k] if x["half"] == h and x["kept"]) for h in nwin}
print("   mean ROI per kept trade: " + ", ".join(f"{h} {100*roi[h]:+.1f}%" for h in ("FIT", "TEST", "NEW")))
a = math.log(kept_per_win["NEW"] / kept_per_win["FIT"]); b = math.log(roi["NEW"] / roi["FIT"])
print(f"   FIT -> NEW: trades per window x{kept_per_win['NEW']/kept_per_win['FIT']:.2f}, ROI per trade x{roi['NEW']/roi['FIT']:.2f}; of the drop in (trades x ROI) per window, {100*a/(a+b):.0f}% is fewer trades (crowding), {100*b/(a+b):.0f}% is less return per trade (demand)")
a = math.log(kept_per_win["NEW"] / kept_per_win["TEST"]); b = math.log(roi["NEW"] / roi["TEST"])
print(f"   TEST -> NEW: trades per window x{kept_per_win['NEW']/kept_per_win['TEST']:.2f}, ROI per trade x{roi['NEW']/roi['TEST']:.2f}; {100*a/(a+b):.0f}% fewer trades, {100*b/(a+b):.0f}% less return per trade")
TIERS = lambda x: 1.0 if x["gauge"] is None else (0.0 if x["gauge"] < 0.15 else (0.5 if x["gauge"] < 0.25 else (1.0 if x["gauge"] < 0.35 else 1.5)))
print("\n=== stop odds (bankroll below half of $300 at any point) over 1000 shuffles of each window's kept trades, then averaged per half; and the median end")
def resample(frac, rule, paths=1000):
    out = collections.defaultdict(list)
    for k in sorted(byk):
        recs = [x for x in byk[k] if x["kept"]]
        if len(recs) < 10: continue
        random.seed(7); stops = 0; ends = []; worst_dd = []
        for _ in range(paths):
            random.shuffle(recs); bank = 300.0; stopped = False; peak = 300.0; dd = 0.0
            for x in recs:
                if bank < 150.0: stopped = True; break
                m = rule(x)
                if m <= 0: continue
                stake = min(max(bank * frac * m, 25.0), min(300.0, bank)); near = min(RH.STAKES, key=lambda s_: abs(s_ - stake)); rr = x["by"][near]
                bank += (min(stake, rr[1]) * (rr[0] / rr[1]) if rr[1] > 1e-6 else rr[0]); peak = max(peak, bank); dd = max(dd, 1 - bank / peak)
            ends.append(bank); stops += stopped; worst_dd.append(dd)
        ends.sort(); out[recs[0]["half"]].append((stops / paths, ends[len(ends) // 2] - 300, sorted(worst_dd)[int(0.95 * paths)]))
    return out
for label, frac, rule in (("flat 15% (the rule)", 0.15, lambda x: 1.0), ("flat 17.5%", 0.175, lambda x: 1.0), ("flat 20%", 0.20, lambda x: 1.0), ("flat 22.5%", 0.225, lambda x: 1.0), ("flat 25%", 0.25, lambda x: 1.0),
                          ("tiers on 15%", 0.15, TIERS), ("tiers on 20%", 0.20, TIERS)):
    o = resample(frac, rule)
    print(f"   {label:22s} " + " | ".join(f"{h} P(stop) {100*st.mean(p for p, e, d in o[h]):4.1f}% max {100*max(p for p, e, d in o[h]):4.1f}%  median end {st.mean(e for p, e, d in o[h]):7,.0f}  95th drawdown {100*st.mean(d for p, e, d in o[h]):4.1f}%" for h in ("FIT", "TEST", "NEW")))
