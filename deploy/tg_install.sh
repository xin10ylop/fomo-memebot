#!/bin/bash
# Installs the Telegram notifier as a service (runbook 5ai). Run as root after /etc/sniper/telegram.env holds TG_TOKEN
# (TG_CHAT is filled in here from the bot's latest message when missing).
set -e; ENV=/etc/sniper/telegram.env; REPO=$(cd "$(dirname "$0")/.." && pwd)
[ -f $ENV ] || { echo "write $ENV first (TG_TOKEN=...)"; exit 1; }; chmod 600 $ENV
if ! grep -q "^TG_CHAT=." $ENV; then
  ID=$(python3 $REPO/deploy/tg_notify.py --whoami | grep -o '\[[-0-9, ]*\]' | tr -d '[] ' | cut -d, -f1)
  [ -n "$ID" ] || { echo "the bot has no message yet: open it in Telegram, send it 'hi', run this again"; exit 1; }
  sed -i '/^TG_CHAT=/d' $ENV; echo "TG_CHAT=$ID" >> $ENV; echo "TG_CHAT set to $ID"
fi
grep -q "^TG_PNL_BASE=" $ENV || echo "TG_PNL_BASE=0.015412" >> $ENV
cat > /etc/systemd/system/sniper-notify.service <<UNIT
[Unit]
Description=sniper telegram notifier (follows the engine log; never touches the engine)
After=network-online.target
[Service]
Type=simple
WorkingDirectory=$REPO
ExecStart=/usr/bin/python3 $REPO/deploy/tg_notify.py
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload && systemctl enable --now sniper-notify >/dev/null && systemctl restart sniper-notify && sleep 3 && systemctl is-active sniper-notify && echo "notifier running; the balance | P&L line should be on your phone"
