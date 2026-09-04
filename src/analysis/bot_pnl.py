import json,glob,bisect,datetime,collections,statistics as st,itertools
DAY='2026-09-03'
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
tm=json.load(open('/home/user/fomo-memebot/data/derived/token_metrics.json'))
DEC={'native':18,'0x0bd7d308f8e1639fab988df18a8011f41eacad73':18,'0x5fc5360d0400a0fd4f2af552add042d716f1d168':6,'0xc1a0957594a80aa55a12e76ae4cdf513e84301c7':6}
PX={'native':2445.0,'0x0000000000000000000000000000000000000000':2445.0,'0x0bd7d308f8e1639fab988df18a8011f41eacad73':2445.0,'0x5fc5360d0400a0fd4f2af552add042d716f1d168':1.0,'0xc1a0957594a80aa55a12e76ae4cdf513e84301c7':1.0}
def usd(raw,q):
    dec=DEC.get(q,18); px=PX.get(q) or tm.get(q,{}).get('price')
    return raw/10**dec*px if px else None
creates={}; curve_of_tok={}
for line in open(f'rh/creates_v2_{DAY}.jsonl'):
    b,tx,topics,data=json.loads(line); cv='0x'+topics[2][-40:].lower(); tok='0x'+topics[1][-40:].lower(); creates[cv]={'tok':tok,'ts':bts(b),'creator':'0x'+topics[3][-40:].lower()}; curve_of_tok[tok]=cv
quotes=json.load(open('rh/launch_quotes_2026-09-03.json'))
bots=json.load(open('rh/bot_transfers_2026-09-03.json'))
bot_txs={tx for logs in bots.values() for l in logs for tx in [l['tx']]}
# curve events by tx (only bots' txs)
curve_by_tx=collections.defaultdict(list)
for line in open(f'rh/v2curve_{DAY}_12-18.jsonl'):
    b,li,tx,addr,t0,data=json.loads(line)
    if tx in bot_txs:
        d=data[2:]; w=[int(d[i:i+64],16) for i in range(0,len(d),64)]
        curve_by_tx[tx].append({'curve':addr,'buy':t0=='0xec36bf57','q':(w[0] if t0=='0xec36bf57' else w[1]),'tk':(w[1] if t0=='0xec36bf57' else w[0]),'b':b})
# v4 swaps by tx (bots' txs), with pool meta
init={x['pid']:x for x in json.load(open(f'rh/v4init_{DAY}.json'))}
v4_by_tx=collections.defaultdict(list)
for line in itertools.chain.from_iterable(open(p) for p in sorted(glob.glob(f'rh/v4swaps_{DAY}.p*.jsonl'))):
    try: b,li,tx,pid,a0,a1,sp,liq=json.loads(line)
    except Exception: continue
    if tx in bot_txs: v4_by_tx[tx].append({'pid':pid,'a0':a0,'a1':a1,'b':b})
print('bots',len(bots),'bot txs',len(bot_txs),'curve-event txs',len(curve_by_tx),'v4 txs',len(v4_by_tx))
summary=[]
for w,logs in bots.items():
    per=collections.defaultdict(lambda:{'spent':0.0,'recv':0.0,'spent_u':0.0,'recv_u':0.0,'tk_in':0,'tk_out':0,'first_buy_t':None,'sells_t':[],'q':None,'n_buy':0,'n_sell':0})
    txs=sorted({l['tx'] for l in logs},key=lambda t:min(l['b'] for l in logs if l['tx']==t))
    for tx in txs:
        # token flows in this tx
        for l in logs:
            if l['tx']!=tx: continue
            cv=curve_of_tok.get(l['token'])
            if cv is None: continue
            p=per[cv]; p['q']=quotes.get(cv,'native')
            if l['side']=='in': p['tk_in']+=l['amt']
            else: p['tk_out']+=l['amt']
        for e in curve_by_tx.get(tx,[]):
            if e['curve'] not in creates: continue
            p=per[e['curve']]; p['q']=quotes.get(e['curve'],'native'); u=usd(e['q'],p['q'])
            t=bts(e['b'])-creates[e['curve']]['ts']
            if e['buy']:
                p['spent']+=e['q']; p['n_buy']+=1
                if u: p['spent_u']+=u
                if p['first_buy_t'] is None: p['first_buy_t']=t
            else:
                p['recv']+=e['q']; p['n_sell']+=1; p['sells_t'].append(t)
                if u: p['recv_u']+=u
        for s in v4_by_tx.get(tx,[]):
            m=init.get(s['pid'])
            if not m: continue
            c0=m['c0'].lower(); c1=m['c1'].lower(); tok=c1 if c1 in curve_of_tok else (c0 if c0 in curve_of_tok else None)
            if not tok: continue
            cv=curve_of_tok[tok]; quote=c0 if tok==c1 else c1; qamt=s['a0'] if tok==c1 else s['a1']   # quote delta for the user: negative = paid
            p=per[cv]; u=usd(abs(qamt),quote if quote!='0x'+'0'*40 else 'native'); t=bts(s['b'])-creates[cv]['ts']
            if qamt<0:
                p['n_buy']+=1
                if u: p['spent_u']+=u
                if p['first_buy_t'] is None: p['first_buy_t']=t
            else:
                p['n_sell']+=1; p['sells_t'].append(t)
                if u: p['recv_u']+=u
    launches=[(cv,p) for cv,p in per.items() if p['spent_u']>0]
    if not launches: continue
    spent=sum(p['spent_u'] for cv,p in launches); recv=sum(p['recv_u'] for cv,p in launches)
    held=sum(1 for cv,p in launches if p['tk_out']<0.9*p['tk_in'])
    wins=sum(1 for cv,p in launches if p['recv_u']>p['spent_u'])
    fbt=[p['first_buy_t'] for cv,p in launches if p['first_buy_t'] is not None]; hold=[st.median(p['sells_t'])-p['first_buy_t'] for cv,p in launches if p['sells_t'] and p['first_buy_t'] is not None]
    if w[:10] in ('0xbc46a7f0','0x9eed092b','0xbbcea8b6','0xd91abf0e'):
        json.dump({cv:{k:v for k,v in p.items()} for cv,p in launches},open(f'rh/bot_detail_{w[:10]}.json','w'))
    summary.append({'bot':w,'launches':len(launches),'spent_usd':spent,'recv_usd':recv,'net_usd':recv-spent,'roi':recv/spent-1,'win_rate':wins/len(launches),'still_holding':held/len(launches),'buy_t_med':st.median(fbt) if fbt else None,'buy_t_p10':sorted(fbt)[len(fbt)//10] if fbt else None,'hold_med_s':st.median(hold) if hold else None,'spent_per_launch':spent/len(launches)})
summary.sort(key=lambda s:-s['launches'])
print(f"\n{'bot':12s} {'launches':>8s} {'spent $':>10s} {'received $':>11s} {'net $ (unsold=0)':>16s} {'ROI':>7s} {'win%':>5s} {'unsold%':>7s} {'buy t (s) p10/med':>18s} {'hold med (s)':>12s} {'$/launch':>9s}")
for s in summary:
    f=lambda x,r=1:('n/a' if x is None else str(round(x,r)))
    print(f"{s['bot'][:12]} {s['launches']:8d} {s['spent_usd']:10,.0f} {s['recv_usd']:11,.0f} {s['net_usd']:16,.0f} {100*s['roi']:6.1f}% {100*s['win_rate']:4.0f}% {100*s['still_holding']:6.0f}% {f(s['buy_t_p10']):>8}/{f(s['buy_t_med']):<8} {f(s['hold_med_s'],0):>12} {s['spent_per_launch']:9,.0f}")
json.dump(summary,open('/home/user/fomo-memebot/data/derived/bot_pnl_2026-09-03.json','w'))
