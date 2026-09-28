"""Q0: today since 12:27 on the replay's three views at the live guard (0.20), against the live P&L (+$0.03 -> +$11.76)."""
import sys; sys.path.insert(0, "."); from common import *
for v in ("k2", "k1reg", "kreg"):
    R = [r for r in load_view(v).values() if r["T0"] >= SWITCH]; f = [r for r in R if r.get("fired")]; u = [usd(r) for r in f]
    fills = [r for r in f if r.get("guard_ratio") is None or r["guard_ratio"] >= 0.80]
    print(f"{v:6s}: {len(R)} launches, {len(f)} fires, {len(fills)} fills at second place, ${sum(u):+.2f} ({sum(u) / (8.55 / 24):+.2f}/day over 8.55 h)")
print("live: 7 bursts, 5 fills, +$11.73 (fills +$11.84 less gas); landing index 1, 4, 2, 1, 1")
