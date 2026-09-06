#!/usr/bin/env python3
"""Regime switch, one-position-at-a-time netting, compounding and ruin odds for the first-block sniper on the exact-curve
trades written by sniper_exact.py (report section 20). Unlike section 19, the switch only uses outcomes already known at
decision time (a launch's score becomes available 20 s after its exit, as the engine scores it), and the stake actually
deployed is the simulated cost at the nearest simulated stake.
usage: python3 sniper_compound.py   (from the repo root or anywhere; reads data/derived/sniper_exact_trades.json)
"""
import json, os, random, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "..", "..", "data", "derived", "sniper_exact_trades.json")))
DAYS = ["2026-08-12", "2026-08-20", "2026-08-27", "2026-09-02", "2026-09-03"]
SWITCH_N, SWITCH_T, SCORE_DELAY, DAILY_STOP = 30, 0.05, 20.0, 0.30


def run_day(by_stake, start, sizing, switch=True, one_at_a_time=True, stop=True, clamp=(50.0, 300.0)):
    """trades in time order; returns (end bankroll, n trades, low, stopped, live share)"""
    ref = sorted(by_stake["300"], key=lambda r: r[2]); scored = []           # (available_at, roi)
    bank = float(start); low = bank; busy = 0.0; n = 0; stopped = False; live = 0
    for r in ref:
        t_in = r[2]; avail = [x[1] for x in scored if x[0] <= t_in]
        on = (not switch) or (len(avail) >= SWITCH_N and st.mean(avail[-SWITCH_N:]) >= SWITCH_T)
        scored.append((r[3] + SCORE_DELAY, r[0] / r[1]))
        if stop and bank < (1 - DAILY_STOP) * start:
            stopped = True
        if not on or (one_at_a_time and t_in < busy) or stopped or bank < clamp[0]:
            continue
        live += 1
        stake = min(max(bank * sizing, clamp[0]), min(clamp[1], bank))
        near = min(by_stake, key=lambda s_: abs(float(s_) - stake)); rr = next((x for x in by_stake[near] if x[2] == t_in), None)
        if not rr:
            continue
        deployed = min(stake, rr[1]); bank += deployed * (rr[0] / rr[1]); busy = rr[3]; low = min(low, bank); n += 1
    return bank, n, low, stopped, live / max(1, len(ref))


def main():
    for seat in ("E0", "E0_late03", "E0_late075", "E1", "E2", "E1_bundle3", "E1_bundle3_late03", "E1_bundle3_late075", "E2_bundle3_late03"):
        for frac in ("0.03", "0.05"):
            print(f"\n=== seat {seat}, {float(frac)*100:.0f}% of supply ===")
            print(f"{'window':>12s} {'n':>5s} {'always-on $300':>15s} {'switched':>10s} {'switched, 1 at a time':>22s} {'live':>5s} | compounding from $300 @20%: end | from $1000 @20%: end | from $50 all-in: end")
            for day in DAYS:
                bs = D[seat][frac]; by_stake = {stk: bs[stk][day] for stk in bs}
                rows = sorted(by_stake["300"], key=lambda r: r[2])
                if len(rows) < 10:
                    print(f"{day:>12s} {len(rows):5d} (too few launches pass)"); continue
                always = sum(r[0] for r in rows)
                # switched (availability-correct), no netting, fixed $300 stake, no stop
                sw = run_day(by_stake, 1e9, 300 / 1e9, switch=True, one_at_a_time=False, stop=False, clamp=(300.0, 300.0))
                sw1 = run_day(by_stake, 1e9, 300 / 1e9, switch=True, one_at_a_time=True, stop=False, clamp=(300.0, 300.0))
                c300 = run_day(by_stake, 300, 0.2); c1000 = run_day(by_stake, 1000, 0.2); c50 = run_day(by_stake, 50, 1.0, clamp=(25.0, 300.0))
                print(f"{day:>12s} {len(rows):5d} {always:15,.0f} {sw[0]-1e9:10,.0f} {sw1[0]-1e9:22,.0f} {100*sw1[4]:4.0f}% | ${c300[0]:8,.0f} ({c300[1]:3d} tr{', stop' if c300[3] else ''}) | ${c1000[0]:8,.0f} ({c1000[1]:3d} tr) | ${c50[0]:7,.0f} ({c50[1]:3d} tr, low ${c50[2]:.0f})")
    # ruin odds from $50 all-in on the E0 seat: resample the day's trades (time order shuffled), stake = min(bank, 300), stop at $25 or $300
    print("\nfrom $50, all-in each trade (stake = min(bankroll, $300)), 3% of supply: chance of reaching $300 before dropping under $25, 2000 resampled sequences per window")
    random.seed(7)
    for seat_r in ("E0", "E1_bundle3_late03"):
        print(f"  seat {seat_r}:")
        for day in DAYS:
            bs = D[seat_r]["0.03"]; by_stake = {stk: {r[2]: r for r in bs[stk][day]} for stk in bs}; keys = list(by_stake["300"])
            if len(keys) < 10:
                print(f"    {day}: too few launches"); continue
            win = 0; trades = []
            for _ in range(2000):
                bank = 50.0; k = 0
                while 25 <= bank < 300 and k < 400:
                    t = random.choice(keys); stake = min(bank, 300.0); near = min(by_stake, key=lambda s_: abs(float(s_) - stake)); rr = by_stake[near][t]
                    bank += min(stake, rr[1]) * (rr[0] / rr[1]); k += 1
                win += bank >= 300; trades.append(k)
            print(f"    {day}: reaches $300 {100*win/2000:.0f}% of the time, median {st.median(trades):.0f} trades")


if __name__ == "__main__":
    main()
