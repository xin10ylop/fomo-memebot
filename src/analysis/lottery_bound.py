import json,glob,os,collections,statistics as st,random,bisect
# Lottery test on Robinhood Chain: tokens a leaderboard trader bought within N minutes of mint. Supply is 1e9 for every launchpad token.
# Bounds: optimistic = buy at the first observed candle open after the leader's first buy (or at launch price when older candles are missing), sell at the best later close; realistic = hold to horizons.
pools=json.load(open('gt/pools_v3.json')); dex=json.load(open('dex/tokens.json')); c=json.load(open('rh/creators/creators.json')); mints=json.load(open('rh/mints/mints.json'))
blocks={}
for f in glob.glob('rh/blocks/blocks*.json'):
    try: blocks.update(json.load(open(f)))
    except Exception: pass
pts=sorted((int(k,16),v) for k,v in blocks.items()); xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
def bts(b):
    b=int(b,16) if isinstance(b,str) else b; i=bisect.bisect_left(xs,b)
    if i<=0: return ys[0]-(xs[0]-b)/9.9
    if i>=len(xs): return ys[-1]+(b-xs[-1])/9.9
    x0,y0,x1,y1=xs[i-1],ys[i-1],xs[i],ys[i]; return y0+(y1-y0)*(b-x0)/(x1-x0) if x1>x0 else y0
lb={}
for w in ('all','30d','7d','24h'):
    for t in json.load(open(f'fapi/lb/{w}.json'))['traders']: lb.setdefault(t['handle'],t)
firsts={}   # token -> first leaderboard buy
for f in glob.glob('rh/logs/*.ledger.json'):
    h=os.path.basename(f).split('.')[0]
    for r in json.load(open(f)):
        if r['side']=='buy':
            a=r['token']
            if a not in firsts or r['ts']<firsts[a]['ts']: firsts[a]={'h':h,'ts':r['ts'],'usd':r.get('usd'),'px':r.get('px'),'followers':lb.get(h,{}).get('followers') or 0}
def candles(a):
    out=[]
    for f in (f'gt/ohlcv1m/{a}.json',f'gt/ohlcv/{a}.json'):
        if os.path.exists(f):
            d=json.load(open(f)); cs=sorted(d.get('candles') or [],key=lambda x:x[0])
            if cs: out.append(cs)
    return out
def alive(a):
    p=pools.get(a) or {}; liq=max([float(x.get('liq') or 0) for x in p.get('pools',[])],default=0)
    d=dex.get(a) or {}
    for pr in d.get('pairs',[]): liq=max(liq,float((pr.get('liquidity') or {}).get('usd') or 0))
    fdv=float(p['fdv']) if p.get('fdv') else None
    return liq,fdv
rows=[]
for a,fb in firsts.items():
    m=mints.get(a)
    if not m: continue
    mint_ts=bts(m); age=(fb['ts']-mint_ts)/60
    if age<0 or age>24*60: continue
    liq,fdv_now=alive(a); cs=candles(a)
    r={'tok':a,'h':fb['h'],'followers':fb['followers'],'age_min':age,'liq_now':liq,'fdv_now':fdv_now,'has_candles':bool(cs),'launchpad':(c.get(a) or {}).get('factory')}
    if cs:
        s=cs[0]; ts=[x[0] for x in s]
        i=bisect.bisect_right(ts,fb['ts'])   # first candle starting after the buy
        if i<len(s):
            entry=s[i][1]; r['entry_fdv']=entry*1e9; r['entry_lag_min']=(s[i][0]-fb['ts'])/60
            closes=[x[4] for x in s[i:]]; times=[x[0] for x in s[i:]]
            r['best_close_mult']=max(closes)/entry; r['last_close_mult']=closes[-1]/entry
            for H,name in ((3600,'1h'),(4*3600,'4h'),(86400,'24h'),(3*86400,'3d'),(7*86400,'7d'),(14*86400,'14d'),(30*86400,'30d')):
                j=bisect.bisect_right(times,fb['ts']+H)-1
                r['r_'+name]=closes[j]/entry-1 if j>=0 and times[j]>=fb['ts']+H*0.5 else None
            r['first_candle_open_fdv']=s[0][1]*1e9; r['candles_start_lag_min']=(s[0][0]-mint_ts)/60
    rows.append(r)
print('tokens with a leaderboard buy within 24h of mint:',len(rows),'| with candles',sum(1 for r in rows if r['has_candles']),'| alive now (liq>$1k)',sum(1 for r in rows if r['liq_now']>1000),'| priced entry',sum(1 for r in rows if r.get('entry_fdv')))
def q(v,p): v=sorted(v); return v[int(p*(len(v)-1))] if v else None
ef=[r['entry_fdv'] for r in rows if r.get('entry_fdv')]; print('entry FDV quantiles (priced):',[round(q(ef,p)) for p in (0.1,0.25,0.5,0.75,0.9)])
lo=[r['first_candle_open_fdv'] for r in rows if r.get('first_candle_open_fdv') and r['candles_start_lag_min']<30]; print('launch-candle open FDV (candles start <30min after mint):',[round(q(lo,p)) for p in (0.1,0.5,0.9)],'n',len(lo))
def report(sub,label):
    n=len(sub); dead=[r for r in sub if not r.get('entry_fdv')]
    priced=[r for r in sub if r.get('entry_fdv')]
    print(f"\n## {label}: n={n}, no candles/dead={len(dead)} ({100*len(dead)/max(1,n):.0f}%), priced={len(priced)}")
    for H in ('1h','4h','24h','3d','7d','14d','30d'):
        v=[r['r_'+H] for r in priced if r.get('r_'+H) is not None]
        if not v: continue
        cons=v+[-1.0]*len(dead)    # dead tokens = -100%
        print(f"  hold {H:>3}: priced n={len(v):3d} mean {100*st.mean(v):7.1f}% median {100*st.median(v):6.1f}% hit>+100%: {100*sum(1 for x in v if x>1)/len(v):4.0f}%  | with dead=-100%: mean {100*st.mean(cons):7.1f}% ")
    bc=[r['best_close_mult'] for r in priced]
    if bc:
        opt=[x-1 for x in bc]+[-1.0]*len(dead)
        print(f"  OPTIMISTIC (sell at best later close, dead=-100%): mean {100*st.mean(opt):.0f}%  share of tokens ever ≥2x {100*sum(1 for x in bc if x>=2)/len(bc):.0f}% (of priced), ≥10x {100*sum(1 for x in bc if x>=10)/len(bc):.0f}%, ≥50x {100*sum(1 for x in bc if x>=50)/len(bc):.0f}% ; ≥10x of ALL incl dead {100*sum(1 for x in bc if x>=10)/n:.1f}%")
        big=sorted(priced,key=lambda r:-r['best_close_mult'])[:5]; print('  top runners:',[(r['tok'][:8],round(r['best_close_mult'],1),round(r['entry_fdv']),r['h']) for r in big])
report(rows,'all leaderboard first buys within 24h of mint')
report([r for r in rows if r['age_min']<=60],'within 60 min of mint')
report([r for r in rows if r['age_min']<=60 and r['followers']>=30000],'within 60 min, trader followers ≥30k')
report([r for r in rows if r.get('entry_fdv') and r['entry_fdv']<2e5] + [r for r in rows if not r.get('entry_fdv') and r['age_min']<=60],'entry FDV < $200k (dead assumed micro)')
json.dump(rows,open('/home/user/fomo-memebot/data/derived/lottery_rh.json','w'))
