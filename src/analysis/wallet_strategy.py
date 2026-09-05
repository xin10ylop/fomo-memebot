#!/usr/bin/env python3
"""What the consistent wallets actually do: trade-level description (report section 17).

Reads data/derived/wallet_history_{tag}.json (from wallet_history_pnl.py) and, for the wallets given, prints every
closed round trip (token, venue, entry age, cost, hold, return) and the aggregate profile: entry-age distribution
(how long after the pool/curve was created they buy), hold-time distribution, size, exit-return distribution (how
often they take +50% / +100%, how often they cut at -30%/-50%), time of day, venue mix, whether the tokens were
leaderboard memes (token_metrics.json), and how many distinct tokens carry the P&L.

usage: python3 wallet_strategy.py TAG WALLET [WALLET ...] | --consistent
"""
import json, sys, os, collections, statistics as st, datetime

HERE = os.path.dirname(os.path.abspath(__file__)); TAG = sys.argv[1]
H = json.load(open(os.path.join(HERE, "..", "..", "data", "derived", f"wallet_history_{TAG}.json")))
tm = json.load(open(os.path.join(HERE, "..", "..", "data", "derived", "token_metrics.json")))
if sys.argv[2] == "--consistent":
    rows = [v["summary"] for v in H.values()]
    wallets = [r["wallet"] for r in rows if r["closed_trips"] >= 20 and r["weeks_active"] >= 3 and r["weeks_positive"] >= 0.75 * r["weeks_active"] and r["realized"] >= 2000 and (r["top_token_share"] or 1) <= 0.5]
else:
    wallets = [w.lower() for w in sys.argv[2:]]


def pct(xs, q):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def fmt_age(a):
    return "n/a" if a is None else (f"{a / 60:.0f}m" if a < 7200 else f"{a / 3600:.1f}h" if a < 172800 else f"{a / 86400:.1f}d")


for w in wallets:
    v = H.get(w)
    if not v:
        print("no history for", w); continue
    s = v["summary"]; toks = v["tokens"]
    trips = []
    for tok, p in toks.items():
        for c in p["closed"]:
            trips.append({"tok": tok, "sym": tm.get(tok, {}).get("symbol") or tok[:8], "lb": tok in tm, "venue": p["venue"], "age0": p["age0"], "cost": c["cost"], "pnl": c["pnl"], "ret": (c["proceeds"] / c["cost"] - 1) if c["cost"] > 0 else 0.0, "hold": c["t_out"] - c["t_in"], "t_in": c["t_in"], "t_out": c["t_out"]})
    trips.sort(key=lambda t: t["t_in"])
    rets = [t["ret"] for t in trips]; holds = [t["hold"] for t in trips]; sizes = [t["cost"] for t in trips]; ages = [t["age0"] for t in trips if t["age0"] is not None]
    per_tok = collections.defaultdict(float)
    for t in trips:
        per_tok[t["sym"]] += t["pnl"]
    top = sorted(per_tok.items(), key=lambda kv: -kv[1])
    hours = collections.Counter(datetime.datetime.utcfromtimestamp(t["t_in"]).hour for t in trips)
    print(f"\n=== {w}  realized ${s['realized']:,.0f} over {s['closed_trips']} round trips in {s['tokens']} tokens, {s['weeks_active']} active weeks ({s['weeks_positive']} positive), open cost ${s['open_cost']:,.0f} marked ${s['open_marked']:,.0f}, unpriced events {s['unpriced']}")
    print(f"  weekly: " + " ".join(f"{k}:{x:+.0f}" for k, x in sorted(s["weekly"].items())))
    print(f"  size $: median {st.median(sizes):,.0f} p90 {pct(sizes, .9):,.0f} max {max(sizes):,.0f} | hold: p25 {fmt_age(pct(holds, .25))} median {fmt_age(st.median(holds))} p75 {fmt_age(pct(holds, .75))} | win {100 * sum(1 for r in rets if r > 0) / len(rets):.0f}%")
    print(f"  entry age (pool/curve age at first buy, n={len(ages)}): p10 {fmt_age(pct(ages, .1))} p25 {fmt_age(pct(ages, .25))} median {fmt_age(pct(ages, .5))} p75 {fmt_age(pct(ages, .75))} | <10 min {100 * sum(1 for a in ages if a < 600) / max(1, len(ages)):.0f}%  <1 h {100 * sum(1 for a in ages if a < 3600) / max(1, len(ages)):.0f}%  >1 d {100 * sum(1 for a in ages if a > 86400) / max(1, len(ages)):.0f}%")
    print(f"  exit returns: median {100 * st.median(rets):+.0f}% p10 {100 * pct(rets, .1):+.0f}% p90 {100 * pct(rets, .9):+.0f}% | share >= +50%: {100 * sum(1 for r in rets if r >= .5) / len(rets):.0f}%  >= +100%: {100 * sum(1 for r in rets if r >= 1) / len(rets):.0f}%  <= -30%: {100 * sum(1 for r in rets if r <= -.3) / len(rets):.0f}%  <= -50%: {100 * sum(1 for r in rets if r <= -.5) / len(rets):.0f}%")
    print(f"  venues {s['venues']} | leaderboard memes among traded tokens: {100 * sum(1 for t in toks if t in tm) / len(toks):.0f}% | top tokens by P&L: " + ", ".join(f"{k} {x:+,.0f}" for k, x in top[:6]) + f" | worst: " + ", ".join(f"{k} {x:+,.0f}" for k, x in top[-3:]))
    print(f"  entry hours UTC: " + " ".join(f"{h}:{n}" for h, n in sorted(hours.items())))
    print(f"  {'when':16s} {'token':12s} {'venue':6s} {'age@entry':>9s} {'cost $':>8s} {'hold':>7s} {'ret':>7s} {'pnl $':>8s}")
    for t in trips[-40:]:
        print(f"  {datetime.datetime.utcfromtimestamp(t['t_in']):%m-%d %H:%M} {t['sym'][:12]:12s} {str(t['venue'])[:6]:6s} {fmt_age(t['age0']):>9s} {t['cost']:8,.0f} {fmt_age(t['hold']):>7s} {100 * t['ret']:+6.0f}% {t['pnl']:8,.0f}")
