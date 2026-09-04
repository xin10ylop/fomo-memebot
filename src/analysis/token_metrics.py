import json,glob,gzip,csv,collections,os,sys,datetime,statistics as st,bisect
sys.path.insert(0,'/home/user/fomo-memebot/src/analysis')
REPO='/home/user/fomo-memebot'
# ---- block timestamps (Robinhood Chain)
blocks={}
for _f in glob.glob('rh/blocks/blocks*.json'):
    try: blocks.update(json.load(open(_f)))
    except Exception: pass
_pts=sorted((int(k,16),v) for k,v in blocks.items()); _xs=[p[0] for p in _pts]; _ys=[p[1] for p in _pts]
def block_ts(b):
    if isinstance(b,str): 
        if b in blocks: return blocks[b]
        b=int(b,16)
    i=bisect.bisect_left(_xs,b)
    if i<=0: return _ys[0]-(_xs[0]-b)/9.9
    if i>=len(_xs): return _ys[-1]+(b-_xs[-1])/9.9
    x0,y0,x1,y1=_xs[i-1],_ys[i-1],_xs[i],_ys[i]; return y0+(y1-y0)*(b-x0)/(x1-x0) if x1>x0 else y0
def iso(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp() if s else None
def dt(ts): return datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M') if ts else ''
def tkey(a): return a.lower() if a and a.startswith('0x') else a
# ---- sources
pools=json.load(open('gt/pools_v3.json')); dex=json.load(open('dex/tokens.json')); mints=json.load(open('rh/mints/mints.json'))
creators=json.load(open('rh/creators/creators.json')) if os.path.exists('rh/creators/creators.json') else {}
userops=json.load(open('rh/creators/userop_senders.json')) if os.path.exists('rh/creators/userop_senders.json') else {}
memes=json.load(open(f'{REPO}/data/derived/memes_traded.json'))
lb_wallets={}
for w in ('all','30d','7d','24h'):
    for t in json.load(open(f'fapi/lb/{w}.json'))['traders']:
        lb_wallets.setdefault(t['handle'],t.get('wallets') or {})
evm2h={ (v.get('evm') or '').lower():h for h,v in lb_wallets.items() if v.get('evm')}
sol2h={ v.get('solana'):h for h,v in lb_wallets.items() if v.get('solana')}
WETH="0x0bd7d308f8e1639fab988df18a8011f41eacad73"
STOCKS={'NVDA','SPCX','SPCXB','QQQB','GOOGL','AAPL','TSLA','SPY','HOOD','AMZN','MSFT','META','COIN','MSTR','PLTR','AMD','NFLX','OPEN','QQQ','IWM','GLD','SLV','TLT','VOO','VTI','ARKK','SOXL','TQQQ','SQQQ','GME','AMC','SMCI','INTC','BABA','RIVN','LCID','NIO','SOFI','DIS','UBER','PYPL','SHOP','SNAP','ROKU','ZM','CRWD','PANW','AVGO','ORCL','CSCO','IBM','TSM','ASML','BA','GE','CAT','DE','XOM','CVX','JPM','BAC','WFC','GS','MS','C','V','MA','AXP','KO','PEP','MCD','SBUX','NKE','WMT','TGT','COST','HD','LOW','PFE','JNJ','MRK','ABBV','LLY','UNH','CVS'}
sym_of={}
for r in memes: sym_of[tkey(r['address'])]=r['symbol']
def pool_created(a):
    p=pools.get(a) or {}; cs=[iso(x['created']) for x in p.get('pools',[]) if x.get('created') and x.get('base',True)]
    return min(cs) if cs else None
def supply_of(a):
    p=pools.get(a) or {}
    try:
        if p.get('total_supply'): return float(p['total_supply'])/10**int(p.get('decimals') or 0)
    except Exception: pass
    d=dex.get(a) or {}
    for pr in d.get('pairs',[]):
        try:
            if pr.get('fdv') and float(pr.get('priceUsd') or 0)>0: return float(pr['fdv'])/float(pr['priceUsd'])
        except Exception: pass
    return None
def dex_main(a):
    d=dex.get(a) or {}; ps=[p for p in d.get('pairs',[]) if p.get('liquidity')]
    if not ps: return None
    return max(ps,key=lambda p:float((p.get('liquidity') or {}).get('usd') or 0))
def launchpad(a,chain,sym):
    if chain=='solana':
        if a.endswith('pump'): return 'pump.fun'
        if a.endswith('bonk'): return 'bonk (letsbonk)'
        if a.endswith('BAGS') or a.endswith('bags'): return 'bags'
        if a.endswith('moon'): return 'moonshot'
        return 'solana/other'
    if chain=='robinhood':
        c=creators.get(a) or {}; f=(c.get('factory') or '').lower()
        p=pools.get(a) or {}; qs=set()
        for x in p.get('pools',[]):
            if x.get('base',True) and x.get('quote'): qs.add(x['quote'].lower())
        qsyms={sym_of.get(q,'?') for q in qs}
        d=dex_main(a); labels=set((d or {}).get('labels') or [])
        FACT={'0xa5aab3f0c6eeadf30ef1d3eb997108e976351feb':'Pons V1 (v3 pool)','0xe33e9e479df8802cb0866d5d05258bec4cf62948':'Pons V2 (v4 hook curve)',
              '0x22e99278308b393ea1260859b181ad7e78f5eeed':'LONG (stock-paired)','0xd9ec2db5f3d1b236843925949fe5bd8a3836fccb':'pre-Pons v3 factory (0xd9ec, Jun-Jul)',
              '0x7ed598bcef8bd9edd8c97a195c6d13f40801ec7e':'v4 launchpad 0x7ed5','0x0000000071727de22e5e9d8baf0edac6f37da032':'fomo-app launch (ERC-4337 userOp)',
              '0x26605f322f7ff986f381bb9a6e3f5dab0beaeb09':'v2 launchpad 0x2660','0x5bd1fbe78a78fe8236fa00cf48fbeba74ae34661':'v4 launchpad 0x5bd1'}
        if f in FACT and FACT[f]!='LONG (stock-paired)' and any(s in STOCKS or (s.endswith('B') and s[:-1] in STOCKS) for s in qsyms): return 'LONG (stock-paired)'
        if f in FACT: return FACT[f]
        if any(s in STOCKS or (s.endswith('B') and s[:-1] in STOCKS) for s in qsyms): return 'LONG (stock-paired)'
        if 'v4' in labels: return 'Pons V2 (v4 hook curve)'
        if 'v3' in labels: return 'Pons V1 (v3 pool)'
        if WETH in qs: return 'Pons (WETH pool)'
        return 'robinhood/other'
    return chain+'/other'
# ---- holders (fomoapi tracked top holders)
holders={}
for f in glob.glob('fapi/holders/*.json'):
    d=json.load(open(f)); a=tkey(d.get('token') or os.path.basename(f)[:-5]); hs=d.get('holders') or []
    holders[a]=hs
theses_dev={}; theses_n={}
for f in glob.glob('fapi/theses/*.json'):
    d=json.load(open(f)); a=tkey(os.path.basename(f)[:-5]); th=d.get('theses') or []
    theses_n[a]=len(th); theses_dev[a]=sorted({x.get('handle') for x in th if x.get('isDev') and x.get('handle')})
dep_count=collections.Counter((v.get('deployer') or '').lower() for v in creators.values() if v.get('deployer'))
def holder_metrics(a,supply):
    hs=holders.get(a)
    if hs is None: return {}
    lbh=[h for h in hs if h.get('handle') in lb_wallets]
    devs=[h.get('handle') for h in hs if h.get('isDev')]
    amt=[float(h.get('amount') or 0) for h in hs]
    top10=sum(sorted(amt,reverse=True)[:10]); tot=sum(amt)
    cb=[]
    for h in hs:
        try:
            if float(h.get('amount') or 0)>0 and h.get('costBasisUsd') and supply: cb.append(float(h['costBasisUsd'])/float(h['amount'])*supply)
        except Exception: pass
    return {"tracked_holders":len(hs),"lb_holders":len(lbh),"lb_holder_handles":[h['handle'] for h in lbh][:30],"dev_holders":devs,
            "top10_tracked_pct_supply":(100*top10/supply if supply else None),"tracked_pct_supply":(100*tot/supply if supply else None),
            "median_holder_entry_fdv":(st.median(cb) if cb else None),"holders_value_usd":sum(float(h.get('valueUsd') or 0) for h in hs)}
# ---- per token table
rows=list(csv.DictReader(gzip.open(f'{REPO}/data/derived/positions_all.csv.gz','rt')))
by_tok=collections.defaultdict(list)
for r in rows: by_tok[tkey(r['address'])].append(r)
tok={}
for a,rs in by_tok.items():
    chain=rs[0]['chain']; sym=rs[0]['symbol'] or sym_of.get(a) or a[:8]
    supply=supply_of(a); d=dex_main(a); p=pools.get(a) or {}
    created=None; created_src=None
    m=mints.get(a)
    if m:
        try: created=block_ts(m); created_src='mint block'
        except Exception: pass
    if not created and d and d.get('pairCreatedAt'): created=d['pairCreatedAt']/1000; created_src='dex pair'
    if not created: 
        pc=pool_created(a)
        if pc: created,created_src=pc,'gt pool'
    price=float(d['priceUsd']) if d and d.get('priceUsd') else None
    fdv=(float(d['fdv']) if d and d.get('fdv') else (float(p['fdv']) if p.get('fdv') else None))
    liq=float((d.get('liquidity') or {}).get('usd') or 0) if d else max([float(x.get('liq') or 0) for x in p.get('pools',[])],default=None)
    c=creators.get(a) or {}
    dep=(c.get('deployer') or '').lower(); fee=(c.get('fee_recipient') or '').lower()
    uo=(userops.get(a) or {}).get('senders') or []
    if uo: dep=uo[0].lower()   # ERC-4337 launch: the smart-account sender is the creator, not the bundler
    t={"address":a,"symbol":sym,"chain":chain,"category":next((r['category'] for r in memes if tkey(r['address'])==a),None),
       "supply":supply,"price":price,"fdv":fdv,"liq":liq,"created":created,"created_src":created_src,
       "launchpad":launchpad(a,chain,sym),
       "dex":({"txns24_buys":((d.get('txns') or {}).get('h24') or {}).get('buys'),"txns24_sells":((d.get('txns') or {}).get('h24') or {}).get('sells'),"vol24":(d.get('volume') or {}).get('h24'),"chg24":(d.get('priceChange') or {}).get('h24'),"dexId":d.get('dexId'),"labels":d.get('labels')} if d else None),
       "deployer":dep or None,"fee_recipient":fee or None,"deployer_handle":evm2h.get(dep),"fee_recipient_handle":evm2h.get(fee),"factory":c.get('factory'),
       "deployer_n_tokens":(dep_count.get(dep) if dep else None),"theses":theses_n.get(a),"dev_handles_thesis":theses_dev.get(a,[])}
    t.update(holder_metrics(a,supply))
    # leaderboard entries
    ent=[]
    for r in rs:
        if r['side'] not in ('buy','open','closed') and r['source']!='fomo': continue
        px=None
        if r['source']=='fomo' and r['entry_price']: px=float(r['entry_price'])
        elif r['source']!='fomo' and r['side']=='buy' and r['usd'] and r['amount'] and float(r['amount'])>0: px=float(r['usd'])/float(r['amount'])
        if px is None or not supply: continue
        ts=iso(r['time']) if r['time'] else None
        ent.append({"handle":r['handle'],"src":r['source'],"ts":ts,"entry_fdv":px*supply,"age_min":((ts-created)/60 if ts and created else None),"usd":(float(r['usd']) if r['usd'] else None)})
    t["n_entries_priced"]=len(ent)
    if ent:
        fd=[e['entry_fdv'] for e in ent]; ag=[e['age_min'] for e in ent if e['age_min'] is not None]
        t["entry_fdv_median"]=st.median(fd); t["entry_fdv_min"]=min(fd); t["entry_fdv_p25"]=sorted(fd)[len(fd)//4]
        t["first_lb_entry_age_min"]=min(ag) if ag else None; t["median_lb_entry_age_min"]=st.median(ag) if ag else None
        t["pct_entries_under_1m"]=100*sum(1 for x in fd if x<1e6)/len(fd); t["pct_entries_under_100k"]=100*sum(1 for x in fd if x<1e5)/len(fd)
    t["traders"]=len({r['handle'] for r in rs}); t["handles"]=sorted({r['handle'] for r in rs})
    tok[a]=t
json.dump(tok,open(f'{REPO}/data/derived/token_metrics.json','w'),default=float)
# ---- per position enrichment -> positions_all.csv.gz new columns
out=gzip.open(f'{REPO}/data/derived/positions_all.csv.gz','wt',newline='')
EXTRA=['entry_fdv_usd','age_at_entry_min','launchpad','token_created','trader_is_dev','fdv_now']
cols=[c for c in rows[0].keys() if c not in EXTRA]+EXTRA
w=csv.DictWriter(out,fieldnames=cols); w.writeheader()
for r in rows:
    a=tkey(r['address']); t=tok.get(a) or {}
    px=None
    if r['source']=='fomo' and r['entry_price']: px=float(r['entry_price'])
    elif r['source']!='fomo' and r['usd'] and r['amount'] and float(r['amount'])!=0: px=abs(float(r['usd'])/float(r['amount']))
    ts=iso(r['time']) if r['time'] else None
    r2={k:v for k,v in r.items() if k not in EXTRA}; r2['entry_fdv_usd']=round(px*t['supply']) if px and t.get('supply') else ''
    r2['age_at_entry_min']=round((ts-t['created'])/60,1) if ts and t.get('created') else ''
    r2['launchpad']=t.get('launchpad',''); r2['token_created']=dt(t.get('created')) if t.get('created') else ''
    h=r['handle']; ev=((lb_wallets.get(h) or {}).get('evm') or '').lower()
    isdev = (ev and (ev==t.get('deployer') or ev==t.get('fee_recipient'))) or (h in (t.get('dev_holders') or [])) or (h in (t.get('dev_handles_thesis') or []))
    r2['trader_is_dev']='yes' if isdev else ''; r2['fdv_now']=round(t['fdv']) if t.get('fdv') else ''
    w.writerow(r2)
out.close()
# ---- per trader entry metrics
by_h=collections.defaultdict(list)
for r in rows:
    a=tkey(r['address']); t=tok.get(a) or {}
    if not t or t.get('category')!='meme': continue
    px=None
    if r['source']=='fomo' and r['entry_price']: px=float(r['entry_price'])
    elif r['source']!='fomo' and r['side']=='buy' and r['usd'] and r['amount'] and float(r['amount'])>0: px=float(r['usd'])/float(r['amount'])
    if px is None or not t.get('supply'): continue
    ts=iso(r['time']) if r['time'] else None
    by_h[r['handle']].append({"fdv":px*t['supply'],"age":((ts-t['created'])/60 if ts and t.get('created') else None),"lp":t['launchpad'],"usd":float(r['usd']) if r['usd'] else None,"tok":a,"src":r['source'],"fdv_now":t.get('fdv')})
cls={x['handle']:x for x in json.load(open(f'{REPO}/data/derived/trader_classification.json'))} if os.path.exists(f'{REPO}/data/derived/trader_classification.json') else {}
trader={}
for h,es in by_h.items():
    fd=[e['fdv'] for e in es]; ag=[e['age'] for e in es if e['age'] is not None]
    lp=collections.Counter(e['lp'] for e in es)
    ev=((lb_wallets.get(h) or {}).get('evm') or '').lower()
    devtoks=[t['symbol'] for t in tok.values() if (ev and ev in (t.get('deployer'),t.get('fee_recipient'))) or h in (t.get('dev_holders') or []) or h in (t.get('dev_handles_thesis') or [])]
    trader[h]={"entries_priced":len(es),"tokens":len({e['tok'] for e in es}),"entry_fdv_median":st.median(fd),"entry_fdv_p25":sorted(fd)[len(fd)//4],"entry_fdv_p75":sorted(fd)[3*len(fd)//4],
               "pct_under_100k":100*sum(1 for x in fd if x<1e5)/len(fd),"pct_under_1m":100*sum(1 for x in fd if x<1e6)/len(fd),"pct_over_10m":100*sum(1 for x in fd if x>1e7)/len(fd),
               "age_median_min":(st.median(ag) if ag else None),"pct_under_1h":(100*sum(1 for x in ag if x<60)/len(ag) if ag else None),"pct_under_24h":(100*sum(1 for x in ag if x<1440)/len(ag) if ag else None),"pct_over_7d":(100*sum(1 for x in ag if x>10080)/len(ag) if ag else None),
               "launchpads":dict(lp.most_common(4)),"dev_tokens":devtoks,"class":(cls.get(h) or {}).get('classification')}
json.dump(trader,open(f'{REPO}/data/derived/trader_entry_metrics.json','w'),default=float)
print("tokens",len(tok),"with supply",sum(1 for t in tok.values() if t['supply']),"with created",sum(1 for t in tok.values() if t['created']),"holders",sum(1 for t in tok.values() if 'tracked_holders' in t),"creators",sum(1 for t in tok.values() if t.get('deployer')),"traders",len(trader))
print("dev matches", [(t['symbol'],t.get('deployer_handle') or t.get('fee_recipient_handle') or t.get('dev_holders') or t.get('dev_handles_thesis')) for t in tok.values() if t.get('deployer_handle') or t.get('fee_recipient_handle') or t.get('dev_holders') or t.get('dev_handles_thesis')][:40])
print("serial deployers (tokens deployed among traded set):", dep_count.most_common(8))
print("launchpads", collections.Counter(t['launchpad'] for t in tok.values() if t.get('category')=='meme').most_common(12))
