#!/usr/bin/env python3
"""Reproduces the plan tables of report sections 21.6-21.8 and 22 from the raw windows: per-window returns under the final
rule, the switch/stop sweep, compounding from several starting bankrolls, and doubling odds. Everything here is on the
exact-curve replay (sniper_exact.replay) at the E2 seat, 0.3 s behind the first buyer of the seat, 3% of supply, 7 s
hold, sell 0.3 s late, minOut refusals at 25%.
usage: python3 sniper_plan.py [--refresh]   (from the data root; caches replays in data/derived/sniper_plan_cache.json)
"""
import sys, os, json, random, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sniper_exact as SE, sniper_core as C
PX = C.PX["native"]; Y0 = SE.Y0
WINS = [("2026-08-12", "12-18"), ("2026-08-20", "12-18"), ("2026-08-27", "12-18"), ("2026-08-30", "12-18"), ("2026-08-31", "12-18"), ("2026-09-01", "12-18"),
        ("2026-09-02", "12-18"), ("2026-09-03", "0-6"), ("2026-09-03", "12-18"), ("2026-09-03", "18-24"), ("2026-09-04", "12-18"), ("2026-09-05", "0-6"),
        ("2026-09-05", "12-18"), ("2026-09-06", "12-18")]
CACHE = os.path.join(C.HERE, "..", "..", "data", "derived", "sniper_plan_cache.json")
STAKES = (50, 100, 200, 300)


def rule_pass(L):
    tier = L["tier"]; rows = L["rows"]
    first_taxed = next((r[0] for r in rows[1:] if r[1] == "B" and r[5] - tier > 0.001), 9e9)
    bundle = [r for r in rows[1:] if r[1] == "B" and r[0] < min(1.0, first_taxed) and r[5] - tier <= 0.0008]
    out1 = sum(1 for r in rows[1:] if r[1] == "B" and 0.05 <= r[5] - tier <= 0.075)
    return len(bundle) >= 3 and sum(r[2] for r in bundle) >= 0.3 and rows[0][3] >= 0.01 * Y0 and out1 == 0


def build():
    data = {}
    for day, win in WINS:
        SE.WINDOW = win
        try:
            launches, prior = SE.load_exact(day)
        except FileNotFoundError:
            continue
        R = [cv for cv, L in launches.items() if prior[L["creator"]][0] == L["ts"] and rule_pass(L)]
        by = {}
        for stk in STAKES:
            res = []
            for cv in R:
                pnl, cost, t_in, t_out, kind, _ = SE.replay(launches[cv], stk / PX, frac=0.03, entry="E2", tol=0.10, slip=0.3, lat=0.3, min_out_slip=0.25)
                res.append((pnl * PX - (C.GAS if kind != "reverted" else 0.0), cost * PX if kind != "reverted" else 1e-9, launches[cv]["ts"] + t_in, launches[cv]["ts"] + t_out, kind))
            by[str(stk)] = res
        data[f"{day} {win}"] = {"n_eligible": sum(1 for cv, L in launches.items() if prior[L["creator"]][0] == L["ts"]), "by_stake": by}
    json.dump(data, open(CACHE, "w")); return data


def run_day(by, start, sizing, n_sw=15, thr=-0.10, stop=0.50, one=True, clamp=(50.0, 300.0), delay=20.0):
    ref = sorted(by["300"], key=lambda r: r[2]); scored = []; bank = float(start); low = bank; busy = 0.0; n = 0; stopped = False
    for r in ref:
        t_in = r[2]; avail = [x[1] for x in scored if x[0] <= t_in]; on = (n_sw == 0) or len(avail) < n_sw or st.mean(avail[-n_sw:]) >= thr
        scored.append((r[3] + delay, r[0] / r[1] if r[1] > 1e-6 else 0.0))
        if stop is not None and bank < (1 - stop) * start:
            stopped = True
        if not on or (one and t_in < busy) or stopped or bank < clamp[0]:
            continue
        stake = min(max(bank * sizing, clamp[0]), min(clamp[1], bank)); near = min(by, key=lambda s_: abs(float(s_) - stake)); rr = next((x for x in by[near] if x[2] == t_in), None)
        if not rr:
            continue
        dep = min(stake, rr[1]) if rr[1] > 1e-6 else 0.0; bank += dep * (rr[0] / rr[1]) if rr[1] > 1e-6 else rr[0]; busy = rr[3]; low = min(low, bank); n += 1
    return bank, n, low, stopped


def main():
    data = build() if not os.path.exists(CACHE) or "--refresh" in sys.argv else json.load(open(CACHE))
    keys = [k for k in data if len(data[k]["by_stake"]["300"]) >= 10]
    print("FINAL RULE (bundle >=3 wallets and >=0.3 ETH, creator buy >=1% of supply, no outsider in second one), E2 seat 0.3 s behind, 3% of supply, hold 7 s, minOut 25%")
    print(f"{'window':16s} {'eligible':>8s} {'rule':>5s} {'refused':>7s} {'mean ROI':>9s} {'median':>7s} {'always-on $':>11s} {'1-at-a-time $':>13s}")
    tot = collections.Counter()
    for k in keys:
        rows = data[k]["by_stake"]["300"]; taken = [r for r in rows if r[4] != "reverted"]; v = [r[0] / r[1] for r in taken]
        sw = run_day(data[k]["by_stake"], 1e9, 300 / 1e9, n_sw=0, stop=None, clamp=(300.0, 300.0))[0] - 1e9
        tot["always"] += sum(r[0] for r in rows); tot["sw"] += sw; tot["n"] += len(rows)
        print(f"{k:16s} {data[k]['n_eligible']:8d} {len(rows):5d} {len(rows)-len(taken):7d} {100*st.mean(v):+8.1f}% {100*st.median(v):+6.1f}% {sum(r[0] for r in rows):11,.0f} {sw:13,.0f}")
    print(f"{'sum':16s} {'':>8s} {tot['n']:5d} {'':>7s} {'':>9s} {'':>7s} {tot['always']:11,.0f} {tot['sw']:13,.0f}")
    print("\nswitch and stop, compounding from $300 at 20% sizing (stakes $50-$300), one position at a time: end bankroll per window")
    configs = [("switch 30/+5%, stop -30% (section 19)", 30, 0.05, 0.30), ("safety switch 15/-10%, stop -50% (engine default)", 15, -0.10, 0.50), ("no switch, stop -50%", 0, 0, 0.50), ("no switch, no stop", 0, 0, None)]
    print(f"{'config':48s} " + " ".join(f"{k[5:10]+'/'+k[11:13]:>9s}" for k in keys) + f" {'sum gains':>10s} {'<start':>6s}")
    for name, n_sw, thr, stop in configs:
        ends = [run_day(data[k]["by_stake"], 300, 0.2, n_sw, thr, stop)[0] for k in keys]
        print(f"{name:48s} " + " ".join(f"{e:9,.0f}" for e in ends) + f" {sum(e - 300 for e in ends):10,.0f} {sum(1 for e in ends if e < 300):6d}")
    print("\ncompounding with the engine defaults from several starts: end bankroll per window")
    print(f"{'start':>7s} " + " ".join(f"{k[5:10]+'/'+k[11:13]:>9s}" for k in keys) + f" {'sum gains':>10s} {'<start':>6s} {'median':>8s}")
    for start in (100, 150, 200, 300, 500, 1000):
        ends = [run_day(data[k]["by_stake"], start, 0.2)[0] for k in keys]
        print(f"{start:>7d} " + " ".join(f"{e:9,.0f}" for e in ends) + f" {sum(e - start for e in ends):10,.0f} {sum(1 for e in ends if e < start):6d} {st.median(ends):8,.0f}")
    print("\nresampled trade order within each window (1,000 paths, 20% sizing, stop -50%, from $300): median end, p10 end, chance of hitting the stop")
    random.seed(7)
    for k in keys:
        by = data[k]["by_stake"]; rows = by["300"]; ends = []; stops = 0
        for _ in range(1000):
            order = rows[:]; random.shuffle(order); bank = 300.0; stopped = False
            for r in order:
                if bank < 150:
                    stopped = True; break
                stake = min(max(bank * 0.2, 50.0), min(300.0, bank)); near = min(by, key=lambda s_: abs(float(s_) - stake)); rr = next((x for x in by[near] if x[2] == r[2]), r)
                bank += (min(stake, rr[1]) * (rr[0] / rr[1]) if rr[1] > 1e-6 else rr[0])
            ends.append(bank); stops += stopped
        ends.sort(); print(f"  {k:16s} median ${ends[len(ends) // 2]:8,.0f}  p10 ${ends[len(ends) // 10]:8,.0f}  stop {100 * stops / 1000:3.0f}%")


if __name__ == "__main__":
    main()
