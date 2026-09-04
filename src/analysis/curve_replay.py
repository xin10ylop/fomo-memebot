import json,glob,bisect,datetime,collections,statistics as st,sys,random
# Replay Pons V2 bonding-curve launches from curve Buy/Sell events (per-token curve contracts). Prices are in quote units per token; returns are scale-free.
DAY=sys.argv[1]; H0=int(sys.argv[2]); H1=int(sys.argv[3])
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
# creation events: topics [sig, token, curve, creator], data [creator, p1, p2]
creates={}
for line in open(f'rh/creates_v2_{DAY}.jsonl'):
    b,tx,topics,data=json.loads(line)
    if len(topics)<3: continue
    curve='0x'+topics[2][-40:].lower(); d=data[2:]; w=[int(d[i:i+64],16) for i in range(0,len(d),64)]
    creates[curve]={'b':b,'ts':bts(b),'token':'0x'+topics[1][-40:].lower(),'creator':('0x'+topics[3][-40:].lower()) if len(topics)>3 else None,'init_buy_q':(w[1]/1e18 if len(w)>1 else None),'init_buy_tk':(w[2]/1e18 if len(w)>2 else None)}
grad_tokens=set()
try:
    for x in json.load(open(f'rh/v4init_{DAY}.json')): grad_tokens.add(x['c0'].lower()); grad_tokens.add(x['c1'].lower())
except Exception: pass
serial=collections.Counter(c['creator'] for c in creates.values())
t0day=datetime.datetime.fromisoformat(DAY+'T00:00:00+00:00').timestamp()
win=[c for c in creates.values() if t0day+H0*3600<=c['ts']<t0day+H1*3600-1800]   # launches inside the window with >=30 min of data
print('V2 launches in day',len(creates),'in window (with >=30min follow-up)',len(win),'distinct creators (day)',len(serial),'creators with >=10 launches today',sum(1 for k,v in serial.items() if v>=10),'share of launches by them',100*sum(v for v in serial.values() if v>=10)/max(1,len(creates)))
# curve trades
trades=collections.defaultdict(list); n=0; bad=0
for line in open(f'rh/v2curve_{DAY}_{H0}-{H1}.jsonl'):
    b,li,tx,addr,t0,data=json.loads(line); n+=1
    if addr not in creates: continue
    d=data[2:]; w=[int(d[i:i+64],16) for i in range(0,len(d),64)]
    if len(w)<2: bad+=1; continue
    if t0=='0xec36bf57': q,tk=w[0],w[1]; buy=True     # Buy(quoteIn, tokensOut, fee, ...)
    else: tk,q=w[0],w[1]; buy=False                    # Sell(tokensIn, quoteOut, fee, ...)  [verify]
    if tk<=0 or q<=0: bad+=1; continue
    trades[addr].append((b,li,buy,q,tk))
print('curve events',n,'matched to today launches',sum(len(v) for v in trades.values()),'bad',bad,'launches with trades',len(trades))
rows=[]
for c in win:
    curve=[k for k,v in creates.items() if v is c][0] if False else None
for curve,meta in creates.items():
    if not (t0day+H0*3600<=meta['ts']<t0day+H1*3600-1800): continue
    tr=sorted(trades.get(curve,[]))
    if not tr: rows.append({'curve':curve,'creator':meta['creator'],'serial':serial[meta['creator']],'n':0}); continue
    t0=meta['ts']; ev=[]
    for b,li,buy,q,tk in tr: ev.append({'t':bts(b)-t0,'buy':buy,'q':q/1e18,'tk':tk/1e18,'p':q/tk})
    p0=ev[0]['p']
    def at(t):
        p=None
        for e in ev:
            if e['t']<=t: p=e['p']
            else: break
        return p
    def cnt(t1,buy=None): return sum(1 for e in ev if e['t']<=t1 and (buy is None or e['buy']==buy))
    def qin(t1): return sum(e['q'] for e in ev if e['t']<=t1 and e['buy'])-sum(e['q'] for e in ev if e['t']<=t1 and not e['buy'])
    r={'curve':curve,'token':meta['token'],'creator':meta['creator'],'serial':serial[meta['creator']],'init_buy_q':meta['init_buy_q'],'init_buy_pct':(100*meta['init_buy_tk']/1e9 if meta['init_buy_tk'] else None),'graduated_v4':meta['token'] in grad_tokens,'t0':t0,'hour':datetime.datetime.utcfromtimestamp(t0).hour,'n':len(ev),
       'b30':cnt(30,True),'s30':cnt(30,False),'b60':cnt(60,True),'s60':cnt(60,False),'b300':cnt(300,True),'s300':cnt(300,False),'q60':qin(60),'q300':qin(300),'q_final':qin(1e9),'first_buy_q':ev[0]['q'],
       'life_s':ev[-1]['t'],'p0':p0,'maxall':max(e['p'] for e in ev)/p0,'last':ev[-1]['p']/p0,'ev':ev}
    for s in (10,30,60,120,300,900,1800):
        p=at(s); r[f'p{s}']=(p/p0 if p else None)
    rows.append(r)
traded=[r for r in rows if r['n']>0]
print(f"launches in window {len(rows)}; with any trade {len(traded)} ({100*len(traded)/max(1,len(rows)):.0f}%); >=10 trades {sum(1 for r in traded if r['n']>=10)}; >=100 trades {sum(1 for r in traded if r['n']>=100)}")
def q(v,p): v=sorted(v); return v[int(p*(len(v)-1))] if v else None
print(f"first-buy quote p50/p90: {q([r['first_buy_q'] for r in traded],0.5):.4f} / {q([r['first_buy_q'] for r in traded],0.9):.4f}; net quote collected p50/p90/p99: {q([r['q_final'] for r in traded],0.5):.3f} / {q([r['q_final'] for r in traded],0.9):.3f} / {q([r['q_final'] for r in traded],0.99):.2f}; >=4.2 collected: {sum(1 for r in traded if r['q_final']>=4.2)}; ever 2x: {100*sum(1 for r in traded if r['maxall']>=2)/len(traded):.1f}%; ever 5x: {100*sum(1 for r in traded if r['maxall']>=5)/len(traded):.1f}%; ended below first price: {100*sum(1 for r in traded if r['last']<1)/len(traded):.0f}%; life>30min: {100*sum(1 for r in traded if r['life_s']>1800)/len(traded):.0f}%")
print(f"graduated to a v4 pool (same day): {sum(1 for r in traded if r['graduated_v4'])} of {len(traded)} traded ({100*sum(1 for r in traded if r['graduated_v4'])/max(1,len(traded)):.2f}%); creator initial buy share of supply p50/p90: {q([r['init_buy_pct'] for r in traded if r['init_buy_pct'] is not None],0.5):.2f}% / {q([r['init_buy_pct'] for r in traded if r['init_buy_pct'] is not None],0.9):.2f}%")
print(f"serial creators (>=10 launches/day): share of traded launches {100*sum(1 for r in traded if r['serial']>=10)/len(traded):.0f}%; their launches reach >=10 trades {100*sum(1 for r in traded if r['serial']>=10 and r['n']>=10)/max(1,sum(1 for r in traded if r['serial']>=10)):.0f}% vs one-off creators {100*sum(1 for r in traded if r['serial']==1 and r['n']>=10)/max(1,sum(1 for r in traded if r['serial']==1)):.0f}%")
def sim(r,t_entry,t_exit,tp=None,sl=None,clip_frac=0.02):
    p_in=None
    for e in r['ev']:
        if e['t']>=t_entry: p_in=e['p']; break
    if p_in is None: return None
    depth=max(1e-6,sum(e['q'] for e in r['ev'] if e['t']<t_entry and e['buy'])); clip=max(0.005,clip_frac*depth)   # clip = 2% of quote already in the curve, min 0.005 quote units
    cost=2*0.01+2*min(0.5,clip/depth)+(0.25 if t_entry<1 else 0.0)
    p_out=None
    for e in r['ev']:
        if e['t']<=t_entry: continue
        if e['t']>t_exit: break
        if tp and e['p']/p_in>=tp: p_out=p_in*tp; break
        if sl and e['p']/p_in<=sl: p_out=p_in*sl*0.95; break
        p_out=e['p']
    if p_out is None: p_out=p_in*0.5   # no later print: assume you exit at half (no bid)
    return p_out/p_in-1-cost
def run(label,sel,t_entry,t_exit,tp=None,sl=None):
    tr=[r for r in traded if sel(r)]
    if len(tr)<20: print(f"{label:72s} n={len(tr)} (too few)"); return
    res=[(r['hour'],sim(r,t_entry,t_exit,tp,sl)) for r in tr]; res=[(h,x) for h,x in res if x is not None]
    a=[x for h,x in res if h<(H0+H1)//2]; b=[x for h,x in res if h>=(H0+H1)//2]
    def s(v):
        if len(v)<5: return f'n={len(v)}'
        random.seed(0); bs=sorted(st.mean(random.choices(v,k=len(v))) for _ in range(400)); return f"n={len(v):5d} mean {100*st.mean(v):+6.1f}% [{100*bs[10]:+.0f},{100*bs[389]:+.0f}] med {100*st.median(v):+6.1f}% win {100*sum(1 for x in v if x>0)/len(v):3.0f}%"
    print(f"{label:72s} | fit: {s(a)} | holdout: {s(b)}")
print("\n## V2 curve scalp rules (costs: 1%+1% fees, impact of a 2%-of-curve clip both ways, no-bid exit at 0.5x)")
run('ALL traded launches: enter 10s, exit 60s',lambda r:True,10,60)
run('ALL: enter 10s, exit 300s',lambda r:True,10,300)
run('>=5 buys & 0 sells in 30s: enter 30s, exit 120s',lambda r:r['b30']>=5 and r['s30']==0,30,120)
run('>=5 buys & 0 sells in 30s: enter 30s, exit 300s, TP1.5 SL0.7',lambda r:r['b30']>=5 and r['s30']==0,30,300,1.5,0.7)
run('>=10 buys in 60s & p60>=1.5x: enter 60s, exit 300s',lambda r:r['b60']>=10 and (r['p60'] or 0)>=1.5,60,300)
run('>=10 buys in 60s & p60>=1.5x: enter 60s, exit 300s TP2 SL0.7',lambda r:r['b60']>=10 and (r['p60'] or 0)>=1.5,60,300,2.0,0.7)
run('>=20 buys in 60s: enter 60s, exit 900s',lambda r:r['b60']>=20,60,900)
run('>=20 buys in 60s: enter 60s, exit 900s TP1.5 SL0.7',lambda r:r['b60']>=20,60,900,1.5,0.7)
run('buys/sells>=3 & q300>=1: enter 300s, exit 1800s',lambda r:r['q300']>=1 and r['b300']>=3*max(1,r['s300']),300,1800)
run('buys/sells>=3 & q300>=1: enter 300s, exit 1800s TP1.5 SL0.7',lambda r:r['q300']>=1 and r['b300']>=3*max(1,r['s300']),300,1800,1.5,0.7)
run('near graduation q>=3 by 900s: enter 900s, exit 1800s',lambda r:sum(e['q'] for e in r['ev'] if e['t']<=900 and e['buy'])-sum(e['q'] for e in r['ev'] if e['t']<=900 and not e['buy'])>=3,900,1800)
run('dip: p60 < 0.7 x max(0-60s) & >=8 buys: enter 60s, exit 600s',lambda r:(r['p60'] or 1)<0.7*max(e['p'] for e in r['ev'] if e['t']<=60)/r['p0'] and r['b60']>=8,60,600)
run('one-off creator & >=10 buys 60s: enter 60s exit 900s',lambda r:r['serial']==1 and r['b60']>=10,60,900)
run('serial creator (>=10/day) & >=10 buys 60s: enter 60s exit 900s',lambda r:r['serial']>=10 and r['b60']>=10,60,900)
run('big first buy (>=0.2 quote): enter 10s, exit 300s',lambda r:r['first_buy_q']>=0.2,10,300)
run('creator init buy >=3% supply & >=10 buys 60s: enter 60s exit 900s',lambda r:(r['init_buy_pct'] or 0)>=3 and r['b60']>=10,60,900)
run('creator init buy <1% supply & >=10 buys 60s: enter 60s exit 900s',lambda r:(r['init_buy_pct'] or 0)<1 and r['b60']>=10,60,900)
run('graduated same day (hindsight): enter 60s exit 1800s',lambda r:r['graduated_v4'],60,1800)
# base rates by filter: probability of >=2x after entry point, for the filter cohorts (no costs)
print("\n## hit rates: share of cohort whose price after t=60s later exceeds 2x / 5x of the 60s price (before costs), and share that never prints again")
def hit(label,sel):
    tr=[r for r in traded if sel(r)]
    if len(tr)<20: return
    h2=h5=dead=0
    for r in tr:
        p_in=None
        for e in r['ev']:
            if e['t']>=60: p_in=e['p']; break
        if p_in is None: dead+=1; continue
        later=[e['p'] for e in r['ev'] if e['t']>60]
        if not later: dead+=1; continue
        m=max(later)/p_in; h2+= m>=2; h5+= m>=5
    print(f"  {label:60s} n={len(tr):5d} >=2x {100*h2/len(tr):5.1f}% >=5x {100*h5/len(tr):5.1f}% no-later-print {100*dead/len(tr):4.0f}%")
hit('all traded',lambda r:True); hit('>=10 buys in 60s',lambda r:r['b60']>=10); hit('>=20 buys in 60s',lambda r:r['b60']>=20); hit('>=10 buys & 0 sells in 60s',lambda r:r['b60']>=10 and r['s60']==0)
hit('serial creator >=10/day',lambda r:r['serial']>=10); hit('one-off creator',lambda r:r['serial']==1); hit('creator init buy >=3%',lambda r:(r['init_buy_pct'] or 0)>=3); hit('creator init buy <1%',lambda r:(r['init_buy_pct'] or 0)<1)
json.dump([{k:v for k,v in r.items() if k!='ev'} for r in rows],open(f'/home/user/fomo-memebot/data/derived/curve_replay_{DAY}_{H0}-{H1}.json','w'))
