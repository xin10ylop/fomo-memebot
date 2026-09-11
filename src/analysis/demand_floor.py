"""a demand floor: no new trade while the mean follow-on ETH of the last 60 scored launches (the engine's follow_eth_last_60,
over every bundled launch it scores, kept or not) is below a threshold. What the tables say it would have cost."""
import sys, statistics as st, collections
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX
data = RH.load(); data.update(RH.load_new())
def follow_eth(L, t_in, t_out):
    return sum(r[2] for r in L["rows"] if r[1] == "B" and t_in <= r[0] < t_out)
by_win = {}
for k in sorted(data):
    recs = []
    for cv, (L, f) in data[k].items():
        kept = f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)
        x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5)
        if x[1] <= 1e-6 or x[4] == "reverted": continue
        recs.append(dict(t=L["ts"] + x[2], t_score=L["ts"] + x[3] + 20, roi=(x[0] * PX - 0.10) / (x[1] * PX), feth=follow_eth(L, x[2], x[3]), kept=kept))
    recs.sort(key=lambda r: r["t"]); by_win[k] = recs
bins = [(0, 0.05), (0.05, 0.10), (0.10, 0.15), (0.15, 0.20), (0.20, 0.30), (0.30, 9)]
tab = collections.defaultdict(list); tab_n = collections.defaultdict(int)
for k, recs in by_win.items():
    for i, r in enumerate(recs):
        prev = [y["feth"] for y in recs[:i] if y["t_score"] <= r["t"]][-60:]
        r["gauge"] = st.mean(prev) if len(prev) >= 20 else None
        if r["kept"] and r["gauge"] is not None:
            for lo, hi in bins:
                if lo <= r["gauge"] < hi: tab[(lo, hi)].append(r["roi"])
print("kept trades by the 60-launch demand reading at decision time (needs 20 scored launches), all windows:")
for b in bins:
    v = tab[b]; print(f"   [{b[0]:.2f}-{b[1]:.2f})  n {len(v):5d}  mean {100*st.mean(v) if v else 0:+6.1f}%  sum at $25 {25*sum(v) if v else 0:+8.0f} $  share <-40% {100*sum(1 for x in v if x < -0.4)/len(v) if v else 0:.0f}%")
print("\nper window: kept trades and $25 profit, and what a floor at 0.10 / 0.15 would have removed")
tot = collections.Counter()
for k, recs in by_win.items():
    kept = [r for r in recs if r["kept"]]
    for thr in (0.10, 0.15):
        rem = [r for r in kept if r["gauge"] is not None and r["gauge"] < thr]
        tot[(thr, "n")] += len(rem); tot[(thr, "usd")] += 25 * sum(r["roi"] for r in rem)
    rem10 = [r for r in kept if r["gauge"] is not None and r["gauge"] < 0.10]; rem15 = [r for r in kept if r["gauge"] is not None and r["gauge"] < 0.15]
    print(f"   {k[0]} {k[1]:6s} kept {len(kept):4d} ${25*sum(r['roi'] for r in kept):+7.0f} | floor 0.10 removes {len(rem10):3d} (${25*sum(r['roi'] for r in rem10):+6.0f}) | floor 0.15 removes {len(rem15):3d} (${25*sum(r['roi'] for r in rem15):+6.0f}) | lowest reading {min((r['gauge'] for r in recs if r['gauge'] is not None), default=float('nan')):.3f}")
print(f"\nfloor 0.10: removes {tot[(0.10,'n')]} trades worth ${tot[(0.10,'usd')]:+.0f} over all windows; floor 0.15: removes {tot[(0.15,'n')]} trades worth ${tot[(0.15,'usd')]:+.0f}")
