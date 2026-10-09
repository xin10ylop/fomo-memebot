#!/usr/bin/env python3
"""Telegram P&L notifier (runbook 5ai): one message, the same line as the box's `pnl`, only when the P&L changes.

    balance 0.018972 ETH ($50.70) | P&L +0.003560 ETH ($9.51) (+23.1%)

A separate process (service sniper-notify) that never touches the engine: it reads the engine's log to know when a trade
closed or a burst landed (then reads the balances 25 s later, once the refill is in) and reads them anyway every 10 minutes.
The line is sent when the P&L in ETH moved by 0.00005 ETH or more since the last message (a trade or a burst's gas, not the
ETH price moving). Secrets in /etc/sniper/telegram.env (root, 0600): TG_TOKEN, TG_CHAT, TG_PNL_BASE.

    sudo python3 deploy/tg_notify.py --whoami      # chat ids that have messaged the bot
    sudo python3 deploy/tg_notify.py --test        # send the line once, now
"""
import json, os, re, sys, time, subprocess, urllib.request, urllib.parse
ENV = "/etc/sniper/telegram.env"; LOG = os.environ.get("LOG_PATH", "/var/log/sniper/engine.jsonl")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PY = "/opt/sniper-venv/bin/python3"
POLL_S = 600; SETTLE_S = 25; MIN_MOVE_ETH = 0.00005
def cfg():
    c = {}
    if os.path.exists(ENV):
        for line in open(ENV):
            if "=" in line and not line.startswith("#"): k, v = line.strip().split("=", 1); c[k] = v.strip().strip('"')
    return c
C = cfg(); TOKEN = C.get("TG_TOKEN", ""); CHAT = C.get("TG_CHAT", ""); BASE = C.get("TG_PNL_BASE", "0.015412")
LABEL = os.environ.get("TG_LABEL", "")                                   # 6.25: a second instance's notifier names itself and reads its own base
if os.environ.get("SNIPER_ENV"):
    try:
        for line in open(os.environ["SNIPER_ENV"]):
            if line.startswith("PNL_BASE="): BASE = line.split("=", 1)[1].strip() or BASE
    except Exception: pass
def api(method, **params):
    data = urllib.parse.urlencode(params).encode() if params else None
    for i in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data), timeout=15))
        except Exception as e: err = e; time.sleep(2 * (i + 1))
    print(f"telegram {method} failed: {str(err)[:80]}", file=sys.stderr); return None
def tag(text): return f"[{LABEL}] {text}" if LABEL else text
def pnl_line():
    """(the line, pnl_eth) from relay_ops status, or (None, None)"""
    try:
        out = subprocess.run([PY, os.path.join(REPO, "deploy", "relay_ops.py"), "status", BASE], capture_output=True, text=True, timeout=90).stdout
        t = re.search(r"TOTAL capital: ([\d.]+) ETH \(\$([\d.,]+)\)", out); p = re.search(r"P&L since [\d.]+ ETH: ([+-][\d.]+) ETH \(\$([+-]?[\d.,]+)\) \(([+-][\d.]+%)\)", out)
        if not (t and p): return None, None
        return f"balance {t.group(1)} ETH (${t.group(2)}) | P&L {p.group(1)} ETH (${p.group(2)}) ({p.group(3)})", float(p.group(1))
    except Exception as e:
        print(f"status failed: {str(e)[:80]}", file=sys.stderr); return None, None
def follow(path):
    """new log lines as they are appended; a truncation (the daily rotation) restarts from the top; never blocks longer than 0.5 s"""
    f = None; pos = 0
    while True:
        try:
            if f is None: f = open(path); f.seek(0, 2); pos = f.tell()
            line = f.readline()
            if line: pos = f.tell(); yield line; continue
            if os.stat(path).st_size < pos: f.close(); f = None; continue
        except FileNotFoundError:
            f = None
        yield None; time.sleep(0.5)
if __name__ == "__main__":
    a = sys.argv[1:]
    if not TOKEN: sys.exit(f"no TG_TOKEN in {ENV}")
    if "--whoami" in a:
        r = api("getUpdates") or {}
        seen = {(u.get("message") or u.get("channel_post") or {}).get("chat", {}).get("id") for u in r.get("result", [])} - {None}
        print("chat ids that have messaged the bot:", sorted(seen) or "none yet: send the bot a message first"); sys.exit(0)
    if not CHAT: sys.exit(f"no TG_CHAT in {ENV} (run --whoami after messaging the bot)")
    line, pnl = pnl_line()
    if "--test" in a:
        api("sendMessage", chat_id=CHAT, text=tag(line or "status unavailable")); print("sent:", line); sys.exit(0)
    last = pnl; due = time.time() + POLL_S; settle_at = None
    if line: api("sendMessage", chat_id=CHAT, text=tag(line))
    for raw in follow(LOG):
        if raw:
            try: e = json.loads(raw)
            except Exception: e = {}
            if e.get("ev") in ("trade_done", "burst_landing") and not e.get("dry_run"): settle_at = time.time() + SETTLE_S
        now = time.time()
        if (settle_at and now >= settle_at) or now >= due:
            settle_at = None; due = now + POLL_S; line, pnl = pnl_line()
            if line and pnl is not None and (last is None or abs(pnl - last) >= MIN_MOVE_ETH):
                api("sendMessage", chat_id=CHAT, text=tag(line)); last = pnl
