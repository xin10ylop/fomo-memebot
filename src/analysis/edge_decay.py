"""Was it a sudden death or a decay, and could six losing trades be luck?

Per calendar day, from the chain: team launches, the share with a bot ahead of our seat, how many seats were left clean,
what the clean ones paid our seat and the front seat, and the buyers behind them. Then two tests against the question
"what are the odds the edge stopped exactly when we went live":
  1. is the crowding a trend or a break? (linear fit, and the day-by-day series)
  2. under the old distribution, how likely is a run of five losing trades, and how far is the September 10-12 sample mean?"""
import sys, statistics as st, collections, random, datetime
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
PX = RH.PX
data = RH.load(); data.update(RH.load_new())
def follow_eth(L, a, b): return sum(r[2] for r in L["rows"] if r[1] == "B" and a <= r[0] < b)
days = collections.defaultdict(lambda: dict(bundled=0, crowded=0, clean=[], feth=[], e1=[], hours=set()))
for k in sorted(data):
    for cv, (L, f) in data[k].items():
        d = datetime.datetime.fromtimestamp(L["ts"], datetime.timezone.utc).strftime("%m-%d")
        D = days[d]; D["bundled"] += 1; D["hours"].add(k[1])
        if f["out1_n"] > 0:
            D["crowded"] += 1
        x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5)
        if x[1] <= 1e-6 or x[4] == "reverted":
            continue
        roi = (x[0] * PX - 0.10) / (x[1] * PX)
        x1 = RH.replay(L, 25 / PX, hold=5.0, tp=0.5, entry="E1")
        if x1[1] > 1e-6 and x1[4] != "reverted":
            D["e1"].append((x1[0] * PX - 0.10) / (x1[1] * PX))
        if f["out1_n"] == 0 and not RH.G_WAIT(0.3)(f):
            D["clean"].append(roi); D["feth"].append(follow_eth(L, x[2], x[3]))
print(f"{'day':6s} {'blocks':16s} {'team':>5s} {'bot ahead':>9s} {'clean':>6s} {'clean/h':>7s} {'mean':>7s} {'median':>7s} {'win%':>5s} {'<-40%':>6s} {'buyers':>7s} {'E1 front':>9s}")
rows = []
for d in sorted(days):
    D = days[d]; c = D["clean"]; hrs = 6 * len(D["hours"])
    if not D["bundled"]:
        continue
    crowd = D["crowded"] / D["bundled"]
    print(f"{d:6s} {','.join(sorted(D['hours'])):16s} {D['bundled']:5d} {100*crowd:8.0f}% {len(c):6d} {len(c)/hrs if hrs else 0:7.1f} "
          f"{100*st.mean(c) if c else 0:+6.1f}% {100*st.median(c) if c else 0:+6.1f}% {100*sum(1 for x in c if x > 0)/len(c) if c else 0:4.0f}% "
          f"{100*sum(1 for x in c if x < -0.4)/len(c) if c else 0:5.0f}% {st.mean(D['feth']) if D['feth'] else 0:7.3f} {100*st.mean(D['e1']) if D['e1'] else 0:+8.1f}%")
    rows.append((d, crowd, len(c) / hrs if hrs else 0, st.mean(c) if c else None, len(c)))
# 1. trend or break
xs = list(range(len(rows))); ys = [r[1] for r in rows]
mx, my = st.mean(xs), st.mean(ys)
slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
print(f"\ncrowding: {100*ys[0]:.0f}% on {rows[0][0]} -> {100*ys[-1]:.0f}% on {rows[-1][0]}; straight-line fit {100*slope:+.1f} points per measured day")
print("day-by-day: " + " ".join(f"{r[0]}:{100*r[1]:.0f}%" for r in rows))
print("clean seats an hour: " + " ".join(f"{r[0]}:{r[2]:.0f}" for r in rows))
# 2. could the live run be luck?
old = [x for d, D in days.items() if d < "09-08" for x in D["clean"]]
recent = [x for d, D in days.items() if d >= "09-10" for x in D["clean"]]
if old and recent:
    wr = sum(1 for x in old if x > 0) / len(old)
    print(f"\nthe old distribution (before 09-08, n={len(old)}): mean {100*st.mean(old):+.1f}%, median {100*st.median(old):+.1f}%, win rate {100*wr:.0f}%")
    print(f"the recent one (09-10 onward, n={len(recent)}): mean {100*st.mean(recent):+.1f}%, median {100*st.median(recent):+.1f}%, win rate {100*sum(1 for x in recent if x > 0)/len(recent):.0f}%")
    random.seed(1); runs = sum(1 for _ in range(200000) if all(random.choice(old) < 0 for _ in range(5)))
    print(f"P(five trades in a row all losing | the old distribution) = {100*runs/200000:.2f}%   [we saw five clean live trades, all losing]")
    sd = st.pstdev(old); se = sd / len(recent) ** 0.5
    print(f"the recent sample mean is {(st.mean(recent) - st.mean(old)) / se:+.1f} standard errors from the old mean "
          f"(old {100*st.mean(old):+.1f}%, recent {100*st.mean(recent):+.1f}%, n={len(recent)}, sd={sd:.2f})")
    top = sorted(old, reverse=True); share = sum(top[:max(1, len(top) // 20)]) / sum(top) if sum(top) > 0 else 0
    print(f"was the old edge carried by outliers? the best 5% of trades are {100*share:.0f}% of the total profit; "
          f"drop them and the mean is {100*st.mean(top[max(1, len(top)//20):]):+.1f}%")
