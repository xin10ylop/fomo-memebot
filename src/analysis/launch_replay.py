import json,glob,bisect,datetime,collections,statistics as st,sys,math,random
# Replay every launch of one day from the v4 swap stream: features in the first minutes, outcomes, filter/scalp backtests with V2 costs.
DAY=sys.argv[1] if len(sys.argv)>1 else '2026-09-03'
blocks={}
for f in glob.glob('rh/blocks/blocks*.json'):
    try: blocks.update(json.load(open(f)))
    except Exception: pass
pts=sorted((int(k,16),v) for k,v in blocks.items()); xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
def bts(b):
    i=bisect.bisect_left(xs,b)
    if i<=0: return ys[0]-(xs[0]-b)/9.9
    if i>=len(xs): return ys[-1]+(b-xs[-1])/9.9
    x0,y0,x1,y1=xs[i-1],ys[i-1],xs[i],ys[i]; return y0+(y1-y0)*(b-x0)/(x1-x0)
eth=json.load(open('prices/eth_3d.json'))['prices']; et=[p[0]/1000 for p in eth]; ep=[p[1] for p in eth]
def ethusd(ts):
    i=bisect.bisect_right(et,ts)-1; i=max(0,min(i,len(et)-2)); return ep[i]+(ep[i+1]-ep[i])*(ts-et[i])/(et[i+1]-et[i])
launches=[x for x in json.load(open('rh/launches_all.json')) if datetime.datetime.utcfromtimestamp(x['ts']).strftime('%Y-%m-%d')==DAY]
tok2launch={x['t1']:x for x in launches}
init=json.load(open(f'rh/v4init_{DAY}.json')); pool_meta={}
for x in init:
    c0=x['c0'][2:].lower(); c1=x['c1'][2:].lower()
    if c1 in tok2launch: pool_meta[x['pid']]={'launch':tok2launch[c1],'tok_is_c1':True,'quote':c0,'hooks':x['hooks'],'fee':x['fee']}
    elif c0 in tok2launch: pool_meta[x['pid']]={'launch':tok2launch[c0],'tok_is_c1':False,'quote':c1,'hooks':x['hooks'],'fee':x['fee']}
pad_creator={}; pad_grad=set()
try:
    for line in open(f'rh/creates_pad_{DAY}.jsonl'):
        b,tx,topics,data=json.loads(line)
        if topics[0].startswith('0x8d4aad49') and len(topics)>3: pad_creator['0x'+topics[1][-40:].lower()]='0x'+topics[3][-40:].lower()
        if topics[0].startswith('0xcdb72f15'): pad_grad.add('0x'+topics[1][-40:].lower())
except Exception as e: print('no pad creates',e)
pad_serial=collections.Counter(pad_creator.values())
QUOTE_DEC={'0000000000000000000000000000000000000000':18,'0bd7d308f8e1639fab988df18a8011f41eacad73':18,'c1a0957594a80aa55a12e76ae4cdf513e84301c7':6}
# stream swaps: [block, logIndex, tx, poolId, amount0, amount1, sqrtPriceX96, liquidity]
by_pool=collections.defaultdict(list); pool2launch={}
n=0
import itertools
for line in itertools.chain.from_iterable(open(p) for p in sorted(glob.glob(f'rh/v4swaps_{DAY}.p*.jsonl'))):
    try: b,li,tx,pid,a0,a1,sp,liq=json.loads(line)
    except Exception: continue
    n+=1
    if pid in pool_meta: by_pool[pid].append((b,li,a0,a1,sp,liq))
pool2launch={pid:m['launch'] for pid,m in pool_meta.items() if pid in by_pool}
print(f"swaps {n}, launches today {len(launches)}, pools initialized for launches {len(pool_meta)}, with swaps {len(pool2launch)}; quotes {collections.Counter(m['quote'][:6] for m in pool_meta.values()).most_common(4)}")
# per launch features
rows=[]
for pid,L in pool2launch.items():
    sw=sorted(x for x in by_pool[pid] if x[5]>0)   # drop zero-liquidity prints (pool initialisation artefacts)
    if len(sw)<2: continue
    t0=bts(sw[0][0]); meta=pool_meta[pid]
    if meta['quote'] not in QUOTE_DEC: continue   # only ETH/WETH/USDG-quoted launches
    qdec=QUOTE_DEC[meta['quote']]; tok_is_c1=meta['tok_is_c1']
    def px(sp):   # price of token in quote units
        r=(sp/2**96)**2   # c1 per c0 in raw units
        if r<=0: return None
        return (1/r)*10**(18-qdec) if tok_is_c1 else r*10**(18-qdec)
    qusd=1.0 if qdec==6 else None
    p0=px(sw[0][4])
    if not p0: continue
    ev=[]
    for b,li,a0,a1,sp,liq in sw:
        ts=bts(b); buy=(a1>0) if tok_is_c1 else (a0>0)   # user receives the token
        qamt=abs(a0 if tok_is_c1 else a1)/10**qdec; qeth=qamt if qdec==18 else qamt/ethusd(ts)
        ev.append({'t':ts-t0,'buy':buy,'eth':qeth,'p':px(sp)})
    def at(t):
        # last price at or before t seconds after launch
        p=None
        for e in ev:
            if e['t']<=t: p=e['p']
            else: break
        return p
    def mx(t0s,t1s): 
        v=[e['p'] for e in ev if t0s<e['t']<=t1s]; return max(v) if v else None
    def cnt(t1s,buy=None): return sum(1 for e in ev if e['t']<=t1s and (buy is None or e['buy']==buy))
    def ethin(t1s): return sum(e['eth'] for e in ev if e['t']<=t1s and e['buy'])-sum(e['eth'] for e in ev if e['t']<=t1s and not e['buy'])
    total_eth=ethin(1e9)
    r={'venue':L['venue'],'tok':L['t1'],'t0':t0,'hour':datetime.datetime.utcfromtimestamp(t0).hour,'p0':p0,'n_swaps':len(ev),'usd0':p0*1e9*(ethusd(t0) if qdec==18 else 1.0),'quote':meta['quote'][:6],
       'b60':cnt(60,True),'s60':cnt(60,False),'b300':cnt(300,True),'s300':cnt(300,False),'b900':cnt(900,True),'eth60':ethin(60),'eth300':ethin(300),'eth_final':total_eth,
       'launch_buy_eth':ev[0]['eth'] if ev[0]['buy'] else 0.0,'creator':pad_creator.get('0x'+L['t1']),'serial':pad_serial.get(pad_creator.get('0x'+L['t1']),0),'grad_event':('0x'+L['t1']) in pad_grad,
       'life_s':ev[-1]['t'],'graduated':total_eth>=4.2}
    for s in (10,30,60,120,300,900,1800,3600,6*3600):
        p=at(s); r[f'p{s}']=(p/p0 if p else None)
    r['max60']=(mx(0,60) or p0)/p0; r['max300']=(mx(0,300) or p0)/p0; r['max3600']=(mx(0,3600) or p0)/p0; r['maxall']=max(e['p'] for e in ev)/p0; r['last']=ev[-1]['p']/p0
    r['ev']=ev
    rows.append(r)
print(f"launches with price path {len(rows)}; venues {collections.Counter(r['venue'] for r in rows)}")
def q(v,p): v=sorted(v); return v[int(p*(len(v)-1))] if v else None
print(f"launch FDV (USD, first swap) p10/p50/p90: {q([r['usd0'] for r in rows],0.1):,.0f} / {q([r['usd0'] for r in rows],0.5):,.0f} / {q([r['usd0'] for r in rows],0.9):,.0f}")
print(f"swaps per launch p50/p90/p99: {q([r['n_swaps'] for r in rows],0.5)} / {q([r['n_swaps'] for r in rows],0.9)} / {q([r['n_swaps'] for r in rows],0.99)}; graduated (>=4.2 ETH net): {sum(1 for r in rows if r['graduated'])} ({100*sum(1 for r in rows if r['graduated'])/len(rows):.2f}%); ever 2x: {100*sum(1 for r in rows if r['maxall']>=2)/len(rows):.1f}%; ever 10x: {100*sum(1 for r in rows if r['maxall']>=10)/len(rows):.2f}%; ended below launch: {100*sum(1 for r in rows if r['last']<1)/len(rows):.0f}%; life>1h: {100*sum(1 for r in rows if r['life_s']>3600)/len(rows):.1f}%")
# ---- scalp / filter backtests. Enter at t_entry (after the 5 s tax window), exit at t_exit or TP/SL on subsequent prints. Costs: 1% each side, hook tax 0 after 5s, impact = clip_eth / max(eth_in_curve, 0.05) per side (curve depth ~ ETH collected).
def sim(r,t_entry,t_exit,tp=None,sl=None,clip_eth=0.05):
    p_in=None
    for e in r['ev']:
        if e['t']>=t_entry: p_in=e['p']; break   # first print at/after entry time (the trade itself would be the next print; conservative: use next price)
    if p_in is None: return None
    depth=max(0.05,sum(e['eth'] for e in r['ev'] if e['t']<t_entry and e['buy'])); cost=2*0.01+2*min(0.5,clip_eth/depth)
    p_out=None
    for e in r['ev']:
        if e['t']<=t_entry: continue
        if e['t']>t_exit: break
        if tp and e['p']/p_in>=tp: p_out=p_in*tp; break
        if sl and e['p']/p_in<=sl: p_out=p_in*sl*0.95; break   # stop fills worse
        p_out=e['p']
    if p_out is None: p_out=p_in*0.5   # no later print: no bid, assume exit at half
    return min(9.0,p_out/p_in-1-cost)
def run(label,sel,t_entry,t_exit,tp=None,sl=None,clip=0.05):
    tr=[r for r in rows if sel(r)]
    if len(tr)<20: print(f"{label:70s} n={len(tr)} (too few)"); return
    res=[(r['hour'],sim(r,t_entry,t_exit,tp,sl,clip)) for r in tr]; res=[(h,x) for h,x in res if x is not None]
    if not res: return
    a=[x for h,x in res if h<12]; b=[x for h,x in res if h>=12]
    def s(v): 
        if not v: return 'n=0'
        random.seed(0); bs=sorted(st.mean(random.choices(v,k=len(v))) for _ in range(500)); return f"n={len(v):5d} mean {100*st.mean(v):+6.1f}% [{100*bs[12]:+.0f},{100*bs[487]:+.0f}] med {100*st.median(v):+6.1f}% win {100*sum(1 for x in v if x>0)/len(v):3.0f}%"
    print(f"{label:70s} | h0-11: {s(a)} | h12-23: {s(b)}")
print("\n## scalp rules (entry at t_entry seconds after launch, exit at t_exit or TP/SL), costs 2% + impact for a 0.05 ETH clip; split by hour of day (fit/holdout)")
run('ALL launches: enter 10s, exit 60s',lambda r:True,10,60)
run('ALL launches: enter 10s, exit 300s',lambda r:True,10,300)
run('>=5 buys in first 30s: enter 30s, exit 120s',lambda r:cnt_ok(r,30,5) if False else sum(1 for e in r['ev'] if e['t']<=30 and e['buy'])>=5,30,120)
run('>=10 buys & 0 sells in first 30s: enter 30s, exit 120s',lambda r:sum(1 for e in r['ev'] if e['t']<=30 and e['buy'])>=10 and sum(1 for e in r['ev'] if e['t']<=30 and not e['buy'])==0,30,120)
run('>=10 buys in 60s & price >=1.5x at 60s: enter 60s, exit 300s',lambda r:r['b60']>=10 and (r['p60'] or 0)>=1.5,60,300)
run('>=10 buys in 60s & price >=1.5x at 60s: enter 60s, exit 300s, TP2x SL0.7',lambda r:r['b60']>=10 and (r['p60'] or 0)>=1.5,60,300,2.0,0.7)
run('>=20 buys in 60s: enter 60s, exit 900s',lambda r:r['b60']>=20,60,900)
run('>=20 buys in 60s: enter 60s, exit 900s, TP1.5x SL0.7',lambda r:r['b60']>=20,60,900,1.5,0.7)
run('eth in >=0.5 by 60s: enter 60s, exit 600s',lambda r:r['eth60']>=0.5,60,600)
run('eth in >=1 by 300s & buys/sells>=3: enter 300s, exit 1800s',lambda r:r['eth300']>=1 and r['b300']>=3*max(1,r['s300']),300,1800)
run('eth in >=1 by 300s & buys/sells>=3: enter 300s, exit 1800s TP1.5 SL0.7',lambda r:r['eth300']>=1 and r['b300']>=3*max(1,r['s300']),300,1800,1.5,0.7)
run('post-snipe dip: price at 60s <0.8x of max60 & >=8 buys: enter 60s, exit 600s',lambda r:(r['p60'] or 1)<0.8*r['max60'] and r['b60']>=8,60,600)
run('near graduation: eth in >=3 by 900s: enter 900s, exit 3600s',lambda r:r['eth_final']>=3 and sum(e['eth'] for e in r['ev'] if e['t']<=900 and e['buy'])-sum(e['eth'] for e in r['ev'] if e['t']<=900 and not e['buy'])>=3,900,3600)
run('big launch buy >=0.3 ETH: enter 10s, exit 300s',lambda r:r['launch_buy_eth']>=0.3,10,300)
run('serial creator (>=10/day) & >=10 buys 60s: enter 60s exit 900s',lambda r:r['serial']>=10 and r['b60']>=10,60,900)
run('one-off creator & >=10 buys 60s: enter 60s exit 900s',lambda r:r['serial']==1 and r['b60']>=10,60,900)
run('LONG venue, >=10 buys 60s: enter 60s exit 900s',lambda r:r['venue']=='long' and r['b60']>=10,60,900)
run('ponsV2 venue, >=10 buys 60s: enter 60s exit 900s',lambda r:r['venue']=='ponsV2' and r['b60']>=10,60,900)
run('pad_7ed5 venue, >=10 buys 60s: enter 60s exit 900s',lambda r:r['venue']=='pad_7ed5' and r['b60']>=10,60,900)
json.dump([{k:v for k,v in r.items() if k!='ev'} for r in rows],open(f'/home/user/fomo-memebot/data/derived/launch_replay_{DAY}.json','w'))
