import json,glob,os,collections,statistics as st,bisect,math
REPO='/home/user/fomo-memebot'
tm=json.load(open(f'{REPO}/data/derived/token_metrics.json'))
cls={x['handle']:x for x in json.load(open(f'{REPO}/data/derived/trader_classification.json'))}
lb={}
for w in ('all','30d','7d','24h'):
    for t in json.load(open(f'fapi/lb/{w}.json'))['traders']: lb.setdefault(t['handle'],t)
_cc={}
def candles(a):
    if a in _cc: return _cc[a]
    out=None
    for f in (f'gt/ohlcv1m/{a}.json',f'gt/ohlcv/{a}.json'):
        if os.path.exists(f):
            cs=sorted(json.load(open(f)).get('candles') or [],key=lambda x:x[0])
            if cs: out=(cs,[c[0] for c in cs]); break
    _cc[a]=out; return out
def px_at(a,ts):
    c=candles(a)
    if not c: return None
    cs,T=c; i=bisect.bisect_right(T,ts)-1
    return cs[i][4] if i>=0 and ts-T[i]<3600*6 else None
def ret_before(a,ts,secs):
    p1=px_at(a,ts); p0=px_at(a,ts-secs); return (p1/p0-1) if p0 and p1 else None
def max_after(a,ts,secs):
    c=candles(a)
    if not c: return None
    cs,T=c; i=bisect.bisect_right(T,ts); j=bisect.bisect_right(T,ts+secs)
    seg=[x[4] for x in cs[i:j]]; return max(seg) if seg else None
# ---- build positions with fill detail
pos=[]
def add(h,chain,a,fills):
    fills.sort(key=lambda r:r['ts']); buys=[r for r in fills if r['side']=='buy']; sells=[r for r in fills if r['side']=='sell']
    if not buys: return
    if any(r.get('usd') is None for r in fills): return
    inv=sum(r['usd'] for r in buys); pro=sum(r['usd'] for r in sells); bought=sum(r['amt'] for r in buys); sold=sum(r['amt'] for r in sells)
    if inv<20: return
    t=tm.get(a) or {}; supply=t.get('supply'); created=t.get('created')
    fb=buys[0]; entry_px=fb['usd']/fb['amt'] if fb['amt']>0 else None
    avg_cost=inv/bought if bought>0 else None
    p={'h':h,'chain':chain,'tok':a,'sym':t.get('symbol'),'inv':inv,'pro':pro,'roi_cons':pro/inv-1,'n_buys':len(buys),'n_sells':len(sells),
       'first_ts':fb['ts'],'first_size_frac':fb['usd']/inv,'scale_in_min':(buys[-1]['ts']-fb['ts'])/60,
       'entry_fdv':entry_px*supply if (entry_px and supply) else None,'age_min':((fb['ts']-created)/60 if created else None),'launchpad':t.get('launchpad'),
       'sold_frac':(sold/bought if bought else 0),'closed':sold>=0.95*bought}
    if sells:
        fs=sells[0]; p['hold_first_sell_min']=(fs['ts']-fb['ts'])/60; p['hold_last_sell_min']=(sells[-1]['ts']-fb['ts'])/60
        p['first_sell_frac']=fs['amt']/bought if bought else None
        # exit multiples vs average cost at the time of each sell
        mults=[]; cost=0; qty=0; k=0
        for r in fills:
            if r['side']=='buy': cost+=r['usd']; qty+=r['amt']
            else:
                if qty>0 and cost>0: mults.append((r['usd']/r['amt'])/(cost/qty))
                # reduce cost basis proportionally
                if qty>0: cost*=max(0,(qty-r['amt'])/qty); qty=max(0,qty-r['amt'])
        p['exit_mults']=mults; p['first_exit_mult']=mults[0] if mults else None; p['best_exit_mult']=max(mults) if mults else None
        p['sold_within_1h']=(fs['ts']-fb['ts'])<3600
    # market context from candles
    p['pre_1h']=ret_before(a,fb['ts'],3600); p['pre_24h']=ret_before(a,fb['ts'],86400)
    mx7=max_after(a,fb['ts'],7*86400); p['peak_mult_7d']=(mx7/entry_px if (mx7 and entry_px) else None)
    if p.get('best_exit_mult') and p.get('peak_mult_7d'): p['captured']=p['best_exit_mult']/p['peak_mult_7d']
    pos.append(p)
for f in glob.glob('helius/parsed/*.ledger.json'):
    h=os.path.basename(f).split('.')[0]; g=collections.defaultdict(list)
    for r in json.load(open(f)).get('rows') or []:
        if r.get('side') in ('buy','sell') and r.get('usd') is not None and r.get('amount'): g[r['mint']].append({'ts':r['ts'],'side':r['side'],'usd':abs(r['usd']),'amt':abs(r['amount'])})
    for a,fl in g.items(): add(h,'solana',a,fl)
for f in glob.glob('rh/logs/*.ledger.json'):
    h=os.path.basename(f).split('.')[0]; g=collections.defaultdict(list)
    for r in json.load(open(f)):
        if r.get('side') in ('buy','sell'): g[r['token']].append({'ts':r['ts'],'side':r['side'],'usd':r.get('usd'),'amt':abs(r['amt'])})
    for a,fl in g.items(): add(h,'robinhood',a,fl)
pos=[p for p in pos if (tm.get(p['tok']) or {}).get('category')=='meme']
json.dump(pos,open(f'{REPO}/data/derived/behavior_positions.json','w'),default=float)
print('positions',len(pos),'traders',len({p['h'] for p in pos}),'with candles',sum(1 for p in pos if p.get('pre_1h') is not None))
# ---- trader skill: realized (bag at zero) over closed+open positions, need >=15 positions
byh=collections.defaultdict(list)
for p in pos: byh[p['h']].append(p)
skill={}
for h,ps in byh.items():
    if len(ps)<15: continue
    inv=sum(p['inv'] for p in ps); pro=sum(p['pro'] for p in ps); wins=sum(1 for p in ps if p['roi_cons']>0)/len(ps)
    skill[h]={'n':len(ps),'roi':pro/inv-1,'win':wins,'inv':inv,'med_roi':st.median(p['roi_cons'] for p in ps)}
top=sorted(skill.items(),key=lambda kv:-kv[1]['roi']); 
print('\n## traders by realized ROI (bag at zero), >=15 fully priced positions')
for h,v in top[:15]: print(f"  {h:18s} n={v['n']:4d} ROI {100*v['roi']:+6.1f}% win {100*v['win']:3.0f}% median {100*v['med_roi']:+5.1f}% invested ${v['inv']:,.0f} class={cls.get(h,{}).get('classification')} followers={lb.get(h,{}).get('followers')}")
print('  ...')
for h,v in top[-8:]: print(f"  {h:18s} n={v['n']:4d} ROI {100*v['roi']:+6.1f}% win {100*v['win']:3.0f}% median {100*v['med_roi']:+5.1f}% invested ${v['inv']:,.0f}")
winners={h for h,v in skill.items() if v['roi']>0.15 and v['win']>=0.35}; losers={h for h,v in skill.items() if v['roi']<-0.15}
print(f"\nwinners (ROI>+15%, win>=35%): {len(winners)} {sorted(winners)}\nlosers (ROI<-15%): {len(losers)}")
def q(v,p): v=sorted(v); return v[int(p*(len(v)-1))] if v else None
def desc(name,key,fmt=lambda x:f"{x:.2f}",pct=(0.25,0.5,0.75)):
    W=[p[key] for p in pos if p['h'] in winners and p.get(key) is not None]; L=[p[key] for p in pos if p['h'] in losers and p.get(key) is not None]
    if not W or not L: return
    print(f"{name:42s} winners(n={len(W):4d}): "+' / '.join(fmt(q(W,x)) for x in pct)+f"   losers(n={len(L):4d}): "+' / '.join(fmt(q(L,x)) for x in pct))
m=lambda x:(f"${x/1e6:.1f}M" if x>=1e6 else f"${x/1e3:.0f}k")
mins=lambda x:(f"{x:.0f}m" if x<120 else (f"{x/60:.1f}h" if x<2880 else f"{x/1440:.1f}d"))
print("\n## SELECTION (p25 / median / p75)")
desc('entry FDV','entry_fdv',m); desc('token age at first buy','age_min',mins); desc('price change 1h before entry','pre_1h',lambda x:f"{100*x:+.0f}%"); desc('price change 24h before entry','pre_24h',lambda x:f"{100*x:+.0f}%")
print("\n## ENTRY / SIZING")
desc('position size $','inv',lambda x:f"${x:,.0f}"); desc('first buy as share of total','first_size_frac',lambda x:f"{100*x:.0f}%"); desc('number of buys','n_buys',lambda x:f"{x:.0f}"); desc('scale-in window','scale_in_min',mins)
print("\n## EXIT")
desc('hold to first sell','hold_first_sell_min',mins); desc('hold to last sell','hold_last_sell_min',mins); desc('first sell share of position','first_sell_frac',lambda x:f"{100*x:.0f}%"); desc('first exit multiple (vs avg cost)','first_exit_mult'); desc('best exit multiple','best_exit_mult'); desc('share of position sold (all time)','sold_frac',lambda x:f"{100*x:.0f}%"); desc('7d peak multiple after entry','peak_mult_7d'); desc('captured: best exit / 7d peak','captured',lambda x:f"{100*x:.0f}%")
for grp,name in ((winners,'winners'),(losers,'losers')):
    ps=[p for p in pos if p['h'] in grp]
    ex=[m2 for p in ps for m2 in p.get('exit_mults',[])]
    print(f"{name}: share of sells at <1x {100*sum(1 for x in ex if x<1)/len(ex):.0f}%, 1-1.5x {100*sum(1 for x in ex if 1<=x<1.5)/len(ex):.0f}%, 1.5-2x {100*sum(1 for x in ex if 1.5<=x<2)/len(ex):.0f}%, 2-5x {100*sum(1 for x in ex if 2<=x<5)/len(ex):.0f}%, >5x {100*sum(1 for x in ex if x>=5)/len(ex):.0f}% (n={len(ex)}); positions sold within 1h {100*sum(1 for p in ps if p.get('sold_within_1h'))/len(ps):.0f}%; never sold {100*sum(1 for p in ps if p['n_sells']==0)/len(ps):.0f}%; by launchpad {collections.Counter(p['launchpad'] for p in ps).most_common(4)}")
