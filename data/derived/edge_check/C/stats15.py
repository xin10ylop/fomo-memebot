"""stats15.py (edge_check/C): questions 2 and 4. The rule's fires at 15 and 300 blocks: the recent fires one by one, how robust
the recent h15 mean is (bootstrap, leave-one-out, trimmed), whether h15 changed between the periods, the $/day at the recent
supply with the tables' full-fill assumption and with the live execution mix, and the sequential tests (SPRT) that settle each
candidate on chain-scored fires, with the expected number of fires to a decision (resampled from the fires' own returns).
    python3 data/derived/edge_check/C/stats15.py > data/derived/edge_check/C/stats15.txt"""
import sys, json, random, math, statistics as st
sys.path.insert(0, "data/derived/edge_check/C"); from common import *
P = [x for x in json.load(open(C + "pop.json")) if x["ret"] is not None]
for x in P:
    for key in ("ret", "ret_first", "ret_third"): x[key] = {int(h): v for h, v in x[key].items()}
fire = lambda x: x["f_k2"] >= 2
fit = [x for x in P if x["set"] == "fit" and fire(x)]; rec = sorted([x for x in P if x["set"] == "rec" and fire(x)], key=lambda x: x["T0"])
random.seed(11); NB = 100000
print("=== 1. the recent fires one by one (second place, $13): h15, h300, the bundle's share sold by +300, outsider ETH E1+16..60")
for x in rec:
    print(f"  {hms(x['T0'])} {x['cv'][:10]} {x['win']:12s} f_k2 {x['f_k2']}  h15 {x['ret'][15]:+7.1%}  h300 {x['ret'][300]:+7.1%}  bundle sold {x['named_sold300']:4.0%}  outsider ETH16-60 {x['a16_60_eth']:.2f}")
def boot_ci(v, n=NB):
    ms = sorted(mean(random.choices(v, k=len(v))) for _ in range(n)); return ms[int(0.025 * n)], ms[int(0.975 * n)], sum(m <= 0.0254 for m in ms) / n
for h in (15, 300):
    v = [x["ret"][h] for x in rec]; f = [x["ret"][h] for x in fit]
    lo, hi, p0 = boot_ci(v); flo, fhi, _ = boot_ci(f)
    loo = [mean(v[:i] + v[i + 1:]) for i in range(len(v))]; tr = sorted(v)[1:-1]
    draws = sum(mean(random.choices(f, k=len(v))) <= mean(v) for _ in range(NB)) / NB
    print(f"\n=== 2. h{h}: recent {len(v)} fires mean {mean(v):+.1%} (95% bootstrap {lo:+.1%} to {hi:+.1%}; P(mean <= break-even 2.54%) {p0:.1%})  median {st.median(v):+.1%}"
          f"  leave-one-out min {min(loo):+.1%} max {max(loo):+.1%}  trimmed (drop best and worst) {mean(tr):+.1%}")
    print(f"      fit {len(f)} fires mean {mean(f):+.1%} (95% {flo:+.1%} to {fhi:+.1%}), median {st.median(f):+.1%}; 19 fires drawn from the fit's read <= the recent mean in {draws:.1%}")
    print(f"      sd per fire: fit {sd(f):.3f}, recent {sd(v):.3f}, pooled {sd(f + v):.3f}")
# the recent set without the one best fire at h15
v15 = [x["ret"][15] for x in rec]
print(f"\n  recent h15 without its two best fires (+86%, +70%): {mean([x['ret'][15] for x in rec if x['ret'][15] < 0.6]):+.1%} on {sum(x['ret'][15] < 0.6 for x in rec)};  paper stretch (Sep 24 12:55 - Sep 26 09:15) h15 {mean([x['ret'][15] for x in rec if x['T0'] < 1790414100]):+.1%} ({sum(x['T0'] < 1790414100 for x in rec)}),"
      f" after h15 {mean([x['ret'][15] for x in rec if x['T0'] >= 1790414100]):+.1%} ({sum(x['T0'] >= 1790414100 for x in rec)})")
print("\n=== 3. $/day at the recent supply (0.32 fires an hour = 7.7 a day), per burst after $0.33 gas")
FPD = 0.32 * 24
for h in (15, 300):
    for per, s in (("fit", fit), ("recent", rec)):
        full = mean([usd(x["ret"][h]) for x in s])
        # live mix (24.29/24.31): a fill on about half the bursts; of fills, 2/3 second place, 1/3 third; gas on every burst
        mix = 0.5 * STAKE * (2 / 3 * mean([x["ret"][h] for x in s]) + 1 / 3 * mean([x["ret_third"][h] for x in s])) - GAS
        print(f"  h{h:3d} at the {per:6s} per-fire return: full fill at second place ${full:+.2f}/burst ${full*FPD:+6.1f}/day ${full*FPD*7:+7.1f}/week;"
              f"   live mix (fill 1 burst in 2, 2/3 second, 1/3 third) ${mix:+.2f}/burst ${mix*FPD:+6.1f}/day ${mix*FPD*7:+7.1f}/week")
    s_all = [usd(x["ret"][h]) for x in rec]
    print(f"        weekly sd at 54 fires (recent per-fire $ sd {sd(s_all):.2f}): ${sd(s_all)*math.sqrt(FPD*7):.0f}")
print("\n=== 4. sequential tests on chain-scored fires (Wald SPRT, alpha = beta = 0.05, boundaries +-2.94; normal likelihood, sd per fire as given)")
def llr(xs, m0, m1, s): return sum((m1 - m0) / s ** 2 * (x - (m0 + m1) / 2) for x in xs)
def asn(src, shift, m0, m1, s, start=0.0, n=20000, cap=400):
    """expected fires to a decision and P(accept H1) when fires are drawn from src shifted to mean `shift`"""
    base = [x - mean(src) + shift for x in src]; tot = 0; acc = 0
    for _ in range(n):
        L = start; k = 0
        while -2.944 < L < 2.944 and k < cap: L += (m1 - m0) / s ** 2 * (random.choice(base) - (m0 + m1) / 2); k += 1
        tot += k; acc += L >= 2.944
    return tot / n, acc / n
for name, h, m1, m0 in (("keep (h300): H1 the fit's mean +26.3%, H0 0", 300, mean([x["ret"][300] for x in fit]), 0.0),
                        ("h15: H1 the fit's h15 mean +16.2%, H0 break-even +2.5%", 15, mean([x["ret"][15] for x in fit]), GAS / STAKE)):
    s = sd([x["ret"][h] for x in fit + rec]); L = llr([x["ret"][h] for x in rec], m0, m1, s)
    src = [x["ret"][h] for x in fit]
    a1 = asn(src, m1, m0, m1, s); a0 = asn(src, m0, m0, m1, s); b1 = asn(src, m1, m0, m1, s, start=L); b0 = asn(src, m0, m0, m1, s, start=L)
    print(f"  {name}; sd {s:.3f}.  LLR on the 19 recent fires {L:+.2f}")
    print(f"     from zero (a fresh start at the next fire): if H1 true {a1[0]:.0f} fires on average (accepts H1 {a1[1]:.0%}); if H0 true {a0[0]:.0f} fires (accepts H1 {a0[1]:.0%})")
    print(f"     continuing from the recent LLR:              if H1 true {b1[0]:.0f} fires (accepts H1 {b1[1]:.0%}); if H0 true {b0[0]:.0f} fires (accepts H1 {b0[1]:.0%})")
    print(f"     at 7.7 fires a day: fresh {a1[0]/FPD:.1f} / {a0[0]/FPD:.1f} days; continuing {b1[0]/FPD:.1f} / {b0[0]/FPD:.1f} days")
