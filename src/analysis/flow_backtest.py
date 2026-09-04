import json,glob,os,bisect,collections,statistics as st,sys
# Event study on live feed buy alerts using 1-minute candles: forward returns after the alert (entry = open of the NEXT 1-min candle after alert ts + delay)
lb={}
for w in ['24h','7d','30d','all']:
    for t in json.load(open(f'fapi/lb/{w}.json'))['traders']: lb[t['handle']]=t
def load(a):
    f=f'gt/ohlcv1m/{a}.json'
    if not os.path.exists(f): return None
    c=sorted(json.load(open(f))['candles'],key=lambda x:x[0])
    return {"t":[x[0] for x in c],"o":[x[1] for x in c],"h":[x[2] for x in c],"l":[x[3] for x in c],"c":[x[4] for x in c],"v":[x[5] for x in c]}
def fwd(o,ts,delay=60,hz=(300,900,1800,3600,14400)):
    i=bisect.bisect_right(o['t'],ts+delay)
    if i>=len(o['t']) or o['t'][i]-(ts+delay)>300: return None
    e=o['o'][i]; out={"entry_t":o['t'][i],"entry":e}
    for h in hz:
        j=bisect.bisect_right(o['t'],ts+delay+h)-1
        out[f"r{h}"]=(o['c'][j]/e-1) if j>i else None
    return out
al=[json.loads(l) for l in open('fapi/ws_alerts.jsonl')]
al=[a for a in al if a.get('type')=='alert' and a.get('alertType')=='buy' and a.get('tokenAddress')]
al.sort(key=lambda a:a['ts'])
# cascade features: buys on same token in prior 10 min, distinct buyers prior 30 min
by=collections.defaultdict(list)
res=[]; cache={}
for a in al:
    k=a['tokenAddress'].lower(); prior=[b for b in by[k] if a['ts']-b['ts']<=1800]
    a['_prior10']=sum(1 for b in prior if a['ts']-b['ts']<=600); a['_prior30_distinct']=len({b['trader'] for b in prior})
    by[k].append(a)
    if k not in cache: cache[k]=load(k)
    o=cache[k]
    if not o: continue
    for delay in (60,180):
        r=fwd(o,a['ts']/1000,delay)
        if r: res.append({**{x:a.get(x) for x in ['trader','token','chain','usdValue','ts','_prior10','_prior30_distinct']},"followers":lb.get(a['trader'],{}).get('followers'),"delay":delay,**r})
print("buy alerts",len(al),"with prices",len(res))
def rep(rows,label):
    for h in (300,900,1800,3600,14400):
        xs=[r[f"r{h}"] for r in rows if r.get(f"r{h}") is not None]
        if len(xs)>=5: print(f"  {label:34s} h={h:>5} n={len(xs):4d} mean={st.mean(xs):+.3f} med={st.median(xs):+.4f} p>0={sum(x>0 for x in xs)/len(xs):.2f}")
for delay in (60,180):
    rows=[r for r in res if r['delay']==delay]
    print(f"== delay {delay}s ==")
    rep(rows,"all buys")
    rep([r for r in rows if (r['followers'] or 0)>=10000],"followers>=10k")
    rep([r for r in rows if (r['usdValue'] or 0)>=20000],"size>=20k")
    rep([r for r in rows if r['_prior30_distinct']>=3],"prior30 distinct buyers>=3")
    rep([r for r in rows if r['_prior10']==0],"first buy (no prior 10m)")
    rep([r for r in rows if r['chain']=='robinhood'],"robinhood")
    rep([r for r in rows if r['chain']=='solana'],"solana")
json.dump(res,open('flow_backtest_results.json','w'))
