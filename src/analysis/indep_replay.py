"""An independent re-implementation of the seat replay, written without reading risk_harness.replay's control flow for
the answer: the curve is x*y=k from (X0, Y0), a buy pays tier+surcharge, a sell pays tier, we take 3% of supply capped at
the stake, land 0.3 s into the seat's second, hold 5 s or take +50%, later buyers who would get 10% fewer tokens than
quoted revert (their minOut), and our own minOut (25%) reverts us if the seat moved 25% before we landed."""
import pickle, sys, statistics as st, random, datetime, collections, os
X0, Y0, PX, GAS_USD = 1.68, 1e9, 2445.0, 0.10
S = "/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad/"
data = pickle.load(open(S + "risk_harness_cache_new_v2.pkl", "rb"))
if os.path.exists(S + "risk_harness_cache_v2.pkl"):
    data.update(pickle.load(open(S + "risk_harness_cache_v2.pkl", "rb")))
S1, S2 = (0.05, 0.075), (0.0012, 0.0035)
def kind(r, tier):
    d = r[5] - tier
    return "s1" if S1[0] <= d <= S1[1] else "s2" if S2[0] <= d <= S2[1] else "plain"
def sim(L, seat, stake_usd=25.0, wait=0.3, hold=5.0, tp=0.5, tol=0.10, our_slip=0.25, anchor="boundary"):
    rows = L["rows"]; tier = L["tier"]; pos = L["ts"] % 1.0
    surcharge = 0.0618 if seat == "E1" else 0.0019
    if anchor == "boundary":
        t_entry = (seat == "E1" and 1.0 or 2.0) - pos + wait
    else:                                                          # the harness's choice: 0.3 s after the first buy carrying the seat's surcharge
        first = next((r[0] for r in rows[1:] if r[1] == "B" and r[0] <= 3.0 and kind(r, tier) == ("s1" if seat == "E1" else "s2")), None)
        t_entry = (first if first is not None else (1.0 if seat == "E1" else 2.0)) + wait
    X, Y = X0, Y0; i = 0; p_seat = None
    for i, r in enumerate(rows):
        if i > 0 and r[0] >= t_entry:
            break
        if r[1] == "B":
            X += r[4]; Y -= r[3]
        else:
            X -= r[4]; Y += r[3]
        i += 1
    else:
        i = len(rows)
    # our own minOut: the engine quotes at send time from everything the feed has shown (blocks up to ~0.1 s before we land), 25% tolerance
    Xs, Ys = X0, Y0
    for r in rows:
        if r[0] >= t_entry - 0.1:
            break
        if r[1] == "B": Xs += r[4]; Ys -= r[3]
        else: Xs -= r[4]; Ys += r[3]
    if X / Y > (Xs / Ys) * (1 + our_slip):
        return dict(roi=-GAS_USD / stake_usd, status="reverted", t_in=t_entry, t_out=t_entry)
    fee = tier + surcharge; stake_eth = stake_usd / PX
    tk = 0.03 * Y0; net = X * tk / (Y - tk); gross = net / (1 - fee)
    if gross > stake_eth:
        gross = stake_eth; net = gross * (1 - fee); tk = Y * net / (X + net)
    X += net; Y -= tk; p_in = X / Y; t_out = t_entry + hold + 0.3
    for r in rows[i:]:
        if r[0] >= t_out:
            break
        if r[1] == "B":
            got = Y - X * Y / (X + r[4])
            if tol is not None and got < r[3] * (1 - tol):
                continue                                           # his minOut reverts him: our buy moved the price
            X += r[4]; Y -= got
        else:
            s = min(r[3], Y0 - Y - tk); g = X - X * Y / (Y + s); X -= g; Y += s
        if tp and X / Y >= p_in * (1 + tp) and t_out > r[0] + 0.3:
            t_out = r[0] + 0.3
    out = (X - X * Y / (Y + tk)) * (1 - tier)
    return dict(roi=((out - gross) * PX - GAS_USD) / (gross * PX), status="ok", t_in=t_entry, t_out=t_out)
def feats(L):
    rows = L["rows"]; tier = L["tier"]; pos = L["ts"] % 1.0
    out1 = sum(1 for r in rows[1:] if r[1] == "B" and kind(r, tier) == "s1")
    first_s2 = next((r[0] for r in rows[1:] if r[1] == "B" and r[0] <= 3.0 and kind(r, tier) == "s2"), None)
    rival_lag = first_s2 - (2.0 - pos) if first_s2 is not None else None
    first_tax = next((r[0] for r in rows[1:] if r[1] == "B" and kind(r, tier) != "plain"), 9e9)
    bundle = [r for r in rows[1:] if r[1] == "B" and r[0] < min(1.0, first_tax) and kind(r, tier) == "plain"]
    return dict(out1=out1, rival_lag=rival_lag, n=len(bundle), eth=sum(r[2] for r in bundle), tk0=rows[0][3] / Y0)
recs = []
for (day, win), launches in data.items():
    for cv, (L, f) in launches.items():
        g = feats(L); d = datetime.datetime.fromtimestamp(L["ts"], datetime.timezone.utc)
        clean = g["out1"] == 0 and not (g["rival_lag"] is not None and g["rival_lag"] < 0.3)
        a = sim(L, "E2"); b = sim(L, "E2", anchor="harness"); e1 = sim(L, "E1"); e1f = sim(L, "E1", wait=0.0)
        recs.append(dict(day=day, hour=d.hour, ts=L["ts"], cv=cv, clean=clean, harness_clean=(f["out1_n"] == 0 and not (f["rival_lag"] is not None and f["rival_lag"] < 0.3)),
                         roi=a["roi"], roi_h=b["roi"], rev=a["status"] == "reverted", e1=e1["roi"], e1f=e1f["roi"], t_in=L["ts"] + a["t_in"], t_out=L["ts"] + a["t_out"], **g))
recs.sort(key=lambda r: r["ts"])
def ci(xs, n=3000):
    random.seed(1); b = sorted(st.mean(random.choice(xs) for _ in xs) for _ in range(n)); return b[int(0.025 * n)], b[int(0.975 * n)]
def line(name, xs):
    if not xs: return f"{name:46s}    n 0"
    lo, hi = ci(xs) if len(xs) > 15 else (float('nan'),) * 2
    return f"{name:46s} n {len(xs):4d} mean {100*st.mean(xs):+6.1f}% median {100*st.median(xs):+6.1f}% win {100*sum(x>0 for x in xs)/len(xs):3.0f}%  95% [{100*lo:+.1f}%, {100*hi:+.1f}%]"
oos = [r for r in recs if r["day"] >= "2026-09-12"]
print("agreement with the harness on which launches are clean:", f"{100*sum(r['clean']==r['harness_clean'] for r in recs)/len(recs):.1f}%")
print("\n=== A. Sep 12-16 (never used for any choice), E2 seat, $25, my simulator")
print(line("clean seats, entry 0.3 s after the boundary", [r["roi"] for r in oos if r["clean"]]))
print(line("clean seats, entry anchored like the harness", [r["roi_h"] for r in oos if r["clean"]]))
print(line("clean seats, no later-buyer reverts (tol=None)", [sim(L, "E2", tol=None)["roi"] for k in data if k[0] >= "2026-09-12" for cv, (L, f) in data[k].items() if feats(L)["out1"] == 0 and not (feats(L)["rival_lag"] is not None and feats(L)["rival_lag"] < 0.3)]))
print(line("crowded seats (an outsider in second one)", [r["roi"] for r in oos if r["out1"] > 0]))
filt = lambda r: r["n"] >= 5 and 0.3 <= r["eth"] <= 1.2 and r["tk0"] >= 0.03
print(line("clean + the re-fitted filter (5+, 0.3-1.2 ETH, 3%)", [r["roi"] for r in oos if r["clean"] and filt(r)]))
print(line("clean + filter, hours 12-05 only", [r["roi"] for r in oos if r["clean"] and filt(r) and (r["hour"] >= 12 or r["hour"] < 5)]))
print("\n=== B. E1 (second one, +6.18% surcharge), all bundled launches, by day")
print(f"{'day':12s} {'launches':>8s} {'crowded':>8s} {'E2 clean n':>10s} {'E2 clean mean':>13s} {'E2 clean+filter':>15s} {'E1 0.3s':>9s} {'E1 front':>9s}")
for d in sorted({r["day"] for r in recs}):
    rs = [r for r in recs if r["day"] == d]; cl = [r for r in rs if r["clean"]]; cf = [r for r in cl if filt(r)]
    print(f"{d:12s} {len(rs):8d} {100*sum(r['out1']>0 for r in rs)/len(rs):7.0f}% {len(cl):10d} {100*st.mean(r['roi'] for r in cl) if cl else 0:+12.1f}% {100*st.mean(r['roi'] for r in cf) if cf else 0:+14.1f}% {100*st.mean(r['e1'] for r in rs):+8.1f}% {100*st.mean(r['e1f'] for r in rs):+8.1f}%")
print("\n=== C. by hour (UTC), clean E2 + filter, every day")
for h0, h1 in ((0, 5), (5, 12), (12, 18), (18, 24)):
    print(line(f"hours {h0:02d}-{h1:02d}", [r["roi"] for r in recs if r["clean"] and filt(r) and h0 <= r["hour"] < h1]))
print("\n=== D. the money, Sep 12-16 from $62: one position at a time, hours 12-05, clean + filter, $25 flat and 15% of the bankroll capped at $25")
for label, sizing in (("flat $25", lambda bank: 25.0), ("15% capped $25", lambda bank: min(max(bank * 0.15, 25.0), min(25.0, bank)))):
    bank = 62.0; busy = -1; n = 0; peak = 62.0; dd = 0.0; day_pl = collections.Counter()
    for r in oos:
        if not (r["clean"] and filt(r) and (r["hour"] >= 12 or r["hour"] < 5)) or r["t_in"] < busy: continue
        stake = sizing(bank); bank += stake * r["roi"]; busy = r["t_out"]; n += 1; peak = max(peak, bank); dd = max(dd, 1 - bank / peak); day_pl[r["day"]] += stake * r["roi"]
    print(f"   {label:16s}: {n} trades, end ${bank:,.0f} ({bank-62:+,.0f}), worst drawdown {100*dd:.0f}%, by day " + ", ".join(f"{d[5:]} {v:+.0f}" for d, v in sorted(day_pl.items())))
pickle.dump(recs, open(S + "indep_recs.pkl", "wb"))
