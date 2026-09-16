"""A change is only worth making if it helps in BOTH periods: the days the rule was built on (to Sep 8), the days in
between (Sep 9-11), and the four days nothing was fitted to (Sep 12-16). Anything that only helps in one is a fit."""
import sys, statistics as st, collections, datetime, random
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX
data = RH.load(); data.update(RH.load_new())
rows = []
for k in sorted(data):
    for cv, (L, f) in data[k].items():
        d = datetime.datetime.fromtimestamp(L["ts"], datetime.timezone.utc)
        per = "old (to Sep 8)" if d.strftime("%Y-%m-%d") < "2026-09-09" else ("middle (Sep 9-11)" if d.strftime("%Y-%m-%d") < "2026-09-12" else "NEW (Sep 12-16)")
        clean = f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)
        if not clean: continue
        x5 = RH.replay(L, 25 / PX, hold=5.0, tp=0.5); x7 = RH.replay(L, 25 / PX, hold=7.0, tp=0.5)
        if x5[1] <= 1e-6 or x5[4] == "reverted": continue
        rows.append(dict(per=per, t=L["ts"] + x5[2], t_exit5=L["ts"] + x5[3], t_exit7=L["ts"] + (x7[3] if x7[1] > 1e-6 else x5[3]),
                         hour=d.hour, roi5=(x5[0] * PX - 0.10) / (x5[1] * PX),
                         roi7=((x7[0] * PX - 0.10) / (x7[1] * PX)) if (x7[1] > 1e-6 and x7[4] != "reverted") else None,
                         eth=f["bundle_eth"], n=f["bundle_n"], tk0=f["tk0"]))
rows.sort(key=lambda r: r["t"])
PERS = ["old (to Sep 8)", "middle (Sep 9-11)", "NEW (Sep 12-16)"]
def ci(xs, n=2500):
    if len(xs) < 15: return float("nan"), float("nan")
    random.seed(7); b = sorted(st.mean(random.choice(xs) for _ in xs) for _ in range(n)); return b[int(0.025*n)], b[int(0.975*n)]
cands = [("the rule as it runs now", lambda r: True, "roi5"),
         ("+ hold 7 s instead of 5", lambda r: True, "roi7"),
         ("+ at least 5 team wallets", lambda r: r["n"] >= 5, "roi5"),
         ("+ team ETH capped at 1.2", lambda r: r["eth"] <= 1.2, "roi5"),
         ("+ creator holds 3% or more", lambda r: r["tk0"] >= 0.03, "roi5"),
         ("+ creator holds 4% or more", lambda r: r["tk0"] >= 0.04, "roi5"),
         ("5 wallets + ETH<=1.2", lambda r: r["n"] >= 5 and r["eth"] <= 1.2, "roi5"),
         ("5 wallets + ETH<=1.2 + creator>=3%", lambda r: r["n"] >= 5 and r["eth"] <= 1.2 and r["tk0"] >= 0.03, "roi5"),
         ("all three + hold 7 s", lambda r: r["n"] >= 5 and r["eth"] <= 1.2 and r["tk0"] >= 0.03, "roi7")]
print(f"{'change':38s} " + " ".join(f"{p:>26s}" for p in PERS))
print(f"{'':38s} " + " ".join(f"{'n':>5s} {'mean':>7s} {'win':>5s}{'':6s}" for _ in PERS))
for name, fn, key in cands:
    out = []
    for p in PERS:
        v = [r[key] for r in rows if r["per"] == p and fn(r) and r[key] is not None]
        out.append(f"{len(v):5d} {100*st.mean(v) if v else 0:+6.1f}% {100*sum(1 for x in v if x>0)/len(v) if v else 0:4.0f}%{'':6s}")
    print(f"{name:38s} " + " ".join(out))
print("\nthe four new days as money, from $62, flat $25, one position at a time, engine gates on")
def path(fn, key, start=62.0, stop=0.5):
    bank = start; busy = -1e9; taken = []; peak = start; dd = 0.0; day = None; day_start = start; stopped_days = 0
    for i, r in enumerate(rows):
        if r["per"] != "NEW (Sep 12-16)" or r[key] is None: continue
        d = datetime.datetime.fromtimestamp(r["t"], datetime.timezone.utc).strftime("%m-%d")
        if d != day:
            day = d; day_start = bank; blocked_today = False
        if bank < day_start * stop:
            stopped_days += 1; continue
        if not (r["hour"] >= 12 or r["hour"] < 5): continue
        if r["t"] < busy or not fn(r): continue
        if bank < 25: break
        bank += 25 * r[key]; busy = r["t_exit7" if key == "roi7" else "t_exit5"]; taken.append(r[key])
        peak = max(peak, bank); dd = max(dd, 1 - bank / peak)
    return bank, taken, dd
print(f"{'change':38s} {'trades':>7s} {'mean':>7s} {'end $':>8s} {'profit':>8s} {'drawdown':>9s} {'worst trade':>12s}")
for name, fn, key in cands:
    b, tk, dd = path(fn, key)
    print(f"{name:38s} {len(tk):7d} {100*st.mean(tk) if tk else 0:+6.1f}% {b:8,.0f} {b-62:+8,.0f} {100*dd:8.0f}% {100*min(tk) if tk else 0:11.0f}%")
# ruin from $62 and from $200, reshuffled
print("\nrunning out of money before the daily stop saves you, 3000 reshuffles of the four new days:")
for name, fn, key in cands[:1] + cands[4:5] + cands[7:8]:
    v = [r[key] for r in rows if r["per"] == "NEW (Sep 12-16)" and fn(r) and r[key] is not None]
    for start in (62, 120, 250):
        random.seed(11); ruin = 0
        for _ in range(3000):
            bank = start; seq = v[:]; random.shuffle(seq)
            for roi in seq:
                if bank < 25: ruin += 1; break
                bank += 25 * roi
        print(f"   {name:38s} from ${start:3d}: {100*ruin/3000:5.1f}%")
