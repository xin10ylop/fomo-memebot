#!/bin/sh
# cron watchdog (every 5 minutes). Alerts on stdout (cron mails it) or through ALERT_CMD.
# Three ways the engine can be useless while systemd still calls it active:
#   1. the log stops growing (the process is wedged);
#   2. the clock drifts (the seat's second is the sequencer's clock);
#   3. it keeps seeing launches but scores none - a node that refuses eth_getLogs (rate limit, monthly cap,
#      revoked key) blinds the gauge silently. This cost four paper days on Sep 12-16.
LOG=${1:-/var/log/sniper/engine.jsonl}; ALERT_CMD=${ALERT_CMD:-cat}; PY=/opt/sniper-venv/bin/python3
[ -x "$PY" ] || PY=python3
if [ ! -f "$LOG" ] || [ $(( $(date +%s) - $(stat -c %Y "$LOG") )) -gt 600 ]; then echo "sniper: engine log has not grown for 10 minutes" | $ALERT_CMD; fi
OFF=$(chronyc tracking 2>/dev/null | awk '/System time/ {print $4}'); if [ -n "$OFF" ] && [ "$(echo "$OFF > 0.02" | bc)" = "1" ]; then echo "sniper: clock offset ${OFF}s" | $ALERT_CMD; fi
$PY - "$LOG" <<'PYEOF' | $ALERT_CMD
import json, sys, time
last = {"score": 0.0, "creation": 0.0}; errs = {}
try:
    with open(sys.argv[1], "rb") as f:                                   # the tail is enough: this runs every five minutes
        f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 4_000_000))
        if size > 4_000_000:
            f.readline()
        for line in f:
            try:
                e = json.loads(line)
            except Exception:
                continue
            ev = e.get("ev"); t = e.get("t") or 0.0
            if ev in last:
                last[ev] = max(last[ev], t)
            elif ev == "error" and t > time.time() - 3600:
                errs[str(e.get("err"))[:90]] = errs.get(str(e.get("err"))[:90], 0) + 1
except OSError:
    raise SystemExit(0)
now = time.time()
if last["creation"] > now - 1800 and last["score"] < now - 7200:          # launches arriving, nothing scored for two hours
    top = sorted(errs.items(), key=lambda kv: -kv[1])[:2]
    print("sniper: the engine has seen launches in the last 30 minutes but scored none for %.1f hours: the gauge is blind." % ((now - last["score"]) / 3600))
    for k, v in top:
        print("        last hour's errors: %s (x%d)" % (k, v))
    print("        check the node: %s" % ("free-tier cap or rate limit on RPC_URL/LOGS_RPC_URL" if any("capacity" in k or "429" in k or "rate" in k.lower() for k, _ in top) else "run: journalctl -u sniper-engine -n 30"))
PYEOF
