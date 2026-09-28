"""Q2: the guard-admitted class (fills 7-20% under the sizing) today, the running rule, and the slip re-read on data no one fit on:
Sep 28 09:40-21:00 (after K0-K3's read window closed). Rows: engine_replay --dump at slip 0.20 (the guard ratio is stored, so any slip
is re-applied here); second-place return at h11, $13, gas $0.33 a burst. Deep landings priced with e1_multi's E1_last (h15, $10)."""
import json, os, time, glob, statistics as st
H = os.path.dirname(os.path.abspath(__file__)); D = "/home/user/fomo-memebot/data/derived/live_vs_table"
TODAY = 1790588400   # Sep 28 09:40 UTC
FIT = (0, 1790208000); READ = (1790208000, TODAY); NEW = (TODAY, 2e9)
L = {}
for lf in glob.glob(f"{D}/launches_*.json"):
    try:
        for l in json.load(open(lf)): L[l["cv"].lower()] = l
    except Exception: pass
def res(cv, key):
    r = (L.get(cv) or {}).get("res") or {}; v = r.get(key); return v[0] if v else None
for view in ("k2", "k1reg", "kreg"):
    R = json.load(open(f"{H}/rows_{view}.json")); fired = [x for x in R if x.get("fired")]
    print(f"\n== view {view}: fired bursts by window, $ at $13 (fills) for each slip")
    print(f"{'slip':>5s} " + " ".join(f"{w:>22s}" for w in ("Sep 21-23", "Sep 24-28 09:40", "Sep 28 09:40-21:00")))
    for slip in (0.07, 0.10, 0.15, 0.20, 0.25, 0.30):
        cells = []
        for lo, hi in (FIT, READ, NEW):
            f = [x for x in fired if lo <= x["T0"] < hi]; usd = 0; n = 0
            for x in f:
                g = x.get("guard_ratio"); r = x["ret"].get("11")
                if g is not None and g < 1 - slip or r is None: usd -= 0.33
                else: usd += r * 13 - 0.33; n += 1
            cells.append(f"{usd:+8.2f} ({n:2d} of {len(f):2d})")
        print(f"{slip:5.2f} " + " ".join(f"{c:>22s}" for c in cells))
    if view == "k1reg":
        print("\ntoday's fired launches at the usual view: guard ratio (seat tokens / sized tokens), second-place h11, E1-last h15 ($10)")
        for x in fired:
            if x["T0"] >= TODAY:
                print(f"  {time.strftime('%H:%M', time.gmtime(x['T0']))} {x['cv'][:10]} ratio {x['guard_ratio'] if x['guard_ratio'] is None else round(x['guard_ratio'], 3)}  second {x['ret']['11']:+.1%}  E1_last {res(x['cv'], 'E1_last_h15_10') if res(x['cv'], 'E1_last_h15_10') is None else format(res(x['cv'], 'E1_last_h15_10'), '+.1%')}  {x['why']}")
        adm = [x for x in fired if x.get("guard_ratio") is not None and 0.80 <= x["guard_ratio"] < 0.93]
        for lab, (lo, hi) in (("Sep 21-23", FIT), ("Sep 24-28 09:40", READ), ("Sep 28 09:40-21:00", NEW)):
            v = [x["ret"]["11"] for x in adm if lo <= x["T0"] < hi and x["ret"].get("11") is not None]
            if v: print(f"  admitted class (ratio 0.80-0.93) at second place, {lab}: n={len(v)} mean {st.mean(v):+.1%} median {st.median(v):+.1%} win {sum(r > 0 for r in v)}/{len(v)}")
# the admitted class's own sequential test (H0 +2.5%, H1 +19%, sd 0.34, bounds +-2.94) on the one live admitted fill (15:36, -7.1% real)
m0, m1, sd = 0.025, 0.19, 0.34
llr = lambda xs: sum(((x - m0) ** 2 - (x - m1) ** 2) / (2 * sd * sd) for x in xs)
print(f"\nadmitted fills' sequential test after 15:36 (-7.1%): LLR {llr([-0.071]):+.2f} (bounds +-2.94); per fill at the class's week mean +15%: {llr([0.15]):+.3f}, so about {2.94 / llr([0.15]):.0f} fills to the upper bound at that mean")
