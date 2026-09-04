import json,glob,collections,os,random,statistics as st
REPO='/home/user/fomo-memebot'
tok=json.load(open(f'{REPO}/data/derived/token_metrics.json')); dex=json.load(open('dex/tokens.json'))
hs=json.load(open('fapi/holders_series.json')) if os.path.exists('fapi/holders_series.json') else {}
def tkey(a): return a.lower() if a and a.startswith('0x') else a
def cur_price(a):
    d=dex.get(a) or {}; ps=[p for p in d.get('pairs',[]) if p.get('priceUsd')]
    if not ps: return None
    p=max(ps,key=lambda p:float((p.get('liquidity') or {}).get('usd') or 0)); return float(p['priceUsd'])
pos=[]  # one row per (handle, token)
for f in glob.glob('helius/parsed/*.ledger.json'):
    h=os.path.basename(f).split('.')[0]; rows=json.load(open(f)).get('rows') or []
    g=collections.defaultdict(list)
    for r in rows:
        if r.get('side') in ('buy','sell') and r.get('usd') is not None: g[r['mint']].append(r)
    for a,rs in g.items():
        rs.sort(key=lambda r:r['ts']); buys=[r for r in rs if r['side']=='buy']
        if not buys: continue
        inv=sum(r['usd'] for r in buys); pro=sum(r['usd'] for r in rs if r['side']=='sell')
        bought=sum(r['amount'] for r in buys); rem=sum(r['amount'] for r in rs)
        px=cur_price(a); mark=rem*px if (px and rem>0) else 0.0
        closed=rem<=0.05*bought
        pos.append({"h":h,"tok":a,"chain":"solana","inv":inv,"pro":pro,"mark":mark,"closed":closed,"first_ts":buys[0]['ts'],"first_px":(buys[0]['usd']/buys[0]['amount'] if buys[0]['amount']>0 else None),"n_buys":len(buys)})
for f in glob.glob('rh/logs/*.ledger.json'):
    h=os.path.basename(f).split('.')[0]; rows=json.load(open(f))
    g=collections.defaultdict(list)
    for r in rows:
        if r.get('side') in ('buy','sell'): g[r['token']].append(r)
    for a,rs in g.items():
        if any(r.get('usd') is None for r in rs): continue   # only fully priced token histories
        rs.sort(key=lambda r:r['ts']); buys=[r for r in rs if r['side']=='buy']
        if not buys: continue
        inv=sum(r['usd'] for r in buys); pro=sum(r['usd'] for r in rs if r['side']=='sell')
        bought=sum(r['amt'] for r in buys); rem=sum(r['amt'] if r['side']=='buy' else -r['amt'] for r in rs)
        px=cur_price(a); mark=rem*px if (px and rem>0) else 0.0
        pos.append({"h":h,"tok":a,"chain":"robinhood","inv":inv,"pro":pro,"mark":mark,"closed":rem<=0.05*bought,"first_ts":buys[0]['ts'],"first_px":(buys[0]['usd']/buys[0]['amt'] if buys[0]['amt']>0 else None),"n_buys":len(buys)})
# enrich
for p in pos:
    t=tok.get(p['tok']) or {}
    p['entry_fdv']=p['first_px']*t['supply'] if (p['first_px'] and t.get('supply')) else None
    p['age_min']=(p['first_ts']-t['created'])/60 if t.get('created') else None
    p['launchpad']=t.get('launchpad'); p['category']=t.get('category')
    b=hs.get(p['tok']); p['holders_now']=b.get('holders_last') if b else None
    p['pnl_cons']=p['pro']-p['inv']          # remaining bags worth 0
    p['pnl_mtm']=p['pro']+p['mark']-p['inv'] # remaining bags at current price
pos=[p for p in pos if p['inv']>=20 and p['category']=='meme']
print("positions (handle,token) with full pricing:",len(pos),"traders",len({p['h'] for p in pos}),"tokens",len({p['tok'] for p in pos}))
def fdv_bucket(x):
    if x is None: return 'unknown'
    for lim,name in ((1e5,'<$100k'),(1e6,'$100k–1M'),(1e7,'$1M–10M'),(1e8,'$10M–100M')):
        if x<lim: return name
    return '>$100M'
def age_bucket(x):
    if x is None: return 'unknown'
    if x<0: return 'before pool (data err)'
    for lim,name in ((60,'<1h'),(1440,'1h–24h'),(10080,'1–7d')):
        if x<lim: return name
    return '>7d'
def summarize(groups,label):
    print(f"\n## by {label}: n_pos, n_tok, win%, median ROI, pooled ROI (cons), pooled ROI (mtm), 95% CI pooled cons (token bootstrap)")
    for k,ps in groups:
        if len(ps)<10: continue
        inv=sum(p['inv'] for p in ps); roi_c=sum(p['pnl_cons'] for p in ps)/inv; roi_m=sum(p['pnl_mtm'] for p in ps)/inv
        wins=sum(1 for p in ps if p['pnl_mtm']>0)/len(ps); med=st.median(p['pnl_mtm']/p['inv'] for p in ps)
        bytok=collections.defaultdict(list)
        for p in ps: bytok[p['tok']].append(p)
        toks=list(bytok); bs=[]
        random.seed(1)
        for _ in range(400):
            s=[bytok[random.choice(toks)] for _ in toks]; ss=[p for grp in s for p in grp]
            bs.append(sum(p['pnl_cons'] for p in ss)/max(1,sum(p['inv'] for p in ss)))
        bs.sort(); print(f"{k:28s} {len(ps):5d} {len(toks):5d} {100*wins:5.0f}% {100*med:7.1f}% {100*roi_c:8.1f}% {100*roi_m:8.1f}%   [{100*bs[10]:.0f}%, {100*bs[389]:.0f}%]  invested ${inv:,.0f}")
def grp(key,order=None):
    g=collections.defaultdict(list)
    for p in pos: g[key(p)].append(p)
    ks=order if order else sorted(g)
    return [(k,g[k]) for k in ks if k in g]
summarize(grp(lambda p:fdv_bucket(p['entry_fdv']),['<$100k','$100k–1M','$1M–10M','$10M–100M','>$100M','unknown']),'entry FDV (first buy price x supply)')
summarize(grp(lambda p:age_bucket(p['age_min']),['<1h','1h–24h','1–7d','>7d','before pool (data err)','unknown']),'token age at first buy')
summarize(grp(lambda p:p['launchpad'] or 'unknown'),'launchpad')
summarize(grp(lambda p:p['chain']),'chain')
summarize(grp(lambda p:'holders≥10k' if (p['holders_now'] or 0)>=10000 else ('holders 1k–10k' if (p['holders_now'] or 0)>=1000 else ('holders<1k' if p['holders_now'] else 'no board data'))),'current fomo holder count (boards; hindsight!)')
# fdv x chain
summarize(grp(lambda p:p['chain'][:3]+' '+fdv_bucket(p['entry_fdv'])),'chain x entry FDV')
json.dump(pos,open(f'{REPO}/data/derived/entry_outcomes.json','w'))
