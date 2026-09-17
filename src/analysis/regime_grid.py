"""the new regime (Sep 16-17: 4.5-6 bots a launch, half the launches, thin demand) searched for any seat that still pays:
seat (front of second one, 0.3 s into second one, 0.3 s into second two, second three), hold (2-7 s), take-profit, on
every bundled launch / clean-in-second-one only / crowded only. Same grid on Sep 12-15 and Sep 11 for comparison."""
import os, statistics as st, random, collections
exec(open("/home/user/fomo-memebot/src/analysis/indep_replay.py").read().split("recs = []")[0])
def ci(xs, n=800):
    random.seed(2); b = sorted(st.mean(random.choice(xs) for _ in xs) for _ in range(n)); return b[int(0.025*n)], b[int(0.975*n)]
periods = {"NEW Sep 16-17": lambda d: d >= "2026-09-16", "Sep 12-15": lambda d: "2026-09-12" <= d <= "2026-09-15", "Sep 11": lambda d: d == "2026-09-11"}
def sim_seat(L, seat, hold, tp):
    if seat == "E1 front":  return sim(L, "E1", stake_usd=25, wait=0.0, hold=hold, tp=tp)["roi"]
    if seat == "E1 +0.3s":  return sim(L, "E1", stake_usd=25, wait=0.3, hold=hold, tp=tp)["roi"]
    if seat == "E2 +0.3s":  return sim(L, "E2", stake_usd=25, wait=0.3, hold=hold, tp=tp)["roi"]
    if seat == "E3 +0.3s":                                            # second three: no surcharge, after the bot wave
        rows = L["rows"]; tier = L["tier"]; pos = L["ts"] % 1.0; t_entry = 3.0 - pos + 0.3
        X, Y = X0, Y0; i = 0
        for i, r in enumerate(rows):
            if i > 0 and r[0] >= t_entry: break
            if r[1] == "B": X += r[4]; Y -= r[3]
            else: X -= r[4]; Y += r[3]
        else: i = len(rows)
        fee = tier; stake_eth = 25 / PX; tk = 0.03 * Y0; net = X * tk / (Y - tk); gross = net / (1 - fee)
        if gross > stake_eth: gross = stake_eth; net = gross * (1 - fee); tk = Y * net / (X + net)
        X += net; Y -= tk; p_in = X / Y; t_out = t_entry + hold + 0.3
        for r in rows[i:]:
            if r[0] >= t_out: break
            if r[1] == "B":
                got = Y - X * Y / (X + r[4])
                if got < r[3] * 0.9: continue
                X += r[4]; Y -= got
            else:
                s = min(r[3], Y0 - Y - tk); g = X - X * Y / (Y + s); X -= g; Y += s
            if tp and X / Y >= p_in * (1 + tp) and t_out > r[0] + 0.3: t_out = r[0] + 0.3
        out = (X - X * Y / (Y + tk)) * (1 - tier)
        return ((out - gross) * PX - 0.11) / (gross * PX)
for pname, pf in periods.items():
    Ls = [(L, feats(L)) for (d, w), dd in data.items() if pf(d) for cv, (L, f) in dd.items()]
    print(f"\n==================== {pname}: {len(Ls)} bundled launches ====================")
    print(f"{'seat':10s} {'hold':>4s} {'tp':>4s} | {'ALL n':>5s} {'mean':>7s} {'95%':>16s} | {'CLEAN-s1 n':>10s} {'mean':>7s} | {'CROWDED n':>9s} {'mean':>7s} | {'>=3 bots n':>10s} {'mean':>7s}")
    for seat in ("E1 front", "E1 +0.3s", "E2 +0.3s", "E3 +0.3s"):
        for hold, tp in ((2, 0.5), (3, 0.5), (5, 0.5), (5, None), (7, 0.5)):
            res = [(sim_seat(L, seat, hold, tp), g) for L, g in Ls]
            a = [r for r, g in res]; cl = [r for r, g in res if g["out1"] == 0]; cr = [r for r, g in res if g["out1"] > 0]; b3 = [r for r, g in res if g["out1"] >= 3]
            lo, hi = ci(a)
            print(f"{seat:10s} {hold:4d} {str(tp):>4s} | {len(a):5d} {100*st.mean(a):+6.1f}% [{100*lo:+5.1f}%,{100*hi:+5.1f}%] | {len(cl):10d} {100*st.mean(cl) if cl else 0:+6.1f}% | {len(cr):9d} {100*st.mean(cr) if cr else 0:+6.1f}% | {len(b3):10d} {100*st.mean(b3) if b3 else 0:+6.1f}%")
# the creation second: what an outsider pays there (the tax bands seen on buys in second zero that are not at the tier)
print("\n=== surcharge seen on non-team buys inside the creation second (second zero), Sep 16-17")
s0 = collections.Counter()
for (d, w), dd in data.items():
    if d < "2026-09-16": continue
    for cv, (L, f) in dd.items():
        tier = L["tier"]; pos = L["ts"] % 1.0
        for r in L["rows"][1:]:
            if r[1] == "B" and r[0] < 1.0 - pos and r[5] - tier > 0.001: s0[round(100 * (r[5] - tier), 1)] += 1
print(s0.most_common(8))
