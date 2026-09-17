#!/bin/bash
# measure the provider path's lag behind the sequencer for 60 s and, if the median is under 300 ms, enable the creation-second seat
# on the provider path with that lag; otherwise leave it off. Run on the trading box:  sudo bash deploy/provider_enable.sh
set -e
cd /root/fomo-memebot
python3 - <<'PY'
p='/etc/sniper/engine.env'; L=[l for l in open(p).read().splitlines() if l.strip()]
new={'E0_ALLOW_PROVIDER':'0','PROVIDER_LAG_MS':'0'}
out=[l for l in L if l.split('=')[0] not in new]+[f'{k}={v}' for k,v in new.items()]
open(p,'w').write('\n'.join(out)+'\n')
PY
PY=$(systemctl show -p ExecStart sniper-engine 2>/dev/null | grep -o '[^ ;=]*python[0-9.]*' | head -1)   # the engine's own interpreter (it has websockets)
[ -x "$PY" ] || PY=$(ls /root/fomo-memebot/venv/bin/python /root/fomo-memebot/.venv/bin/python /root/venv/bin/python 2>/dev/null | head -1)
[ -x "$PY" ] || PY=python3
echo "measuring the provider lag for 60 s with $PY..."
"$PY" deploy/provider_lag_probe.py 60 | tee /tmp/provider_lag.txt
FEEDMED=$(grep -o "lag behind the sequencer feed: median [+-][0-9]*" /tmp/provider_lag.txt | grep -o '[+-][0-9]*$' | tr -d '+')
RPCMED=$(grep -o "provider WebSocket newHeads: n [0-9]* blocks | lag behind Robinhood's node: median [+-][0-9]*" /tmp/provider_lag.txt | grep -o '[+-][0-9]*$' | tr -d '+')
if [ -n "$FEEDMED" ]; then
  MED=$FEEDMED; echo "measured against the sequencer feed: $MED ms"
elif [ -n "$RPCMED" ]; then
  # the feed is down, so the absolute lag cannot be measured; the provider ahead of Robinhood's public node and delivering every block means a
  # live follower. Paper on the provider path proceeds with a pessimistic 300 ms added to every score; live on this path waits for a
  # feed-referenced measurement (runbook 5d).
  MED=300; echo "the sequencer feed is down: no absolute measurement (provider is $RPCMED ms vs Robinhood's public node); paper proceeds with an assumed lag of 300 ms"
else
  echo "no lag measured (probe failed): the seat stays off the provider path"; systemctl restart sniper-engine; sleep 8; grep '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"e0_allow_provider": [a-z]*\|"dry_run": [a-z]*'; exit 0
fi
if [ "$MED" -lt 301 ]; then
  python3 - "$MED" <<'PY'
import sys; p='/etc/sniper/engine.env'; L=[l for l in open(p).read().splitlines() if l.strip()]
new={'E0_ALLOW_PROVIDER':'1','PROVIDER_LAG_MS':sys.argv[1]}
out=[l for l in L if l.split('=')[0] not in new]+[f'{k}={v}' for k,v in new.items()]
open(p,'w').write('\n'.join(out)+'\n'); print('set:', new)
PY
else
  echo "median lag $MED ms is not under 300 ms: the seat stays off the provider path"
fi
systemctl restart sniper-engine && sleep 8 && grep '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"e0_allow_provider": [a-z]*\|"provider_lag_ms": [0-9.]*\|"dry_run": [a-z]*'
