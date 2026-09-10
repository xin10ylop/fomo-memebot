"""did the flow move to a seat we could still take? per window, on every bundled launch (bundle >= 3 wallets, >= 0.3 ETH,
creator >= 1%): E2 0.3 s behind / hold 5 by class (no outsider in second one and no seat rival = the rule; second-one
outsider present; seat rival present), and the E1 seat (second one, +6.18%) at the front and 0.3 s behind"""
import sys, os, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sniper_exact as SE, risk_harness as RH
PX = RH.PX
wins = [("2026-08-31","12-18"),("2026-09-02","12-18"),("2026-09-03","12-18"),("2026-09-03","18-24"),("2026-09-05","12-18"),("2026-09-06","12-18")] + RH.new_windows()
def m(v):
    return f"{len(v):4d} {100*st.mean(v):+6.1f}%" if v else "   -       "
print(f"{'window':16s} | {'E2 rule (kept)':>16s} | {'E2, out1>0':>16s} | {'E2, seat rival':>16s} | {'E1 front, out1==0':>18s} | {'E1 front, all':>16s} | {'E1 0.3s behind, all':>19s}")
for day, win in wins:
    SE.WINDOW = win
    try:
        launches, prior = SE.load_exact(day)
    except FileNotFoundError:
        continue
    c = {k: [] for k in ("rule", "out1", "rival", "e1f0", "e1f", "e1b")}
    for cv, L in launches.items():
        if prior[L["creator"]][0] != L["ts"]:
            continue
        f = RH.features(L)
        if not (f["bundle_n"] >= 3 and f["bundle_eth"] >= 0.3 and f["tk0"] >= 0.01):
            continue
        def roi(**kw):
            r = RH.replay(L, 300 / PX, hold=5.0, **kw); return None if r[4] == "reverted" else r[0] / r[1]
        r2 = roi()
        if r2 is not None:
            if f["out1_n"] > 0:
                c["out1"].append(r2)
            elif RH.G_WAIT(0.3)(f):
                c["rival"].append(r2)
            else:
                c["rule"].append(r2)
        r = roi(entry="E1", lat=0.0, slip=0.3, min_out_slip=None)
        if r is not None:
            c["e1f"].append(r)
            if f["out1_n"] == 0:
                c["e1f0"].append(r)
        r = roi(entry="E1", lat=0.3)
        if r is not None:
            c["e1b"].append(r)
    print(f"{day[5:]} {win:5s}     | {m(c['rule']):>16s} | {m(c['out1']):>16s} | {m(c['rival']):>16s} | {m(c['e1f0']):>18s} | {m(c['e1f']):>16s} | {m(c['e1b']):>19s}", flush=True)
