import json,glob,bisect,datetime,collections,statistics as st,random
# (1) fit/holdout + bootstrap CI for the actual P&L of the profitable snipers; (2) generic "block-2 sniper" simulation on every launch of the window.
import sys
DAY=sys.argv[1] if len(sys.argv)>1 else '2026-09-03'; H0,H1=12,18
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
creates={}
for line in open(f'rh/creates_v2_{DAY}.jsonl'):
    b,tx,topics,data=json.loads(line); cv='0x'+topics[2][-40:].lower(); d=data[2:]; w=[int(d[i:i+64],16) for i in range(0,len(d),64)]
    creates[cv]={'ts':bts(b),'creator':'0x'+topics[3][-40:].lower(),'q0':w[1]/1e18,'tk0':w[2]/1e18,'hour':datetime.datetime.utcfromtimestamp(bts(b)).hour}
serial=collections.Counter(c['creator'] for c in creates.values())
import os
bundle=set(); bots=set(); by_curve=collections.defaultdict(list)
if os.path.exists(f'rh/bundle_wallets_{DAY}.json'):
    bw=json.load(open(f'rh/bundle_wallets_{DAY}.json')); bundle={tuple(x) for x in bw['bundle']}; bots=set(bw['bots'])
    fb=json.load(open(f'rh/first_buyers_{DAY}.json'))
    for tx,v in fb.items(): by_curve[v['curve']].append(v['from'])
has_bundle=lambda cv:any((creates[cv]['creator'],w) in bundle for w in by_curve.get(cv,[]))
quotes=json.load(open(f'rh/launch_quotes_{DAY}.json')); tm=json.load(open('/home/user/fomo-memebot/data/derived/token_metrics.json'))
DEC={'native':18,'0x0bd7d308f8e1639fab988df18a8011f41eacad73':18,'0x5fc5360d0400a0fd4f2af552add042d716f1d168':6,'0xc1a0957594a80aa55a12e76ae4cdf513e84301c7':6}
PX={'native':2445.0,'0x0bd7d308f8e1639fab988df18a8011f41eacad73':2445.0,'0x5fc5360d0400a0fd4f2af552add042d716f1d168':1.0,'0xc1a0957594a80aa55a12e76ae4cdf513e84301c7':1.0}
def usd(units,q):
    dec=DEC.get(q,18); px=PX.get(q) or tm.get(q,{}).get('price'); return units*1e18/10**dec*px if px else None
def ci(v,B=500):
    random.seed(0); n=len(v); bs=sorted(st.mean(random.choices(v,k=n)) for _ in range(B)); return bs[int(0.025*B)],bs[int(0.975*B)]
print("## (1) actual sniper P&L, fit (12-15h) vs holdout (15-18h), per-launch ROI with bootstrap CI")
for b in ('0xbc46a7f0','0x9eed092b','0xbbcea8b6'):
    if not os.path.exists(f'rh/bot_detail_{b}.json') or DAY!='2026-09-03': continue
    d=json.load(open(f'rh/bot_detail_{b}.json'))
    for part,cond in (('fit',lambda h:h<15),('holdout',lambda h:h>=15)):
        g=[(p['spent_u'],p['recv_u']) for cv,p in d.items() if cv in creates and cond(creates[cv]['hour']) and p['spent_u']>0]
        if len(g)<10: continue
        roi=[r/s-1 for s,r in g]; lo,hi=ci(roi); S=sum(s for s,r in g); R=sum(r for s,r in g)
        print(f"  {b} {part:8s} n={len(g):3d} pooled ROI {100*(R/S-1):+6.1f}% net ${R-S:,.0f} | per-launch mean {100*st.mean(roi):+6.1f}% CI[{100*lo:+.0f},{100*hi:+.0f}] median {100*st.median(roi):+.0f}% win {100*sum(1 for x in roi if x>0)/len(roi):.0f}%")
# (2) generic block-2 sniper simulation on every launch
trades=collections.defaultdict(list)
for line in open(f'rh/v2curve_{DAY}_{H0}-{H1}.jsonl'):
    b,li,tx,addr,t0,data=json.loads(line)
    if addr not in creates: continue
    d=data[2:]; w=[int(d[i:i+64],16) for i in range(0,len(d),64)]
    trades[addr].append((b,li,t0=='0xec36bf57',(w[0] if t0=='0xec36bf57' else w[1])/1e18,(w[1] if t0=='0xec36bf57' else w[0])/1e18,tx))
def lifo_value(stack,tk):
    out=0.0; need=tk
    for tokens,quote in reversed(stack):
        if need<=0: break
        take=min(tokens,need); out+=quote*take/tokens; need-=take
    return out*0.99
prior=collections.defaultdict(list)
for cv,m in creates.items(): prior[m['creator']].append(m['ts'])
for k in prior: prior[k].sort()
def prior_launches(cv):
    m=creates[cv]; return bisect.bisect_left(prior[m['creator']],m['ts'])
def sim(cv,frac=0.03,hold=7.0,tp=None,cap_usd=300.0,slip=0.0,delay=0.0):
    m=creates[cv]; tr=sorted(trades.get(cv,[])); 
    if len(tr)<2: return None
    t_launch=m['ts']; evs=[(bts(b)-t_launch,buy,q,tk,tx) for b,li,buy,q,tk,tx in tr]
    # the sniper buys right after the creator: fill at the price of the first non-creator trade (what the fastest bot paid), size frac of supply
    first=[e for e in evs[1:] if e[1]]
    if not first: return None
    if delay>0:
        later=[e for e in first if e[0]>=first[0][0]+delay]
        if not later: return None
        t_in,_,q1,tk1,_=later[0]
    else: t_in,_,q1,tk1,_=first[0]
    p_in=q1/tk1*(1+slip); tk_bot=frac*1e9
    qname=quotes.get(cv,'native'); pu=usd(p_in,qname)
    if pu is None: return None
    if tk_bot*pu>cap_usd: tk_bot=cap_usd/pu
    cost=tk_bot*p_in*1.01
    if t_in>3.0: return None      # nobody bought within 3 s: a fast bot would still have bought at the post-creator curve price; conservative: skip
    stack=[[m['tk0'],m['q0']],[tk_bot,tk_bot*p_in]]; best=0; out=None
    for t,buy,q,tk,tx in evs[1:]:
        if t<=t_in: continue
        if buy: stack.append([tk,q])
        else:
            need=tk
            while need>1e-12 and stack:
                tokens,quote=stack[-1]; take=min(tokens,need)
                if take>=tokens-1e-12: stack.pop()
                else: stack[-1]=[tokens-take,quote*(tokens-take)/tokens]
                need-=take
        v=lifo_value(stack,tk_bot)
        if tp and v>=tp*cost: out=v; break
        if t>=t_in+hold: out=v; break
    if out is None: out=lifo_value(stack,tk_bot)
    return out-cost,cost,t_in
print("\n## (2) generic block-2 sniper on every launch: buy 3% of supply at the first non-creator price, sell 7 s later into whoever bought after (exact curve exits), fees 1%+1%")
def run(label,sel,frac=0.03,hold=7.0,tp=None,cap_usd=300.0,slip=0.0,delay=0.0):
    res=[]
    for cv in creates:
        if not (creates[cv]['ts']>=datetime.datetime.fromisoformat(DAY+'T00:00:00+00:00').timestamp()+H0*3600 and creates[cv]['ts']<datetime.datetime.fromisoformat(DAY+'T00:00:00+00:00').timestamp()+H1*3600-1800): continue
        if not sel(cv): continue
        r=sim(cv,frac,hold,tp,cap_usd,slip,delay)
        if r is None: continue
        pnl,cost,t_in=r; q=quotes.get(cv,'native'); u=usd(pnl,q); c=usd(cost,q)
        if u is None: continue
        res.append((creates[cv]['hour'],pnl/cost,u,c))
    for part,cond in (('fit',lambda h:h<15),('holdout',lambda h:h>=15)):
        g=[x for x in res if cond(x[0])]
        if len(g)<20: print(f"  {label:44s} {part}: n={len(g)} too few"); continue
        roi=[x[1] for x in g]; lo,hi=ci(roi); U=sum(x[2] for x in g); C=sum(x[3] for x in g); us=sorted(x[2] for x in g); top=sum(us[-max(1,len(us)//20):])
        print(f"  {label:48s} {part:8s} n={len(g):4d} net ${U:>9,.0f} on ${C:>9,.0f} ({100*U/C:+5.1f}%) | per-launch mean {100*st.mean(roi):+6.1f}% CI[{100*lo:+.0f},{100*hi:+.0f}] median {100*st.median(roi):+.0f}% win {100*sum(1 for x in roi if x>0)/len(roi):.0f}% | top-5% launches = ${top:,.0f} of profit | worst ${us[0]:,.0f}")
print("   sensitivity of the launch-time rule (creator's first launch today, ETH-quoted, $300 cap, 3% supply)")
R=lambda cv:prior_launches(cv)==0 and quotes.get(cv)=='native'
run('baseline: first-in-line, hold 7 s',R)
run('pay 10% more than first-in-line price',R,slip=0.10)
run('pay 25% more than first-in-line price',R,slip=0.25)
run('pay 50% more (third in line)',R,slip=0.50)
run('land 0.5 s late (enter at first trade >=0.5 s after)',R,delay=0.5)
run('land 1 s late',R,delay=1.0)
run('land 2 s late',R,delay=2.0)
run('land 1 s late, hold 3 s',R,0.03,3.0,None,300.0,0.0,1.0)
run('pay 25% more AND land 1 s late',R,0.03,7.0,None,300.0,0.25,1.0)
run('6% of supply (two equal snipers share the exit)',R,0.06,7.0,None,600.0)

# hourly breakdown of the baseline rule (pooled $ ROI per hour) for regime reading
import datetime as _dt
hourly=collections.defaultdict(lambda:[0.0,0.0,0])
t0d=_dt.datetime.fromisoformat(DAY+'T00:00:00+00:00').timestamp()
for cv in creates:
    m=creates[cv]
    if not (t0d+H0*3600<=m['ts']<t0d+H1*3600-1800) or not R(cv): continue
    r=sim(cv,0.03,7.0,None,300.0)
    if r is None: continue
    pnl,cost,t_in=r; q=quotes.get(cv,'native'); u=usd(pnl,q); c=usd(cost,q)
    if u is None: continue
    h=hourly[m['hour']]; h[0]+=u; h[1]+=c; h[2]+=1
print(f"\n## {DAY} baseline rule by hour (UTC): hour, launches, net $, pooled ROI")
for h in sorted(hourly): print(f"  {h:02d}h n={hourly[h][2]:4d} net ${hourly[h][0]:>8,.0f} on ${hourly[h][1]:>8,.0f} ({100*hourly[h][0]/max(1,hourly[h][1]):+5.1f}%)")
