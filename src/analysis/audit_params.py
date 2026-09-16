"""Audit every knob against the four days the rule has never seen (Sep 12-16), plus the hours question.
Nothing here is fitted: each row is the same replay with one setting changed, judged on the out-of-sample days."""
import sys, statistics as st, collections, datetime, random
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX; OOS = "2026-09-12"
data = RH.load(); data.update(RH.load_new())
def ci(xs, n=3000):
    if len(xs) < 15: return float("nan"), float("nan")
    random.seed(5); b = sorted(st.mean(random.choice(xs) for _ in xs) for _ in range(n)); return b[int(0.025*n)], b[int(0.975*n)]
# one pass: keep the launch objects for the out-of-sample days so the sweeps can re-replay them
keep = []
for k in sorted(data):
    for cv, (L, f) in data[k].items():
        d = datetime.datetime.fromtimestamp(L["ts"], datetime.timezone.utc)
        keep.append((d.strftime("%Y-%m-%d") >= OOS, d.hour, L, f))
print(f"launches loaded: {sum(1 for o, _, _, _ in keep if o)} out of sample, {sum(1 for o, _, _, _ in keep if not o)} before\n")
def run(rows, hold=5.0, tp=0.5, frac=0.03, clean_only=True, min_eth=0.3, min_n=3, min_tk0=0.01, wait=0.3, stake=25):
    out = []
    for oos, hour, L, f in rows:
        if f["bundle_n"] < min_n or f["bundle_eth"] < min_eth or f["tk0"] < min_tk0: continue
        if clean_only and (f["out1_n"] > 0 or RH.G_WAIT(wait)(f)): continue
        x = RH.replay(L, stake / PX, hold=hold, tp=tp, frac=frac)
        if x[1] <= 1e-6 or x[4] == "reverted": continue
        out.append(((x[0] * PX - 0.10) / (x[1] * PX), hour, L["ts"]))
    return out
oos_rows = [r for r in keep if r[0]]
base = run(oos_rows)
print("=== 1. HOURS (out of sample, clean seats)")
byh = collections.defaultdict(list)
for roi, h, _ in base: byh[h].append(roi)
print(f"{'hour UTC':9s} {'n':>5s} {'mean':>7s} {'win':>5s} {'<-40%':>6s}   {'total $ at $25':>14s}")
for h in sorted(byh):
    v = byh[h]
    print(f"   {h:02d}:00  {len(v):5d} {100*st.mean(v):+6.1f}% {100*sum(1 for x in v if x>0)/len(v):4.0f}% {100*sum(1 for x in v if x<-0.4)/len(v):5.0f}% {25*sum(v):+14.0f}")
miss = [h for h in range(24) if h not in byh]
print(f"   hours with no data at all: {miss}")
blocks = {"12-18": range(12, 18), "18-24": range(18, 24), "00-06": range(0, 6), "06-12": range(6, 12)}
print(f"\n{'block':9s} {'n':>5s} {'mean':>7s} {'win':>5s} {'$ at $25':>9s} {'95% interval':>20s}")
for name, rng in blocks.items():
    v = [r for r, h, _ in base if h in rng]
    lo, hi = ci(v)
    print(f"   {name:6s} {len(v):5d} {100*st.mean(v) if v else 0:+6.1f}% {100*sum(1 for x in v if x>0)/len(v) if v else 0:4.0f}% {25*sum(v):+9.0f} {('[%+.1f%%, %+.1f%%]' % (100*lo, 100*hi)) if lo == lo else 'too few':>20s}")
print("\n=== 2. EVERY KNOB, one at a time, on the out-of-sample days")
print(f"{'setting':34s} {'n':>5s} {'mean':>7s} {'median':>7s} {'win':>5s} {'<-40%':>6s} {'$ at $25':>9s} {'95% interval':>20s}")
def show(label, v):
    lo, hi = ci([x[0] for x in v]) if v else (float("nan"), float("nan")); r = [x[0] for x in v]
    print(f"{label:34s} {len(r):5d} {100*st.mean(r) if r else 0:+6.1f}% {100*st.median(r) if r else 0:+6.1f}% {100*sum(1 for x in r if x>0)/len(r) if r else 0:4.0f}% "
          f"{100*sum(1 for x in r if x<-0.4)/len(r) if r else 0:5.0f}% {25*sum(r):+9.0f} {('[%+.1f%%, %+.1f%%]' % (100*lo, 100*hi)) if lo == lo else '':>20s}")
show("as it runs now", base)
for hold in (3.0, 4.0, 6.0, 7.0): show(f"  hold {hold:.0f}s instead of 5", run(oos_rows, hold=hold))
for tp in (0.0, 0.25, 0.35, 0.75): show(f"  take-profit {tp:.2f} instead of 0.50", run(oos_rows, tp=tp if tp > 0 else None))
for fr in (0.015, 0.02, 0.04, 0.05): show(f"  size {100*fr:.1f}% of supply not 3%", run(oos_rows, frac=fr))
for tk in (0.02, 0.03, 0.04, 0.05): show(f"  creator holds >= {100*tk:.0f}% not 1%", run(oos_rows, min_tk0=tk))
for me in (0.5, 0.8, 1.0): show(f"  team ETH >= {me} not 0.3", run(oos_rows, min_eth=me))
for mn in (4, 5, 6, 8): show(f"  team wallets >= {mn} not 3", run(oos_rows, min_n=mn))
for w in (0.15, 0.5, 0.8): show(f"  wait {w}s in the seat not 0.3", run(oos_rows, wait=w))
show("  no seat check at all (any bundled)", run(oos_rows, clean_only=False))
