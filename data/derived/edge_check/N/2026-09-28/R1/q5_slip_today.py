"""Q5b: does today's data move the guard? The replay's slip sweep at second place with today's pieces added to the read half
(Sep 24 - Sep 28 21:00), and today alone (Sep 28, 20.3 h). The replay's convention (every burst lands second) is the optimistic side."""
import sys; sys.path.insert(0, "."); from common import *
V = {v: load_view(v) for v in ("k2", "k1reg", "kreg")}
today0 = calendar.timegm(time.strptime("2026-09-28 00:00", "%Y-%m-%d %H:%M")) if False else None
import time as _t; T28 = calendar.timegm(_t.strptime("2026-09-28 00:00", "%Y-%m-%d %H:%M"))
print(f"{'view':6s} {'slip':>5s} {'fit $':>8s} {'fills':>5s} {'read $':>8s} {'fills':>5s} {'Sep 28 $':>9s} {'fills':>5s}")
for v in ("k2", "k1reg", "kreg"):
    for slip in (0.07, 0.10, 0.15, 0.20, 0.25, 0.30):
        out = []
        for sel in (lambda r: period(r["T0"]) == "fit", lambda r: period(r["T0"]) == "read", lambda r: r["T0"] >= T28):
            f = [r for r in V[v].values() if r.get("fired") and sel(r)]
            u = [usd(r, slip) for r in f if usd(r, slip) is not None]
            n = sum(1 for r in f if (r.get("guard_ratio") is None or r["guard_ratio"] >= 1 - slip) and r["ret"]["11"] is not None)
            out += [sum(u), n]
        print(f"{v:6s} {slip:5.2f} {out[0]:+8.2f} {out[1]:5d} {out[2]:+8.2f} {out[3]:5d} {out[4]:+9.2f} {out[5]:5d}")
