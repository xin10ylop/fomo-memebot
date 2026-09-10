"""killer checks on the replay: (1) the E1 seat under realistic landing mixes, its hold and sizing; (2) a walk-forward hold that
follows the teams' dump timing; (3) whether tiny second-one buys (a cheap way to trip the gate) predict anything; (4) a bootstrap
interval on the September mean; (5) gas at the measured level"""
import sys, os, random, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import risk_harness as RH, sniper_core as C
PX = RH.PX
data = RH.load(); new = RH.load_new(); data.update(new)
NEWK = set(new)
def half(k): return "FIT" if k in RH.FIT else ("TEST" if k in RH.TEST else "NEW")
print("=== (1) E1 seat: per-launch ROI at the front, one block behind, two blocks behind, 0.3 s behind (hold 7, no TP, $300), every bundled launch (rival-in-seat launches included: at E1 nothing is visible before the send)")
mix = {}
for k, keep in data.items():
    rows = []
    for cv, (L, f) in keep.items():
        r = {}
        for lab, lat in (("front", 0.0), ("b1", 0.1), ("b2", 0.2), ("b3", 0.3)):
            x = RH.replay(L, 300 / PX, entry="E1", lat=lat, hold=7.0, min_out_slip=None if lat == 0 else 0.25)
            r[lab] = None if x[4] == "reverted" else x[0] / x[1]
        if r["front"] is not None:
            rows.append(r)
    mix[k] = rows
def ev(rows, p):
    """p = probabilities of landing (front, block 2, block 3, later); a landing in the creation second reverts on minOut: gas only (-1/300)"""
    out = []
    for r in rows:
        v = 0.0
        for lab, pr in zip(("front", "b1", "b2", "b3"), p):
            x = r[lab] if r[lab] is not None else -1 / 300
            v += pr * x
        out.append(v)
    return st.mean(out) if out else 0.0
for hname, keys in (("FIT", RH.FIT), ("TEST", RH.TEST), ("NEW", NEWK)):
    rows = [r for k in mix if k in keys for r in mix[k]]
    if not rows: continue
    print(f"{hname}: n {len(rows)}  front {100*st.mean(r['front'] for r in rows):+5.1f}%  block2 {100*st.mean(r['b1'] or -1/300 for r in rows):+5.1f}%  block3 {100*st.mean(r['b2'] or -1/300 for r in rows):+5.1f}%  0.3s {100*st.mean(r['b3'] or -1/300 for r in rows):+5.1f}%"
          f" | mixes: 90/8/2/0 {100*ev(rows,(0.9,0.08,0.02,0)):+5.1f}%  70/20/7/3 {100*ev(rows,(0.7,0.2,0.07,0.03)):+5.1f}%  50/30/15/5 {100*ev(rows,(0.5,0.3,0.15,0.05)):+5.1f}%  30/40/20/10 {100*ev(rows,(0.3,0.4,0.2,0.1)):+5.1f}%")
print("per new window, front / block2 / mix 70-20-7-3:")
for k in sorted(mix):
    if k in NEWK and mix[k]:
        rows = mix[k]; print(f"   {k[0][5:]} {k[1]:5s} n {len(rows):4d} front {100*st.mean(r['front'] for r in rows):+6.1f}%  block2 {100*st.mean(r['b1'] or -1/300 for r in rows):+6.1f}%  mix {100*ev(rows,(0.7,0.2,0.07,0.03)):+6.1f}%")
print("\n=== (1b) E1 front as a plan: hold and sizing (every bundled launch, no gate possible before the send)")
for label, cfg in (("E1 front, hold 7, 15%/$25", {"entry": "E1", "lat": 0.0, "min_out_slip": None, "hold": 7.0, "sizing": 0.15, "clamp": (25.0, 300.0), "include_out1": True}),
                   ("E1 front, hold 9, 15%/$25", {"entry": "E1", "lat": 0.0, "min_out_slip": None, "hold": 9.0, "sizing": 0.15, "clamp": (25.0, 300.0), "include_out1": True}),
                   ("E1 front, hold 7, TP 50%, 15%/$25", {"entry": "E1", "lat": 0.0, "min_out_slip": None, "hold": 7.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "include_out1": True}),
                   ("E1 one block behind, hold 7, 15%/$25", {"entry": "E1", "lat": 0.1, "hold": 7.0, "sizing": 0.15, "clamp": (25.0, 300.0), "include_out1": True}),
                   ("E1 front, hold 7, 20%/$50", {"entry": "E1", "lat": 0.0, "min_out_slip": None, "hold": 7.0, "include_out1": True})):
    RH.summarize(RH.evaluate(cfg, data), label)
print("\n=== (2) walk-forward hold: each window uses the hold (3,4,5,6,7) that did best on the previous window; the E2 rule, TP 50%, 15%/$25")
keys = sorted(data); res = {}; prev_best = 5.0; picks = []
books = {h: RH.trade_book({"skip_fn": RH.G_WAIT(0.3), "hold": h, "take_profit": 0.5}, data) for h in (3.0, 4.0, 5.0, 6.0, 7.0)}
def mean_roi(book, k):
    v = [t[0][300][0] / t[0][300][1] for t in book[k] if t[0][300][4] != "reverted"]; return st.mean(v) if v else None
tot = {"walk": 0.0, "fixed5": 0.0}; lines = []
for i, k in enumerate(keys):
    if len(books[5.0][k]) < 10: continue
    if i > 0:
        prevs = [kk for kk in keys[:i] if len(books[5.0][kk]) >= 10]
        if prevs:
            pk = prevs[-1]; prev_best = max((3.0, 4.0, 5.0, 6.0, 7.0), key=lambda h: mean_roi(books[h], pk) or -9)
    w = RH.evaluate({"skip_fn": RH.G_WAIT(0.3), "hold": prev_best, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0)}, {k: data[k]}, book={k: books[prev_best][k]})[k]
    f5 = RH.evaluate({"skip_fn": RH.G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0)}, {k: data[k]}, book={k: books[5.0][k]})[k]
    tot["walk"] += w["own"] - 300; tot["fixed5"] += f5["own"] - 300
    lines.append(f"   {k[0][5:]} {k[1]:5s} hold used {prev_best:.0f}: ROI {100*w['roi']:+5.1f}% own {w['own']:6,.0f} | fixed 5: ROI {100*f5['roi']:+5.1f}% own {f5['own']:6,.0f}")
print("\n".join(lines)); print(f"   sum of gains: walk-forward {tot['walk']:,.0f}  fixed 5 s {tot['fixed5']:,.0f}")
print("\n=== (3) tiny second-one outsiders: does a small (< 0.01 ETH) second-one buy predict the same loss as a big one? E2 0.3 s in, hold 5, $300")
def out1_max_eth(L, f):
    tier = L["tier"]; return max((r[2] for r in L["rows"][1:] if r[1] == "B" and 0.05 <= r[5] - tier <= 0.075), default=0.0)
for hname, keys_ in (("FIT+TEST", RH.FIT | RH.TEST), ("NEW", NEWK)):
    cl = collections.defaultdict(list)
    for k in data:
        if k not in keys_: continue
        for cv, (L, f) in data[k].items():
            if RH.G_WAIT(0.3)(f): continue
            x = RH.replay(L, 300 / PX, hold=5.0)
            if x[4] == "reverted": continue
            m = out1_max_eth(L, f); cls = "clean" if f["out1_n"] == 0 else ("tiny (<0.01 ETH)" if m < 0.01 else ("small (0.01-0.05)" if m < 0.05 else "big (>=0.05 ETH)"))
            cl[cls].append(x[0] / x[1])
    print(f"{hname}: " + "  ".join(f"{c}: n {len(v)} {100*st.mean(v):+5.1f}%" for c, v in sorted(cl.items())))
print("\n=== (4) bootstrap: the September mean per trade and per-window gains (final rule), 2,000 resamples of trades within each window")
random.seed(3); cfg = {"skip_fn": RH.G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5}
book = RH.trade_book(cfg, {k: data[k] for k in NEWK}); allv = []; per = {}
for k, trades in book.items():
    v = [t[0][300][0] / t[0][300][1] for t in trades if t[0][300][4] != "reverted"]; per[k] = v; allv += v
bs = []
for _ in range(2000):
    bs.append(st.mean(random.choice(allv) for _ in range(len(allv))))
bs.sort(); print(f"all ten windows: n {len(allv)} mean {100*st.mean(allv):+5.1f}%  90% interval [{100*bs[100]:+5.1f}%, {100*bs[1900]:+5.1f}%]  P(mean<0) {sum(1 for x in bs if x < 0)/len(bs):.3f}")
for k in sorted(per):
    v = per[k]
    if len(v) < 10: continue
    b = sorted(st.mean(random.choice(v) for _ in range(len(v))) for _ in range(1000))
    print(f"   {k[0][5:]} {k[1]:5s} n {len(v):3d} mean {100*st.mean(v):+5.1f}%  90% [{100*b[50]:+5.1f}%, {100*b[950]:+5.1f}%]")
print("\n=== (5) gas at the measured level ($0.10 per round trip at 0.18 gwei) instead of the $1 assumed")
C.GAS = 0.10
for label, cfg in (("final rule, gas $0.10, 15%/$25", {"skip_fn": RH.G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0)}),
                   ("final rule, gas $0.10, from $100", {"skip_fn": RH.G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "start": 100}),
                   ("final rule, gas $0.10, from $50", {"skip_fn": RH.G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "start": 50})):
    RH.summarize(RH.evaluate(cfg, data), label, start=float(cfg.get("start", 300.0)))
C.GAS = 1.0
