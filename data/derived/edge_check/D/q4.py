"""q4.py (reviewer D), brief question 4: the expectation for the next week under keep (the rule, 300 blocks) / 15 blocks / stop,
and the stopping rule on chain-scored fires.
 Expectation: per fire at the position mix live got (24.29: behind one on 8 of 12 crowd fills, behind two or three on the rest:
 2/3 second place, 1/3 third place), three estimates of the per-fire return (the fit, the recent, and the trend line of all 91
 fires at the middle of next week), the chain's fire rate (recent 0.32/h; 0.10/h in the last 10 h per round 1 A), the engine's
 reach (0.7 of chain fires: 24.33 addendum 3's pre-gate filters kept 87 of 123) and a fill on 3/4 of bursts; a burst that does not
 fill pays its gas. Stopping rule: Wald's SPRT per chain-scored fire (normal, sd from the 91 fires), boundaries +-2.94 (5%/5%),
 the expected number of fires under each hypothesis, and the stopping time simulated by resampling the real fires.
    python3 data/derived/edge_check/D/q4.py > data/derived/edge_check/D/q4.txt"""
import sys, os, math, random, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c, kit as K
random.seed(4); ALL = sorted(K.FIT + K.REC, key=lambda f: f["T0"]); F = [f for f in ALL if f["fire"]]
def pos_mix(S, h):
    """2/3 second place (the path), 1/3 third place (model_eff with two buys ahead)"""
    v2 = [f["path"][h] for f in S]; v3 = []
    for f in S:
        L = c.tape(f["cv"]); e = c.seat_block(L, L["b0"]); v3.append(c.model_eff(L, 13 / c.E, e, 2, h)[0])
    return 2 / 3 * c.mean(v2) + 1 / 3 * c.mean(v3)
t0 = F[0]["T0"]; mid_next_week = 1790856000   # Oct 1 2026 12:00 UTC
def trend_at(h, T):
    x = [(f["T0"] - t0) / 86400 for f in F]; y = [f["path"][h] for f in F]; mx, my = st.mean(x), st.mean(y)
    b = sum((a - mx) * (d - my) for a, d in zip(x, y)) / sum((a - mx) ** 2 for a in x); return my + b * ((T - t0) / 86400 - mx)
print("EXPECTATION FOR THE NEXT WEEK at $13 (per week = 7 days)")
print(" per-fire return at the live position mix (2/3 second, 1/3 third place), three readings:")
est = {}
for h in (15, 300):
    fit = pos_mix([f for f in K.FIT if f["fire"]], h); rec = pos_mix([f for f in K.REC if f["fire"]], h); tr = trend_at(h, mid_next_week) - (c.mean([f["path"][h] for f in F]) - pos_mix(F, h))
    est[h] = {"fit": fit, "recent": rec, "trend (Oct 1)": tr}
    print(f"  h{h:<3d} fit {fit:+6.1%}   recent {rec:+6.1%}   trend line at Oct 1 {tr:+6.1%}")
print(" $ per week = chain fires/h x 168 x reach 0.7 x (fill 0.75 x return x $13 - $0.33 gas per burst):")
for rate in (0.32, 0.10):
    for h in (15, 300):
        cells = []
        for lab, r in est[h].items():
            bursts = rate * 168 * 0.7; w = bursts * (0.75 * r * 13 - 0.33); cells.append(f"{lab} ${w:+6.1f}")
        print(f"  {rate:.2f} fires/h  h{h:<3d} " + "   ".join(cells) + f"   ({rate*168*0.7:.0f} bursts)")
    print(f"  {rate:.2f} fires/h  stop  $0")
sd15 = st.stdev([f["path"][15] for f in F]); sd300 = st.stdev([f["path"][300] for f in F])
print(f"\n weekly sd at $13 (fills only): h15 ${sd15*13*math.sqrt(0.32*168*0.7*0.75):.0f}, h300 ${sd300*13*math.sqrt(0.32*168*0.7*0.75):.0f} at 0.32 fires/h")
print("\nSTOPPING RULES (Wald SPRT on each chain-scored fire, normal likelihood, A = -B = ln(19) = 2.94)")
def llr(xs, m0, m1, s): return sum(((x - m0) ** 2 - (x - m1) ** 2) / (2 * s * s) for x in xs)
def asn(m0, m1, s, true):
    d = (m1 - m0) ** 2 / (2 * s * s); step = (2 * true - m0 - m1) * (m1 - m0) / (2 * s * s)
    if abs(step) < 1e-9: return float("inf")
    return (0.95 * (2.94 if step > 0 else -2.94) + 0.05 * (-2.94 if step > 0 else 2.94)) / step
def sim(pool, shift, m0, m1, s, n=4000, cap=400):
    out = []
    for _ in range(n):
        L = 0.0; k = 0
        while abs(L) < 2.94 and k < cap:
            x = random.choice(pool) + shift; L += ((x - m0) ** 2 - (x - m1) ** 2) / (2 * s * s); k += 1
        out.append((k, L >= 2.94))
    ks = sorted(k for k, _ in out); return ks[len(ks) // 2], ks[int(0.9 * len(ks))], sum(u for _, u in out) / len(out)
tests = [("KEEP: h300, H1 fit mean +26.3% vs H0 0 (round 1 A's test)", 300, 0.0, 0.263, sd300),
         ("KEEP: h300, H1 +26.3% vs H0 gas break-even +2.5%", 300, 0.0254, 0.263, sd300),
         ("15 BLOCKS: h15, H1 +12.8% (recent) vs H0 +2.5% (break-even)", 15, 0.0254, 0.128, sd15),
         ("15 BLOCKS: h15, H1 +15.5% (all 91) vs H0 +2.5%", 15, 0.0254, 0.155, sd15)]
for name, h, m0, m1, s in tests:
    rec = [f["path"][h] for f in K.REC if f["fire"]]; fit = [f["path"][h] for f in K.FIT if f["fire"]]
    print(f" {name}   sd {s:.3f}")
    print(f"   expected fires to decide: if H0 true {asn(m0, m1, s, m0):.0f}, if H1 true {asn(m0, m1, s, m1):.0f};  LLR of the 18 recent fires {llr(rec, m0, m1, s):+.2f} (information only: a test starts at 0 on the first new fire)")
    for lab, pool, shift in (("resampling the fit's fires (H1-like)", fit, 0.0), ("resampling the recent fires", rec, 0.0), (f"resampling the fit's fires shifted to mean {m0:+.1%} (H0)", fit, m0 - st.mean(fit))):
        med, p90, up = sim(pool, shift, m0, m1, s)
        print(f"   {lab:58s} median {med:3d} fires, 90th pct {p90:3d}, ends at H1 {up:.0%}")
