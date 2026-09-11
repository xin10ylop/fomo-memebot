"""today's afternoon against yesterday's and every other measured afternoon: launches, crowding, demand, and what the seat made"""
import sys, statistics as st, collections
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX
data = RH.load(); data.update(RH.load_new())
def follow_eth(L, t_in, t_out): return sum(r[2] for r in L["rows"] if r[1] == "B" and t_in <= r[0] < t_out)
print(f"{'window':18s} {'bundled':>7s} {'bot in 2nd one':>14s} {'seat empty':>10s} {'kept':>5s} {'demand/launch':>13s} {'kept ROI':>9s} {'$25 sum':>8s} {'<-40%':>6s}")
rows = []
for k in sorted(data):
    if k[1] != "12-18" and k != ("2026-09-11", "12-15"): continue
    L_all = data[k]
    if not L_all: continue
    feth = []; kept = []; out1 = 0; empty = 0
    for cv, (L, f) in L_all.items():
        x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5)
        if x[1] <= 1e-6: continue
        feth.append(follow_eth(L, x[2], x[3]))
        if f["out1_n"] > 0: out1 += 1
        elif f["rival_t"] is None: empty += 1
        if f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f) and x[4] != "reverted": kept.append((x[0] * PX - 0.10) / (x[1] * PX))
    n = len(feth)
    print(f"{k[0]} {k[1]:6s} {n:7d} {100*out1/n:13.0f}% {100*empty/n:9.0f}% {len(kept):5d} {st.mean(feth):13.3f} {100*st.mean(kept) if kept else 0:+8.1f}% {25*sum(kept):+8.0f} {100*sum(1 for r in kept if r < -0.4)/len(kept) if kept else 0:5.0f}%")
# today by hour
k = ("2026-09-11", "12-15")
if k in data:
    byh = collections.defaultdict(lambda: [0, 0, [], []])
    for cv, (L, f) in data[k].items():
        x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5)
        if x[1] <= 1e-6: continue
        h = int(f["hour"]); b = byh[h]; b[0] += 1; b[1] += f["out1_n"] > 0; b[2].append(follow_eth(L, x[2], x[3]))
        if f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f) and x[4] != "reverted": b[3].append((x[0] * PX - 0.10) / (x[1] * PX))
    print("\ntoday by hour (UTC): bundled, bot in second one, demand per launch, kept trades and their mean")
    for h in sorted(byh):
        b = byh[h]; print(f"   {h:02d}:00  bundled {b[0]:3d}  crowded {100*b[1]/b[0]:3.0f}%  demand {st.mean(b[2]):.3f}  kept {len(b[3]):2d}  mean {100*st.mean(b[3]) if b[3] else 0:+6.1f}%")
