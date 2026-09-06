#!/usr/bin/env python3
"""Out-of-sample check of the outsider's seats on new windows (report section 21): exact-curve replay per seat, with and
without the bundle filter, plus the switched one-position-at-a-time net for the seat the runbook runs.
usage: python3 sniper_oos.py 2026-09-04:12-18 [2026-09-05:12-18 ...]   (from the data root)
"""
import sys, os, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sniper_exact as SE, sniper_core as C
PX = C.PX["native"]; STAKE = 300.0
SEATS = [("E0 named wallets (reference)", dict(entry="E0", tol=0.10, exempt=True, slip=0.3)),
         ("E1 first outsider, front", dict(entry="E1", tol=0.10, slip=0.3)),
         ("E1, 0.3 s behind", dict(entry="E1", tol=0.10, slip=0.3, lat=0.3)),
         ("E2 next second, front", dict(entry="E2", tol=0.10, slip=0.3)),
         ("E2, 0.3 s behind", dict(entry="E2", tol=0.10, slip=0.3, lat=0.3))]


def switched_net(trades, one_at_a_time=True, n=30, thr=0.05, delay=20.0):
    trades = sorted(trades, key=lambda r: r[2]); scored = []; net = 0.0; busy = 0.0; live = 0
    for pnl, cost, t_in, t_out in trades:
        avail = [x[1] for x in scored if x[0] <= t_in]
        on = len(avail) >= n and st.mean(avail[-n:]) >= thr
        scored.append((t_out + delay, pnl / cost))
        if on and (not one_at_a_time or t_in >= busy):
            net += pnl; busy = t_out; live += 1
    return net, live


for arg in sys.argv[1:]:
    day, win = arg.split(":"); SE.WINDOW = win
    launches, prior = SE.load_exact(day)
    elig = [cv for cv, L in launches.items() if prior[L["creator"]][0] == L["ts"]]
    nb = {cv: SE.bundle_count(launches[cv]) for cv in elig}
    print(f"\n=== {day} {win} UTC: {len(elig)} eligible launches, {sum(1 for v in nb.values() if v >= 3)} with a bundle of >= 3 ({100*sum(1 for v in nb.values() if v >= 3)/max(1,len(elig)):.0f}%) ===")
    print(f"{'seat (3% of supply, $300 stake)':36s} {'all launches: ROI [CI] net$ n':>36s} {'bundle>=3: ROI [CI] net$ n':>34s} {'bundle>=3 switched, 1 at a time':>32s}")
    for name, kw in SEATS:
        cells = []
        for sel in (lambda cv: True, lambda cv: nb[cv] >= 3):
            res = []
            for cv in elig:
                if not sel(cv):
                    continue
                pnl, cost, t_in, t_out, kind, _ = SE.replay(launches[cv], STAKE / PX, frac=0.03, **kw)
                res.append((pnl * PX - C.GAS, cost * PX, launches[cv]["ts"] + t_in, launches[cv]["ts"] + t_out))
            if len(res) >= 10:
                v = [r[0] / r[1] for r in res]; lo, hi = C.ci(v)
                cells.append(f"{100*st.mean(v):+6.1f} [{100*lo:+.0f},{100*hi:+.0f}] {sum(r[0] for r in res):7.0f} {len(res):4d}")
            else:
                cells.append(f"n={len(res)}")
            last = res
        sw = switched_net(last) if len(last) >= 10 else (0.0, 0)
        print(f"{name:36s} {cells[0]:>36s} {cells[1]:>34s} {sw[0]:>22,.0f} ({sw[1]:3d} tr)")
