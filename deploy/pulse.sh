#!/bin/bash
# The engine's pulse: is it alive, and has it been all along? An hour-by-hour table of what the engine logged over the last N
# hours (creations seen, decisions, the ten-minute flow line, feed reconnects, alarms, errors) and the minutes since each event's
# last line. A healthy sniper shows creations every hour, a skip or decision for each, 6 flow lines an hour and small
# "minutes since" for creation and flow; a frozen one shows a column that stops while the box is up. Run with sudo:
#
#     sudo bash deploy/pulse.sh 16            # the sniper (engine.jsonl) over the last 16 hours
#     sudo bash deploy/pulse.sh 16 runner     # the runner's log
R="$(cd "$(dirname "$0")/.." && pwd)"; H=${1:-16}; NAME=${2:-engine}
date -u; uptime | sed 's/^ *//'
for s in sniper-engine sniper-notify flip-engine runner-engine runner-notify; do systemctl cat "$s" >/dev/null 2>&1 && printf "%-14s %s since %s\n" "$s" "$(systemctl is-active "$s")" "$(systemctl show -p ActiveEnterTimestamp --value "$s" | cut -d' ' -f2-3)"; done
python3 - <(python3 "$R/deploy/englog.py" "$H" "$NAME") <<'PY'
import json, sys, time, collections
c = collections.Counter(); last = {}; n = 0; starts = []
for l in open(sys.argv[1]):
    try: d = json.loads(l)
    except Exception: continue
    n += 1; ev = d.get("ev"); t = d.get("t", 0); h = time.strftime("%d %Hh", time.gmtime(t)); c[(h, ev)] += 1; last[ev] = t
    if ev == "start": starts.append(f'{time.strftime("%H:%M", time.gmtime(t))} release {d.get("release")} dry_run {d.get("dry_run")}')
evs = ["creation", "skip", "eligible_not_traded", "trade_decision", "trade_done", "flow", "feed_connected", "feed_stall", "feed_error", "alarm", "error"]
print("starts:", "; ".join(starts) or "none in the window")
print(f"{n} lines | hour  " + "".join(f"{e[:8]:>9}" for e in evs))
for h in sorted(set(h for h, _ in c)): print(f"{h:13}" + "".join(f"{c[(h, e)]:>9}" for e in evs))
now = time.time(); print("minutes since last:", {e: int((now - last[e]) // 60) for e in evs if e in last})
PY
