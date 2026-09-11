"""each of engine 4.94's mechanisms added one at a time on top of the rule, every window, $25 stakes, gas $0.10.
The demand readout of a long-running engine is already armed when a window opens: the first ten scored launches of the
window stand in for the previous hour's readout (a restart's arming cost is shown separately)."""
import sys, statistics as st, collections
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX; FLOOR = 0.10; ARM = 10; SWITCH_N = 15; SWITCH = -0.10
data = RH.load(); data.update(RH.load_new())
def follow_eth(L, t_in, t_out): return sum(r[2] for r in L["rows"] if r[1] == "B" and t_in <= r[0] < t_out)
wins = {}
for k in sorted(data):
    recs = []
    for cv, (L, f) in data[k].items():
        x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5)
        if x[1] <= 1e-6 or x[4] == "reverted": continue
        scored = f["out1_n"] == 0
        recs.append(dict(t=L["ts"] + x[2], t_score=L["ts"] + x[3] + 20, t_exit=L["ts"] + x[3], roi=(x[0] * PX - 0.10) / (x[1] * PX), feth=follow_eth(L, x[2], x[3]),
                         scored=scored, clean=scored and not RH.G_WAIT(0.3)(f), hour=int(f["hour"])))
    recs.sort(key=lambda r: r["t"]); wins[k] = recs
def run(recs, one_at_a_time=False, switch=False, hours=False, floor=False, restart=False):
    out = []; busy = -1e9; seed = [y["feth"] for y in recs if y["scored"]][:ARM]
    for i, r in enumerate(recs):
        if not r["clean"]: continue
        past = [y for y in recs[:i] if y["scored"] and y["t_score"] <= r["t"]]
        if hours and not (r["hour"] >= 12 or r["hour"] < 5): continue
        if floor:
            tm = [y["feth"] for y in past][-60:]
            if len(tm) < ARM:
                if restart: continue
                tm = seed
            if st.mean(tm) < FLOOR: continue
        if switch:
            sc = [y["roi"] for y in past][-SWITCH_N:]
            if len(sc) >= SWITCH_N and st.mean(sc) < SWITCH: continue
        if one_at_a_time and r["t"] < busy: continue
        out.append(r["roi"]); busy = r["t_exit"]
    return out
steps = [("the rule alone (the afternoons table)", {}), ("+ one position at a time (one wallet)", dict(one_at_a_time=True)),
         ("+ safety switch, 15 scores under -10% (existed before today)", dict(one_at_a_time=True, switch=True)),
         ("+ hours 12-05 UTC (4.7)", dict(one_at_a_time=True, switch=True, hours=True)),
         ("+ demand floor 0.10 (4.91-4.94) = the current version", dict(one_at_a_time=True, switch=True, hours=True, floor=True)),
         ("   same, with every window starting from a restart", dict(one_at_a_time=True, switch=True, hours=True, floor=True, restart=True))]
res = {name: {k: run(recs, **kw) for k, recs in wins.items()} for name, kw in steps}
print(f"{'configuration':64s} {'trades':>6s} {'$ at $25':>9s} {'vs rule alone':>14s}")
base = sum(25 * sum(v) for v in res[steps[0][0]].values())
for name, _ in steps:
    r = res[name]; n = sum(len(v) for v in r.values()); usd = sum(25 * sum(v) for v in r.values())
    print(f"{name:64s} {n:6d} {usd:+9.0f} {usd - base:+14.0f}")
cur = res[steps[4][0]]; rule = res[steps[0][0]]
print(f"\n{'window':18s} {'rule alone':>11s} {'current':>9s} {'difference':>11s} {'trades':>12s}")
for k in sorted(wins):
    b, c = 25 * sum(rule[k]), 25 * sum(cur[k]); print(f"{k[0]} {k[1]:6s} {b:+11.0f} {c:+9.0f} {c - b:+11.0f} {len(rule[k]):5d} -> {len(cur[k]):3d}")
