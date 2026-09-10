"""can the demand be read in real time? The engine scores every bundled launch 25 s after it: the ETH later buyers brought inside
the hold is known then. Test: the rolling mean of that over the previous 20 scored launches (available before the next launch's
send) against the next launch's return; then walk-forward rules keyed on it (on/off, tiered sizing) over all 21 windows;
and the chain-wide bonding-curve volume per window as the outside driver."""
import sys, json, statistics as st, collections
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH, sniper_exact as SE
PX = RH.PX; Y0 = SE.Y0; X0 = SE.X0
data = RH.load(); new = RH.load_new(); data.update(new); NEWK = set(new)
def follow_eth(L, t_in, t_out):
    return sum(r[2] for r in L["rows"] if r[1] == "B" and t_in <= r[0] < t_out)
rows_all = []
for k in sorted(data):
    half = "NEW" if k in NEWK else ("FIT" if k in RH.FIT else "TEST"); recs = []
    for cv, (L, f) in data[k].items():
        r = RH.replay(L, 300 / PX, hold=5.0, tp=0.5)                      # every bundled launch is scored (the switch sees all of them)
        if r[4] == "reverted":
            continue
        kept = f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)
        by = {}
        for stk in RH.STAKES:
            x = RH.replay(L, stk / PX, hold=5.0, tp=0.5); by[stk] = (x[0] * PX - 1.0, x[1] * PX, L["ts"] + x[2], L["ts"] + x[3])
        recs.append(dict(t_in=L["ts"] + r[2], t_score=L["ts"] + r[3] + 20.0, roi=r[0] / r[1], feth=follow_eth(L, r[2], r[3]), kept=kept, by=by, k=k, half=half, hour=f["hour"]))
    recs.sort(key=lambda x: x["t_in"]); rows_all += recs
    for x in recs:
        x["gauge"] = None; x["gauge_roi"] = None
    if len(recs) < 10: continue
    # the gauge for each launch: mean follow-on ETH of the previous 20 launches already scored at its send time
    for i, x in enumerate(recs):
        prev = [y["feth"] for y in recs[:i] if y["t_score"] <= x["t_in"]][-20:]
        x["gauge"] = st.mean(prev) if len(prev) >= 10 else None
        prevr = [y["roi"] for y in recs[:i] if y["t_score"] <= x["t_in"]][-20:]
        x["gauge_roi"] = st.mean(prevr) if len(prevr) >= 10 else None
print("=== the gauge (mean follow-on ETH of the previous 20 scored launches) against the next kept launch's return, all 21 windows pooled")
bins = [(0, 0.15), (0.15, 0.25), (0.25, 0.35), (0.35, 0.5), (0.5, 9)]
for half in ("FIT", "TEST", "NEW", "ALL"):
    xs = [x for x in rows_all if x["kept"] and x["gauge"] is not None and (half == "ALL" or x["half"] == half)]
    line = f"   {half:4s}: "
    for a, b in bins:
        v = [x["roi"] for x in xs if a <= x["gauge"] < b]
        line += f"[{a:.2f}-{b:.2f}) n {len(v):4d} {100*st.mean(v):+6.1f}%   " if v else f"[{a:.2f}-{b:.2f}) n    0     -     "
    print(line)
def corr(a, b):
    ma, mb = st.mean(a), st.mean(b); sa, sb = st.pstdev(a), st.pstdev(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (len(a) * sa * sb) if sa and sb else 0.0
xs = [x for x in rows_all if x["kept"] and x["gauge"] is not None]
print(f"   launch-level correlation, gauge vs next return: r = {corr([x['gauge'] for x in xs], [x['roi'] for x in xs]):+.3f} (n {len(xs)}); rolling ROI of the previous 20 vs next return: r = {corr([x['gauge_roi'] for x in xs if x['gauge_roi'] is not None], [x['roi'] for x in xs if x['gauge_roi'] is not None]):+.3f}")
print("\n=== walk-forward rules on the gauge (own path from $300, 15% sizing, $25 floor, one position at a time, stop -50%), gains summed per half")
def path(recs, rule, start=300.0):
    bank = start; busy = -1e9; taken = []; stopped = False
    for x in recs:
        if not x["kept"] or x["t_in"] < busy: continue
        if bank < 0.5 * start: stopped = True
        if stopped: continue
        mult = rule(x)
        if mult <= 0: continue
        stake = min(max(bank * 0.15 * mult, 25.0), min(300.0, bank)); near = min(RH.STAKES, key=lambda s_: abs(s_ - stake)); rr = x["by"][near]
        dep = min(stake, rr[1]) if rr[1] > 1e-6 else 0.0; bank += dep * (rr[0] / rr[1]) if rr[1] > 1e-6 else rr[0]; busy = rr[3]; taken.append(rr[0] / rr[1] if rr[1] > 1e-6 else 0.0)
    return bank - start, taken, stopped
rules = {"always on (the rule as is)": lambda x: 1.0,
         "off below 0.15 ETH": lambda x: 0.0 if (x["gauge"] is not None and x["gauge"] < 0.15) else 1.0,
         "off below 0.20 ETH": lambda x: 0.0 if (x["gauge"] is not None and x["gauge"] < 0.20) else 1.0,
         "off below 0.25 ETH": lambda x: 0.0 if (x["gauge"] is not None and x["gauge"] < 0.25) else 1.0,
         "tiers: <0.15 off, 0.15-0.25 half, 0.25-0.35 full, >=0.35 x1.5": lambda x: 1.0 if x["gauge"] is None else (0.0 if x["gauge"] < 0.15 else (0.5 if x["gauge"] < 0.25 else (1.0 if x["gauge"] < 0.35 else 1.5))),
         "tiers: <0.20 half, 0.20-0.35 full, >=0.35 x1.5": lambda x: 1.0 if x["gauge"] is None else (0.5 if x["gauge"] < 0.20 else (1.0 if x["gauge"] < 0.35 else 1.5)),
         "rolling ROI switch 20/+3% (for comparison)": lambda x: 0.0 if (x["gauge_roi"] is not None and x["gauge_roi"] < 0.03) else 1.0}
byk = collections.defaultdict(list)
for x in rows_all: byk[x["k"]].append(x)
for name, rule in rules.items():
    tot = collections.Counter(); ntr = collections.Counter(); stops = collections.Counter(); worst = {}
    per = []
    for k in sorted(byk):
        recs = byk[k]
        if sum(1 for x in recs if x["kept"]) < 10: continue
        g, taken, stopped = path(recs, rule); half = recs[0]["half"]; tot[half] += g; ntr[half] += len(taken); stops[half] += stopped; per.append((k, g, len(taken)))
        worst[half] = min(worst.get(half, 9e9), g)
    print(f"   {name:62s} FIT {tot['FIT']:7,.0f} ({ntr['FIT']:4d} trades, worst {worst.get('FIT',0):6,.0f}) | TEST {tot['TEST']:7,.0f} ({ntr['TEST']:4d}, worst {worst.get('TEST',0):6,.0f}) | NEW {tot['NEW']:7,.0f} ({ntr['NEW']:4d}, worst {worst.get('NEW',0):6,.0f}) | stops {sum(stops.values())}")
    if name.startswith("tiers: <0.15"):
        print("      per window: " + ", ".join(f"{k[0][5:]}/{k[1]} {g:+,.0f}" for k, g, n in per))
print("\n=== chain-wide bonding-curve buy volume per window (every curve, every buy) as the outside driver; kept launches' ROI next to it")
import glob
vol = {}
for k in sorted(byk):
    day, win = k; tot_eth = 0.0; nbuys = 0
    try:
        for line in open(f"rh/v2curve_{day}_{win}.jsonl"):
            b, li, tx, addr, t0, d = json.loads(line)
            if t0 == SE.BUY[:10]:
                tot_eth += int(d[2:66], 16) / 1e18; nbuys += 1
    except FileNotFoundError:
        continue
    kept = [x for x in byk[k] if x["kept"]]
    vol[k] = (tot_eth, nbuys); print(f"   {day[5:]} {win:5s} buys {nbuys:7d}  ETH {tot_eth:9,.0f}  | kept {len(kept):4d} ROI {100*st.mean(x['roi'] for x in kept):+5.1f}%  follow-on ETH/hold {st.mean(x['feth'] for x in kept):.2f}" if kept else f"   {day[5:]} {win}: no kept launches")
ks = [k for k in vol if sum(1 for x in byk[k] if x["kept"]) >= 10]
print("   correlation of window buy volume with kept ROI: r = %+.2f; with follow-on ETH per hold: r = %+.2f" % (corr([vol[k][0] for k in ks], [st.mean(x['roi'] for x in byk[k] if x['kept']) for k in ks]), corr([vol[k][0] for k in ks], [st.mean(x['feth'] for x in byk[k] if x['kept']) for k in ks])))
