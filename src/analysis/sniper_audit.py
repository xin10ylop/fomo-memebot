#!/usr/bin/env python3
"""Audit checks on the sniper simulation (report section 20): (a) launches with no outside buyer within 3 s, which the
rule skips but a live bot would have bought; (b) capital actually deployed per trade against the stake (the 3%-of-supply
cap); (c) the per-trade return distribution, the share of trades losing more than half, and the probability that a
$50 all-in bankroll reaches $300 before it dies; (d) the fee actually charged by the curve, from the Buy/Sell event
fee field; (e) robustness of the regime switch to its lookback and threshold.
usage: python3 sniper_audit.py   (run from the data root)
"""
import sys, os, json, random, statistics as st, collections, datetime, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sniper_core as C

random.seed(1)
DAYS = ["2026-08-12", "2026-08-20", "2026-08-27", "2026-09-02", "2026-09-03"]


def eligible(day, creates, quotes, prior):
    t0d = datetime.datetime.fromisoformat(day + "T00:00:00+00:00").timestamp()
    return [cv for cv, m in creates.items() if t0d + 12 * 3600 <= m["ts"] < t0d + 18 * 3600 - 1800 and bisect.bisect_left(prior[m["creator"]], m["ts"]) == 0 and quotes.get(cv) == "native"]


def sim_all(cv, creates, trades, quotes, stake, hold=7.0):
    """like C.sim but also handles launches with no outside buyer within 3 s: the bot buys at the post-creator curve
    price (approximated by the creator's own average price times 1.0, the curve's next marginal price is higher) and
    sells back 7 s later into whatever happened. Returns (pnl_usd, cost_usd, t_in, t_out, kind)."""
    m = creates[cv]; tr = sorted(trades.get(cv, []))
    if len(tr) < 1:
        return None
    t0 = m["ts"]; evs = [(C.bts(b) - t0, buy, q, tk) for b, li, buy, q, tk in tr]
    first = [e for e in evs[1:] if e[1]]
    q = quotes.get(cv, "native")
    if first and first[0][0] <= 3.0:
        r = C.sim(cv, creates, trades, quotes, stake, hold)
        return (r + ("followed",)) if r else None
    # no outside buyer within 3 s: entry at the creator's average price (a lower bound on the curve's next price), 0.2 s after creation
    if m["tk0"] <= 0 or m["q0"] <= 0:
        return None
    p_in = m["q0"] / m["tk0"] * 1.05; pu = C.usd(p_in, q)
    if pu is None:
        return None
    t_in = 0.2; tk_bot = min(0.03e9, stake / pu); cost = tk_bot * p_in * 1.01
    stack = [[m["tk0"], m["q0"]], [tk_bot, tk_bot * p_in]]
    for t, buy, qq, tk in evs[1:]:
        if t <= t_in:
            continue
        if t >= t_in + hold:
            break
        if buy:
            stack.append([tk, qq])
        else:
            need = tk
            while need > 1e-12 and stack:
                tokens, quote = stack[-1]; take = min(tokens, need)
                if take >= tokens - 1e-12:
                    stack.pop()
                else:
                    stack[-1] = [tokens - take, quote * (tokens - take) / tokens]
                need -= take
    out = C.lifo_value(stack, tk_bot)
    return (C.usd(out - cost, q) - C.GAS, C.usd(cost, q), t0 + t_in, t0 + t_in + hold, "no_follower")


print("(a) launches the rule skipped because nobody bought within 3 s; a live bot buys them all. $300 stake, base filter.")
print(f"{'window':10s} {'eligible':>8s} {'followed':>8s} {'no follower':>11s} {'mean ROI followed':>17s} {'mean ROI no-follower':>20s} {'mean ROI all':>12s} {'net $ followed':>14s} {'net $ all':>10s}")
dist = {}
for day in DAYS:
    creates, trades, quotes, prior = C.load(day); el = eligible(day, creates, quotes, prior)
    rows = [r for r in (sim_all(cv, creates, trades, quotes, 300.0) for cv in el) if r]
    f = [r for r in rows if r[4] == "followed"]; n = [r for r in rows if r[4] == "no_follower"]
    roi_f = [r[0] / r[1] for r in f]; roi_n = [r[0] / r[1] for r in n]; roi_a = roi_f + roi_n
    dist[day] = rows
    print(f"{day:10s} {len(el):8d} {len(f):8d} {len(n):11d} {100 * st.mean(roi_f):+16.1f}% {100 * (st.mean(roi_n) if roi_n else 0):+19.1f}% {100 * st.mean(roi_a):+11.1f}% {sum(r[0] for r in f):14,.0f} {sum(r[0] for r in rows):10,.0f}")

print("\n(b) capital deployed per trade at a $300 stake (the 3%-of-supply cap binds when 3% of supply costs less than the stake)")
for day in DAYS:
    c = sorted(r[1] for r in dist[day] if r[4] == "followed")
    if c:
        print(f"  {day}: cost per trade p10 ${c[len(c) // 10]:.0f} median ${c[len(c) // 2]:.0f} p90 ${c[9 * len(c) // 10]:.0f} mean ${st.mean(c):.0f}; share of trades at the full $300: {100 * sum(1 for x in c if x >= 290) / len(c):.0f}%")

print("\n(c) per-trade return distribution (followed launches, $300 and $50 stakes) and ruin from $50 all-in")
for day in ("2026-08-27", "2026-09-02", "2026-09-03"):
    creates, trades, quotes, prior = C.load(day); el = eligible(day, creates, quotes, prior)
    for stake in (50.0, 300.0):
        rows = [r for r in (sim_all(cv, creates, trades, quotes, stake) for cv in el) if r]
        roi = [r[0] / r[1] for r in rows]; roi_t = sorted(roi)
        print(f"  {day} ${stake:.0f}: n={len(roi)} mean {100 * st.mean(roi):+.1f}% p5 {100 * roi_t[len(roi) // 20]:+.0f}% p25 {100 * roi_t[len(roi) // 4]:+.0f}% median {100 * st.median(roi):+.0f}% p75 {100 * roi_t[3 * len(roi) // 4]:+.0f}% p95 {100 * roi_t[19 * len(roi) // 20]:+.0f}% | loss > 50%: {100 * sum(1 for x in roi if x < -0.5) / len(roi):.1f}%  loss > 90%: {100 * sum(1 for x in roi if x < -0.9) / len(roi):.1f}%  gain > 100%: {100 * sum(1 for x in roi if x > 1) / len(roi):.1f}%")
        if stake == 50.0:
            seq = [r[0] / r[1] for r in sorted(rows, key=lambda r: r[2])]
            # ruin: bankroll 50, bet the whole bankroll each trade (stake 50 floor), stop at >= 300 (success) or < 50 (ruin)
            def run(order):
                bank = 50.0
                for x in order:
                    if bank < 50:
                        return False
                    if bank >= 300:
                        return True
                    bank *= (1 + x)
                return bank >= 300
            succ_seq = run(seq)
            iid = [run([random.choice(seq) for _ in range(len(seq))]) for _ in range(2000)]
            blk = []
            for _ in range(2000):
                i = random.randint(0, max(0, len(seq) - 200)); blk.append(run(seq[i:i + 200]))
            print(f"    $50 all-in until $300: actual day sequence {'reached $300' if succ_seq else 'ruined'}; i.i.d. bootstrap success {100 * sum(iid) / len(iid):.0f}%; 200-trade block bootstrap success {100 * sum(blk) / len(blk):.0f}%")

print("\n(d) fee charged by the curve, from the Buy/Sell event fee field, Sep 3 sample")
creates, trades, quotes, prior = C.load("2026-09-03")
ratios = []
for line in open("rh/v2curve_2026-09-03_12-18.jsonl"):
    b, li, tx, addr, t0, data = json.loads(line)
    if addr not in creates:
        continue
    d = data[2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
    if len(w) >= 3 and w[0] > 0 and w[1] > 0:
        q = w[0] if t0 == "0xec36bf57" else w[1]
        if q > 0:
            ratios.append(w[2] / q)
    if len(ratios) >= 20000:
        break
ratios.sort(); print(f"  fee / quote: median {100 * ratios[len(ratios) // 2]:.3f}% p10 {100 * ratios[len(ratios) // 10]:.3f}% p90 {100 * ratios[9 * len(ratios) // 10]:.3f}% (n={len(ratios)})")

print("\n(e) regime-switch robustness: net $ per window at $300, base filter, by lookback N and threshold T (trade live while mean of last N scores >= T)")
print(f"{'N/T':8s} " + " ".join(f"{d[5:]:>10s}" for d in DAYS))
for N in (20, 30, 50):
    for T in (0.0, 0.02, 0.05, 0.10):
        line = f"{N:3d}/{100 * T:3.0f}% "
        for day in DAYS:
            rows = sorted([r for r in dist[day] if r[4] == "followed"], key=lambda r: r[2]); hist = []; cum = 0.0
            for p, c, a, b, k in rows:
                on = len(hist) >= N and st.mean(hist[-N:]) >= T
                if on:
                    cum += p
                hist.append(p / c)
            line += f" {cum:10,.0f}"
        print(line)
