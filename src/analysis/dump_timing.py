"""did the teams start dumping sooner on clean launches? every window: clean launches, their seat return, the share where the
team sold inside the 5-second hold, the median time of the first sell after the seat, and the buyers behind the seat"""
import sys, statistics as st
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX
data = RH.load(); data.update(RH.load_new())
print(f"{'window':18s} {'clean':>5s} {'return':>7s} {'dumped in hold':>14s} {'1st sell after seat':>19s} {'buyers':>7s} {'<-40%':>6s}")
for k in sorted(data):
    rows = []
    for cv, (L, f) in data[k].items():
        if not (f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)): continue
        x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5)
        if x[1] <= 1e-6 or x[4] == "reverted": continue
        t_in, t_out = x[2], x[3]; roi = (x[0] * PX - 0.10) / (x[1] * PX)
        sells = [r for r in L["rows"] if r[1] == "S" and r[0] >= t_in]
        dumped = sum(r[3] for r in sells if r[0] < t_in + 5.3) / RH.Y0
        first = (sells[0][0] - t_in) if sells else None
        follow = sum(r[2] for r in L["rows"] if r[1] == "B" and t_in <= r[0] < t_out)
        rows.append((roi, dumped, first, follow))
    if not rows: continue
    fs = [r[2] for r in rows if r[2] is not None]
    print(f"{k[0]} {k[1]:6s} {len(rows):5d} {100*st.mean(r[0] for r in rows):+6.1f}% {100*sum(1 for r in rows if r[1] > 0.005) / len(rows):13.0f}% {st.median(fs) if fs else float('nan'):18.1f}s {st.mean(r[3] for r in rows):7.3f} {100*sum(1 for r in rows if r[0] < -0.4)/len(rows):5.0f}%")
