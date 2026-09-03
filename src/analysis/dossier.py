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
def rh_stats(h):
    f=f'rh/receipts/{h}.json'
    if not os.path.exists(f): return None
    d=json.load(open(f)); w=d['wallet']; WETH="0x0bd7d308f8e1639fab988df18a8011f41eacad73"
    rows=[]
    for txh,rc in d['receipts'].items():
        if rc['s']!='0x1': continue
        tx=d['tx'].get(txh,{}); bn=rc['b']; ts=blocks.get(bn)
        tok=collections.defaultdict(float); weth_in=0.0; weth_out=0.0
        for lg in rc['l']:
            if lg['e']!='T': continue
            amt=int(lg['v'],16)/1e18 if lg['v'] and lg['v']!='0x' else 0
            if lg['a']==WETH:
                if lg['t']==w: weth_in+=amt
                if lg['f']==w: weth_out+=amt
                continue
            if lg['t']==w: tok[lg['a']]+=amt
            if lg['f']==w: tok[lg['a']]-=amt
        eth_val=int(tx['value'],16)/1e18 if tx.get('value') and tx.get('from')==w else 0.0
        # ETH received on sells is native (not in logs); use swap events: sum WETH legs of S3 swaps in tx
        swap_weth=0.0
        for lg in rc['l']:
            if lg['e']=='S3':
                a0=int(lg['d'][2:66],16); a1=int(lg['d'][66:130],16)
                a0=a0-(1<<256) if a0>=(1<<255) else a0; a1=a1-(1<<256) if a1>=(1<<255) else a1
                # WETH is token0 if WETH addr < token addr; we don't know pool's token; approximate: the leg with smaller magnitude in 1e18 units that is 'WETH-like' — instead record both
                swap_weth+=0
        for a,v in tok.items():
            if abs(v)<1e-9: continue
            side="in" if v>0 else "out"; eth=None
            if v>0 and (eth_val>0 or weth_out>0): side="buy"; eth=eth_val+weth_out
            elif v<0 and weth_in>0: side="sell"; eth=weth_in
            rows.append({"ts":ts,"b":int(bn,16),"tx":txh,"token":a,"amt":v,"eth":eth,"usd":(eth*eth_usd(ts) if (eth and ts) else None),"side":side,"n":len(tok),"mint":mints.get(a),"gas_eth":(int(rc['g'],16)*int(rc['gp'],16)/1e18) if rc.get('g') and rc.get('gp') else None})
    rows.sort(key=lambda r:r['b'])
    buys=[r for r in rows if r['side']=='buy']; sells=[r for r in rows if r['side']=='sell']
    outs=[r for r in rows if r['side']=='out']; ins=[r for r in rows if r['side']=='in']
    # entry timing vs launch (blocks): for buys with known mint block
    lag=[]
    for r in buys:
        if r['mint']: lag.append((r['b']-int(r['mint'],16))/9.9/60)  # ~9.9 blocks/s -> minutes
    # per-token realized (avg cost) using ETH legs
    pos=collections.defaultdict(lambda:{"q":0.0,"c":0.0,"r":0.0,"bu":0.0,"se":0.0})
    for r in rows:
        p=pos[r['token']]
        if r['side']=='buy' and r['eth']: p['q']+=r['amt']; p['c']+=r['eth']; p['bu']+=r['eth']
        elif r['side']=='sell' and r['eth']:
            qty=-r['amt']; avg=p['c']/p['q'] if p['q']>0 else 0; used=min(qty,p['q']); p['r']+=r['eth']-avg*used; p['c']-=avg*used; p['q']-=used; p['se']+=r['eth']
        elif r['side']=='in': p['q']+=r['amt']
        elif r['side']=='out': p['q']=max(0.0,p['q']+r['amt'])
    real_eth=sum(p['r'] for p in pos.values()); toks=[k for k,p in pos.items() if p['bu']>0]
    wins=[k for k in toks if pos[k]['r']>0]
    top=sorted(((k,p['r']) for k,p in pos.items()),key=lambda kv:-kv[1])[:5]
    hours=collections.Counter(datetime.datetime.utcfromtimestamp(r['ts']).hour for r in buys if r['ts'])
    return {"n_tx_total":d.get('n_tx_total'),"n_buys":len(buys),"n_sells":len(sells),"n_in_unpriced":len(ins),"n_out_unpriced":len(outs),
            "buy_eth":sum(r['eth'] for r in buys),"sell_eth":sum(r['eth'] for r in sells),"buy_usd":sum(r['usd'] or 0 for r in buys),"sell_usd":sum(r['usd'] or 0 for r in sells),
            "realized_eth_avgcost":real_eth,"tokens_bought":len(toks),"token_win_rate":(len(wins)/len(toks)) if toks else None,
            "top5_tokens_realized_eth":[(k[:10],round(v,3)) for k,v in top],"top1_share_of_gains":(top[0][1]/sum(v for _,v in top if v>0)) if top and top[0][1]>0 else None,
            "median_buy_usd":q([r['usd'] for r in buys if r['usd']],0.5),"p90_buy_usd":q([r['usd'] for r in buys if r['usd']],0.9),
            "entry_lag_min_median":q(lag,0.5),"entry_lag_min_p25":q(lag,0.25),"share_buys_within_10min_of_launch":(sum(1 for x in lag if x<=10)/len(lag)) if lag else None,"share_buys_within_60min":(sum(1 for x in lag if x<=60)/len(lag)) if lag else None,
            "first_ts":datetime.datetime.utcfromtimestamp(min(r['ts'] for r in rows if r['ts'])).isoformat() if any(r['ts'] for r in rows) else None,
            "active_hours_utc_top4":[h for h,_ in hours.most_common(4)],"gas_eth_total":sum(r['gas_eth'] or 0 for r in rows),"rows":rows}
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
        rows=rh.pop("rows"); r["robinhood_onchain"]=rh
        json.dump(rows,open(f'rh/receipts/{h}.ledger.json','w'))
    out[h]=r
json.dump(out,open('dossiers.json','w'),indent=1)
print("dossiers",len(out),"with balances",sum(1 for v in out.values() if 'portfolio' in v),"with trades",sum(1 for v in out.values() if 'fomo_trades' in v),"with rh",sum(1 for v in out.values() if 'robinhood_onchain' in v),"with sol ledger",sum(1 for v in out.values() if v.get('solana_onchain',{}).get('ledger')))
for h in ['unipcs','ogle','DumbCrayonEater']:
    if h in out and 'robinhood_onchain' in out[h]: print(h,json.dumps({k:v for k,v in out[h]['robinhood_onchain'].items()},default=str)[:1500])
