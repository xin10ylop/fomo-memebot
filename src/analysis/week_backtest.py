"""week_backtest.py: the last seven days through the readings' own pipeline, day by day (report 24.41). Every piece of the week
(the windows' launches/crowd/hold-grid files, the gaps scanned on Sep 28), the engine's count of fleets at k-2 after the curve's
registration (predict_window's `eng`), the second-place return at the hold, priced at $13 after gas, with and without the
3.0 ETH bundle cap. Launches are deduplicated across overlapping pieces; hours covered are the union of the pieces' spans.

    python3 src/analysis/week_backtest.py [--from "2026-09-21 09:40"] [--to "2026-09-28 09:40"]"""
import json, gzip, os, sys, math, time, calendar, glob, statistics as st, collections
sys.argv_saved = list(sys.argv); args = sys.argv[1:]
def arg(k, d):
    if k in args: i = args.index(k); v = args[i + 1]; del args[i:i + 2]; return v
    return d
T0 = calendar.timegm(time.strptime(arg("--from", "2026-09-21 09:40"), "%Y-%m-%d %H:%M")); T1 = calendar.timegm(time.strptime(arg("--to", "2026-09-28 09:40"), "%Y-%m-%d %H:%M"))
sys.argv = ["x", "0.76", "0.71"]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "crowd_rules.py")).read().split("rules = [")[0])   # cums, view, at, US, STAKE, GAS
D = "data/derived/live_vs_table"; E = "data/derived"
CAP = 3.0
# the pieces: name -> (launches file, crowd file, hold grid file, span (lo, hi) from the scan or the known window)
def span_of(name):
    for f in glob.glob(f"{E}/*/e1m_{name}.json"):
        d = json.load(open(f)); return d["t_lo"], d["t_hi"]
    return None
KNOWN = {"sep2021": ("2026-09-20 13:26", "2026-09-22 01:02"), "sep2223": ("2026-09-22 01:02", "2026-09-23 06:35"), "sep23day": ("2026-09-23 10:22", "2026-09-23 20:20"), "sep24_paper": ("2026-09-24 12:38", "2026-09-24 21:36"), "sep24": ("2026-09-24 12:38", "2026-09-24 21:36")}
CROWD_ALIAS = {"sep24_paper": "sep24paper"}
pieces = []
for lf in sorted(glob.glob(f"{D}/launches_*.json")):
    n = os.path.basename(lf)[9:-5]
    if n in ("141_creators", "175_sep2223", "oos_sep2021", "today_sep23", "sep1819"): continue
    cf = f"{D}/crowd_raw_{CROWD_ALIAS.get(n, n)}.json.gz"
    if not os.path.exists(cf): cf = f"{D}/crowd_raw_{CROWD_ALIAS.get(n, n)}.json"
    if not os.path.exists(cf): continue
    hg = f"{D}/hold_grid_week_{n}.json" if os.path.exists(f"{D}/hold_grid_week_{n}.json") else (f"{D}/hold_grid_{n}.json" if os.path.exists(f"{D}/hold_grid_{n}.json") else None)
    sp = span_of(n) or (KNOWN.get(n) and tuple(calendar.timegm(time.strptime(x, "%Y-%m-%d %H:%M")) for x in KNOWN[n]))
    if not sp: continue
    if sp[1] < T0 or sp[0] > T1: continue
    pieces.append((n, lf, cf, hg, sp))
def eng_count(r):
    cw, cf = cums(r); k = r["k"]
    j = next((i for i, rw in enumerate(r["blocks"]) if any(t.get("named_fr") or t.get("named_data") for t in rw)), -1)
    fe = set()
    for off, rw in enumerate(r["blocks"][: max(0, k - 1)]):
        if off <= j: continue
        for t in rw:
            if t["to"] in US or t["to_token"] or t["fr"] in US: continue
            if t["direct"]:
                if not t["named_fr"]: fe.add(t["fr"])
            elif not t["named_data"]: fe.add(t["to"])
    return len(fe), at(cf, k - 2), at(cf, k - 1)
rows = {}; cover = []
for n, lf, cf, hg, sp in pieces:
    L = {l["cv"].lower(): l for l in json.load(open(lf))}
    R = json.load(gzip.open(cf, "rt")) if cf.endswith(".gz") else json.load(open(cf))
    H = {h["cv"].lower(): h for h in json.load(open(hg))} if hg else {}
    cover.append((max(sp[0], T0), min(sp[1], T1), n))
    for r in R:
        cv = r["cv"].lower(); l = L.get(cv)
        if not l or not (T0 <= l["T0"] <= T1): continue
        h = H.get(cv, {})
        def g(key):
            x = h.get(key); return None if x is None or (isinstance(x, float) and math.isnan(x)) else x
        eng, k2, k1 = eng_count(r)
        rec = {"cv": cv, "T0": l["T0"], "piece": n, "bundle": l.get("bundle_eth", 0.0), "eng": eng, "k2": k2, "k1": k1, "h11": g("behind1_15_h11"), "h15": g("behind1_15_h15"), "h9": g("behind1_15_h9"), "h13": g("behind1_15_h13")}
        if cv not in rows or (rows[cv]["h11"] is None and rec["h11"] is not None): rows[cv] = rec
rows = sorted(rows.values(), key=lambda r: r["T0"])
# hours covered per day: union of the pieces' spans
def day(t): return time.strftime("%b %d", time.gmtime(t))
cover.sort(); merged = []
for lo, hi, n in cover:
    if merged and lo <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], hi)
    else: merged.append([lo, hi])
hours = collections.Counter()
for lo, hi in merged:
    t = lo
    while t < hi:
        nxt = min(hi, (t // 86400 + 1) * 86400); hours[day(t)] += (nxt - t) / 3600; t = nxt
def line(name, rs, hold):
    v = [r[hold] for r in rs if r[hold] is not None]
    if not v: return f"{name:34s} {len(rs):3d} fires (no {hold} column yet)"
    usd = [x * STAKE - GAS for x in v]
    return f"{name:34s} {len(v):3d} fires  mean {st.mean(v):+6.1%}  median {st.median(v):+6.1%}  win {sum(x > 0 for x in v) / len(v):3.0%}  dead {sum(x < -0.4 for x in v) / len(v):3.0%}  ${sum(usd):+8.2f} at ${STAKE:.0f} after gas"
print(f"week {time.strftime('%b %d %H:%M', time.gmtime(T0))} - {time.strftime('%b %d %H:%M', time.gmtime(T1))} UTC: {len(rows)} qualifying launches over {sum(hours.values()):.0f} covered hours of {(T1 - T0) / 3600:.0f}; pieces: {', '.join(p[0] for p in pieces)}")
gaps = []; cur = T0
for lo, hi in merged:
    if lo > cur + 300: gaps.append((cur, lo))
    cur = max(cur, hi)
if cur < T1 - 300: gaps.append((cur, T1))
if gaps: print("uncovered: " + "; ".join(f"{time.strftime('%b %d %H:%M', time.gmtime(a))}-{time.strftime('%b %d %H:%M', time.gmtime(b))}" for a, b in gaps))
print(f"\n{'day':7s} {'hours':>5s} {'launches':>8s} {'k-2':>4s} {'eng':>4s} {'eng<=cap':>8s}  {'h11 mean':>9s} {'win':>4s}  {'h15 mean':>9s}  {'$ h11':>8s}  {'fires/24h':>9s}")
days = sorted(set(day(r["T0"]) for r in rows) | set(hours), key=lambda d: time.strptime(d + " 2026", "%b %d %Y"))
for d in days:
    rs = [r for r in rows if day(r["T0"]) == d]; fe = [r for r in rs if r["eng"] >= 2]; fc = [r for r in fe if r["bundle"] <= CAP]
    v11 = [r["h11"] for r in fc if r["h11"] is not None]; v15 = [r["h15"] for r in fc if r["h15"] is not None]
    hrs = hours.get(d, 0.0)
    print(f"{d:7s} {hrs:5.1f} {len(rs):8d} {sum(r['k2'] >= 2 for r in rs):4d} {len(fe):4d} {len(fc):8d}  {(st.mean(v11) if v11 else float('nan')):+9.1%} {(sum(x > 0 for x in v11) / len(v11) if v11 else float('nan')):4.0%}  {(st.mean(v15) if v15 else float('nan')):+9.1%}  {sum(x * STAKE - GAS for x in v11):+8.2f}  {(len(fc) / hrs * 24 if hrs else float('nan')):9.1f}")
fe = [r for r in rows if r["eng"] >= 2]; fc = [r for r in fe if r["bundle"] <= CAP]
print()
for hold in ("h9", "h11", "h13", "h15"):
    print(line(f"engine count, cap 3.0, {hold}", fc, hold))
print(line("engine count, no cap, h11", fe, "h11"))
print(line("tables' count (k-2), cap, h11", [r for r in rows if r["k2"] >= 2 and r["bundle"] <= CAP], "h11"))
tot_h = sum(hours.values())
print(f"\nrate: {len(fc)} engine fires (cap) in {tot_h:.0f} covered hours = {len(fc) / tot_h * 24:.1f} a day; at $13 and full fill ${sum(r['h11'] * STAKE - GAS for r in fc if r['h11'] is not None) / tot_h * 24:+.2f} a day (h11)")
big = sorted((r for r in fc if r["h11"] is not None), key=lambda r: -r["h11"])[:5]
print("largest fires at h11: " + ", ".join(f"{time.strftime('%b %d %H:%M', time.gmtime(r['T0']))} {r['cv'][:10]} {r['h11']:+.0%}" for r in big))
if big: 
    rest = [r["h11"] for r in fc if r["h11"] is not None and r["cv"] != big[0]["cv"]]
    print(f"without the largest: mean {st.mean(rest):+.1%} on {len(rest)} fires" if rest else "")
