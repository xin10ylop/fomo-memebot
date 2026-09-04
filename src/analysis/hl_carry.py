import json,urllib.request,time,datetime,statistics as st,bisect,sys
# Hyperliquid funding scan + delta-neutral carry simulation (long Robinhood spot, short HL perp) for the fomo mania tokens.
def post(p):
    req=urllib.request.Request('https://api.hyperliquid.xyz/info',data=json.dumps(p).encode(),headers={'Content-Type':'application/json'}); return json.load(urllib.request.urlopen(req,timeout=60))
def funding_history(coin,days=90):
    rows=[]; s=int((time.time()-days*86400)*1000)
    while True:
        r=post({"type":"fundingHistory","coin":coin,"startTime":s})
        if not r: break
        rows+=r
        if len(r)<500: break
        s=r[-1]['time']+1; time.sleep(0.3)
    return rows
def simulate(coin,gt_candles,hl_candles,funding,margin=0.7,cost=2*0.003+0.005+2*0.00035):
    gts=[x[0] for x in gt_candles]; fund={x['time']//1000//3600*3600:float(x['fundingRate']) for x in funding}
    rows=[]
    for k in hl_candles:
        t=k['t']//1000; i=bisect.bisect_right(gts,t+3600)-1
        if i<0 or t+3600-gt_candles[i][0]>1800: continue
        rows.append({'t':t,'spot':gt_candles[i][4],'perp':float(k['c']),'f':fund.get(t,0.0)})
    cum=0; eq=[]
    for r in rows:
        cum+=r['f']; eq.append(cum+(r['spot']/rows[0]['spot']-r['perp']/rows[0]['perp']))
    days=(rows[-1]['t']-rows[0]['t'])/86400; net=eq[-1]-cost; cap=1+margin
    peak=-1e9; mdd=0
    for e in eq: peak=max(peak,e); mdd=min(mdd,e-peak)
    return {'coin':coin,'days':days,'funding':cum,'basis_end':eq[-1]-cum,'net_notional':net,'net_on_capital':net/cap,'ann_on_capital':net/cap*365/days,'max_dd_notional':mdd,'max_perp_up':max(r['perp']/rows[0]['perp']-1 for r in rows)}
if __name__=='__main__':
    tm=json.load(open('/home/user/fomo-memebot/data/derived/token_metrics.json'))
    for coin in ('CASHCAT','PONS'):
        a=[k for k,t in tm.items() if t['symbol']==coin and t['chain']=='robinhood'][0]
        gt=sorted(json.load(open(f'gt/ohlcv/{a}.json'))['candles'],key=lambda x:x[0])
        hl=json.load(open(f'hl/candles_{coin}.json')); fh=json.load(open('hl/funding.json'))[coin]
        print(simulate(coin,gt,hl,fh))
