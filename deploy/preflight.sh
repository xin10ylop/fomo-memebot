#!/bin/sh
# Everything that must be true on the machine before the engine is allowed to spend money.
# Prints one line per check with ok / FAIL, and never prints the private key.
#   sudo sh deploy/preflight.sh
ENV=/etc/sniper/engine.env; LOG=/var/log/sniper/engine.jsonl; PY=/opt/sniper-venv/bin/python3
fail=0
say() { printf '%-4s %s\n' "$1" "$2"; [ "$1" = "FAIL" ] && fail=$((fail+1)); return 0; }
val() { grep -E "^$1=" "$ENV" 2>/dev/null | head -1 | cut -d= -f2- | sed 's/ #.*//'; }
has() { grep -qE "^$1=" "$ENV" 2>/dev/null; }
# what the engine actually used, from the line it logged when it started: the settings file may simply not mention a key,
# in which case the engine's own default applies and an empty value here would be misleading.
START=$(grep '"ev": "start"' "$LOG" 2>/dev/null | tail -1)
eff() { echo "$START" | grep -o "\"$1\": [^,}]*" | head -1 | cut -d: -f2- | tr -d ' "'; }
echo "=== settings"
for k in SEAT FEED_SOURCE TRADE_HOURS BUNDLE_MIN BUNDLE_MIN_ETH BUNDLE_MAX_ETH MIN_CREATOR_SUPPLY OUT1_MAX OUT2_MAX SEAT_WAIT_MS HOLD_S TAKE_PROFIT SUPPLY_FRAC SLIP FRAC STAKE_MIN STAKE_MAX DAILY_STOP SWITCH_N SWITCH MIN_FOLLOW_ETH_60 GAS_HEADROOM MAX_RESOLVE_MS; do
  if has "$k"; then printf '     %-20s %s\n' "$k" "$(val $k)"
  else
    case "$k" in
      TRADE_HOURS) e=$(eff trade_hours);; BUNDLE_MIN) e=$(eff bundle_min);; BUNDLE_MIN_ETH) e=$(eff bundle_min_eth);;
      BUNDLE_MAX_ETH) e=$(eff bundle_max_eth);; MIN_CREATOR_SUPPLY) e=$(eff min_creator_supply);; HOLD_S) e=$(eff hold_s);;
      TAKE_PROFIT) e=$(eff take_profit);; SUPPLY_FRAC) e=$(eff supply_frac);; MIN_FOLLOW_ETH_60) e=$(eff min_follow_eth_60);; *) e="";;
    esac
    printf '     %-20s %s\n' "$k" "${e:-?}  (not in the file: the engine's own default)"
  fi
done
printf '     %-20s %s\n' "WALLET" "$(val WALLET)"
printf '     %-20s %s\n' "RPC_URL" "$(val RPC_URL | sed 's#/v2/.*#/v2/(key hidden)#')"
printf '     %-20s %s\n' "LOGS_RPC_URL" "$(val LOGS_RPC_URL | sed 's#/v2/.*#/v2/(key hidden)#')"
printf '     %-20s %s\n' "PROVIDER_WS" "$(val PROVIDER_WS | sed 's#/v2/.*#/v2/(key hidden)#')"
printf '     %-20s %s\n' "SEND_MODULE" "$(val SEND_MODULE)"
echo "=== the money path"
[ -n "$(val SEND_MODULE)" ] && say ok "SEND_MODULE is set: the engine will send real transactions" || say ok "SEND_MODULE is empty: paper mode, nothing will be sent"
[ -s "$(val SEND_MODULE)" ] 2>/dev/null && say ok "the send step file exists" || { [ -z "$(val SEND_MODULE)" ] && say ok "no send step needed in paper mode" || say FAIL "SEND_MODULE points at a file that is not there"; }
[ -n "$(val PRIVATE_KEY)" ] && say ok "a private key is set (not shown)" || say ok "no private key set (paper mode)"
P=$(stat -c %a "$ENV" 2>/dev/null); [ "$P" = "600" ] && say ok "the settings file is owner-only (600)" || say FAIL "the settings file is mode $P: run chmod 600 $ENV"
if [ -n "$(val PRIVATE_KEY)" ]; then
  $PY -c "
import os,sys
sys.path.insert(0,'/root/fomo-memebot/src/strategy')
from eth_account import Account
env=dict(l.strip().split('=',1) for l in open('$ENV') if '=' in l and not l.startswith('#'))
a=Account.from_key(env['PRIVATE_KEY'].split(' #')[0].strip()).address
w=env['WALLET'].split(' #')[0].strip()
print('ok   the key matches WALLET' if a.lower()==w.lower() else 'FAIL the key is for '+a+' but WALLET is '+w)" 2>/dev/null || say FAIL "could not check the key against WALLET"
fi
echo "=== the engine"
systemctl is-active --quiet sniper-engine && say ok "the service is running" || say FAIL "the service is not running"
V=$(grep '"ev": "start"' $LOG 2>/dev/null | tail -1 | grep -o '"version": [0-9.]*' | cut -d' ' -f2)
say ok "version $V"
grep '"ev": "start"' $LOG 2>/dev/null | tail -1 | grep -q '"dry_run": false' && say ok "dry_run false: live" || say ok "dry_run true: paper"
LAST=$($PY - "$LOG" <<'PYEOF' 2>/dev/null
import json,sys,time
last={"score":0,"creation":0,"trade_done":0}
with open(sys.argv[1],'rb') as f:
    f.seek(0,2); s=f.tell(); f.seek(max(0,s-3000000))
    if s>3000000: f.readline()
    for line in f:
        try: e=json.loads(line)
        except: continue
        if e.get("ev") in last: last[e["ev"]]=max(last[e["ev"]], e.get("t") or 0)
n=time.time()
print(" ".join("%s:%.0f" % (k, (n-v)/60 if v else -1) for k,v in last.items()))
PYEOF
)
echo "     minutes since the last: $LAST  (-1 = never seen in the tail)"
case "$LAST" in *creation:-1*) say FAIL "no launch seen at all: the feed is not delivering";; esac
echo "=== the chain"
$PY - <<'PYEOF'
import json,urllib.request,time,ssl
env=dict(l.strip().split('=',1) for l in open('/etc/sniper/engine.env') if '=' in l and not l.startswith('#'))
def clean(k): return env.get(k,'').split(' #')[0].strip()
H={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'}
DEFAULTS={'RPC_URL':'https://rpc.mainnet.chain.robinhood.com','LOGS_RPC_URL':'https://rpc.mainnet.chain.robinhood.com','SEQ_URL':'https://sequencer.mainnet.chain.robinhood.com'}
for name in ('RPC_URL','LOGS_RPC_URL','SEQ_URL'):
    u=clean(name) or DEFAULTS[name]; note='' if clean(name) else ' (the engine default)'
    # the sequencer takes transactions, not queries: ask it the one thing it answers, which is what the engine pings it with
    m='eth_chainId' if name=='SEQ_URL' else 'eth_blockNumber'
    try:
        t=time.time(); r=urllib.request.urlopen(urllib.request.Request(u,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':[]}).encode(),headers=H),timeout=10)
        d=json.load(r); v=int(d['result'],16); print('ok   %-14s %s %d, %.0f ms%s'%(name,'chain' if m=='eth_chainId' else 'block',v,1000*(time.time()-t),note))
    except Exception as e: print('FAIL %-14s %s%s'%(name,str(e)[:70],note))
w=clean('WALLET')
try:
    r=urllib.request.urlopen(urllib.request.Request(clean('RPC_URL'),data=json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_getBalance','params':[w,'latest']}).encode(),headers=H),timeout=10)
    bal=int(json.load(r)['result'],16)/1e18
    px=float(json.load(urllib.request.urlopen(urllib.request.Request('https://api.coinbase.com/v2/prices/ETH-USD/spot',headers=H),timeout=10))['data']['amount'])
    print('ok   wallet %.5f ETH = $%.2f'%(bal,bal*px))
    print(('ok   ' if bal*px>=55 else 'FAIL ')+'the bankroll covers at least two $25 trades' )
except Exception as e: print('FAIL wallet balance: %s'%str(e)[:70])
PYEOF
echo "=== the box"
OFF=$(chronyc tracking 2>/dev/null | awk '/System time/ {print $4}')
[ -n "$OFF" ] && { [ "$(echo "$OFF < 0.02" | bc)" = "1" ] && say ok "clock offset ${OFF}s" || say FAIL "clock offset ${OFF}s (over 20 ms)"; } || say FAIL "chrony is not answering"
D=$(df -P / | awk 'NR==2{print $5}' | tr -d '%'); [ "$D" -lt 90 ] && say ok "disk ${D}% used" || say FAIL "disk ${D}% used"
[ -x /usr/local/bin/sniper-check ] && grep -q "scored none" /usr/local/bin/sniper-check 2>/dev/null && say ok "the watchdog is the current one (catches a blind gauge)" || say FAIL "old or missing watchdog: install -m 755 deploy/sniper-check.sh /usr/local/bin/sniper-check"
crontab -l 2>/dev/null | grep -q sniper-check && say ok "the watchdog runs from cron" || say FAIL "the watchdog is not in cron"
$PY -c "import coincurve, eth_keys; b=eth_keys.KeyAPI().backend.__class__.__name__; print(('ok   ' if 'CoinCurve' in b else 'FAIL ')+'signature backend '+b)"
if [ -f /etc/logrotate.d/sniper ]; then
  N=$(ls /var/log/sniper/engine.jsonl.* 2>/dev/null | grep -c '[0-9]$')
  say ok "log rotation is configured ($N rotated file(s) present)"
else
  say FAIL "log rotation is not configured: no /etc/logrotate.d/sniper"
fi
echo
[ "$fail" = "0" ] && echo "PREFLIGHT PASSED: nothing is blocking a live start" || echo "PREFLIGHT: $fail check(s) failed above - fix them before going live"
