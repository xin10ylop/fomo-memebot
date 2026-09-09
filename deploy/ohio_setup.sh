#!/bin/bash
# One-shot setup for the sniper's machine: an EC2 instance in us-east-2 (Ohio), Ubuntu 24.04, any small size (t3.small is enough).
# Installs the engine and the probe as systemd services in DRY RUN. Nothing here signs or sends a transaction.
# usage: sudo bash deploy/ohio_setup.sh   (run from a clone of the repository)
set -euo pipefail
REPO_DIR=$(cd "$(dirname "$0")/.." && pwd)
apt-get update -y && apt-get install -y python3 python3-pip python3-venv chrony git logrotate build-essential python3-dev
grep -q 169.254.169.123 /etc/chrony/chrony.conf || sed -i '1i server 169.254.169.123 prefer iburst minpoll 4 maxpoll 4' /etc/chrony/chrony.conf   # Amazon Time Sync
systemctl enable --now chrony && systemctl restart chrony         # the second boundary is the sequencer's clock: keep ours on NTP
python3 -m venv /opt/sniper-venv && /opt/sniper-venv/bin/pip install -q websockets rlp eth-account coincurve   # coincurve: 70 us signature recovery instead of milliseconds
install -d -m 700 /etc/sniper /var/log/sniper
cat > /etc/sniper/engine.env <<'ENV'
# fill in and keep private (chmod 600). The engine runs in dry run until submit() is replaced (runbook section 5).
# SEQ_URL is for your send step (second endpoint); the engine itself only reads RPC_URL and FEED_URL.
FEED_URL=wss://feed.mainnet.chain.robinhood.com
RPC_URL=https://REPLACE-WITH-YOUR-PROVIDER-ENDPOINT   # the public https://rpc.mainnet.chain.robinhood.com rate-limits; the engine needs a provider key
SEQ_URL=https://sequencer.mainnet.chain.robinhood.com
WALLET=0x0000000000000000000000000000000000000000
SEAT=E2
BUNDLE_MIN=3
BUNDLE_MIN_ETH=0.3
OUT1_MAX=0
MIN_CREATOR_SUPPLY=0.01
STOP_SELL_FRAC=0
SUPPLY_FRAC=0.03
SLIP=0.25
HOLD_S=7
BANKROLL_USD=300
FRAC=0.2
STAKE_MIN=50
STAKE_MAX=300
SWITCH_N=15
SWITCH=-0.10
DAILY_STOP=0.50
MAX_RESOLVE_MS=1500
GAS_MAX_SHARE=0.03
TIER_ASSUMED=0.05
SEND_MODE=react
MARGIN_MS=25
LOG_PATH=/var/log/sniper/engine.jsonl
ENV
chmod 600 /etc/sniper/engine.env                                  # this file will hold the key: owner-only
cat > /etc/logrotate.d/sniper <<'ROT'
/var/log/sniper/*.jsonl { daily rotate 14 compress missingok notifempty copytruncate }
ROT
cat > /usr/local/bin/sniper-check <<'CHK'
#!/bin/sh
# alerts (stdout -> cron mail, or set ALERT_CMD to e.g. a Telegram curl) when the engine log stalls or the clock drifts
LOG=/var/log/sniper/engine.jsonl; ALERT_CMD=${ALERT_CMD:-cat}
if [ ! -f "$LOG" ] || [ $(( $(date +%s) - $(stat -c %Y "$LOG") )) -gt 600 ]; then echo "sniper: engine log has not grown for 10 minutes" | $ALERT_CMD; fi
OFF=$(chronyc tracking 2>/dev/null | awk '/System time/ {print $4}'); if [ -n "$OFF" ] && [ "$(echo "$OFF > 0.02" | bc)" = "1" ]; then echo "sniper: clock offset ${OFF}s" | $ALERT_CMD; fi
CHK
chmod +x /usr/local/bin/sniper-check; apt-get install -y bc >/dev/null 2>&1 || true
( crontab -l 2>/dev/null | grep -v sniper-check; echo "*/5 * * * * /usr/local/bin/sniper-check" ) | crontab -
cat > /etc/systemd/system/sniper-engine.service <<UNIT
[Unit]
Description=first-block sniper engine (dry run until submit() is replaced)
After=network-online.target chrony.service
[Service]
EnvironmentFile=/etc/sniper/engine.env
WorkingDirectory=$REPO_DIR
ExecStart=/opt/sniper-venv/bin/python3 $REPO_DIR/src/strategy/sniper_engine.py
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
UNIT
cat > /etc/systemd/system/sniper-probe.service <<UNIT
[Unit]
Description=latency probe: feed boundary phase and round trips, 10 minutes, output in /var/log/sniper
After=network-online.target chrony.service
[Service]
EnvironmentFile=/etc/sniper/engine.env
WorkingDirectory=/var/log/sniper
ExecStart=/opt/sniper-venv/bin/python3 $REPO_DIR/src/strategy/latency_probe.py 600
Type=oneshot
TimeoutStartSec=900
UNIT
systemctl daemon-reload
systemctl enable --now sniper-engine
echo "engine started in dry run; log: /var/log/sniper/engine.jsonl"
echo "run the probe once:   sudo systemctl start sniper-probe && sleep 620 && cat /var/log/sniper/latency_probe.json"
echo "watch decisions:      tail -f /var/log/sniper/engine.jsonl | grep -E 'trade_decision|feed_resolution|boundary|score'"
