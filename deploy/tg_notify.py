#!/usr/bin/env python3
"""Telegram notifier for the sniper (runbook 5ai): a separate process that follows the engine's log and sends a message when a
trade closes (with the capital and P&L lines of `relay_ops.py status`), when a burst fills, on every alarm and on every engine
start. It never touches the engine. Secrets live in /etc/sniper/telegram.env (root, 0600): TG_TOKEN, TG_CHAT, TG_PNL_BASE.

    sudo python3 deploy/tg_notify.py --whoami      # the chat ids that have messaged the bot (to fill TG_CHAT)
    sudo python3 deploy/tg_notify.py --test        # one test message
    sudo python3 deploy/tg_notify.py               # follow the log (the sniper-notify service runs this)
    python3 deploy/tg_notify.py --replay FILE      # dry: print what the messages would be for a log file, no sending
"""
import json, os, sys, time, subprocess, urllib.request, urllib.parse
ENV = "/etc/sniper/telegram.env"; LOG = os.environ.get("LOG_PATH", "/var/log/sniper/engine.jsonl")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PY = "/opt/sniper-venv/bin/python3"
def cfg():
    c = {}
    if os.path.exists(ENV):
        for line in open(ENV):
            if "=" in line and not line.startswith("#"): k, v = line.strip().split("=", 1); c[k] = v.strip().strip('"')
    return c
C = cfg(); TOKEN = C.get("TG_TOKEN", ""); CHAT = C.get("TG_CHAT", ""); BASE = C.get("TG_PNL_BASE", "0.015412")
def api(method, **params):
    data = urllib.parse.urlencode(params).encode() if params else None
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data), timeout=15))
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    print(f"telegram {method} failed: {str(err)[:80]}", file=sys.stderr); return None
_last = [0.0]
def send(text, dry=False):
    if dry: print("--- message ---\n" + text); return
    wait = 3.0 - (time.time() - _last[0])
    if wait > 0: time.sleep(wait)
    _last[0] = time.time(); api("sendMessage", chat_id=CHAT, text=text[:3900])
def status_lines():
    try:
        out = subprocess.run([PY, os.path.join(REPO, "deploy", "relay_ops.py"), "status", BASE], capture_output=True, text=True, timeout=60).stdout.strip().splitlines()
        return "\n".join(out[-2:]) if out else "(status unavailable)"
    except Exception as e:
        return f"(status failed: {str(e)[:60]})"
def message_for(e, dry=False):
    """the text for one log event, or None"""
    ev = e.get("ev"); ts = time.strftime("%H:%M:%S", time.gmtime(e.get("t", time.time()))) + " UTC"
    if ev == "start":
        return f"{ts} engine started: release {e.get('release', e.get('version'))}, stake ${e.get('stake_min')}-{e.get('stake_max')}, tier {e.get('tier_min_bps')}-{e.get('tier_max_bps')} bps, dry_run {e.get('dry_run')}"
    if ev == "burst_landing" and (e.get("filled") or 0) >= 1:
        return f"{ts} FILLED {e.get('curve', '')[:10]} ({e.get('filled')} fill): position open, selling in about 1 s"
    if ev == "trade_done" and not e.get("dry_run"):
        if not dry: time.sleep(25)                                      # the sell's proceeds and the relay's refill land first
        return f"{ts} trade closed {e.get('curve', '')[:10]}: exit '{e.get('exit')}', held {e.get('held_s')} s\n" + ("(status)" if dry else status_lines())
    if ev == "alarm":
        return f"{ts} ALARM: {e.get('what')}"
    return None
def follow(path):
    """yield new lines as they are appended; a truncation (the daily copytruncate rotation) restarts from the top"""
    f = open(path); f.seek(0, 2); pos = f.tell()
    while True:
        line = f.readline()
        if line:
            pos = f.tell(); yield line; continue
        time.sleep(0.5)
        try:
            if os.stat(path).st_size < pos: f.close(); f = open(path); pos = 0
        except FileNotFoundError:
            time.sleep(2)
if __name__ == "__main__":
    a = sys.argv[1:]
    if "--replay" in a:
        for line in open(a[a.index("--replay") + 1]):
            try: m = message_for(json.loads(line), dry=True)
            except Exception: m = None
            if m: send(m, dry=True)
        sys.exit(0)
    if not TOKEN: sys.exit(f"no TG_TOKEN in {ENV}")
    if "--whoami" in a:
        r = api("getUpdates") or {}
        seen = {(u.get("message") or u.get("channel_post") or {}).get("chat", {}).get("id") for u in r.get("result", [])} - {None}
        print("chat ids that have messaged the bot:", sorted(seen) or "none yet: send the bot a message first"); sys.exit(0)
    if not CHAT: sys.exit(f"no TG_CHAT in {ENV} (run --whoami after messaging the bot)")
    if "--test" in a:
        send("sniper notifier online\n" + status_lines()); print("sent"); sys.exit(0)
    send("sniper notifier started\n" + status_lines())
    for line in follow(LOG):
        try: e = json.loads(line)
        except Exception: continue
        try:
            m = message_for(e)
            if m: send(m)
        except Exception as ex:
            print(f"notify error: {str(ex)[:100]}", file=sys.stderr)
