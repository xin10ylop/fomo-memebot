#!/bin/bash
# One-shot setup for the sniper's machine: an EC2 instance in us-east-2 (Ohio), Ubuntu 24.04, any small size (t3.small is enough).
# Installs the engine and the probe as systemd services in DRY RUN. Nothing here signs or sends a transaction.
# usage: sudo bash deploy/ohio_setup.sh   (run from a clone of the repository)
set -euo pipefail
REPO_DIR=$(cd "$(dirname "$0")/.." && pwd)
apt-get update -y && apt-get install -y python3 python3-pip python3-venv chrony git
systemctl enable --now chrony                                    # the second boundary is the sequencer's clock: keep ours on NTP
python3 -m venv /opt/sniper-venv && /opt/sniper-venv/bin/pip install -q websockets rlp eth-account
install -d /etc/sniper /var/log/sniper
cat > /etc/sniper/engine.env <<'ENV'
# fill in and keep private. The engine runs in dry run until submit() is replaced (runbook section 5).
FEED_URL=wss://feed.mainnet.chain.robinhood.com
RPC_URL=https://rpc.mainnet.chain.robinhood.com
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
UNIT
systemctl daemon-reload
systemctl enable --now sniper-engine
echo "engine started in dry run; log: /var/log/sniper/engine.jsonl"
echo "run the probe once:   sudo systemctl start sniper-probe && sleep 620 && cat /var/log/sniper/latency_probe.json"
echo "watch decisions:      tail -f /var/log/sniper/engine.jsonl | grep -E 'trade_decision|feed_resolution|boundary|score'"
