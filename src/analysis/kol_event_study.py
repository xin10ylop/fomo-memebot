import json,glob,os,bisect,collections,statistics as st,sys,datetime
# H1/H2: price path after leader (leaderboard trader) buys/sells on Robinhood Chain, using exact block times from the log ledger
# and 1m (preferred) / 15m candles. Entry = open of first candle after event + delay.
lb={}
for w in ['24h','7d','30d','all']:
    for t in json.load(open(f'fapi/lb/{w}.json'))['traders']: lb[t['handle']]=t
BAD=set(json.load(open('gt/ohlcv1m_bad.json'))) if os.path.exists('gt/ohlcv1m_bad.json') else set()
_cc={}
def load(a):
    if a in _cc: return _cc[a]
    out=[]
    for f,tf in ((f'gt/ohlcv1m/{a}.json',60),(f'gt/ohlcv/{a}.json',900)):
        if os.path.exists(f) and not (tf==60 and a in BAD):
            c=sorted(json.load(open(f))['candles'],key=lambda x:x[0])
            if c: out.append({"tf":tf,"t":[x[0] for x in c],"o":[x[1] for x in c],"h":[x[2] for x in c],"l":[x[3] for x in c],"c":[x[4] for x in c],"v":[x[5] for x in c]})
    _cc[a]=out; return out
def path(series,ts,delay,hz):
    for o in series:  # prefer 1m if covers
        i=bisect.bisect_right(o['t'],ts+delay)
        if i>=len(o['t']) or i==0 and o['t'][0]-ts>o['tf']*2: continue
        if o['t'][i]-(ts+delay)>o['tf']*2: continue
        e=o['o'][i]
        if not e: continue
        r={"tf":o['tf'],"entry":e}
        for h in hz:
            j=bisect.bisect_right(o['t'],ts+delay+h)-1
            r[f"r{h}"]=(o['c'][j]/e-1) if j>=i and (o['t'][j]-o['t'][i])<=h+o['tf'] else None
        j=bisect.bisect_right(o['t'],ts+delay+1800)-1
        if j>=i: r["mfe30"]=max(o['h'][i:j+1])/e-1; r["mae30"]=min(o['l'][i:j+1])/e-1
        return r
    return None
HZ=(300,900,1800,3600,14400)
events=[]
for f in glob.glob('rh/logs/*.ledger.json'):
    h=f.split('/')[-1][:-12]
    for r in json.load(open(f)):
        if r['side'] in ('buy','sell') and r['ts'] and (r['usd'] or 0)>=300:
            events.append({"h":h,"side":r['side'],"token":r['token'],"ts":r['ts'],"usd":r['usd'],"followers":lb.get(h,{}).get('followers') or 0,"age_min":((r['b']-int(r['mint'],16))/9.9/60) if r.get('mint') else None})
for f in glob.glob('helius/parsed/*.ledger.json'):
    h=f.split('/')[-1][:-12]
    for r in json.load(open(f)).get('rows',[]):
        if r.get('side') in ('buy','sell') and r.get('usd') and r['usd']>=300:
            events.append({"h":h,"side":r['side'],"token":r['mint'],"ts":r['ts'],"usd":r['usd'],"followers":lb.get(h,{}).get('followers') or 0,"age_min":None,"chain":"solana"})
for e in events: e.setdefault("chain","robinhood")
print("events",len(events),collections.Counter((e['chain'],e['side']) for e in events))
res=[]
for e in events:
    s=load(e['token'])
    if not s: continue
    for delay in (60,300):
        p=path(s,e['ts'],delay,HZ)
        if p: res.append({**e,"delay":delay,**p})
print("priced",len(res),"1m-based",sum(1 for r in res if r['tf']==60))
json.dump(res,open('kol_event_study.json','w'))
def rep(rows,label):
    for h in HZ:
        xs=[r[f"r{h}"] for r in rows if r.get(f"r{h}") is not None]
        if len(xs)>=8: print(f"  {label:40s} h={h:>5} n={len(xs):4d} mean={st.mean(xs):+.3f} med={st.median(xs):+.4f} p>0={sum(x>0 for x in xs)/len(xs):.2f}")
for side in ('buy','sell'):
    for delay in (60,300):
        rows=[r for r in res if r['side']==side and r['delay']==delay]
        print(f"\n== {side.upper()} events, entry delay {delay}s ==")
        rep(rows,"all")
        rep([r for r in rows if r['followers']>=100000],"followers>=100k")
        rep([r for r in rows if 20000<=r['followers']<100000],"followers 20k-100k")
        rep([r for r in rows if r['followers']<20000],"followers<20k")
        rep([r for r in rows if r['usd']>=5000],"usd>=5k")
        rep([r for r in rows if r['age_min'] is not None and r['age_min']<=60],"token age<=60min")
        rep([r for r in rows if r['age_min'] is not None and r['age_min']>1440],"token age>1d")
        rep([r for r in rows if r['tf']==60],"1m candles only")
        rep([r for r in rows if r['chain']=='solana'],"solana")
        rep([r for r in rows if r['chain']=='robinhood'],"robinhood")
