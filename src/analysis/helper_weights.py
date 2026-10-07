"""helper_weights.py (6.23, runbook 5bd): the helpers' reputation table for the engine's reputation floor, refit from the chain-side
pieces like smart_helpers.py. For every relay contract that attacked qualifying launches before the tick (blocks 1..k-1) over the
trailing window: n and the weight w = sum(min(r, 1)) / (n + 4), r the seat's behind-one hold-11 return of each attacked launch
(kept when n >= MIN_N; negative and small weights kept). rep_sum of a launch = the sum of its attackers' weights; rep_min = the
median rep_sum of the window's live-gate passes (grouped fleets >= 3 by k-1, the sprayers of data/derived/sprayers.json as one),
computed with this table (one refit late against the walk-forward study, which found the rule keeps most of its gain a day stale).

    python3 src/analysis/helper_weights.py [--days 7] [--min-n 4] [--attack-min 3] [--out data/derived/helper_weights.json]

Growth review Oct 7 (walk-forward Sep 27 - Oct 7, behind three buys at the live stake): the live gate $3.96 a fire, the gate plus
the floor $7.98 (se 3.27), win rate 50% -> 70%, 61% of the fires kept; the dropped set -$70 (21 fills, 5 wins)."""
import glob, re, json, gzip, sys, time, statistics as st, collections, os
args = sys.argv[1:]
def arg(k, d): return args[args.index(k) + 1] if k in args else d
DAYS = float(arg("--days", "7")); MIN_N = int(arg("--min-n", "4")); ATTACK_MIN = int(arg("--attack-min", "3")); OUT = arg("--out", "data/derived/helper_weights.json")
OURS = {"0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
try: GROUP = {a.lower() for a in json.load(open("data/derived/sprayers.json")).get("sprayers") or ()}
except Exception: GROUP = set()
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
        blocks = c.get("blocks", []); token = (c.get("token") or "").lower(); creator = (c.get("creator") or "").lower()
        helpers = {t["to"].lower() for bi, blk in enumerate(blocks[:k]) if bi for t in blk if not t.get("direct") and not t.get("named_fr") and not t.get("named_data") and t.get("to")}
        # the engine's fleet count by k-1 with the registration block (engine_replay.fleets): relay targets naming no named wallet, direct senders
        j = next((i for i, blk in enumerate(blocks) if any(t.get("named_fr") or t.get("named_data") for t in blk)), None)
        targets, senders = set(), set()
        if j is not None:
            for bi in range(j, k):
                for t in blocks[bi]:
                    to = (t.get("to") or "").lower(); fr = (t.get("fr") or "").lower()
                    if to in OURS or fr in OURS or to == token: continue
                    if t.get("direct"):
                        if not t.get("named_fr") and fr != creator: senders.add(fr)
                    elif not t.get("named_data"): targets.add(to)
        fl = len(targets - GROUP) + len(senders) + (1 if targets & GROUP else 0)
        rows[m.group(2)] = (g["T0"], helpers, g["behind1_13_h11"], fl, targets)
rec = collections.defaultdict(list)
for T0, helpers, r, fl, targets in rows.values():
    for h in helpers: rec[h].append(r)
weights = {h: round(sum(min(x, 1.0) for x in v) / (len(v) + 4), 4) for h, v in rec.items() if len(v) >= MIN_N}
stats = {h: {"n": len(rec[h]), "mean": round(st.mean(rec[h]), 4), "w": weights[h]} for h in weights}
passes = [sum(weights.get(t, 0.0) for t in targets) for T0, helpers, r, fl, targets in rows.values() if fl >= ATTACK_MIN]
rep_min = round(st.median(passes), 4) if passes else 0.0
out = {"fitted": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "window_days": DAYS, "min_n": MIN_N, "launches": len(rows), "helpers_seen": len(rec),
       "weights": dict(sorted(weights.items(), key=lambda kv: -kv[1])), "stats": stats, "rep_min": rep_min, "passes": len(passes)}
os.makedirs(os.path.dirname(OUT), exist_ok=True); json.dump(out, open(OUT, "w"), indent=1)
print(f"{len(rows)} launches over {DAYS:.0f} days, {len(rec)} helpers seen, {len(weights)} weighted; gate passes {len(passes)}, rep_min {rep_min:.3f} -> {OUT}")
for h, w in list(out["weights"].items())[:12]: print(f"   {h} n {stats[h]['n']:3d} mean {100*stats[h]['mean']:+6.1f}% w {w:+.3f}")
