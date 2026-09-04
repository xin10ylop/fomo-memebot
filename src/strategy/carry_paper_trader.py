import json,urllib.request,time,datetime,os,sys
# Paper trader for the delta-neutral funding carry (section 11.5): long Robinhood spot (DexScreener price) vs short Hyperliquid perp.
# Rule (frozen): enter when trailing 7d funding annualizes >40% and |perp/spot-1|<3%; short at <=1.4x leverage (margin 70%); rebalance hedge at 10% drift; exit when 7d funding annualizes <15% or basis beyond +-8% against the position.
COINS={'CASHCAT':'0x020bfc650a365f8bb26819deaabf3e21291018b4','PONS':'0x39dbed3a2bd333467115de45665cc57f813c4571'}
NOTIONAL=10000.0; MARGIN=0.7; COST=2*0.003+0.005+2*0.00035
LOG='paper/carry_trades.jsonl'; STATE='paper/carry_state.json'
def post(p):
    req=urllib.request.Request('https://api.hyperliquid.xyz/info',data=json.dumps(p).encode(),headers={'Content-Type':'application/json'}); return json.load(urllib.request.urlopen(req,timeout=60))
def spot(addr):
    req=urllib.request.Request(f'https://api.dexscreener.com/tokens/v1/robinhood/{addr}',headers={'User-Agent':'curl/8'}); d=json.load(urllib.request.urlopen(req,timeout=60))
    ps=[p for p in d if p.get('priceUsd') and (p.get('liquidity') or {}).get('usd')]; p=max(ps,key=lambda p:p['liquidity']['usd']); return float(p['priceUsd'])
def log(ev): open(LOG,'a').write(json.dumps(ev)+'\n')
state=json.load(open(STATE)) if os.path.exists(STATE) else {}
while True:
    try:
        meta=post({"type":"metaAndAssetCtxs"}); uni={u['name']:i for i,u in enumerate(meta[0]['universe'])}; ctx=meta[1]
        now=time.time()
        for coin,addr in COINS.items():
            if coin not in uni: continue
            c=ctx[uni[coin]]; mark=float(c['markPx']); f_now=float(c['funding'])
            fh=post({"type":"fundingHistory","coin":coin,"startTime":int((now-7*86400)*1000)}); f7=sum(float(x['fundingRate']) for x in fh); ann7=f7*365/7
            sp=spot(addr); basis=mark/sp-1
            st_=state.get(coin)
            if st_ is None:
                if ann7>0.40 and abs(basis)<0.03:
                    state[coin]={'t':now,'spot0':sp,'perp0':mark,'funding':0.0,'last':now}; log({'t':now,'coin':coin,'ev':'ENTER','spot':sp,'perp':mark,'ann7':ann7,'basis':basis})
                else: log({'t':now,'coin':coin,'ev':'flat','spot':sp,'perp':mark,'ann7':ann7,'basis':basis})
            else:
                # accrue funding since last check (hourly prints)
                new=[x for x in fh if x['time']/1000>st_['last']]; st_['funding']+=sum(float(x['fundingRate']) for x in new); st_['last']=now
                b=sp/st_['spot0']-mark/st_['perp0']; eq=st_['funding']+b-COST
                log({'t':now,'coin':coin,'ev':'mark','spot':sp,'perp':mark,'ann7':ann7,'basis':basis,'funding_acc':st_['funding'],'basis_pnl':b,'equity':eq,'equity_usd':eq*NOTIONAL,'capital':NOTIONAL*(1+MARGIN)})
                if ann7<0.15 or basis>0.08 or basis<-0.08:
                    log({'t':now,'coin':coin,'ev':'EXIT','reason':('funding' if ann7<0.15 else 'basis'),'net':eq,'net_usd':eq*NOTIONAL,'days':(now-st_['t'])/86400}); state.pop(coin)
        json.dump(state,open(STATE,'w'))
    except Exception as e: log({'t':time.time(),'ev':'error','msg':str(e)[:200]})
    time.sleep(3600)
