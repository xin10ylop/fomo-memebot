"""smart_helpers.py: the bot software (helper contracts) whose attacked launches paid, refitted from the chain-side pieces (runbook 5am).
A helper is 'smart' when, over the trailing window, it attacked at least MIN_N qualifying launches before the tick and those paid
more than MIN_MEAN at the seat behind one, hold 11. The engine boosts the stake when one of them is attacking at fire time.

    python3 src/analysis/smart_helpers.py [--days 7] [--min-n 4] [--min-mean 0.05] [--out data/derived/smart_helpers.json]

Walk-forward Sep 26-30 (report 24.50): $50 on the boosted fills against $25 flat, +$470 against +$257 over the same 52 fills."""
import glob, re, json, gzip, sys, time, statistics as st, collections
args = sys.argv[1:]
def arg(k, d): return args[args.index(k) + 1] if k in args else d
DAYS = float(arg("--days", "7")); MIN_N = int(arg("--min-n", "4")); MIN_MEAN = float(arg("--min-mean", "0.05")); OUT = arg("--out", "data/derived/smart_helpers.json")
D = "data/derived/live_vs_table"; cut = time.time() - DAYS * 86400; rows = {}
for pf in sorted(glob.glob(f"{D}/prediction_*.txt")):
    n = pf.split("prediction_")[1][:-4]
    try:
        grid = {g["cv"][:10]: g for g in json.load(open(f"{D}/hold_grid_week_{n}.json"))}; crowd = {c["cv"][:10]: c for c in json.load(gzip.open(f"{D}/crowd_raw_{n}.json.gz", "rt"))}
    except Exception:
        continue
    for line in open(pf):
        m = re.match(r"(\w{3} \d+ \d\d:\d\d)\s+(0x[0-9a-f]{8})\s+(\d+)", line)
        if not m or m.group(2) not in grid or m.group(2) not in crowd: continue
        g = grid[m.group(2)]; c = crowd[m.group(2)]; k = int(m.group(3))
        if "behind1_13_h11" not in g or g["T0"] < cut: continue
        helpers = {t["to"].lower() for bi, blk in enumerate(c.get("blocks", [])[:k]) if bi for t in blk if not t.get("named_fr") and not t.get("named_data")}
        rows[m.group(2)] = (g["T0"], helpers, g["behind1_13_h11"])
rec = collections.defaultdict(list)
for T0, helpers, r in rows.values():
    for h in helpers: rec[h].append(r)
smart = {h: {"n": len(v), "mean": round(st.mean(v), 4), "pos": round(sum(1 for x in v if x > 0) / len(v), 2)} for h, v in rec.items() if len(v) >= MIN_N and st.mean(v) > MIN_MEAN}
out = {"fitted": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "window_days": DAYS, "min_n": MIN_N, "min_mean": MIN_MEAN, "launches": len(rows), "helpers_seen": len(rec), "helpers": dict(sorted(smart.items(), key=lambda kv: -kv[1]["n"]))}
json.dump(out, open(OUT, "w"), indent=1)
print(f"{len(rows)} launches over {DAYS:.0f} days, {len(rec)} helpers seen, {len(smart)} smart -> {OUT}")
for h, v in list(out["helpers"].items())[:12]: print(f"   {h} n {v['n']:3d} mean {100*v['mean']:+6.1f}% pos {100*v['pos']:.0f}%")
