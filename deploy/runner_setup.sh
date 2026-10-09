#!/bin/bash
# The runner (runbook 5bj, rebuilt in 5bk): a second engine instance on its own wallet, its own relay and shooters, its own provider
# key, its own feed address and its own code checkout. Run as root (sudo) from the runner's checkout (~/fomo-runner). Never prints a key.
#   upgrade            rewrite /etc/sniper/runner.env from the template, keeping the wallet, the books, the relay, the shooters,
#                      the feed address and the provider key (the old file is kept as runner.env.bak, 0600); the runner stays stopped
#   install            a fresh wallet and /etc/sniper/runner.env (a new box only; refuses when the file exists)
#   set-rpc            type the runner's OWN provider HTTPS URL (asked without echo; never the sniper's: its quota is the sniper's)
#   add-ip IP          use the box's second private address IP (with its own Elastic IP) for the runner's feed socket: added now
#                      and at every boot (runner-ip.service), checked to leave from a different public address than the sniper
#   units              (re)write runner-engine and runner-notify for THIS checkout: core 0, Nice 10, after runner-ip
#   relay              deploy the runner's own buy-once relay from its wallet and write RELAY (asks yes)
#   shooters [N]       create N shooter keys (default BURST_N), register them on the relay, fund each to SHOOTER_TARGET_ETH
#   base [--reset|--add ETH]   record the P&L base once (the capital when funded); --add a later deposit; --reset start over
#   check              every precondition for going live, each with ok or what is missing
#   dry | live         start the runner in dry run / live (both refuse when a precondition fails); stop: stop it
#   status             services, the start line, the capital and the P&L against the base
set -e; REPO=$(cd "$(dirname "$0")/.." && pwd); ENV=/etc/sniper/runner.env; SRC=/etc/sniper/engine.env; PY=/opt/sniper-venv/bin/python3
TPL="$REPO/deploy/runner.env.template"; LOGF=/var/log/sniper/runner.jsonl; STATEF=/var/log/sniper/runner.jsonl.state.json
RSEND=/etc/sniper/runner_send_step.py                     # the runner's own copy of the send step (the sniper's /etc/sniper/send_step.py is never touched)
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
val() { grep "^$1=" "$2" 2>/dev/null | head -1 | cut -d= -f2-; }
setkv() { KV_K="$1" KV_V="$2" python3 - "$ENV" <<'PYEOF'
import os, sys
p = sys.argv[1]; k = os.environ["KV_K"]; v = os.environ["KV_V"]
lines = open(p).read().splitlines(); out = []; done = False
for l in lines:
    if l.startswith(k + "="): out.append(f"{k}={v}"); done = True
    else: out.append(l)
if not done: out.append(f"{k}={v}")
tmp = p + ".tmp"; fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as f:
    f.write("\n".join(out) + "\n"); f.flush(); os.fsync(f.fileno())
os.replace(tmp, p)
PYEOF
}
render() {  # $1 = the file to write; the template with the box's values; KEEP_FROM = an older runner.env whose identity and books carry over
  KEEP_FROM="${2:-}" python3 - "$TPL" "$SRC" "$1" <<'PYEOF'
import os, sys
tpl, src, out = sys.argv[1:4]; keep_from = os.environ.get("KEEP_FROM", "")
def kv(p):
    d = {}
    if p and os.path.exists(p):
        for l in open(p).read().splitlines():
            if l and not l.startswith("#") and "=" in l: k, v = l.split("=", 1); d.setdefault(k, v)
    return d
S = kv(src); O = kv(keep_from)
defaults = {"SLOT_SEND": "1", "SLOT_LEAD_MS": "50", "FEED_LAG_MS": "85", "MARGIN_MS": "0"}   # the engine's calibration on this box (Oct 8 start line)
subst = {f"@{k}@": (S.get(k) or defaults.get(k, "")) for k in ("FEED_URL", "LOGS_RPC_URL", "SEQ_URL", "SLOT_SEND", "SLOT_LEAD_MS", "FEED_LAG_MS", "MARGIN_MS")}
subst["@RPC_URL@"] = ""                                       # the runner's own key only (set-rpc), never the sniper's
KEEP = ("PRIVATE_KEY", "WALLET", "RPC_URL", "RELAY", "SHOOTER_KEYS", "BURST_N", "FEED_LOCAL_ADDR", "PNL_BASE", "PNL_WITHDRAWN", "STAKE_MIN", "STAKE_MAX", "RELAY_FLOAT_USD")
lines = []
for l in open(tpl).read().splitlines():
    for a, b in subst.items(): l = l.replace(a, b)
    if l and not l.startswith("#") and "=" in l:
        k = l.split("=", 1)[0]
        if k in KEEP and k in O and not O[k].startswith("@") and not (k == "BURST_N" and not O.get("SHOOTER_KEYS")): l = f"{k}={O[k]}"
    lines.append(l)
if "@PRIVATE_KEY@" in "\n".join(lines) or "@WALLET@" in "\n".join(lines):
    if not keep_from: pass
    else: sys.exit("the old file has no PRIVATE_KEY or WALLET: not writing")
if O.get("RPC_URL") and O.get("RPC_URL") == S.get("RPC_URL"):
    lines = [("RPC_URL=" if l.startswith("RPC_URL=") else l) for l in lines]   # the sniper's key copied by 6.25's install: dropped, set-rpc required
    print("the old RPC_URL was the sniper's key: dropped (run set-rpc)")
tmp = out + ".tmp"; fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as f:
    f.write("\n".join(lines) + "\n"); f.flush(); os.fsync(f.fileno())
os.replace(tmp, out)
PYEOF
}
startline() { sleep "${1:-12}"; grep -h '"ev": "start"' "$LOGF" 2>/dev/null | tail -1 | grep -o '"release": "[0-9.]*"\|"seat": "[A-Z0-9]*"\|"burst": \[[^]]*\]\|"shooters": [0-9]*\|"relay": "0x[0-9a-f]\{6\}\|"exit_mark": [a-z]*\|"stop_loss": [0-9.]*\|"take_profit": [0-9.]*\|"hold_blocks": [0-9]*\|"attack_max": [-0-9]*\|"tier_max_bps": [0-9]*\|"stake": \[[^]]*\]\|"dry_run": [a-z]*' | paste -sd' '; }
active() { systemctl is-active --quiet "$1"; }
own_rpc_ok() {  # the runner's provider key: set, not the sniper's, and answering chain 4663
  [ -n "$(val RPC_URL "$ENV")" ] || { echo "RPC_URL: not set (sudo bash deploy/runner_setup.sh set-rpc)"; return 1; }
  [ "$(val RPC_URL "$ENV")" != "$(val RPC_URL "$SRC")" ] || { echo "RPC_URL: the sniper's key (its monthly quota is the sniper's): set-rpc"; return 1; }
  RPCU="$(val RPC_URL "$ENV")" $PY -c 'import os,json,urllib.request; r=urllib.request.Request(os.environ["RPCU"],data=json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}).encode(),headers={"content-type":"application/json"}); c=json.load(urllib.request.urlopen(r,timeout=15)).get("result"); raise SystemExit(0 if c=="0x1237" else 1)' || { echo "RPC_URL: does not answer chain 4663"; return 1; }
}
feed_ip_ok() {
  ip=$(val FEED_LOCAL_ADDR "$ENV"); [ -n "$ip" ] || { echo "FEED_LOCAL_ADDR: not set (sudo bash deploy/runner_setup.sh add-ip <second private IP>)"; return 1; }
  ip -o -4 addr show | grep -q " $ip/" || { echo "FEED_LOCAL_ADDR $ip: not on this machine (add-ip again, or reboot ran without runner-ip)"; return 1; }
  a=$(curl -s -m 8 --interface "$ip" https://checkip.amazonaws.com || true); b=$(curl -s -m 8 https://checkip.amazonaws.com || true)
  [ -n "$a" ] && [ "$a" != "$b" ] || { echo "FEED_LOCAL_ADDR $ip: does not leave from a second public address (public $a, the sniper's $b): associate an Elastic IP with it"; return 1; }
}
no_open_position() { [ ! -f "$STATEF" ] || python3 -c "import json,sys; sys.exit(1 if json.load(open('$STATEF')).get('open') else 0)" || { echo "the runner's state file holds an OPEN position: start it live so it is sold first"; return 1; }; }
case "${1:-status}" in
install)
  [ -f "$ENV" ] && { echo "$ENV exists: use upgrade"; exit 1; }
  render "$ENV"
  KEYADDR=$($PY -c "from eth_account import Account; a = Account.create(); k = a.key.hex(); print(k if k.startswith('0x') else '0x' + k, a.address)")
  setkv PRIVATE_KEY "${KEYADDR% *}"; setkv WALLET "${KEYADDR#* }"; unset KEYADDR
  echo "runner wallet (fund this address): $(val WALLET "$ENV")"; echo "next: set-rpc, add-ip, units, relay, shooters, base, dry" ;;
upgrade)
  [ -f "$ENV" ] || { echo "no $ENV: use install"; exit 1; }
  active runner-engine && { echo "runner-engine is running: sudo systemctl stop runner-engine runner-notify first"; exit 1; }
  install -m 600 "$ENV" "$ENV.bak"; render "$ENV.new" "$ENV.bak" && mv "$ENV.new" "$ENV" && chmod 600 "$ENV"
  grep -q "^PRIVATE_KEY=0x[0-9a-fA-F]\{64\}$" "$ENV" || { cp "$ENV.bak" "$ENV"; echo "the key did not carry over: the old file is restored"; exit 1; }
  echo "runner.env rewritten from the template (the old one is $ENV.bak); wallet $(val WALLET "$ENV"), base $(val PNL_BASE "$ENV")"
  echo "next: $(sudo bash "$0" check 2>/dev/null | grep -v ' ok$' | head -3 | paste -sd';')" ;;
set-rpc)
  read -r -s -p "the runner's own provider HTTPS URL (not shown): " U; echo
  case "$U" in https://*) ;; *) echo "not an https URL: nothing written"; exit 1;; esac
  [ "$U" != "$(val RPC_URL "$SRC")" ] || { echo "that is the sniper's key: create a separate app at the provider for the runner"; exit 1; }
  RPCU="$U" $PY -c 'import os,json,urllib.request; r=urllib.request.Request(os.environ["RPCU"],data=json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}).encode(),headers={"content-type":"application/json"}); c=json.load(urllib.request.urlopen(r,timeout=15)).get("result"); print("chain", int(c,16)); raise SystemExit(0 if c=="0x1237" else 1)' || { echo "the URL does not answer chain 4663: nothing written"; exit 1; }
  setkv RPC_URL "$U"; unset U; echo "RPC_URL set for the runner" ;;
add-ip)
  IP="$2"; [ -n "$IP" ] || { echo "usage: add-ip <the second private IP AWS assigned to this instance>"; exit 1; }
  DEV=$(ip -o -4 route show default | awk '{print $5}' | head -1); PFX=$(ip -o -4 addr show dev "$DEV" | awk '{print $4}' | head -1 | cut -d/ -f2)
  ip addr replace "$IP/$PFX" dev "$DEV"
  cat > /etc/systemd/system/runner-ip.service <<UNIT
[Unit]
Description=the runner's second address on $DEV (its feed socket leaves from it)
After=network-online.target
Wants=network-online.target
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/ip addr replace $IP/$PFX dev $DEV
[Install]
WantedBy=multi-user.target
UNIT
  systemctl daemon-reload; systemctl enable runner-ip >/dev/null 2>&1
  setkv FEED_LOCAL_ADDR "$IP"; feed_ip_ok && echo "FEED_LOCAL_ADDR $IP: ok, it leaves from $(curl -s -m 8 --interface "$IP" https://checkip.amazonaws.com)" ;;
units)
  cat > /etc/systemd/system/runner-engine.service <<UNIT
[Unit]
Description=the runner: the untaxed no-crowd tier on its own wallet (runbook 5bj/5bk)
After=network-online.target chrony.service runner-ip.service
[Service]
EnvironmentFile=$ENV
WorkingDirectory=$REPO
ExecStart=$PY $REPO/src/strategy/sniper_engine.py
Restart=always
RestartSec=3
CPUAffinity=0
Nice=10
[Install]
WantedBy=multi-user.target
UNIT
  cat > /etc/systemd/system/runner-notify.service <<UNIT
[Unit]
Description=the runner's telegram notifier (follows its log; never touches the engine)
After=network-online.target
[Service]
Type=simple
Environment=LOG_PATH=$LOGF
Environment=SNIPER_ENV=$ENV
Environment=TG_LABEL=runner
WorkingDirectory=$REPO
ExecStart=/usr/bin/python3 $REPO/deploy/tg_notify.py
Restart=always
RestartSec=5
CPUAffinity=0
Nice=10
[Install]
WantedBy=multi-user.target
UNIT
  systemctl daemon-reload; echo "units written for $REPO (core 0, Nice 10); nothing started" ;;
relay)
  active runner-engine && { echo "stop the runner first"; exit 1; }
  [ -z "$(val RELAY "$ENV")" ] || { echo "RELAY already set: $(val RELAY "$ENV")"; exit 1; }
  own_rpc_ok
  SNIPER_ENV=$ENV $PY "$REPO/deploy/relay_deploy.py" --write-env ;;
shooters)
  active runner-engine && { echo "stop the runner first"; exit 1; }
  N="${2:-$(val BURST_N "$ENV")}"; [ -n "$(val RELAY "$ENV")" ] || { echo "deploy the relay first (relay)"; exit 1; }
  own_rpc_ok
  SNIPER_ENV=$ENV $PY "$REPO/deploy/relay_ops.py" shooters-create "$N"
  SNIPER_ENV=$ENV $PY "$REPO/deploy/relay_ops.py" shooters-register
  SNIPER_ENV=$ENV $PY "$REPO/deploy/relay_ops.py" shooters-fund "$(val SHOOTER_TARGET_ETH "$ENV")"
  setkv BURST_N "$N"; echo "BURST_N=$N" ;;
base)
  WALLET=$(val WALLET "$ENV"); B=$(val PNL_BASE "$ENV")
  if [ "$2" = "--add" ]; then
    [ -n "$3" ] || { echo "base --add <eth>"; exit 1; }; NB=$(python3 -c "print('%.6f' % (float('${B:-0}') + float('$3')))"); setkv PNL_BASE "$NB"; echo "P&L base $B -> $NB ETH"
  else
    [ "${B:-0}" = "0" ] || [ "$2" = "--reset" ] || { echo "the base is already $B ETH: base --add <eth> for a later deposit, base --reset to start over"; exit 1; }
    BAL=$(SNIPER_ENV=$ENV $PY "$REPO/deploy/relay_ops.py" status 2>/dev/null | grep -o "TOTAL capital: [0-9.]*" | grep -o "[0-9.]*$")
    [ -n "$BAL" ] && [ "$BAL" != "0.000000" ] || { echo "the runner's capital reads ${BAL:-nothing}: fund the wallet $WALLET first"; exit 1; }
    setkv PNL_BASE "$BAL"; echo "P&L base recorded: $BAL ETH (wallet + relay + shooters)"
  fi
  systemctl try-restart runner-notify 2>/dev/null || true ;;
check)
  rc=0
  own_rpc_ok && echo "provider key: ok" || rc=1
  feed_ip_ok && echo "feed address: ok" || rc=1
  [ -n "$(val RELAY "$ENV")" ] && echo "relay: ok ($(val RELAY "$ENV" | cut -c1-12)...)" || { echo "relay: not deployed (relay)"; rc=1; }
  n=$(val SHOOTER_KEYS "$ENV" | tr ',' '\n' | grep -c . || true); [ "$n" -ge "$(val BURST_N "$ENV")" ] && echo "shooters: ok ($n)" || { echo "shooters: $n, BURST_N $(val BURST_N "$ENV") (shooters)"; rc=1; }
  [ "$(val PNL_BASE "$ENV")" != "0" ] && echo "base: ok ($(val PNL_BASE "$ENV") ETH)" || { echo "base: not recorded (base)"; rc=1; }
  grep -q "veto=None" "$REPO/deploy/send_step.py" && echo "send step: ok (this checkout's, with the veto; copied to $RSEND at live)" || { echo "send step: $REPO/deploy/send_step.py has no veto (engine 6.26)"; rc=1; }
  grep -q "WorkingDirectory=$REPO$" /etc/systemd/system/runner-engine.service 2>/dev/null && grep -q "^CPUAffinity=0" /etc/systemd/system/runner-engine.service && echo "units: ok ($REPO)" || { echo "units: not for this checkout (units)"; rc=1; }
  no_open_position && echo "state: ok (no open position)" || rc=1
  exit $rc ;;
dry|live)
  own_rpc_ok; feed_ip_ok; no_open_position
  grep -q "WorkingDirectory=$REPO$" /etc/systemd/system/runner-engine.service || { echo "the units are not for this checkout: units"; exit 1; }
  if [ "$1" = live ]; then bash "$0" check >/dev/null || { bash "$0" check; exit 1; }; install -m 600 "$REPO/deploy/send_step.py" "$RSEND"; setkv SEND_MODULE "$RSEND"; else setkv SEND_MODULE ""; fi
  rm -f "$STATEF"                                         # a fresh state in the new mode (no position open: checked above)
  ( crontab -l 2>/dev/null | grep -v "sniper-check $LOGF" || true; echo "*/5 * * * * /usr/local/bin/sniper-check $LOGF" ) | crontab -
  systemctl restart runner-engine; systemctl enable runner-engine >/dev/null 2>&1
  [ -f /etc/sniper/telegram.env ] && { systemctl restart runner-notify; systemctl enable runner-notify >/dev/null 2>&1; }
  echo "start line: $(startline 14)"; systemctl is-active runner-engine ;;
stop)
  systemctl stop runner-engine runner-notify; systemctl disable runner-engine runner-notify >/dev/null 2>&1 || true
  ( crontab -l 2>/dev/null | grep -v "sniper-check $LOGF" || true ) | crontab -; echo "runner stopped" ;;
status)
  for s in runner-engine runner-notify runner-ip; do printf "%-14s %s\n" "$s:" "$(systemctl is-active $s 2>/dev/null)"; done
  echo "start line: $(startline 0)"
  SNIPER_ENV=$ENV $PY "$REPO/deploy/relay_ops.py" status "$(val PNL_BASE "$ENV")" 2>&1 | grep -v "^  0x" ;;
*) echo "usage: runner_setup.sh upgrade|install|set-rpc|add-ip IP|units|relay|shooters [N]|base [--reset|--add ETH]|check|dry|live|stop|status"; exit 1 ;;
esac
