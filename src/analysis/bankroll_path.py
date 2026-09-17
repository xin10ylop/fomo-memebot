"""the engine's money path day by day from a starting bankroll: the rule as it runs (clean seat, filter 5+/0.3-1.2 ETH/3%,
hours 12-05 UTC, one position at a time, 15% of the bankroll per trade between $25 and $300, the 3% supply cap, the
-50% daily stop, the switch on the last 15 scored seats), every trade re-simulated at the stake actually used, the
bankroll carried from one day to the next. Variant B drops a random third of the clean seats (the true-clock share)."""
import sys, pickle, os, random, statistics as st, datetime, collections
os.chdir("/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad")
exec(open("/home/user/fomo-memebot/src/analysis/indep_replay.py").read().split("recs = []")[0])
START = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0; FIRST = sys.argv[2] if len(sys.argv) > 2 else "2026-09-02"
launches = []
for (day, w), d in data.items():
    if day < FIRST: continue
    for cv, (L, f) in d.items():
        g = feats(L); clean = g["out1"] == 0 and not (g["rival_lag"] is not None and g["rival_lag"] < 0.3)
        rule = g["n"] >= 5 and 0.3 <= g["eth"] <= 1.2 and g["tk0"] >= 0.03
        launches.append((L["ts"], day, w, cv, L, clean, rule))
launches.sort()
hours = collections.defaultdict(float)
for (day, w) in data:
    if day < FIRST: continue
    a, b = (int(x) for x in w.split("-")); hours[day] += (17.23 - 12) if (day == "2026-09-16" and w == "12-18") else b - a
def path(drop_third, seed=11):
    random.seed(seed); bank = START; busy = -1e9; scores = collections.deque(maxlen=15); rows = {}; peak = START
    for ts, day, w, cv, L, clean, rule in launches:
        h = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).hour
        r = rows.setdefault(day, {"start": bank, "trades": 0, "stopped": False, "off": 0, "low": bank})
        if not (clean and rule): continue
        if drop_third and random.random() < 1 / 3: continue                      # a rival inside the 0.3 s wait on the true clock: the engine does not send
        stake = min(max(bank * 0.15, 25.0), 300.0, bank)
        X = X0 + L["rows"][0][4]; Y = Y0 - L["rows"][0][3]; tk3 = 0.03 * Y0
        spent = min(stake, X * tk3 / (Y - tk3) / (1 - L["tier"] - 0.0019) * PX)   # the 3% supply cap: what the trade can actually put in
        roi = sim(L, "E2", stake_usd=stake)["roi"]
        scores.append(roi)                                                    # the engine scores every rule-passing seat, traded or not
        if not (h >= 12 or h < 5): continue
        if r["stopped"] or bank < 0.5 * r["start"]:
            r["stopped"] = True; continue
        if len(scores) == 15 and st.mean(scores) < -0.10:
            r["off"] += 1; continue
        if ts < busy: continue
        bank += spent * roi; busy = ts + 8.0; r["trades"] += 1; r["low"] = min(r["low"], bank); peak = max(peak, bank); r["spent"] = r.get("spent", 0) + spent
        r["end"] = bank
    for day in rows: rows[day].setdefault("end", rows[day]["start"])
    return rows, bank
for label, drop in (("A. every clean seat (replay clock)", False), ("B. a third of the clean seats dropped (true clock)", True)):
    rows, final = path(drop)
    print(f"\n=== {label}: from ${START:,.0f}, 15% of the bankroll per trade ($25-$300), hours 12-05, filter, switch, daily stop")
    print(f"{'day':7s} {'hours':>5s} {'trades':>6s} {'start $':>9s} {'end $':>9s} {'day P&L':>9s} {'worst in day':>12s} {'avg stake':>15s} {'switch-off':>10s}")
    for day in sorted(rows):
        r = rows[day]
        print(f"{day[5:]:7s} {hours[day]:5.1f} {r['trades']:6d} {r['start']:9,.0f} {r['end']:9,.0f} {r['end']-r['start']:+9,.0f} {100*(r['low']/r['start']-1):+11.0f}% {r.get('spent',0)/max(r['trades'],1):9,.0f}/trade {r['off']:8d}{'  DAILY STOP' if r['stopped'] else ''}")
    print(f"end: ${final:,.0f} ({final/START:.1f}x)")
