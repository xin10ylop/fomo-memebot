#!/usr/bin/env python3
"""Exact constant-product replay of the first-block sniper on Pons V2 (report section 20).

The bonding curve is x*y = k with virtual reserves X0 = 1.68 ETH and Y0 = 1e9 tokens (fitted on the creator's
launch-block buy: median 1.6800 ETH, p10 1.6800; every later buy and sell is then predicted to 1e-15). Every curve has
its own trading fee tier (1-5% of the quote, read from the creator's launch-block Buy event), and some early buys pay a
snipe surcharge on top (+6.18% in the timestamp second after creation, +0.19% the next second, 93-98% inside the creation
second). This script
  1. labels every observed event with its implied total tax (1 - net-into-curve / quoteIn for buys, 1 - quoteOut / gross
     for sells) from the exact curve state;
  2. inserts the sniper into the sequence (in front of the first surcharged buyer by default) and replays every later
     trade on the modified curve: later buyers spend the same gross ETH and receive fewer tokens, sellers sell the same
     tokens; buyers whose token shortfall exceeds a slippage tolerance are dropped (reverted on minOut); the sniper sells
     on the curve as it stands HOLD seconds after entry;
  3. compares entry positions, attrition, fee, latency and exit-slip assumptions against the LIFO valuation of sections
     14 and 19, and writes the per-trade list of the planning scenario for the capacity script.
usage: python3 sniper_exact.py [STAKE_USD] [FRAC]   (from the data root)
"""
import json, collections, statistics as st, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sniper_core as C

X0, Y0 = 1.68, 1e9
BUY, SELL = "0xec36bf57", "0x8113d738"
DAYS = ["2026-08-12", "2026-08-20", "2026-08-27", "2026-09-02", "2026-09-03"]
STAKE = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0
FRAC = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05
HOLD = 7.0
PX = C.PX["native"]


def load_exact(day):
    creates = {}
    for line in open(f"rh/creates_v2_{day}.jsonl"):
        b, tx, topics, data = json.loads(line)
        if len(topics) < 4:
            continue
        cv = "0x" + topics[2][-40:].lower()
        creates[cv] = {"b": b, "ts": C.bts(b), "creator": "0x" + topics[3][-40:].lower()}
    quotes = json.load(open(f"rh/launch_quotes_{day}.json"))
    ev = collections.defaultdict(list)
    for line in open(f"rh/v2curve_{day}_12-18.jsonl"):
        b, li, tx, addr, t0, data = json.loads(line)
        if addr not in creates or quotes.get(addr, "native") != "native":
            continue
        d = data[2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]
        if t0 == BUY:
            ev[addr].append((b, li, "B", w[0], w[1], w[2]))      # quoteIn (gross), tokensOut, fee
        elif t0 == SELL:
            ev[addr].append((b, li, "S", w[1], w[0], w[2]))      # quoteOut (net), tokensIn, fee
    launches = {}
    for cv, e in ev.items():
        e.sort(); c = creates[cv]
        if e[0][2] != "B" or e[0][0] != c["b"]:
            continue
        X, Y = X0, Y0; rows = []; tier = None; ok = True
        for i, (b, li, k, q, tk, f) in enumerate(e):
            t = C.bts(b) - c["ts"]
            if k == "B":
                if tk <= 0 or tk >= Y or q <= 0:
                    ok = False; break
                net = X * tk / (Y - tk); tax = 1 - net / q
                if i == 0:
                    tier = max(0.0, min(tax, 0.2))
                rows.append((t, "B", q, tk, net, tax)); X += net; Y -= tk
            else:
                gross = X - X * Y / (Y + tk)
                rows.append((t, "S", q, tk, gross, 1 - q / gross if gross > 0 else 0.0)); X -= gross; Y += tk
        if ok and tier is not None:
            launches[cv] = {"tier": tier, "rows": rows, **c}
    prior = collections.defaultdict(list)
    for cv, c in creates.items():
        prior[c["creator"]].append(c["ts"])
    for k in prior:
        prior[k].sort()
    return launches, prior


def replay(L, stake_eth, frac=FRAC, hold=HOLD, entry="E1", tol=None, exempt=False, lat=0.0, slip=0.0, replace=False):
    """returns (pnl_eth, cost_eth, t_in, t_out, kind, displaced_buy_row_or_None)"""
    rows = L["rows"]; tier = L["tier"]; X, Y = X0, Y0
    t, k, q, tk, net, tax = rows[0]; X += net; Y -= tk                 # the creator's launch-block buy
    # entry seats: E0 = in front of the first outside buy of any kind (creation second; only an exempt address can sit
    # there, anyone else pays 93-98%), E1 = in front of the first buy that paid the +6.18% surcharge (second 1),
    # E2 = in front of the first buy that paid +0.19% (second 2). The surcharge we pay is the seat's unless exempt.
    target, lo, hi, fb = {"E0": (0.0, -1.0, 0.0008, 0.1), "E1": (0.0618, 0.05, 0.075, 1.0), "E2": (0.0019, 0.0012, 0.0035, 2.0)}[entry]
    idx = None
    for i in range(1, len(rows)):
        r = rows[i]
        if r[1] == "B" and r[0] <= 3.0 and lo <= r[5] - tier <= hi:
            idx = i; break
    if idx is None:                                                     # nobody took that seat: enter at the second's start
        idx = next((i for i in range(1, len(rows)) if rows[i][0] >= fb), len(rows)); t_entry = fb
    else:
        t_entry = rows[idx][0]
    if lat > 0:                                                         # slower: behind everything that lands before t_entry + lat
        t_entry += lat; idx = next((i for i in range(1, len(rows)) if rows[i][0] >= t_entry), len(rows))
    displaced = rows[idx] if idx < len(rows) and rows[idx][1] == "B" and rows[idx][0] <= 3.0 else None
    kind = "followed" if any(r[1] == "B" and r[0] <= 3.0 for r in rows[1:]) else "alone"
    for r in rows[1:idx]:                                               # in front of us: exactly as observed
        if r[1] == "B":
            X += r[4]; Y -= r[3]
        else:
            X -= r[4]; Y += r[3]
    fee = tier + (0.0 if exempt else target)
    tk_bot = frac * Y0
    net = X * tk_bot / (Y - tk_bot); gross = net / (1 - fee)
    if gross > stake_eth:
        gross = stake_eth; net = gross * (1 - fee); tk_bot = Y * net / (X + net)
    X += net; Y -= tk_bot; t_in = t_entry
    held = Y0 - Y - tk_bot; phantom = 0.0                              # tokens held by others vs tokens dropped buyers would have held
    for r in rows[idx:]:
        t, k, q, tk, net_obs, tax = r
        if t >= t_in + hold + slip:
            break
        if k == "B":
            tokens = Y - X * Y / (X + net_obs)
            if (replace and r is displaced) or (tol is not None and tokens < tk * (1 - tol)):
                phantom += tk; continue                                 # never bought (replaced, or reverted on its minOut)
            X += net_obs; Y -= tokens; held += tokens
        else:                                                           # sells scale with what is actually held: dropped buyers cannot sell
            share = held / (held + phantom) if held + phantom > 0 else 1.0
            s = min(tk * share, held); g = X - X * Y / (Y + s); X -= g; Y += s; held -= s; phantom = max(0.0, phantom - (tk - s))
    out = (X - X * Y / (Y + tk_bot)) * (1 - tier)
    return out - gross, gross, t_in, t_in + hold + slip, kind, displaced


def bundle_count(L):
    """buys inside the creation second that paid no surcharge, before any surcharged buy: the creator's named wallets.
    Observable from the feed before the second-1 seat."""
    tier = L["tier"]; first_taxed = next((r[0] for r in L["rows"][1:] if r[1] == "B" and r[5] - tier > 0.001), 9e9)
    return sum(1 for r in L["rows"][1:] if r[1] == "B" and r[0] < min(1.0, first_taxed) and r[5] - tier <= 0.0008)


def summarize(res):
    v = [r[0] / r[1] for r in res]; n = len(v); dollars = [r[0] for r in res]; net = sum(dollars)
    top = sum(sorted(dollars)[-max(1, n // 20):]); vs = sorted(v)
    return dict(n=n, roi=st.mean(v), med=vs[n // 2], net=net, per=net / n, lo=C.ci(v)[0], hi=C.ci(v)[1],
                alone=sum(1 for r in res if r[4] == "alone") / n, top5=top / net if net > 0 else float("nan"),
                big_loss=sum(1 for x in v if x < -0.5) / n, cost=st.mean(r[1] for r in res))


def main():
    stake_eth = STAKE / PX
    data = {}
    for day in DAYS:
        launches, prior = load_exact(day)
        creates, trades, quotes, _ = C.load(day)
        elig = [cv for cv, L in launches.items() if prior[L["creator"]][0] == L["ts"]]
        data[day] = (launches, elig, creates, trades, quotes)
    scen = [
        ("LIFO valuation (sections 14/19, sim_all)", None),
        ("E0 true first seat (exempt address only), all later flow comes", dict(entry="E0", exempt=True)),
        ("E0, later buyers revert beyond 10% shortfall", dict(entry="E0", tol=0.10, exempt=True)),
        ("E0, 10% tol, sell 0.3 s late, 3% of supply", dict(entry="E0", tol=0.10, exempt=True, slip=0.3, frac=0.03)),
        ("E0, 10% tol, 0.3 s behind the first outside buyer", dict(entry="E0", tol=0.10, exempt=True, lat=0.3)),
        ("E0, 10% tol, 0.75 s behind", dict(entry="E0", tol=0.10, exempt=True, lat=0.75)),
        ("E1 seat: in front of the first +6.18% buyer, paying +6.18%, all flow comes", dict(entry="E1")),
        ("exact, same, later buyers revert beyond 20% shortfall", dict(entry="E1", tol=0.20)),
        ("exact, same, revert beyond 10% shortfall", dict(entry="E1", tol=0.10)),
        ("exact, same, revert beyond 5% shortfall", dict(entry="E1", tol=0.05)),
        ("exact, 10% tol, displaced first buyer never buys", dict(entry="E1", tol=0.10, replace=True)),
        ("E1 seat but exempt (no surcharge), all flow comes", dict(entry="E1", exempt=True)),
        ("E1 exempt, 10% tol", dict(entry="E1", tol=0.10, exempt=True)),
        ("E1 exempt, 10% tol, sell 0.3 s late, 3% of supply", dict(entry="E1", tol=0.10, exempt=True, slip=0.3, frac=0.03)),
        ("E2 seat: in front of the first +0.19% buyer, paying +0.19%, all flow comes", dict(entry="E2")),
        ("E2, 10% tol", dict(entry="E2", tol=0.10)),
        ("E2, 10% tol, 0.3 s behind", dict(entry="E2", tol=0.10, lat=0.3)),
        ("E2, 10% tol, sell 0.3 s late, 3% of supply", dict(entry="E2", tol=0.10, slip=0.3, frac=0.03)),
        ("exact, 10% tol, 0.3 s behind the first surcharged buyer", dict(entry="E1", tol=0.10, lat=0.3)),
        ("exact, 10% tol, 0.75 s behind", dict(entry="E1", tol=0.10, lat=0.75)),
        ("exact, 10% tol, sell lands 0.3 s late", dict(entry="E1", tol=0.10, slip=0.3)),
        ("PLAN: E0, 10% tol, sell 0.3 s late, 3% of supply", dict(entry="E0", tol=0.10, exempt=True, slip=0.3, frac=0.03)),
        ("exact, 10% tol, sell 0.3 s late, 8% of supply", dict(entry="E1", tol=0.10, slip=0.3, frac=0.08)),
    ]
    print(f"first-block sniper on the exact curve: stake ${STAKE:.0f}, {100*FRAC:.0f}% of supply unless stated, hold {HOLD:.0f} s, gas ${C.GAS:.2f}/round trip, ETH ${PX:.0f}")
    print("eligible = creator's first launch of the day, ETH-quoted, launch-block buy present. cells: mean ROI on cost % [95% CI] | net $ | n")
    hdr = f"{'scenario':70s}" + "".join(f"{d[5:]:>26s}" for d in DAYS); print(hdr)
    plan = {}
    for name, kw in scen:
        line = f"{name:70s}"
        for day in DAYS:
            launches, elig, creates, trades, quotes = data[day]; res = []
            for cv in elig:
                if kw is None:
                    r = C.sim_all(cv, creates, trades, quotes, STAKE, HOLD, FRAC)
                    if r and r[1] >= 5.0:
                        res.append((r[0], r[1], r[2], r[3], r[4]))
                else:
                    pnl, cost, t_in, t_out, kind, _ = replay(launches[cv], stake_eth, **kw)
                    res.append((pnl * PX - C.GAS, cost * PX, launches[cv]["ts"] + t_in, launches[cv]["ts"] + t_out, kind))
            s = summarize(res); line += f"{100*s['roi']:+6.1f}[{100*s['lo']:+.0f},{100*s['hi']:+.0f}] {s['net']:7.0f} {s['n']:4d}"
            if name.startswith("PLAN"):
                plan[day] = dict(trades=res, **{k: v for k, v in s.items()})
        print(line)
    print("\nPLAN scenario detail (E0 seat, 3% of supply, 10% tolerance, sell 0.3 s late):")
    print(f"{'window':>12s} {'n':>5s} {'alone':>6s} {'mean ROI':>9s} {'median':>7s} {'$/trade':>8s} {'cost':>6s} {'top5% share':>11s} {'loss>50%':>9s}")
    for day in DAYS:
        s = plan[day]; print(f"{day:>12s} {s['n']:5d} {100*s['alone']:5.0f}% {100*s['roi']:+8.1f}% {100*s['med']:+6.1f}% {s['per']:+8.2f} {s['cost']:6.0f} {100*s['top5']:10.0f}% {100*s['big_loss']:8.1f}%")
    # per-trade dumps for the compounding script: seat x supply fraction x stake x window
    dumps = {"E0": dict(entry="E0", tol=0.10, exempt=True, slip=0.3), "E0_late03": dict(entry="E0", tol=0.10, exempt=True, slip=0.3, lat=0.3),
             "E0_late075": dict(entry="E0", tol=0.10, exempt=True, slip=0.3, lat=0.75), "E1": dict(entry="E1", tol=0.10, slip=0.3),
             "E2": dict(entry="E2", tol=0.10, slip=0.3),
             "E1_bundle3": dict(entry="E1", tol=0.10, slip=0.3), "E1_bundle3_late03": dict(entry="E1", tol=0.10, slip=0.3, lat=0.3),
             "E1_bundle3_late075": dict(entry="E1", tol=0.10, slip=0.3, lat=0.75), "E2_bundle3_late03": dict(entry="E2", tol=0.10, slip=0.3, lat=0.3)}
    out = {}
    for sname, kw in dumps.items():
        for frac in (0.03, 0.05):
            for stk in (50, 100, 200, 300):
                for day in DAYS:
                    launches, elig, *_ = data[day]; res = []
                    for cv in elig:
                        if "bundle3" in sname and bundle_count(launches[cv]) < 3:
                            continue
                        pnl, cost, t_in, t_out, kind, _ = replay(launches[cv], stk / PX, frac=frac, **kw)
                        res.append((pnl * PX - C.GAS, cost * PX, launches[cv]["ts"] + t_in, launches[cv]["ts"] + t_out, kind))
                    out.setdefault(sname, {}).setdefault(str(frac), {}).setdefault(str(stk), {})[day] = res
    os.makedirs(os.path.join(C.HERE, "..", "..", "data", "derived"), exist_ok=True)
    json.dump(out, open(os.path.join(C.HERE, "..", "..", "data", "derived", "sniper_exact_trades.json"), "w"))
    # fee tiers and surcharge census on the eligible set
    print("\nfee tier of eligible launches (creator-set, read from the launch-block buy):")
    for day in DAYS:
        launches, elig, *_ = data[day]; tiers = collections.Counter(round(launches[cv]["tier"], 3) for cv in elig)
        n = len(elig); print(f"  {day}: " + ", ".join(f"{100*t:.1f}%: {100*c/n:.0f}%" for t, c in sorted(tiers.items())[:6]))


if __name__ == "__main__":
    main()
