"""why the edge thinned: per window, the return of the kept launches decomposed into what later buyers add, what the team's
sells take, and what fees cost; the competition (second-one bots, seat rivals); the flow; and the hour of day. Then the
correlations across the 21 windows, and the hour-of-day pattern with an out-of-sample check."""
import sys, statistics as st, collections, datetime
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH, sniper_exact as SE
PX = RH.PX; Y0 = SE.Y0; X0 = SE.X0
data = RH.load(); new = RH.load_new(); data.update(new); NEWK = set(new)
def parts(L, hold=5.0, tp=0.5):
    """the E2 entry 0.3 s into second two (or behind the first rival), the hold with everything, with buys only, with sells only"""
    rows = L["rows"]; tier = L["tier"]
    r_all = RH.replay(L, 300 / PX, hold=hold, tp=tp)
    if r_all[4] == "reverted":
        return None
    t_in, t_out = r_all[2], r_all[3]
    # rebuild the state at entry, then fold only buys / only sells inside (t_in, t_out)
    X, Y = X0, Y0; X += rows[0][4]; Y -= rows[0][3]
    idx = next((i for i in range(1, len(rows)) if rows[i][0] >= t_in), len(rows))
    for r in rows[1:idx]:
        if r[1] == "B": X += r[4]; Y -= r[3]
        else: X -= r[4]; Y += r[3]
    fee = tier + 0.0019; tk_bot = 0.03 * Y0; net = X * tk_bot / (Y - tk_bot); gross = net / (1 - fee)
    if gross > 300 / PX:
        gross = 300 / PX; net = gross * (1 - fee); tk_bot = Y * net / (X + net)
    X += net; Y -= tk_bot; base = (X - X * Y / (Y + tk_bot)) * (1 - tier) / gross - 1      # sell straight back: the fees and our own impact
    def roll(kinds):
        Xa, Ya = X, Y; nb = 0; eb = 0.0; ns = 0; ss = 0.0
        for r in rows[idx:]:
            if r[0] >= t_out: break
            if r[1] == "B" and "B" in kinds:
                tokens = Ya - Xa * Ya / (Xa + r[4])
                if tokens >= r[3] * 0.9:
                    Xa += r[4]; Ya -= tokens; nb += 1; eb += r[2]
            elif r[1] == "S" and "S" in kinds:
                s = min(r[3], Y0 - Ya - tk_bot); g = Xa - Xa * Ya / (Ya + s); Xa -= g; Ya += s; ns += 1; ss += r[3] / Y0
        return (Xa - Xa * Ya / (Ya + tk_bot)) * (1 - tier) / gross - 1, nb, eb, ns, ss
    buys_only = roll("B"); sells_only = roll("S")
    return dict(roi=r_all[0] / r_all[1], base=base, buys=buys_only[0] - base, sells=sells_only[0] - base, nb=buys_only[1], eb=buys_only[2], ns=sells_only[3], ss=sells_only[4], hold_s=t_out - t_in)
W = []
for k in sorted(data):
    keep = data[k]; ks = [(L, f) for cv, (L, f) in keep.items()]; n_b = len(ks)
    kept = [(L, f) for L, f in ks if f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f)]
    if len(kept) < 10: continue
    P = [p for p in (parts(L) for L, f in kept) if p]
    day = datetime.datetime.strptime(k[0], "%Y-%m-%d"); wd = day.strftime("%a")
    W.append(dict(k=k, wd=wd, half="NEW" if k in NEWK else ("FIT" if k in RH.FIT else "TEST"), n_b=n_b, n=len(P), out1=st.mean(f["out1_n"] > 0 for L, f in ks),
                  rival=st.mean(RH.G_WAIT(0.3)(f) for L, f in ks if f["out1_n"] == 0), roi=st.mean(p["roi"] for p in P), base=st.mean(p["base"] for p in P),
                  buys=st.mean(p["buys"] for p in P), sells=st.mean(p["sells"] for p in P), nb=st.mean(p["nb"] for p in P), eb=st.mean(p["eb"] for p in P), ss=st.mean(p["ss"] for p in P),
                  dumped=st.mean(p["ss"] >= 0.2 for p in P), q0=st.median(f["q0"] for L, f in kept), bundle_eth=st.median(f["bundle_eth"] for L, f in kept), elig=None))
print("=== per window: the kept launches' return decomposed (E2 0.3 s in, hold 5, TP 50%, $300). base = fees and our own impact; buys = what later buyers add; sells = what sells inside the hold take")
print(f"{'window':16s} {'dow':>3s} {'bundled':>7s} {'kept':>4s} {'bots s1':>7s} {'rival':>5s} | {'ROI':>6s} = {'base':>6s} {'+buys':>6s} {'sells':>6s} | {'buys/hold':>9s} {'ETH/hold':>8s} {'dump%':>5s} {'>20% dumped':>11s} | {'creator ETH':>11s} {'bundle ETH':>10s}")
for w in W:
    print(f"{w['k'][0][5:]} {w['k'][1]:5s} {w['wd']:>3s} {w['n_b']:7d} {w['n']:4d} {100*w['out1']:6.0f}% {100*w['rival']:4.0f}% | {100*w['roi']:+5.1f}% = {100*w['base']:+5.1f}% {100*w['buys']:+5.1f}% {100*w['sells']:+5.1f}% | {w['nb']:9.1f} {w['eb']:8.2f} {100*w['ss']:4.1f}% {100*w['dumped']:10.0f}% | {w['q0']:11.3f} {w['bundle_eth']:10.2f}")
for h in ("FIT", "TEST", "NEW"):
    ws = [w for w in W if w["half"] == h]
    if ws:
        print(f"   {h:4s} mean: ROI {100*st.mean(w['roi'] for w in ws):+5.1f}% = base {100*st.mean(w['base'] for w in ws):+5.1f}% + buys {100*st.mean(w['buys'] for w in ws):+5.1f}% + sells {100*st.mean(w['sells'] for w in ws):+5.1f}% | buys/hold {st.mean(w['nb'] for w in ws):.1f}, ETH/hold {st.mean(w['eb'] for w in ws):.2f}, bots in second one {100*st.mean(w['out1'] for w in ws):.0f}%, rivals {100*st.mean(w['rival'] for w in ws):.0f}%")
def corr(a, b):
    ma, mb = st.mean(a), st.mean(b); sa, sb = st.pstdev(a), st.pstdev(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (len(a) * sa * sb) if sa and sb else 0.0
print("\n=== across the 21 windows: correlation of the kept launches' ROI with ...")
for name, key in (("bots in second one (share of bundled launches)", "out1"), ("seat rivals (share of the rest)", "rival"), ("later buyers per hold", "nb"), ("later ETH per hold", "eb"), ("supply sold inside the hold", "ss"), ("bundled launches in the window", "n_b"), ("creator buy (median ETH)", "q0")):
    print(f"   {name:48s} r = {corr([w[key] for w in W], [w['roi'] for w in W]):+.2f}")
print("   and of later buyers per hold with bots in second one: r = %+.2f; with the window's bundled count: r = %+.2f" % (corr([w['out1'] for w in W], [w['nb'] for w in W]), corr([w['n_b'] for w in W], [w['nb'] for w in W])))
print("\n=== hour of day (UTC) on the kept launches, ROI at hold 5 + TP, and competition by hour")
byh = collections.defaultdict(lambda: {"FIT": [], "TEST": [], "NEW": []}); comp = collections.defaultdict(list)
for k in sorted(data):
    half = "NEW" if k in NEWK else ("FIT" if k in RH.FIT else "TEST")
    for cv, (L, f) in data[k].items():
        h = int(f["hour"]); comp[h].append(f["out1_n"] > 0)
        if f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f):
            r = RH.replay(L, 300 / PX, hold=5.0, tp=0.5)
            if r[4] != "reverted": byh[h][half].append(r[0] / r[1])
print(f"{'hour':>4s} {'bots s1':>7s} | " + " | ".join(f"{h:>4s} n  ROI" for h in ("FIT", "TEST", "NEW")))
for h in sorted(byh):
    print(f"{h:4d} {100*st.mean(comp[h]):6.0f}% | " + " | ".join((f"{len(byh[h][hf]):5d} {100*st.mean(byh[h][hf]):+6.1f}%" if len(byh[h][hf]) >= 5 else f"{len(byh[h][hf]):5d}     -  ") for hf in ("FIT", "TEST", "NEW")))
print("\n=== day of week (kept launches, all windows): n and ROI")
byd = collections.defaultdict(list)
for w in W:
    byd[w["wd"]] += [w["roi"]] * w["n"]
for d in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
    if byd[d]: print(f"   {d}: n {len(byd[d]):4d} ROI {100*st.mean(byd[d]):+5.1f}%")
