#!/bin/bash
# One-shot setup for the sniper's machine: an EC2 instance in us-east-2 (Ohio), Ubuntu 24.04. t3.small is enough for the dry run;
# for live, c6i.large / c7i.large (two dedicated cores, no CPU credits) and PIN_CPU=1 (runbook section 3).
# Also fine on a DigitalOcean droplet in New York (Ubuntu 24.04, the $6 plan) for the E2 seat: docs/STEP_BY_STEP.md. On one
# vCPU the script leaves PIN_CPU empty; the Amazon time server line is ignored by chrony where it is unreachable.
# Installs the engine and the probe as systemd services in DRY RUN. Nothing here signs or sends a transaction.
# usage: sudo bash deploy/ohio_setup.sh   (run from a clone of the repository)
set -euo pipefail
REPO_DIR=$(cd "$(dirname "$0")/.." && pwd)
apt-get update -y && apt-get install -y python3 python3-pip python3-venv chrony git logrotate build-essential python3-dev
grep -q 169.254.169.123 /etc/chrony/chrony.conf || sed -i '1i server 169.254.169.123 prefer iburst minpoll 4 maxpoll 4' /etc/chrony/chrony.conf   # Amazon Time Sync
grep -q '^makestep 1.0 3' /etc/chrony/chrony.conf || printf 'makestep 1.0 3\nmaxslewrate 100\n' >> /etc/chrony/chrony.conf   # step only in the first 3 updates, then slew (the engine times on the monotonic clock)
systemctl enable --now chrony && systemctl restart chrony         # the second boundary is the sequencer's clock: keep ours on NTP
python3 -m venv /opt/sniper-venv && /opt/sniper-venv/bin/pip install -q websockets rlp eth-account eth-utils coincurve   # coincurve: 0.1 ms signature recovery instead of 5 ms
/opt/sniper-venv/bin/python3 -c "import coincurve, eth_keys; b = eth_keys.KeyAPI().backend.__class__.__name__; print('signature backend:', b); raise SystemExit(0 if 'CoinCurve' in b else 1)" || { echo "coincurve is not the eth-keys backend: fix before running live"; exit 1; }
sysctl -w net.ipv4.tcp_slow_start_after_idle=0 >/dev/null && grep -q tcp_slow_start_after_idle /etc/sysctl.conf || echo 'net.ipv4.tcp_slow_start_after_idle=0' >> /etc/sysctl.conf   # a warm socket keeps its window between trades
install -d -m 700 /etc/sniper /var/log/sniper
if [ -f /etc/sniper/engine.env ]; then echo "keeping the existing /etc/sniper/engine.env"; else
cat > /etc/sniper/engine.env <<'ENV'
# fill in and keep private (chmod 600). The engine runs in dry run until SEND_MODULE and PRIVATE_KEY are set (docs/STEP_BY_STEP.md).
# Comments only on their own lines: systemd reads everything after '=' as the value.
# live: SEND_MODULE=/etc/sniper/send_step.py (a copy of deploy/send_step.py) and the wallet's private key; empty = dry run
SEND_MODULE=
PRIVATE_KEY=
# FEED_SOURCE sequencer (default) or provider (detection from PROVIDER_WS, no Robinhood endpoint: runbook 0b, posture B).
# SEQ_URL: the engine keeps a warm socket to it for the send step; RPC_URL is your provider (Alchemy) for bookkeeping and the second send endpoint.
# The public https://rpc.mainnet.chain.robinhood.com works for the dry run but rate-limits; put the Alchemy HTTPS URL here before going live.
FEED_SOURCE=sequencer
PROVIDER_WS=
FEED_URL=wss://feed.mainnet.chain.robinhood.com
RPC_URL=https://rpc.mainnet.chain.robinhood.com
# LOGS_RPC_URL serves the log queries (hundreds of blocks per call): the public node; Alchemy's free tier allows ten blocks and is the chunked fallback.
LOGS_RPC_URL=https://rpc.mainnet.chain.robinhood.com
SEQ_URL=https://sequencer.mainnet.chain.robinhood.com
WALLET=0x0000000000000000000000000000000000000000
SEAT=E2
BUNDLE_MIN=3
BUNDLE_MIN_ETH=0.3
OUT1_MAX=0
OUT2_MAX=0
SEAT_WAIT_MS=300
MIN_CREATOR_SUPPLY=0.01
STOP_SELL_FRAC=0
# hours the tables cover (UTC, wraps midnight); the dead-stretch guard is off (no evidence either way)
TRADE_HOURS=12-05
MIN_RULE_PASSING_1H=0
SUPPLY_FRAC=0.03
SLIP=0.25
HOLD_S=5
TAKE_PROFIT=0.5
BANKROLL_USD=300
FRAC=0.15
STAKE_MIN=25
STAKE_MAX=300
SWITCH_N=15
SWITCH=-0.10
DAILY_STOP=0.50
MAX_RESOLVE_MS=1500
GAS_MAX_SHARE=0.05
GAS_HEADROOM=2.0
OUT1_MIN_ETH=0
TIER_ASSUMED=0.05
SEND_MODE=react
MARGIN_MS=25
REQUIRE_COINCURVE=1
PIN_CPU=1
LOG_PATH=/var/log/sniper/engine.jsonl
ENV
fi
chmod 600 /etc/sniper/engine.env                                  # this file will hold the key: owner-only
[ "$(nproc)" -ge 2 ] || sed -i 's/^PIN_CPU=1/PIN_CPU=/' /etc/sniper/engine.env   # one vCPU (the $6 droplet): nothing to pin to
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
( crontab -l 2>/dev/null | grep -v sniper-check || true; echo "*/5 * * * * /usr/local/bin/sniper-check" ) | crontab -   # a fresh machine has no crontab: without the || true, set -e ended the script here
cat > /etc/systemd/system/sniper-engine.service <<UNIT
[Unit]
Description=first-block sniper engine (dry run until submit() is replaced)
After=network-online.target chrony.service
[Service]
EnvironmentFile=/etc/sniper/engine.env
Nice=-10
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
Nice=-10
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
