"""Out of sample: fit nothing on Sep 12-16, then ask three questions of those four days.
  1. pooled, do the clean seats still pay, and by how much, with an interval;
  2. what would the engine as it stands (hours 12-05, demand floor, switch, one position at a time, $25) have made from $62;
  3. do the candidate filters found on Sep 9-11 hold up on days they have never seen? (every candidate reported, no picking)"""
import sys, statistics as st, collections, datetime, random
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX; FIT_END = "2026-09-12"          # everything before this is the fit period; Sep 12 onward is untouched
data = RH.load(); data.update(RH.load_new())
def follow(L, a, b): return sum(r[2] for r in L["rows"] if r[1] == "B" and a <= r[0] < b)
recs = []
for k in sorted(data):
    for cv, (L, f) in data[k].items():
        x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5)
        if x[1] <= 1e-6 or x[4] == "reverted":
            continue
        ts = L["ts"]; d = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
        recs.append(dict(day=d.strftime("%m-%d"), hour=d.hour, t=ts + x[2], t_exit=ts + x[3], t_score=ts + x[3] + 20,
                         roi=(x[0] * PX - 0.10) / (x[1] * PX), feth=follow(L, x[2], x[3]),
                         clean=f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f), eth=f["bundle_eth"], n=f["bundle_n"], tk0=f["tk0"],
                         oos=d.strftime("%Y-%m-%d") >= FIT_END))
recs.sort(key=lambda r: r["t"])
oos = [r for r in recs if r["oos"] and r["clean"]]
fit = [r for r in recs if not r["oos"] and r["clean"]]
def ci(xs, n=4000):
    random.seed(3); b = sorted(st.mean(random.choice(xs) for _ in xs) for _ in range(n)); return b[int(0.025 * n)], b[int(0.975 * n)]
lo, hi = ci([r["roi"] for r in oos])
print(f"=== 1. Sep 12-16, every clean seat, never looked at before today: n {len(oos)}, mean {100*st.mean(r['roi'] for r in oos):+.1f}%, "
      f"median {100*st.median(r['roi'] for r in oos):+.1f}%, win {100*sum(1 for r in oos if r['roi']>0)/len(oos):.0f}%, "
      f"95% interval [{100*lo:+.1f}%, {100*hi:+.1f}%] -> " + ("the edge is there" if lo > 0 else "cannot tell it from zero"))
print(f"    for comparison, the fit period (to Sep 11): n {len(fit)}, mean {100*st.mean(r['roi'] for r in fit):+.1f}%")

# 2. the engine as it stands, from $62
def path(rows, start=62.0, frac=0.15, cap=25.0, floor=0.10, arm=10, switch_n=15, switch=-0.10, hours=True, filt=None):
    bank = start; busy = -1e9; taken = []; blocked = collections.Counter(); peak = start; dd = 0.0
    for i, r in enumerate(rows):
        if not r["clean"]:
            continue
        if hours and not (r["hour"] >= 12 or r["hour"] < 5):
            blocked["hours"] += 1; continue
        past = [y for y in rows[:i] if y["clean"] and y["t_score"] <= r["t"]]
        tm = [y["feth"] for y in past][-60:]
        if len(tm) < arm:
            blocked["floor not armed"] += 1; continue
        if st.mean(tm) < floor:
            blocked["demand floor"] += 1; continue
        sc = [y["roi"] for y in past][-switch_n:]
        if len(sc) >= switch_n and st.mean(sc) < switch:
            blocked["switch off"] += 1; continue
        if r["t"] < busy:
            blocked["position open"] += 1; continue
        if filt and not filt(r):
            blocked["filter"] += 1; continue
        stake = min(max(bank * frac, 25.0), min(cap, bank))
        bank += stake * r["roi"]; busy = r["t_exit"]; taken.append(r["roi"]); peak = max(peak, bank); dd = max(dd, 1 - bank / peak)
    return bank, taken, dd, blocked
rows_oos = [r for r in recs if r["oos"]]
bank, taken, dd, blocked = path(rows_oos)
print(f"\n=== 2. the engine as it stands, Sep 12-16, $25 stakes from $62: {len(taken)} trades, mean {100*st.mean(taken) if taken else 0:+.1f}%, "
      f"end ${bank:,.0f} ({bank-62:+,.0f}), worst drawdown {100*dd:.0f}%")
print("    launches it would have skipped: " + ", ".join(f"{k} {v}" for k, v in blocked.most_common()))
for d in sorted({r["day"] for r in rows_oos}):
    b2, tk, _, _ = path([r for r in rows_oos if r["day"] == d], start=62.0)
    print(f"      {d}: {len(tk):3d} trades {25*sum(tk):+7.0f} $ at a flat $25")

# 3. candidate filters, fitted on Sep 9-11, judged on Sep 12-16
print("\n=== 3. filters found on Sep 9-11, tested on Sep 12-16 (all candidates shown, none picked afterwards)")
cands = [("no filter (the rule as it is)", lambda r: True),
         ("team ETH under 0.8", lambda r: r["eth"] < 0.8),
         ("team ETH 0.3 to 0.8", lambda r: 0.3 <= r["eth"] < 0.8),
         ("team ETH under 1.2", lambda r: r["eth"] < 1.2),
         ("at most 12 team wallets", lambda r: r["n"] <= 12),
         ("creator holds 3% or more", lambda r: r["tk0"] >= 0.03),
         ("team ETH under 0.8 and at most 12 wallets", lambda r: r["eth"] < 0.8 and r["n"] <= 12)]
late_fit = [r for r in fit if r["day"] >= "09-09"]
print(f"{'filter':44s} {'fit Sep 9-11':>22s} {'OUT OF SAMPLE Sep 12-16':>30s}")
print(f"{'':44s} {'n':>6s} {'mean':>7s} {'win':>6s} {'n':>6s} {'mean':>7s} {'win':>6s} {'95% interval':>18s}")
for name, fn in cands:
    a = [r["roi"] for r in late_fit if fn(r)]; b = [r["roi"] for r in oos if fn(r)]
    l, h = ci(b) if len(b) > 20 else (float("nan"), float("nan"))
    print(f"{name:44s} {len(a):6d} {100*st.mean(a) if a else 0:+6.1f}% {100*sum(1 for x in a if x>0)/len(a) if a else 0:5.0f}% "
          f"{len(b):6d} {100*st.mean(b) if b else 0:+6.1f}% {100*sum(1 for x in b if x>0)/len(b) if b else 0:5.0f}% "
          f"{('[%+.1f%%, %+.1f%%]' % (100*l, 100*h)) if l == l else '':>18s}")

# 4. which configuration actually makes the most money over those four days, and what it risks from $62
print("\n=== 4. the four days as money, from $62 at a flat $25, one position at a time")
print(f"{'configuration':44s} {'trades':>7s} {'mean':>7s} {'end $':>8s} {'profit':>8s} {'worst drawdown':>15s}")
for name, fn in cands:
    b, tk, dd, _ = path(rows_oos, filt=None if name.startswith("no filter") else fn)
    print(f"{name:44s} {len(tk):7d} {100*st.mean(tk) if tk else 0:+6.1f}% {b:8,.0f} {b-62:+8,.0f} {100*dd:14.0f}%")
# ruin: the same four days, but the order of trades reshuffled, to see how often $62 does not survive
best = [r for r in rows_oos if r["clean"]]
random.seed(9); ruin = 0; ends = []
for _ in range(2000):
    bank = 62.0; seq = [r["roi"] for r in best]; random.shuffle(seq); day_start = bank; n = 0
    for roi in seq:
        if bank < 25:
            ruin += 1; break
        bank += 25 * roi; n += 1
        if n % 110 == 0:                                   # a day's worth of trades: the daily stop
            if bank < 0.5 * day_start:
                bank = bank; break
            day_start = bank
    ends.append(bank)
ends.sort()
print(f"\nreshuffling the same four days 2000 times from $62 at $25: ends ${ends[len(ends)//2]:,.0f} median, "
      f"${ends[100]:,.0f} at the 5th percentile, ${ends[-100]:,.0f} at the 95th; ran out of money {100*ruin/2000:.1f}% of the time")
