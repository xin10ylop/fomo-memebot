#!/bin/bash
# One-line health check of the box (runbook 5ah):   cd ~/fomo-memebot && git pull -q && sudo bash deploy/health.sh
# Services, the last start line, the engine's ten-minute flow line (feed, probe, bankroll), the last 3 hours' event counts and
# alarms, the "not fresh" refusals, the feed's last creation, an open position, and the capital/P&L line the phone gets.
R=$(cd "$(dirname "$0")/.." && pwd)
for s in sniper-engine sniper-notify $( [ -f /etc/sniper/runner.env ] && echo runner-engine runner-notify ); do printf "%-14s %s since %s\n" "$s:" "$(systemctl is-active $s)" "$(systemctl show -p ActiveEnterTimestamp --value $s | cut -d' ' -f2-3)"; done
python3 "$R/deploy/englog.py" 3 > /tmp/health.jsonl 2>/dev/null
python3 - <<'PY'
import json,time,collections,datetime as d
ev=[json.loads(l) for l in open('/tmp/health.jsonl') if l.strip()]
now=time.time(); f=lambda t: d.datetime.fromtimestamp(t,d.timezone.utc).strftime('%H:%M:%S')
st=[e for e in ev if e.get('ev')=='start']; fl=[e for e in ev if e.get('ev')=='flow']
print('start:         ' + ((f(st[-1]['t'])+' release '+str(st[-1].get('release'))+' probe '+str(st[-1].get('probe'))+' dry_run '+str(st[-1].get('dry_run'))) if st else 'no restart in the last 3 h'))
if fl: x=fl[-1]; print(f"flow {f(x['t'])} ({(now-x['t'])/60:.0f} min ago): creations seen {x.get('creations_seen')}, silent {x.get('silent_min')} min, rule-passing last 1h {x.get('rule_passing_last_1h')}, sequencer probe median {x.get('seq_rtt_med_ms')} ms, bankroll ${x.get('bankroll_usd')}")
else: print('flow:          no line yet (one every 10 min after a start)')
c=collections.Counter(e.get('ev') for e in ev); print('last 3 h:      ' + (', '.join(f"{k} {c[k]}" for k in ('creation','trade_decision','eligible_not_traded','sent_burst','burst_landing','trade_done','alarm','error','feed_stall','feed_connected','landed_inferred') if c.get(k)) or 'nothing logged'))
for e in [e for e in ev if e.get('ev') in ('alarm','error')][-4:]: print('   ', f(e['t']), e.get('ev'), e.get('stage',''), (e.get('what') or e.get('err') or '')[:150])
print('not-fresh:     ' + str(sum(1 for e in ev if 'not fresh' in json.dumps(e.get('gates') or e.get('why') or ''))) + ' refusals')
la=[e for e in ev if e.get('ev')=='creation']; print('last creation: ' + (f(la[-1]['t'])+f" ({(now-la[-1]['t'])/60:.0f} min ago)" if la else 'none in 3 h: check the feed'))
fi=[e for e in ev if e.get('ev')=='burst_landing' and e.get('filled')]; dn=[e for e in ev if e.get('ev')=='trade_done']
print('position:      ' + ('OPEN since '+f(fi[-1]['t'])+' (the sell should land within seconds)' if fi and (not dn or dn[-1]['t']<fi[-1]['t']) else 'none open'))
PY
B=$(grep -s '^TG_PNL_BASE=' /etc/sniper/telegram.env | cut -d= -f2); /opt/sniper-venv/bin/python3 "$R/deploy/relay_ops.py" status "${B:-0.021190}" 2>/dev/null | tail -2
[ -f /etc/sniper/runner.env ] && { echo "runner:        $(python3 "$R/deploy/englog.py" 24 runner 2>/dev/null | grep -h '"ev": "start"' | tail -1 | grep -o '"release": "[0-9.]*"\|"dry_run": [a-z]*' | paste -sd' ')"; }
