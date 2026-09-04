import json,glob,bisect,collections,statistics as st,datetime,random
# Creator economics on the Pons V2 curve with exact exit proceeds: selling tokens walks the same bonding curve backwards, so the quote a creator
# can take out for their tk0 tokens at time t equals the quote the most recent buyers paid for the top tk0 tokens of cumulative sold supply (LIFO), minus the 1% fee.
DAY='2026-09-03'; H0,H1=12,18
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
    b,tx,topics,data=json.loads(line); d=data[2:]; w=[int(d[i:i+64],16) for i in range(0,len(d),64)]
    creates['0x'+topics[2][-40:].lower()]={'ts':bts(b),'creator':'0x'+topics[3][-40:].lower(),'q0':w[1]/1e18,'tk0':w[2]/1e18}
serial=collections.Counter(c['creator'] for c in creates.values())
t0day=datetime.datetime.fromisoformat(DAY+'T00:00:00+00:00').timestamp()
trades=collections.defaultdict(list)
for line in open(f'rh/v2curve_{DAY}_{H0}-{H1}.jsonl'):
    b,li,tx,addr,t0,data=json.loads(line)
    if addr not in creates: continue
    d=data[2:]; w=[int(d[i:i+64],16) for i in range(0,len(d),64)]
    trades[addr].append((b,li,t0=='0xec36bf57',(w[0] if t0=='0xec36bf57' else w[1])/1e18,(w[1] if t0=='0xec36bf57' else w[0])/1e18))
def lifo_value(stack,tk):
    # quote obtainable for tk tokens from the top of the stack
    out=0.0; need=tk
    for tokens,quote in reversed(stack):
        if need<=0: break
        take=min(tokens,need); out+=quote*take/tokens; need-=take
    return out*0.99
rows=[]
for curve,meta in creates.items():
    if not (t0day+H0*3600<=meta['ts']<t0day+H1*3600-1800): continue
    tr=sorted(trades.get(curve,[])); q0,tk0=meta['q0'],meta['tk0']
    if not tr or q0<=0 or tk0<=0: continue
    stack=[]; best=0.0; best_t=None; val_10m=None; val_60m=None; val_end=None; tp15=None; tp2=None; vol=0.0; t_launch=meta['ts']; realized=None; realized_t=None
    for b,li,buy,q,tk in tr:
        t=bts(b)-t_launch; vol+=q
        if buy: stack.append([tk,q])
        else:
            tot=sum(x[0] for x in stack)
            if realized is None and tot-tk<tk0*0.98:   # this sell eats into the creator's launch-block layer: the creator is selling
                realized=lifo_value(stack,tk0); realized_t=t
            need=tk
            while need>1e-12 and stack:
                tokens,quote=stack[-1]; take=min(tokens,need)
                if take>=tokens-1e-12: stack.pop()
                else: stack[-1]=[tokens-take,quote*(tokens-take)/tokens]
                need-=take
        v=lifo_value(stack,tk0)
        if v>best: best,best_t=v,t
        if tp15 is None and v>=1.5*q0: tp15=(v,t)
        if tp2 is None and v>=2.0*q0: tp2=(v,t)
        if val_10m is None and t>=600: val_10m=v
        if val_60m is None and t>=3600: val_60m=v
        val_end=v
    if val_10m is None: val_10m=val_end
    if val_60m is None: val_60m=val_end
    if realized is None: realized=val_end   # never sold: mark at the end-of-window curve exit
    fees=0.007*vol
    rows.append({'creator':meta['creator'],'serial':serial[meta['creator']],'q0':q0,'tk0':tk0,'n':len(tr),'fees':fees,
                 'pnl_best':best-q0,'pnl_10m':val_10m-q0,'pnl_60m':val_60m-q0,'pnl_end':val_end-q0,
                 'pnl_tp15':(tp15[0]-q0) if tp15 else val_end-q0,'pnl_tp2':(tp2[0]-q0) if tp2 else val_end-q0,'hit_tp15':tp15 is not None,'hit_tp2':tp2 is not None,'pnl_realized':realized-q0,'sold':realized_t is not None,'sold_t':realized_t})
print('launches',len(rows))
def grp(label,sel):
    g=[r for r in rows if sel(r)]
    if len(g)<30: return
    Q=sum(r['q0'] for r in g); F=sum(r['fees'] for r in g)
    def tot(k): return sum(r[k] for r in g)
    v=[(r['fees']+r['pnl_realized'])/r['q0'] for r in g if r['q0']>=0.01]
    print(f"{label:30s} n={len(g):5d} stake/launch {Q/len(g):7.3f} | fees {100*F/Q:5.1f}% of stake | trading P&L % of stake: best-time {100*tot('pnl_best')/Q:+5.0f} | TP1.5x {100*tot('pnl_tp15')/Q:+5.0f} (hit {100*sum(1 for r in g if r['hit_tp15'])/len(g):3.0f}%) | ACTUAL (sold when their layer was sold, else marked at end) {100*tot('pnl_realized')/Q:+5.0f} | fees+actual {100*(F+tot('pnl_realized'))/Q:+5.0f} | creators sold within window {100*sum(1 for r in g if r['sold'])/len(g):3.0f}% (median {st.median(r['sold_t'] for r in g if r['sold'])/60 if any(r['sold'] for r in g) else 0:.0f} min) | per-launch median (fees+actual)/stake {100*st.median(v) if v else 0:+.0f}%")
print("\n## creator seat on the Pons V2 curve (exact curve exits, 1% fee; fees = 0.7% of curve volume; % of the creator's launch-block stake)")
grp('all launches',lambda r:True); grp('serial >=10/day',lambda r:r['serial']>=10); grp('serial >=50/day',lambda r:r['serial']>=50); grp('2-9/day',lambda r:2<=r['serial']<10); grp('one-off',lambda r:r['serial']==1)
grp('stake >=1 quote unit',lambda r:r['q0']>=1); grp('stake 0.1-1',lambda r:0.1<=r['q0']<1); grp('stake <0.1',lambda r:r['q0']<0.1)
grp('initial buy >=15% supply',lambda r:r['tk0']>=0.15e9); grp('initial buy 5-15%',lambda r:0.05e9<=r['tk0']<0.15e9); grp('initial buy <5%',lambda r:r['tk0']<0.05e9)
top=collections.defaultdict(list)
for r in rows: top[r['creator']].append(r)
print("\n## busiest creators, realistic rule (fees + sell at TP1.5x else hold to end), quote units")
for c,g in sorted(top.items(),key=lambda kv:-len(kv[1]))[:8]:
    Q=sum(r['q0'] for r in g); print(f"  {c[:12]} launches {len(g):4d} staked {Q:8.1f} fees {sum(r['fees'] for r in g):6.1f} actual trading {sum(r['pnl_realized'] for r in g):+8.1f} (sold {100*sum(1 for r in g if r['sold'])/len(g):.0f}% of launches, median {st.median(r['sold_t'] for r in g if r['sold'])/60 if any(r['sold'] for r in g) else 0:.0f} min) best-time {sum(r['pnl_best'] for r in g):+8.1f} -> fees+actual {100*(sum(r['fees'] for r in g)+sum(r['pnl_realized'] for r in g))/Q:+5.0f}% of stake")
json.dump(rows,open('/home/user/fomo-memebot/data/derived/creator_seat_2026-09-03.json','w'))
