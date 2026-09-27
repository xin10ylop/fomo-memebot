"""visibility.py (reviewer B): our own shots in the crowd files (relay 0xe8e98c35 as target, or our wallet/relay as sender),
by day: when the fleets could first see our bursts. python3 data/derived/edge_check/B/visibility.py"""
import sys, os, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
RELAY = "0xe8e98c3514d5bd83fdd01360896f2382b861a720"; out = collections.defaultdict(list)
for r in c.load(c.FIT) + c.load(c.RECENT):
    relay = [t for rows in r["blocks"] for t in rows if t["to"] == RELAY]; wal = [t for rows in r["blocks"] for t in rows if t["fr"] in c.US]
    if relay or wal: out[time.strftime("%b %d", time.gmtime(r["T0"]))].append((c.hhmm(r["T0"]), len(relay), len({t["fr"] for t in relay}), len(wal)))
for d in sorted(out):
    L = sorted(out[d]); bursts = [x for x in L if x[1] >= 20]
    print(f"{d}: {len(L)} launches with our shots; relay bursts of >= 20 shots at {len(bursts)} ({bursts[0][0][7:] if bursts else '-'} to {bursts[-1][0][7:] if bursts else '-'}, senders {sorted({x[2] for x in bursts})}); wallet-only {sum(1 for x in L if x[1] == 0)}")
