#!/usr/bin/env python3
"""The engine's log in time order across its rotations (engine.jsonl.2.gz, .1, engine.jsonl): the daily rotation split the
night of Sep 29-30 in two and the reading's greps on engine.jsonl alone missed the alarm. Run with sudo:

    sudo python3 deploy/englog.py 12 > /tmp/eng.jsonl      # the last 12 hours (default 24)
    sudo python3 deploy/englog.py 12 runner                # 6.26: the runner's log (runner.jsonl*)
"""
import glob, gzip, os, re, sys, time
hours = float(sys.argv[1]) if len(sys.argv) > 1 else 24.0; cut = time.time() - hours * 3600
NAME = sys.argv[2] if len(sys.argv) > 2 else "engine"
T = re.compile(r'"t": ([0-9.]+)')
for f in sorted((f for f in glob.glob(f"/var/log/sniper/{NAME}.jsonl*") if not f.endswith(".state.json")), key=os.path.getmtime):
    if os.path.getmtime(f) < cut:
        continue
    with (gzip.open if f.endswith(".gz") else open)(f, "rt") as fh:
        for line in fh:
            m = T.search(line)
            if m and float(m.group(1)) >= cut:
                sys.stdout.write(line)
