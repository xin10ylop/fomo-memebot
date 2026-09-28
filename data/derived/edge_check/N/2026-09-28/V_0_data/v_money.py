"""V_0: the $ of 6.8 over 6.7 by view, half, horizon and outsider mode; leave-one-out, sign counts, bootstrap."""
import json, os, sys, time, random, statistics as st, collections
sys.path.insert(0, "/home/user/fomo-memebot/data/derived/edge_check/N/2026-09-28/R1"); from common import usd, period, days, eligible
HERE = os.path.dirname(os.path.abspath(__file__)); R1 = "/home/user/fomo-memebot/data/derived/edge_check/N/2026-09-28/R1"
B = {r["cv"]: r for r in json.load(open(f"{HERE}/v_bundle_rows.json"))}
V = {v: {x["cv"]: x for x in json.load(open(f"{R1}/rows_{v}.json"))} for v in ("k2", "k1reg", "kreg")}
HZ = {"k2": "floor", "k1reg": "usual", "kreg": "usual"}   # what the feed has shown when that view's gate reads (kreg: the tick's own block is not yet shown at the gate)
def affected(cv, hz, mode):
    b7, c7, b8, c8 = B[cv][f"{hz}_{mode}"]; return b7 < 3 <= b8
def fires(v, hz, mode):
    return [V[v][c] for c in V[v] if V[v][c].get("fired") and affected(c, hz, mode)]
def line(f):
    u = [usd(y) for y in f]; return f"{len(f):2d} fires ${sum(u):+7.2f}"
print("=== 1. affected fires by horizon (what the feed had shown) and outsider mode, per view and half (guard 0.20, $13, gas $0.33)")
for v in ("k2", "k1reg", "kreg"):
    for hz in ("floor", "usual", "all"):
        for mode in ("A", "B"):
            f = fires(v, hz, mode); fit = [y for y in f if period(y["T0"]) == "fit"]; rd = [y for y in f if period(y["T0"]) == "read"]
            print(f"  {v:6s} horizon {hz:5s} mode {mode}: fit {line(fit)} ({sum(usd(y) for y in fit)/days('fit'):+.2f}/day) | read {line(rd)} ({sum(usd(y) for y in rd)/days('read'):+.2f}/day)")
print("\n=== 2. affected launches that reach the crowd gate (usual view rows), R1's horizon 'all' mode A vs the gate-time horizon")
for hz in ("floor", "usual", "all"):
    s = [c for c in V["k1reg"] if eligible(V["k1reg"][c]) and affected(c, hz, "A")]
    print(f"  horizon {hz}: {len(s)} launches")
diffset = [c for c in V["k1reg"] if affected(c, "all", "A") != affected(c, "usual", "A") and eligible(V["k1reg"][c])]
for c in diffset:
    y = V["k1reg"][c]; print(f"    differs: {time.strftime('%b %d %H:%M', time.gmtime(y['T0']))} {c[:10]} k {B[c]['k']} usual_A {B[c]['usual_A']} all_A {B[c]['all_A']} {y['why']}")
print("\n=== 3. the usual view's affected fires (gate-time horizon, mode A), each with its closer")
f = sorted(fires("k1reg", "usual", "A"), key=lambda y: y["T0"])
for y in f:
    cl = B[y["cv"]]["closer"]; bb = B[y["cv"]]["usual_B"]
    print(f"  {period(y['T0']):4s} {time.strftime('%b %d %H:%M', time.gmtime(y['T0']))} {y['cv'][:10]} ret {y['ret']['11']:+7.1%} ${usd(y):+6.2f} guard {y.get('guard_ratio') or 0:.3f} fleets {y.get('fleets')} "
          f"| 6.7 bundle A/B {B[y['cv']]['usual_A'][0]}/{bb[0]} | closer blk {cl[0]} ix {cl[1]} {cl[2][:10]} -> {cl[3][:10]} {cl[4]} {cl[5]}")
print("\n=== 4. robustness: leave the largest out, per view and half (gate-time horizon, mode A)")
for v in ("k2", "k1reg", "kreg"):
    f = fires(v, HZ[v], "A")
    for p in ("fit", "read"):
        u = sorted((usd(y) for y in f if period(y["T0"]) == p), reverse=True)
        if not u: print(f"  {v:6s} {p}: none"); continue
        print(f"  {v:6s} {p:4s}: n={len(u)} total ${sum(u):+.2f} largest ${u[0]:+.2f} -> without it ${sum(u[1:]):+.2f} ({sum(u[1:])/days(p):+.2f}/day); median ${st.median(u):+.2f}; wins {sum(x > 0 for x in u)}/{len(u)}")
    u = sorted((usd(y) for y in f), reverse=True)
    print(f"  {v:6s} week: n={len(u)} total ${sum(u):+.2f}, without the week's largest ${sum(u[1:]):+.2f}, without the two largest ${sum(u[2:]):+.2f}")
print("\n=== 5. is the read half distinguishable from zero? (usual view, gate-time horizon, mode A)")
random.seed(7)
for v in ("k2", "k1reg", "kreg"):
    for p in ("fit", "read", "all"):
        u = [usd(y) for y in fires(v, HZ[v], "A") if p == "all" or period(y["T0"]) == p]
        if len(u) < 2: print(f"  {v:6s} {p:4s}: n={len(u)}"); continue
        m = st.mean(u); se = st.stdev(u) / len(u) ** 0.5
        bs = sorted(sum(random.choice(u) for _ in u) for _ in range(20000)); lo, hi = bs[int(0.05 * len(bs))], bs[int(0.95 * len(bs))]
        pneg = sum(1 for x in bs if x <= 0) / len(bs)
        print(f"  {v:6s} {p:4s}: n={len(u):2d} mean ${m:+.2f}/fire, t={m/se:+.2f}; bootstrap 90% of the total ${lo:+.2f} .. ${hi:+.2f}; P(total<=0) {pneg:.2f}")
