"""where the launches go, per window: eligible creations, bundled ones, and what each gate removes (second-one outsider, seat rival)"""
import sys, os, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sniper_exact as SE, risk_harness as RH
wins = [("2026-08-31","12-18"),("2026-09-02","12-18"),("2026-09-03","12-18"),("2026-09-05","12-18"),("2026-09-06","12-18")] + RH.new_windows()
print(f"{'window':16s} {'eligible':>8s} {'bundled':>7s} {'creator<1%':>10s} {'out1>0':>7s} {'rule':>5s} {'rival<0.3s':>10s} {'kept':>5s} {'bundle ETH':>10s} {'named':>6s}")
for day, win in wins:
    SE.WINDOW = win
    try:
        launches, prior = SE.load_exact(day)
    except FileNotFoundError:
        continue
    elig = [L for cv, L in launches.items() if prior[L["creator"]][0] == L["ts"]]
    fs = [RH.features(L) for L in elig]
    bundled = [f for f in fs if f["bundle_n"] >= 3 and f["bundle_eth"] >= 0.3]
    small = [f for f in bundled if f["tk0"] < 0.01]; out1 = [f for f in bundled if f["tk0"] >= 0.01 and f["out1_n"] > 0]
    rule = [f for f in bundled if f["tk0"] >= 0.01 and f["out1_n"] == 0]; rival = [f for f in rule if RH.G_WAIT(0.3)(f)]
    print(f"{day[5:]} {win:5s} {len(elig):8d} {len(bundled):7d} {len(small):10d} {len(out1):7d} {len(rule):5d} {len(rival):10d} {len(rule)-len(rival):5d} {st.median(f['bundle_eth'] for f in bundled) if bundled else 0:10.3f} {st.median(f['bundle_n'] for f in bundled) if bundled else 0:6.0f}", flush=True)
