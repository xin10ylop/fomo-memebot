"""fleets.py (reviewer B), tests 3 and 5 from the crowd files alone (every launch, not only fires): the fleets that shoot, how
many shots, how early, by period: fit (Sep 18-23), Sep 24-26 before our first live burst (Sep 26 09:24 UTC), after it.
    python3 data/derived/edge_check/B/fleets.py"""
import sys, os, json, collections, statistics as st, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
LIVE = 1790414640
RELAY = "0xe8e98c3514d5bd83fdd01360896f2382b861a720"
def per(T0): return "fit" if T0 < 1790200000 else ("pre-live" if T0 < LIVE else "post-live")
# hours covered: the fit windows as crowd_rules.py prices them; the recent windows from the e1m files' spans (union), split at LIVE
iv = sorted((d["t_lo"], d["t_hi"]) for d in (json.load(open(f)) for f in glob.glob("data/derived/e1_sep24/e1m_*.json")))
u = []
for a, b in iv:
    if u and a <= u[-1][1]: u[-1][1] = max(u[-1][1], b)
    else: u.append([a, b])
H = {"fit": 96.0, "pre-live": sum(max(0, min(b, LIVE) - a) for a, b in u) / 3600, "post-live": sum(max(0, b - max(a, LIVE)) for a, b in u) / 3600}
R = c.load(c.FIT) + c.load(c.RECENT); P = collections.defaultdict(list)
for r in R: P[per(r["T0"])].append(r)
roster = {}
print(f"{'period':10s} {'hours':>6s} {'launches':>8s} {'/h':>5s} {'fires':>5s} {'/h':>5s} {'fire%':>6s} {'f@k-2':>6s} {'f@k':>5s} {'f@seat':>6s} {'shots cs':>8s} {'shots seat':>10s} {'k':>5s}  fleets@k-2 distribution  | our relay seen")
for p in ("fit", "pre-live", "post-live"):
    S = P[p]; fires = [r for r in S if c.is_fire(r)]; fk2 = []; fk = []; fseat = []; scs = []; sseat = []; ours = 0
    cnt = collections.Counter(); shots = collections.defaultdict(list); first = collections.defaultdict(list)
    for r in S:
        fb = c.fleets_by_block(r); k = r["k"]; cw, cf = c.cums(r)
        fk2.append(c.at(cf, k - 2)); fk.append(c.at(cf, k)); fseat.append(len(set(x[1] for rows in fb for x in rows)))
        scs.append(sum(len(rows) for rows in fb[: k + 1])); sseat.append(len(fb[k + 1]) if len(fb) > k + 1 else 0)
        ours += any(t["to"] == RELAY for rows in r["blocks"] for t in rows)
        seen = {}
        for off, rows in enumerate(fb):
            for _, fid in rows: seen.setdefault(fid, off); shots[fid].append(off)
        for fid, off in seen.items(): cnt[fid] += 1; first[fid].append(off - k)
    roster[p] = (len(S), cnt, first)
    dist = collections.Counter(min(x, 4) for x in fk2)
    print(f"{p:10s} {H[p]:6.1f} {len(S):8d} {len(S)/H[p]:5.2f} {len(fires):5d} {len(fires)/H[p]:5.2f} {len(fires)/len(S):6.1%} {st.mean(fk2):6.2f} {st.mean(fk):5.2f} {st.mean(fseat):6.2f} {st.mean(scs):8.1f} {st.mean(sseat):10.1f} {st.mean(r['k'] for r in S):5.2f}  {[dist[i] for i in range(5)]} (0,1,2,3,4+) | {ours}")
print("\nthe fleets, share of launches each shoots at (any block 0..k+1), median first block relative to k (k-2 = -2):")
names = sorted(set().union(*[set(roster[p][1]) for p in roster]), key=lambda f: -sum(roster[p][1][f] / roster[p][0] for p in roster))[:20]
for f in names:
    print(f"  {f[:12]} " + "  ".join(f"{p:9s} {roster[p][1][f]/roster[p][0]:5.1%} first {st.median(roster[p][2][f]) if roster[p][2][f] else float('nan'):+5.1f}" for p in ("fit", "pre-live", "post-live")))
new = {p: [f for f in roster[p][1] if roster["fit"][1][f] == 0] for p in ("pre-live", "post-live")}
for p in new: print(f"  {p}: {len(roster[p][1])} fleets shot, {len(new[p])} never seen in the fit windows, at {sum(roster[p][1][f] for f in new[p])} launch-shots; at k-2 of a fire: see compare3.py")
