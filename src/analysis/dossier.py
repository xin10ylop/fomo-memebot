import json,glob,collections,datetime,statistics as st,math,os,bisect
def iso(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00')) if s else None
def q(xs,p): 
    xs=sorted(xs); 
    return xs[min(len(xs)-1,int(p*len(xs)))] if xs else None
lb={w:{t['handle']:t for t in json.load(open(f'fapi/lb/{w}.json'))['traders']} for w in ['24h','7d','30d','all']}
handles=[]
for w in ['all','30d','7d','24h']:
    for h in lb[w]:
        if h not in handles: handles.append(h)
dex=json.load(open('dex/tokens.json')) if os.path.exists('dex/tokens.json') else {}
gtp=json.load(open('gt/pools_multi.json')) if os.path.exists('gt/pools_multi.json') else {}
sol_sum=json.load(open('sol_ledger_summary.json')) if os.path.exists('sol_ledger_summary.json') else {}
blocks=json.load(open('rh/blocks/blocks.json')) if os.path.exists('rh/blocks/blocks.json') else {}
mints=json.load(open('rh/mints/mints.json')) if os.path.exists('rh/mints/mints.json') else {}
ethp=json.load(open('prices/eth_90d.json'))['prices']; etht=[p[0]/1000 for p in ethp]
def eth_usd(ts):
    i=bisect.bisect_left(etht,ts); i=min(max(i,0),len(ethp)-1); return ethp[i][1]
def dexinfo(a):
    v=dex.get(a) or {}; ps=v.get('pairs') or []
    if not ps: 
        g=gtp.get((a or '').lower())
        if g and g.get('pools'):
            pl=max(g['pools'],key=lambda p:p['liq']); return {"chain":g['network'],"liq":pl['liq'],"fdv":float(g['fdv']) if g.get('fdv') else None,"price":None,"created":pl.get('created'),"src":"gt"}
        return None
    ps=sorted(ps,key=lambda p:-((p.get('liquidity') or {}).get('usd') or 0)); p=ps[0]
    return {"chain":p['chainId'],"liq":(p.get('liquidity') or {}).get('usd'),"fdv":p.get('fdv'),"price":float(p['priceUsd']) if p.get('priceUsd') else None,"created":p.get('pairCreatedAt'),"src":"dex"}
TRANSFER="T"
_cc={}
def tok_price(a,ts):
    """USD price at ts: 1m candles if they cover ts, else 15m candles; None if no candle within 6h before ts (or 6h after for pre-history)."""
    if a not in _cc:
        series=[]
        for f in (f'gt/ohlcv1m/{a}.json',f'gt/ohlcv/{a}.json'):
            if os.path.exists(f):
                c=sorted(json.load(open(f))['candles'],key=lambda x:x[0])
                if c: series.append({"t":[x[0] for x in c],"c":[x[4] for x in c],"o":[x[1] for x in c]})
        _cc[a]=series
    if not ts: return None
    for o in _cc[a]:
        i=bisect.bisect_right(o['t'],ts)-1
        if i>=0 and ts-o['t'][i]<=3600*6: return o['c'][i]
        if i<0 and o['t'][0]-ts<3600*6: return o['o'][0]
    return None
ROUTERS={'0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f'}
def rh_stats(h):
    f=f'rh/logs/{h}.ledger.json'
    if not os.path.exists(f): return None
    rows=json.load(open(f)); fills=[r for r in rows if r['side'] in ('buy','sell')]
    buys=[r for r in fills if r['side']=='buy']; sells=[r for r in fills if r['side']=='sell']
    pb=[r for r in buys if r['usd']]; ps=[r for r in sells if r['usd']]
    lag=[((r['b']-int(r['mint'],16))/9.9/60) for r in buys if r.get('mint')]
    pos=collections.defaultdict(lambda:{"q":0.0,"c":0.0,"r":0.0,"bu":0.0,"se":0.0,"nb":0,"ns":0,"first":None,"last":None,"unpriced":0,"sold_nobuy":0.0})
    for r in sorted(fills,key=lambda r:r['b']):
        p=pos[r['token']]; p['first']=p['first'] or r['ts']; p['last']=r['ts']
        if r['usd'] is None: p['unpriced']+=1
        if r['side']=='buy':
            p['q']+=r['amt']; p['nb']+=1
            if r['usd']: p['c']+=r['usd']; p['bu']+=r['usd']
        else:
            qty=-r['amt']; p['ns']+=1
            if r['usd']:
                if p['q']<=1e-9: p['sold_nobuy']+=r['usd']
                avg=p['c']/p['q'] if p['q']>0 else 0; used=min(qty,p['q']); p['r']+=r['usd']-avg*used; p['c']-=avg*used; p['se']+=r['usd']
            p['q']=max(0.0,p['q']-qty)
    # realized only trusted for fully-priced tokens
    full={k:p for k,p in pos.items() if p['unpriced']==0}
    sold_nobuy=sum(p['sold_nobuy'] for p in pos.values())
    pos_all=pos; pos={k:p for k,p in full.items()}
    toks=[k for k,p in pos.items() if p['bu']>0]; wins=[k for k in toks if pos[k]['r']>0]
    real=sum(p['r'] for p in pos.values()); top=sorted(((k,p['r']) for k,p in pos.items()),key=lambda kv:-kv[1])[:5]
    gains=sum(v for _,v in top if v>0)
    hold=[(p['last']-p['first'])/3600 for p in pos.values() if p['first'] and p['last'] and p['ns']>0]
    hours=collections.Counter(datetime.datetime.utcfromtimestamp(r['ts']).hour for r in buys if r['ts'])
    return {"n_fills":len(fills),"n_buys":len(buys),"n_sells":len(sells),"priced_share":(len(pb)+len(ps))/len(fills) if fills else None,"tokens_total":len(pos_all),"tokens_fully_priced":len(pos),"sold_without_buy_usd":sold_nobuy,
            "buy_usd":sum(r['usd'] for r in pb),"sell_usd":sum(r['usd'] for r in ps),"realized_usd_avgcost":real,
            "tokens_bought":len(toks),"token_win_rate":(len(wins)/len(toks)) if toks else None,"top5_tokens_realized_usd":[(k[:10],round(v)) for k,v in top],
            "top1_share_of_gains":(top[0][1]/gains) if gains>0 else None,"median_buy_usd":q([r['usd'] for r in pb],0.5),"p90_buy_usd":q([r['usd'] for r in pb],0.9),
            "entry_lag_min_median":q(lag,0.5),"entry_lag_min_p25":q(lag,0.25),"share_buys_within_10min_of_launch":(sum(1 for x in lag if x<=10)/len(lag)) if lag else None,
            "share_buys_within_60min":(sum(1 for x in lag if x<=60)/len(lag)) if lag else None,"hold_h_median":q(hold,0.5),
            "first_ts":datetime.datetime.utcfromtimestamp(min(r['ts'] for r in fills if r['ts'])).isoformat() if any(r['ts'] for r in fills) else None,
            "active_hours_utc_top4":[h for h,_ in hours.most_common(4)],"airdrops_received":sum(1 for r in rows if r['side']=='airdrop'),"rows":None}
out={}
for h in handles:
    r={"handle":h,"ranks":{w:(lb[w][h]['rank'] if h in lb[w] else None) for w in lb},"pnl":{w:(lb[w][h]['pnlUsd'] if h in lb[w] else None) for w in lb}}
    t=lb['all'].get(h) or lb['30d'].get(h) or lb['7d'].get(h) or lb['24h'].get(h)
    r["profile"]={"followers":t.get('followers'),"trades":t.get('trades'),"volume":t.get('volumeUsd'),"holdings":t.get('holdings'),"sol":t['wallets'].get('solana'),"evm":t['wallets'].get('evm')}
    bf=f'fapi/balances/{h}.json'
    if os.path.exists(bf):
        b=json.load(open(bf)); hs=b.get('holdings') or []
        tot=sum((x.get('valueUsd') or 0) for x in hs); hs2=sorted(hs,key=lambda x:-(x.get('valueUsd') or 0))
        mtm=sum((x.get('valueUsd') or 0)*(1-1/(1+(x.get('change24h') or 0)/100)) for x in hs if x.get('change24h') is not None and x.get('change24h')>-100)
        adj=0; det=[]
        for x in hs2[:10]:
            di=dexinfo((x.get('token') or {}).get('address')); v=x.get('valueUsd') or 0
            L=(di or {}).get('liq')
            proceeds=v/(1+v/(L/2)) if L else v*0.5
            adj+=proceeds; det.append({"sym":(x.get('token') or {}).get('symbol'),"chain":x.get('chain'),"value":round(v),"liq":round(L) if L else None,"est_proceeds":round(proceeds),"chg24":x.get('change24h')})
        adj+=sum((x.get('valueUsd') or 0) for x in hs2[10:])
        r["portfolio"]={"value":tot,"by_chain":{k:round(v.get('valueUsd',0)) for k,v in (b.get('byChain') or {}).items()},"n":len(hs),"top1_share":(hs2[0]['valueUsd']/tot) if hs2 and tot else None,"top3_share":(sum(x['valueUsd'] for x in hs2[:3])/tot) if hs2 and tot else None,"mtm_24h_est":mtm,"pnl24_over_mtm":(r['pnl']['24h']/mtm) if r['pnl']['24h'] and mtm else None,"liq_adjusted_value":adj,"haircut_pct":(1-adj/tot) if tot else None,"top_holdings":det[:6]}
    tf=f'fapi/trades/{h}.json'
    if os.path.exists(tf):
        d=json.load(open(tf)); tr=d.get('trades') or []; c=[x for x in tr if x.get('status')=='closed']; o=[x for x in tr if x.get('status')=='open']
        pn=[x['realizedPnlUsd'] for x in c if x.get('realizedPnlUsd') is not None]
        hold=[(iso(x['closedAt'])-iso(x['createdAt'])).total_seconds()/3600 for x in c if x.get('createdAt') and x.get('closedAt')]
        mult=[x['avgExitPrice']/x['avgEntryPrice'] for x in c if x.get('avgEntryPrice') and x.get('avgExitPrice')]
        wins=[p for p in pn if p>0]; losses=[-p for p in pn if p<0]
        em=[]
        for x in c+o:
            di=dexinfo((x.get('token') or {}).get('address'))
            if di and di.get('fdv') and di.get('price') and x.get('avgEntryPrice'): em.append(x['avgEntryPrice']*di['fdv']/di['price'])
        ch=collections.Counter((dexinfo((x.get('token') or {}).get('address')) or {}).get('chain','unknown') for x in tr)
        r["fomo_trades"]={"open_positions":d.get('activeCount'),"closed_total":d.get('closedCount'),"closed_sampled":len(c),"win_rate_sampled":(len(wins)/len(pn)) if pn else None,"sum_realized_sampled":sum(pn) if pn else None,"avg_win":st.mean(wins) if wins else 0,"avg_loss":st.mean(losses) if losses else 0,"profit_factor":(sum(wins)/sum(losses)) if losses else None,"biggest_win":max(pn) if pn else None,"biggest_loss":min(pn) if pn else None,"hold_h_median":q(hold,0.5),"hold_h_p25":q(hold,0.25),"hold_h_p75":q(hold,0.75),"exit_mult_median":q(mult,0.5),"exit_mult_max":max(mult) if mult else None,"entry_mcap_median":q(em,0.5),"entry_mcap_p25":q(em,0.25),"entry_mcap_p75":q(em,0.75),"unrealized_open_sum":sum((x.get('unrealizedPnlUsd') or 0) for x in o),"thesis_rate":(sum(1 for x in tr if x.get('thesis'))/len(tr)) if tr else None,"chain_mix":dict(ch),"sample_closed":[{"sym":(x.get('token') or {}).get('symbol'),"pnl":x.get('realizedPnlUsd'),"mult":(x['avgExitPrice']/x['avgEntryPrice']) if x.get('avgEntryPrice') and x.get('avgExitPrice') else None,"hold_h":((iso(x['closedAt'])-iso(x['createdAt'])).total_seconds()/3600) if x.get('createdAt') and x.get('closedAt') else None,"thesis":(x.get('thesis') or '')[:80]} for x in sorted(c,key=lambda x:-(x.get('realizedPnlUsd') or 0))[:8]]}
    sf=f'helius/sigs/{h}.json'
    if os.path.exists(sf):
        s=json.load(open(sf))['sigs']; bt=[x['blockTime'] for x in s if x.get('blockTime')]
        r["solana_onchain"]={"tx_n":len(s),"first":datetime.datetime.utcfromtimestamp(min(bt)).date().isoformat() if bt else None,"active_days":len({datetime.datetime.utcfromtimestamp(t).date() for t in bt}) if bt else 0,"fail_rate":(sum(1 for x in s if x.get('err'))/len(s)) if s else None}
        if h in sol_sum: r["solana_onchain"]["ledger"]=sol_sum[h]
    rh=rh_stats(h)
    if rh:
        rh.pop("rows",None); r["robinhood_onchain"]=rh
    out[h]=r
json.dump(out,open('dossiers.json','w'),indent=1)
print("dossiers",len(out),"with balances",sum(1 for v in out.values() if 'portfolio' in v),"with trades",sum(1 for v in out.values() if 'fomo_trades' in v),"with rh",sum(1 for v in out.values() if 'robinhood_onchain' in v),"with sol ledger",sum(1 for v in out.values() if v.get('solana_onchain',{}).get('ledger')))
for h in ['unipcs','ogle','DumbCrayonEater']:
    if h in out and 'robinhood_onchain' in out[h]: print(h,json.dumps({k:v for k,v in out[h]['robinhood_onchain'].items()},default=str)[:1500])
