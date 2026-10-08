"""aim_skips.py (6.24, runbook 5bg): price the launches the burst's aim rule refused before the gate (5.62: the aim passed, logged as
"no confident boundary estimate"). Input: a list of the box's skips (time, curve prefix, boundary, since_creation_ms); each curve
is looked up in the readings' pieces (hold_grid: the seat's returns; crowd_raw: the fleets by k-1 with the registration block and
the sprayers of data/derived/sprayers.json as one, the attackers' reputation from data/derived/helper_weights.json) and the engine's
gate is applied as engine_replay does (fleets >= ATTACK_MIN, rep_sum >= rep_min). Prints each launch and the totals of the set the
gate would have fired, at the live stake behind one and first in the seat block.

    python3 src/analysis/aim_skips.py data/derived/aim_skips/aim_skips_oct04_08.txt [--attack-min 3] [--rep-min 0.1851] [--stake 75]"""
import glob, re, json, gzip, sys, os
args = sys.argv[1:]
def arg(k, d): return args[args.index(k) + 1] if k in args else d
SRC = args[0]; ATTACK_MIN = int(arg("--attack-min", "3")); REP_MIN = float(arg("--rep-min", "0.1851")); STAKE = float(arg("--stake", "75"))
OURS = {"0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
try: GROUP = {a.lower() for a in json.load(open("data/derived/sprayers.json")).get("sprayers") or ()}
except Exception: GROUP = set()
try: W = {k.lower(): v for k, v in json.load(open("data/derived/helper_weights.json"))["weights"].items()}
except Exception: W = {}
D = "data/derived/live_vs_table"; grid = {}; crowd = {}
for hg in glob.glob(f"{D}/hold_grid_week_*.json"):
    n = hg.split("hold_grid_week_")[1][:-5]
    try:
        for g in json.load(open(hg)): grid.setdefault(g["cv"][:10], (n, g))
        for c in json.load(gzip.open(f"{D}/crowd_raw_{n}.json.gz", "rt")): crowd.setdefault(c["cv"][:10], c)
    except Exception: pass
def fleets_rep(c):
    blocks = c.get("blocks", []); k = c["k"]; token = (c.get("token") or "").lower(); creator = (c.get("creator") or "").lower()
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
    return fl, round(sum(W.get(t, 0.0) for t in targets), 4), k
rows = []
for line in open(SRC):
    m = re.match(r"(\d\d-\d\d \d\d:\d\d:\d\d)\s+(0x[0-9a-f]{8})\s+\[([^\]]*)\]\s+(\d+)", line)
    if not m: continue
    cv = m.group(2); when = m.group(1); since = int(m.group(4))
    if cv not in grid or cv not in crowd:
        rows.append((when, cv, since, None)); continue
    n, g = grid[cv]; fl, rep, k = fleets_rep(crowd[cv])
    rows.append((when, cv, since, (n, k, fl, rep, g.get("behind1_13_h11"), g.get("first_13_h11"))))
print(f"{len(rows)} skips, {sum(1 for r in rows if r[3])} in the tables; gate: fleets >= {ATTACK_MIN} by k-1 and rep_sum >= {REP_MIN}; stake ${STAKE:.0f}")
print("when            curve       since_ms piece      k fl  rep     behind1   first   gate")
fired = []
for when, cv, since, r in rows:
    if r is None:
        print(f"{when}  {cv}  {since:6d}   not in the tables (did not qualify, or outside the pieces)"); continue
    n, k, fl, rep, b1, f1 = r; ok = fl >= ATTACK_MIN and rep >= REP_MIN
    print(f"{when}  {cv}  {since:6d}   {n:9s} {k:2d} {fl:2d} {rep:+.3f}  {100*b1:+6.1f}%  {100*f1:+6.1f}%   {'FIRE' if ok else '-'}")
    if ok: fired.append((b1, f1))
if fired:
    b = [x for x, _ in fired]; f = [y for _, y in fired]
    print(f"\nthe gate would have fired {len(fired)}: behind one {sum(1 for x in b if x > 0)} won, {100*sum(b)/len(b):+.1f}% a fill, ${STAKE*sum(b):+.0f} total; first {sum(1 for x in f if x > 0)} won, {100*sum(f)/len(f):+.1f}% a fill, ${STAKE*sum(f):+.0f} total")
else:
    print("\nthe gate would have fired none of them")
