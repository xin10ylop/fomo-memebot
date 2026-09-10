"""(6) a seat chosen by the regime: E1 front when the previous window's share of bundled launches with a second-one outsider was
above a threshold, else the E2 clean rule; (7) small starts at a planning gas of $0.25 (2.5x the measured round trip)"""
import sys, os, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import risk_harness as RH, sniper_core as C
data = RH.load(); new = RH.load_new(); data.update(new); NEWK = set(new)
keys = [k for k in sorted(data) if len(data[k]) >= 10]
E2 = {"skip_fn": RH.G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0)}
E1 = {"entry": "E1", "lat": 0.0, "min_out_slip": None, "hold": 7.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "include_out1": True}
E1b = dict(E1, lat=0.1, min_out_slip=0.25)                   # one block behind: the pessimistic landing
b2 = RH.trade_book(E2, data); b1 = RH.trade_book(E1, data); b1b = RH.trade_book(E1b, data)
r2 = RH.evaluate(E2, data, book=b2); r1 = RH.evaluate(E1, data, book=b1); r1b = RH.evaluate(E1b, data, book=b1b)
share = {k: st.mean(1 if f["out1_n"] > 0 else 0 for cv, (L, f) in data[k].items()) for k in keys}
keys = [k for k in keys if r2.get(k) and r1.get(k) and r1b.get(k)]
print("=== (6) seat by regime: previous window's share of bundled launches with a second-one outsider; E1 front (hold 7, TP 50%) above the threshold, the E2 rule below; both 15%/$25")
for thr in (0.35, 0.45, 0.55):
    tot = {"switch": 0.0, "switch_pess": 0.0, "e2": 0.0, "e1": 0.0}; stops = []; lines = []
    for i, k in enumerate(keys):
        prev = keys[i - 1] if i > 0 else None; sh = share[prev] if prev else 0.0
        use_e1 = sh > thr
        w = r1[k] if use_e1 else r2[k]; wp = r1b[k] if use_e1 else r2[k]
        tot["switch"] += w["own"] - 300; tot["switch_pess"] += wp["own"] - 300; tot["e2"] += r2[k]["own"] - 300; tot["e1"] += r1[k]["own"] - 300; stops.append(w["pstop"])
        lines.append(f"   {k[0][5:]} {k[1]:5s} prev out1 share {100*sh:3.0f}% -> {'E1' if use_e1 else 'E2'}: ROI {100*w['roi']:+5.1f}% own {w['own']:6,.0f} stop {100*w['pstop']:3.0f}% | E2 {r2[k]['own']:6,.0f} E1 {r1[k]['own']:6,.0f} E1 one block late {r1b[k]['own']:6,.0f}")
    print(f"threshold {thr:.2f}: sum of gains switch {tot['switch']:,.0f} (E1 landings one block late: {tot['switch_pess']:,.0f}) | E2 always {tot['e2']:,.0f} | E1 always {tot['e1']:,.0f} | max stop odds on the path {100*max(stops):.0f}%")
    if thr == 0.45:
        print("\n".join(lines))
print("\n=== (7) small starts at a planning gas of $0.25 per round trip")
C.GAS = 0.25
for label, cfg in (("final rule, gas $0.25, from $300", dict(E2)), ("final rule, gas $0.25, from $100", dict(E2, start=100)), ("final rule, gas $0.25, from $50", dict(E2, start=50)),
                   ("final rule, gas $0.25, from $100, 20%/$25", dict(E2, start=100, sizing=0.2))):
    RH.summarize(RH.evaluate(cfg, data), label, start=float(cfg.get("start", 300.0)))
C.GAS = 1.0
