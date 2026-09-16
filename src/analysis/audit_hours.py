"""Do the filters fix the weak afternoon, or is an hours restriction still needed? Both periods, filtered rule."""
import sys, statistics as st, collections, datetime, random
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX
data = RH.load(); data.update(RH.load_new())
rows = []
for k in sorted(data):
    for cv, (L, f) in data[k].items():
        if not (f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)): continue
        if f["bundle_n"] < 3 or f["bundle_eth"] < 0.3: continue
        x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5)
        if x[1] <= 1e-6 or x[4] == "reverted": continue
        d = datetime.datetime.fromtimestamp(L["ts"], datetime.timezone.utc)
        rows.append(dict(new=d.strftime("%Y-%m-%d") >= "2026-09-12", hour=d.hour, roi=(x[0] * PX - 0.10) / (x[1] * PX),
                         ok=f["bundle_n"] >= 5 and f["bundle_eth"] <= 1.2 and f["tk0"] >= 0.03))
def ci(xs, n=2500):
    if len(xs) < 12: return float("nan"), float("nan")
    random.seed(13); b = sorted(st.mean(random.choice(xs) for _ in xs) for _ in range(n)); return b[int(0.025*n)], b[int(0.975*n)]
for label, sub in (("the rule as it runs now", lambda r: True), ("the filtered rule (5 wallets, ETH<=1.2, creator>=3%)", lambda r: r["ok"])):
    print(f"\n=== {label}")
    print(f"{'block':8s} {'old: n':>7s} {'mean':>7s} | {'NEW: n':>7s} {'mean':>7s} {'win':>5s} {'95% interval':>20s}")
    for name, rng in (("12-18", range(12, 18)), ("18-24", range(18, 24)), ("00-06", range(0, 6))):
        o = [r["roi"] for r in rows if not r["new"] and r["hour"] in rng and sub(r)]
        n = [r["roi"] for r in rows if r["new"] and r["hour"] in rng and sub(r)]
        lo, hi = ci(n)
        print(f"{name:8s} {len(o):7d} {100*st.mean(o) if o else 0:+6.1f}% | {len(n):7d} {100*st.mean(n) if n else 0:+6.1f}% "
              f"{100*sum(1 for x in n if x>0)/len(n) if n else 0:4.0f}% {('[%+.1f%%, %+.1f%%]' % (100*lo, 100*hi)) if lo == lo else 'too few':>20s}")
    print(f"{'hour':8s} " + "  ".join(f"{h:02d}" for h in list(range(12, 24)) + list(range(0, 6))))
    line = []
    for h in list(range(12, 24)) + list(range(0, 6)):
        n = [r["roi"] for r in rows if r["new"] and r["hour"] == h and sub(r)]
        line.append(f"{100*st.mean(n):+3.0f}" if len(n) >= 5 else "  .")
    print(f"{'NEW mean':8s} " + " ".join(f"{x:>3s}" for x in line))
