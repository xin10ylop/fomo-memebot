import json,time,os,sys,urllib.request,collections,datetime,glob
"""Live PAPER trader for the dip-reversion strategy (Robinhood Chain + Solana), retail-style:
 - Universe: tokens with >=2 distinct leaderboard traders buying in the prior 24h, taken from the live fomo feed (ws_alerts.jsonl), liquidity >= 100k (DexScreener).
 - Prices: DexScreener batch polls every 30s (free, no key). 15-min return = price now vs price 15 min ago.
 - Signal: 15-min return <= -15% AND prior 1h return (t-75m -> t-15m) <= 0 (no blow-off). One position per token at a time; max 5 open.
 - Fill: next poll price after signal, cost = 0.5% app fee + 1% pool fee per side + impact 2*size/(liq/2); size $500.
 - Exit: stop -30% (poll price), or time 4h; log everything to paper/trades.jsonl. No look-ahead: decisions use only data available at the poll."""
LB=set()
for w in ['24h','7d','30d','all']:
    for t in json.load(open(f'fapi/lb/{w}.json'))['traders']: LB.add(t['handle'])
def dex_prices(addrs):
    out={}
    for i in range(0,len(addrs),30):
        chunk=addrs[i:i+30]
        try:
            req=urllib.request.Request("https://api.dexscreener.com/latest/dex/tokens/"+",".join(chunk),headers={"User-Agent":"Mozilla/5.0 curl/8"})
            d=json.load(urllib.request.urlopen(req,timeout=30))
        except Exception as e: print("dex err",e,file=sys.stderr); continue
        best={}
        for p in d.get('pairs') or []:
            a=p['baseToken']['address'].lower(); liq=(p.get('liquidity') or {}).get('usd') or 0
            if a not in best or liq>best[a][1]: best[a]=(float(p['priceUsd']) if p.get('priceUsd') else None,liq,p.get('chainId'))
        out.update(best); time.sleep(0.3)
    return out
hist=collections.defaultdict(list)   # token -> [(ts,price)]
open_pos={}; closed=[]; SIZE=500; FEE=0.015; MAXPOS=5
seen_alert_lines=0
def universe():
    global seen_alert_lines
    now=time.time(); buys=collections.defaultdict(set)
    try: lines=open('fapi/ws_alerts.jsonl').read().splitlines()
    except Exception: return {}
    for l in lines[-20000:]:
        try: d=json.loads(l)
        except: continue
        if d.get('type')!='alert' or d.get('alertType')!='buy' or not d.get('tokenAddress'): continue
        if d['ts']/1000<now-86400: continue
        if d.get('trader') in LB: buys[d['tokenAddress'].lower()].add(d['trader'])
    return {a:len(s) for a,s in buys.items() if len(s)>=2}
def log(rec):
    with open('paper/trades.jsonl','a') as f: f.write(json.dumps(rec)+"\n")
print("paper trader started",datetime.datetime.utcnow().isoformat(),file=sys.stderr,flush=True)
last_uni=0; uni={}
while True:
    now=time.time()
    if now-last_uni>60: uni=universe(); last_uni=now
    addrs=list(set(uni)|set(open_pos))
    if addrs:
        px=dex_prices(addrs)
        for a,(p,liq,chain) in px.items():
            if p: hist[a].append((now,p)); hist[a]=hist[a][-400:]
        # exits
        for a in list(open_pos):
            pos=open_pos[a]; p=(px.get(a) or (None,0,None))[0]
            if not p: continue
            ret=p/pos['entry']-1
            if ret<=-0.30 or now-pos['t']>=4*3600:
                net=ret-FEE-pos['imp']; rec={**pos,"exit_t":now,"exit":p,"gross":ret,"net":net,"reason":"stop" if ret<=-0.30 else "time"}
                closed.append(rec); log({"event":"close",**rec}); del open_pos[a]
                print(datetime.datetime.utcnow().strftime('%H:%M:%S'),"CLOSE",a[:8],f"net={net:+.3f}",rec['reason'],file=sys.stderr,flush=True)
        # signals
        for a,n in uni.items():
            if a in open_pos or len(open_pos)>=MAXPOS: continue
            p,liq,chain=px.get(a,(None,0,None))
            if not p or liq<100000: continue
            h=hist[a]
            def at(sec):
                c=[q for t,q in h if t<=now-sec]; return c[-1] if c else None
            p15=at(900); p75=at(4500)
            if not p15 or not p75: continue
            r15=p/p15-1; r1h=p15/p75-1
            if r15<=-0.15 and r1h<=0:
                imp=2*SIZE/(liq/2); pos={"token":a,"chain":chain,"t":now,"entry":p,"liq":liq,"r15":r15,"r1h":r1h,"lb_buyers_24h":n,"imp":imp}
                open_pos[a]=pos; log({"event":"open",**pos}); print(datetime.datetime.utcnow().strftime('%H:%M:%S'),"OPEN",a[:8],chain,f"r15={r15:+.3f} liq={liq:,.0f}",file=sys.stderr,flush=True)
    if int(now)%600<30: print(datetime.datetime.utcnow().strftime('%H:%M:%S'),"universe",len(uni),"tracked",len(addrs),"open",len(open_pos),"closed",len(closed),"net sum",round(sum(c['net'] for c in closed),3),file=sys.stderr,flush=True)
    time.sleep(30)
