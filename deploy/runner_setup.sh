#!/bin/bash
# The runner (runbook 5bj): a second engine instance on its own wallet. Run as root (sudo). Never prints a key.
#   runner_setup.sh install   new wallet + /etc/sniper/runner.env from the template (connections copied from engine.env), the
#                             services runner-engine (DRY RUN) and runner-notify; prints the wallet address to fund
#   runner_setup.sh base      after funding: records the wallet's balance as the P&L base (PNL_BASE) and restarts the notifier
#   runner_setup.sh live      switches the send step on (SEND_MODULE) and restarts: trades for real at STAKE_MIN
#   runner_setup.sh dry       back to dry run
#   runner_setup.sh status    the wallet, the P&L against the base, the services, the last start line
set -e; REPO=$(cd "$(dirname "$0")/.." && pwd); ENV=/etc/sniper/runner.env; SRC=/etc/sniper/engine.env; PY=/opt/sniper-venv/bin/python3
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
get() { grep "^$1=" "$SRC" | head -1 | cut -d= -f2-; }
startline() { sleep "${1:-10}"; grep -h '"ev": "start"' /var/log/sniper/runner.jsonl 2>/dev/null | tail -1 | grep -o '"release": "[0-9.]*"\|"seat": "[A-Z0-9]*"\|"burst": \[[^]]*\]\|"exit_mark": [a-z]*\|"stop_loss": [0-9.]*\|"take_profit": [0-9.]*\|"hold_blocks": [0-9]*\|"attack_max": [-0-9]*\|"tier_min_bps": [0-9]*\|"tier_max_bps": [0-9]*\|"stake": \[[^]]*\]\|"dry_run": [a-z]*' | paste -sd' '; }
case "${1:-status}" in
install)
  [ -f "$ENV" ] && { echo "$ENV exists: not overwriting (runner_setup.sh status)"; exit 1; }
  [ -f "$SRC" ] || { echo "no $SRC: the sniper's env is the source of the connection settings"; exit 1; }
  for k in FEED_URL RPC_URL LOGS_RPC_URL SEQ_URL; do [ -n "$(get $k)" ] || { echo "$k missing in $SRC"; exit 1; }; done
  KEYADDR=$($PY -c "from eth_account import Account; a = Account.create(); k = a.key.hex(); print(k if k.startswith('0x') else '0x' + k, a.address)")
  KEY=${KEYADDR% *}; ADDR=${KEYADDR#* }
  umask 077
  sed -e "s|@PRIVATE_KEY@|$KEY|" -e "s|@WALLET@|$ADDR|" -e "s|@FEED_URL@|$(get FEED_URL)|" -e "s|@RPC_URL@|$(get RPC_URL)|" -e "s|@LOGS_RPC_URL@|$(get LOGS_RPC_URL)|" -e "s|@SEQ_URL@|$(get SEQ_URL)|" "$REPO/deploy/runner.env.template" > "$ENV"
  chmod 600 "$ENV"; unset KEY KEYADDR
  grep -q "^PRIVATE_KEY=0x[0-9a-fA-F]\{64\}$" "$ENV" || { echo "the key did not land in $ENV: not starting"; exit 1; }
  grep -q "@" "$ENV" && { echo "a placeholder is left in $ENV: not starting"; grep -n "@" "$ENV" | cut -d= -f1; exit 1; }
  mkdir -p /var/log/sniper
  cat > /etc/systemd/system/runner-engine.service <<UNIT
[Unit]
Description=the runner: the untaxed no-crowd tier on its own wallet (engine 6.25, runbook 5bj)
After=network-online.target chrony.service
[Service]
EnvironmentFile=$ENV
WorkingDirectory=$REPO
ExecStart=$PY $REPO/src/strategy/sniper_engine.py
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
UNIT
  cat > /etc/systemd/system/runner-notify.service <<UNIT
[Unit]
Description=the runner's telegram notifier (follows its log; never touches the engine)
After=network-online.target
[Service]
Type=simple
Environment=LOG_PATH=/var/log/sniper/runner.jsonl
Environment=SNIPER_ENV=$ENV
Environment=TG_LABEL=runner
WorkingDirectory=$REPO
ExecStart=/usr/bin/python3 $REPO/deploy/tg_notify.py
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
UNIT
  systemctl daemon-reload; systemctl enable --now runner-engine >/dev/null
  if [ -f /etc/sniper/telegram.env ]; then systemctl enable --now runner-notify >/dev/null || true; fi
  echo "runner wallet (fund this address): $ADDR"
  echo "start line: $(startline 12)"
  echo "the runner is in DRY RUN; after funding: sudo bash deploy/runner_setup.sh base ; then live" ;;
base)
  . "$ENV"
  BAL=$($PY - "$WALLET" "$RPC_URL" <<'PYEOF'
import sys, json, urllib.request
w, url = sys.argv[1], sys.argv[2]
r = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance", "params": [w, "latest"]}).encode(), headers={"content-type": "application/json"})
print("%.6f" % (int(json.load(urllib.request.urlopen(r, timeout=20))["result"], 16) / 1e18))
PYEOF
)
  [ "$BAL" != "0.000000" ] || { echo "the wallet $WALLET holds nothing yet: fund it first"; exit 1; }
  sed -i "s|^PNL_BASE=.*|PNL_BASE=$BAL|" "$ENV"; systemctl restart runner-notify 2>/dev/null || true
  echo "P&L base recorded: $BAL ETH in $WALLET" ;;
live)
  grep -q "^PNL_BASE=0$" "$ENV" && { echo "record the base first (runner_setup.sh base) so the P&L line is right"; exit 1; }
  [ -f /etc/sniper/send_step.py ] || { echo "no /etc/sniper/send_step.py (the sniper's send step): sudo cp deploy/send_step.py /etc/sniper/send_step.py"; exit 1; }
  sed -i "s|^SEND_MODULE=.*|SEND_MODULE=/etc/sniper/send_step.py|" "$ENV"; systemctl restart runner-engine
  echo "start line: $(startline 12)" ;;
dry)
  sed -i "s|^SEND_MODULE=.*|SEND_MODULE=|" "$ENV"; systemctl restart runner-engine; echo "start line: $(startline 12)" ;;
status)
  . "$ENV"
  for s in runner-engine runner-notify; do printf "%-14s %s\n" "$s:" "$(systemctl is-active $s 2>/dev/null)"; done
  echo "start line: $(startline 0)"
  SNIPER_ENV=$ENV $PY "$REPO/deploy/relay_ops.py" status "$PNL_BASE" 2>&1 | grep -v "^shooters\|low on gas" ;;
*) echo "usage: runner_setup.sh install|base|live|dry|status"; exit 1 ;;
esac
