import json,glob,os,collections,datetime,csv,gzip,bisect,statistics as st
OUT='/home/user/fomo-memebot'
os.makedirs(f'{OUT}/data/derived/positions',exist_ok=True)
def iso(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp() if s else None
def dt(ts): return datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M') if ts else ''
lb={}
for w in ['24h','7d','30d','all']:
    for t in json.load(open(f'fapi/lb/{w}.json'))['traders']: lb.setdefault(t['handle'],t); lb[t['handle']][f'rank_{w}']=t['rank']
pools=json.load(open('gt/pools_v3.json')) if os.path.exists('gt/pools_v3.json') else {}
dex=json.load(open('dex/tokens.json'))
sym={}; meta={}
for a,v in dex.items():
    ps=v.get('pairs') or []
    if ps:
        p=sorted(ps,key=lambda p:-((p.get('liquidity') or {}).get('usd') or 0))[0]
        k=a.lower() if a.startswith('0x') else a
        sym[k]=p['symbol']; meta[k]={"chain":p['chainId'],"liq":(p.get('liquidity') or {}).get('usd'),"fdv":p.get('fdv'),"created":p.get('pairCreatedAt'),"price":p.get('priceUsd')}
for a,v in pools.items():
    if v.get('symbol') and a not in sym: sym[a]=v['symbol']
    if a not in meta: meta[a]={"chain":v.get('network'),"liq":max([q['liq'] for q in v.get('pools',[]) if q.get('base')] or [None]),"fdv":v.get('fdv'),"created":None,"price":None}
mints=json.load(open('rh/mints/mints.json')) if os.path.exists('rh/mints/mints.json') else {}
for _f in glob.glob('fapi/trades/*.json')+glob.glob('fapi/trades_hist/*/*.json'):
    try:
        for _t in json.load(open(_f)).get('trades',[]):
            _tok=_t.get('token') or {}; _a=_tok.get('address'); _s=_tok.get('symbol')
            if _a and _s: sym.setdefault(_a.lower() if _a.startswith('0x') else _a,_s)
    except Exception: pass
STOCKS={'NVDA','SPCX','SPCXB','QQQB','GOOGL','AAPL','TSLA','SPY','HOOD','MSFT','AMZN','META','COIN','MSTR','HIMS','PLTR','GME','AMC','NFLX','AMD','INTC','QQQ','IWM','GLD','SLV','TQQQ','NVDAB','TSLAB','AAPLB','GOOGLB','METAB','AMZNB','MSFTB','SPYB','HIMSB','COINB','MSTRB','PLTRB','HOODB'}
MAJORS={'SOL','WETH','ETH','USDC','USDT','USDG','BTC','WBTC','BNB','WBNB','HYPE','UNITY','cbBTC','USD1','PYUSD'}
def category(symbol,chain):
    if symbol in MAJORS: return 'major/stable/platform'
    if symbol in STOCKS or (symbol and symbol.endswith('B') and symbol[:-1] in STOCKS): return 'stock-token'
    return 'meme'
def tkey(a): return a.lower() if a and a.startswith('0x') else a
def chain_of(a):
    m=meta.get(tkey(a)); 
    if m and m.get('chain'): return m['chain']
    return 'evm?' if a and a.startswith('0x') else 'solana'
# ---- fomo trades: merge trades + trades_hist by tradeId
all_rows=[]; per={}
handles=sorted(set(f.split('/')[-1][:-5] for f in glob.glob('fapi/trades/*.json')))
tokstats=collections.defaultdict(lambda:{"traders":set(),"open_n":0,"closed_n":0,"realized":0.0,"unrealized":0.0,"wins":0,"first":None,"last":None,"chains":collections.Counter()})
for h in handles:
    seen={}
    files=[f'fapi/trades/{h}.json']+sorted(glob.glob(f'fapi/trades_hist/*/{h}.json'))
    for f in files:
        try: d=json.load(open(f))
        except Exception: continue
        for t in d.get('trades',[]):
            tid=t.get('tradeId') or f"{(t.get('token') or {}).get('address')}|{t.get('createdAt')}"
            prev=seen.get(tid)
            if prev is None or (t.get('status')=='closed' and prev.get('status')!='closed'): seen[tid]=t
    trades=list(seen.values())
    for t in trades: t['_symbol']=(t.get('token') or {}).get('symbol') or sym.get(tkey((t.get('token') or {}).get('address')),'?'); t['_chain']=chain_of((t.get('token') or {}).get('address'))
    # holdings
    bal=json.load(open(f'fapi/balances/{h}.json')) if os.path.exists(f'fapi/balances/{h}.json') else {}
    hold=[{"symbol":(x.get('token') or {}).get('symbol'),"address":(x.get('token') or {}).get('address'),"chain":x.get('chain'),"amount":x.get('amount'),"value_usd":x.get('valueUsd'),"change24h":x.get('change24h')} for x in (bal.get('holdings') or [])]
    hold.sort(key=lambda x:-(x['value_usd'] or 0))
    # RH on-chain fills
    rhf=[]
    if os.path.exists(f'rh/logs/{h}.ledger.json'):
        for r in json.load(open(f'rh/logs/{h}.ledger.json')):
            if r['side'] in ('buy','sell'):
                age=((r['b']-int(r['mint'],16))/9.9/60) if r.get('mint') else None
                rhf.append({"ts":r['ts'],"time":dt(r['ts']),"side":r['side'],"symbol":sym.get(r['token'],'?'),"address":r['token'],"amount":r['amt'],"usd":r.get('usd'),"price":r.get('px'),"launch_age_min":age,"block":r['b']})
    # Solana fills
    sf=[]
    if os.path.exists(f'helius/parsed/{h}.ledger.json'):
        for r in json.load(open(f'helius/parsed/{h}.ledger.json')).get('rows',[]):
            if r.get('side') in ('buy','sell'): sf.append({"ts":r['ts'],"time":dt(r['ts']),"side":r['side'],"symbol":sym.get(r['mint'],'?'),"address":r['mint'],"amount":r['amount'],"usd":r.get('usd'),"src":r.get('src')})
    # per-token summary for this trader (fomo trades)
    bytok=collections.defaultdict(lambda:{"open":0,"closed":0,"realized":0.0,"unrealized":0.0,"first":None,"last":None,"entries":[]})
    for t in trades:
        k=t['_symbol']; b=bytok[k]; b['open' if t['status']=='open' else 'closed']+=1
        b['realized']+=t.get('realizedPnlUsd') or 0; b['unrealized']+=t.get('unrealizedPnlUsd') or 0
        ts=iso(t.get('createdAt')); 
        if ts: b['first']=min(b['first'] or ts,ts); b['last']=max(b['last'] or ts,ts)
        b['entries'].append({"time":dt(ts) if ts else '',"status":t['status'],"entry_price":t.get('avgEntryPrice'),"exit_price":t.get('avgExitPrice'),"realized":t.get('realizedPnlUsd'),"unrealized":t.get('unrealizedPnlUsd'),"closed":t.get('closedAt','')[:16].replace('T',' ') if t.get('closedAt') else '',"thesis":(t.get('thesis') or '')[:120],"chain":t['_chain'],"address":(t.get('token') or {}).get('address')})
        a=tkey((t.get('token') or {}).get('address')); g=tokstats[a]; g['traders'].add(h); g['open_n' if t['status']=='open' else 'closed_n']+=1; g['realized']+=t.get('realizedPnlUsd') or 0; g['unrealized']+=t.get('unrealizedPnlUsd') or 0; g['wins']+=1 if (t.get('realizedPnlUsd') or 0)>0 else 0; g['chains'][t['_chain']]+=1
        if ts: g['first']=min(g['first'] or ts,ts); g['last']=max(g['last'] or ts,ts)
    ages=[x['launch_age_min'] for x in rhf if x['side']=='buy' and x['launch_age_min'] is not None]
    rec={"handle":h,"ranks":{w:lb.get(h,{}).get(f'rank_{w}') for w in ['24h','7d','30d','all']},"followers":lb.get(h,{}).get('followers'),"pnl_all":lb.get(h,{}).get('pnlUsd'),
         "fomo_positions":{"open":sum(1 for t in trades if t['status']=='open'),"closed_captured":sum(1 for t in trades if t['status']=='closed'),"closed_total_reported":(json.load(open(f'fapi/trades/{h}.json')).get('closedCount'))},
         "tokens_traded_fomo":sorted(bytok.keys()),"n_tokens_fomo":len(bytok),"chains_fomo":dict(collections.Counter(t['_chain'] for t in trades)),
         "by_token":{k:{**v,"first":dt(v['first']),"last":dt(v['last'])} for k,v in sorted(bytok.items(),key=lambda kv:-(kv[1]['realized']+kv[1]['unrealized']))},
         "holdings_now":hold,"rh_fills":sorted(rhf,key=lambda x:x['ts'] or 0),"sol_fills":sorted(sf,key=lambda x:x['ts'] or 0),
         "rh_summary":{"fills":len(rhf),"buys":sum(1 for x in rhf if x['side']=='buy'),"tokens":len({x['address'] for x in rhf}),"priced_buy_usd":sum(x['usd'] or 0 for x in rhf if x['side']=='buy'),"priced_sell_usd":sum(x['usd'] or 0 for x in rhf if x['side']=='sell'),"launch_age_min_median":st.median(ages) if ages else None,"share_buys_within_1h_of_launch":(sum(1 for a in ages if a<=60)/len(ages)) if ages else None,"share_buys_within_24h":(sum(1 for a in ages if a<=1440)/len(ages)) if ages else None},
         "sol_summary":{"fills":len(sf),"buys":sum(1 for x in sf if x['side']=='buy'),"tokens":len({x['address'] for x in sf}),"buy_usd":sum(x['usd'] or 0 for x in sf if x['side']=='buy'),"sell_usd":sum(x['usd'] or 0 for x in sf if x['side']=='sell')}}
    per[h]=rec; json.dump(rec,open(f'{OUT}/data/derived/positions/{h}.json','w'),indent=1)
    for t in trades: all_rows.append({"handle":h,"source":"fomo","symbol":t['_symbol'],"address":(t.get('token') or {}).get('address'),"chain":t['_chain'],"side":"position","status":t['status'],"time":t.get('createdAt'),"closed":t.get('closedAt'),"entry_price":t.get('avgEntryPrice'),"exit_price":t.get('avgExitPrice'),"realized_usd":t.get('realizedPnlUsd'),"unrealized_usd":t.get('unrealizedPnlUsd'),"amount":t.get('amount'),"usd":None,"launch_age_min":None,"thesis":(t.get('thesis') or '')[:200]})
    for x in rhf: all_rows.append({"handle":h,"source":"robinhood_onchain","symbol":x['symbol'],"address":x['address'],"chain":"robinhood","side":x['side'],"status":"","time":x['time'],"closed":"","entry_price":x['price'],"exit_price":"","realized_usd":"","unrealized_usd":"","amount":x['amount'],"usd":x['usd'],"launch_age_min":x['launch_age_min'],"thesis":""})
    for x in sf: all_rows.append({"handle":h,"source":"solana_onchain","symbol":x['symbol'],"address":x['address'],"chain":"solana","side":x['side'],"status":"","time":x['time'],"closed":"","entry_price":"","exit_price":"","realized_usd":"","unrealized_usd":"","amount":x['amount'],"usd":x['usd'],"launch_age_min":None,"thesis":""})
with gzip.open(f'{OUT}/data/derived/positions_all.csv.gz','wt',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(all_rows[0].keys())); w.writeheader(); w.writerows(all_rows)
print("rows",len(all_rows),"traders",len(per))
# ---- docs/TRADER_POSITIONS.md
L=["# Every position and entry, trader by trader\n","Sources per trader: fomo positions (all open + the closed trades fomo exposes, merged across re-pulls), live holdings, every on-chain buy/sell on Robinhood Chain (priced where candles exist) and Solana. Full detail per trader: `data/derived/positions/<handle>.json`; flat table of every row: `data/derived/positions_all.csv.gz`.\n"]
order=sorted(per.values(),key=lambda r:(r['ranks']['all'] is None, r['ranks']['all'] or 999))
for r in order:
    fp=r['fomo_positions']; rs=r['rh_summary']; ss=r['sol_summary']
    L.append(f"\n## {r['handle']}  (rank all-time {r['ranks']['all']}, 24h {r['ranks']['24h']}; followers {r['followers']:,}; fomo PnL ${r['pnl_all'] or 0:,.0f})")
    L.append(f"fomo positions: {fp['open']} open, {fp['closed_captured']} closed captured of {fp['closed_total_reported']} reported · tokens on fomo: {r['n_tokens_fomo']} · chains: {r['chains_fomo']}")
    L.append(f"on-chain Robinhood: {rs['fills']} fills on {rs['tokens']} tokens (priced buys ${rs['priced_buy_usd']:,.0f} / sells ${rs['priced_sell_usd']:,.0f}); median launch age at buy {rs['launch_age_min_median'] and round(rs['launch_age_min_median']/60,1)} h; buys within 1h of launch {rs['share_buys_within_1h_of_launch'] and round(100*rs['share_buys_within_1h_of_launch'])}% · Solana: {ss['fills']} fills on {ss['tokens']} tokens (buys ${ss['buy_usd']:,.0f} / sells ${ss['sell_usd']:,.0f})")
    top=list(r['by_token'].items())[:12]
    if top:
        L.append("\n| token | open/closed | realized $ | unrealized $ | first entry | last entry | entries |"); L.append("|---|---|---|---|---|---|---|")
        for k,v in top:
            ex="; ".join(f"{e['time'][5:]} {e['status']} in@{e['entry_price']}" + (f" out@{e['exit_price']} pnl {e['realized']:+,.0f}" if e['status']=='closed' and e['realized'] is not None else "") for e in v['entries'][:4])
            L.append(f"| {k} | {v['open']}/{v['closed']} | {v['realized']:,.0f} | {v['unrealized']:,.0f} | {v['first']} | {v['last']} | {ex} |")
    if r['holdings_now']:
        L.append("\nHoldings now (top 8): "+", ".join(f"{h['symbol']} ${h['value_usd'] or 0:,.0f} ({h['chain']})" for h in r['holdings_now'][:8]))
    L.append("All tokens traded on fomo: "+", ".join(r['tokens_traded_fomo'][:150]))
open(f'{OUT}/docs/TRADER_POSITIONS.md','w').write("\n".join(L))
# ---- docs/MEMES.md: which memes the leaderboard trades
rows=[]
for a,g in tokstats.items():
    m=meta.get(a,{}); _sym=sym.get(a,'?'); _fdv=float(m.get('fdv') or 0)
    anomaly = abs(g['unrealized'])>1e8 or (_fdv and abs(g['unrealized'])>50*_fdv)
    rows.append({"symbol":_sym,"category":category(_sym,m.get('chain')),"anomaly":anomaly,"address":a,"chain":m.get('chain') or ('evm?' if a and a.startswith('0x') else 'solana'),"traders":len(g['traders']),"positions":g['open_n']+g['closed_n'],"open":g['open_n'],"closed":g['closed_n'],"realized":g['realized'],"unrealized":g['unrealized'],"first":dt(g['first']),"last":dt(g['last']),"liq":m.get('liq'),"fdv":m.get('fdv'),"handles":sorted(g['traders'])})
rows.sort(key=lambda r:(-r['traders'],-(r['realized']+r['unrealized'])))
json.dump(rows,open(f'{OUT}/data/derived/memes_traded.json','w'),indent=1)
memes=[r for r in rows if r['category']=='meme' and not r['anomaly']]
M=["# Which memes the leaderboard trades\n",f"{len(rows)} tokens appear in the 147 traders' fomo positions (open + captured closed). Chains: "+str(dict(collections.Counter(r['chain'] for r in rows)))+". Ranked by number of leaderboard traders who traded the token; realized = sum of captured closed-trade PnL, unrealized = sum of open-position PnL as fomo marks it.\n","| symbol | chain | traders | positions (open/closed) | realized $ | unrealized $ | first entry | last entry | liquidity now | FDV now | traders (sample) |","|---|---|---|---|---|---|---|---|---|---|---|"]
for r in memes[:150]:
    M.append(f"| {r['symbol']} | {r['chain']} | {r['traders']} | {r['positions']} ({r['open']}/{r['closed']}) | {r['realized']:,.0f} | {r['unrealized']:,.0f} | {r['first']} | {r['last']} | {('$%s' % format(round(r['liq']),',')) if r['liq'] else ''} | {('$%s' % format(round(float(r['fdv'])),',')) if r['fdv'] else ''} | {', '.join(r['handles'][:6])} |")
M.append("\n## Non-meme positions also present (excluded above)\n")
M.append("Tokenized stocks / stock-paired quote tokens: "+", ".join(f"{r['symbol']} ({r['traders']})" for r in rows if r['category']=='stock-token')[:1500])
M.append("\nMajors, stables, platform tokens: "+", ".join(f"{r['symbol']} ({r['traders']})" for r in rows if r['category']=='major/stable/platform')[:800])
M.append("\nAnomalous marks (fomo unrealized PnL implausible vs FDV; excluded from sums): "+", ".join(f"{r['symbol']} {r['address'][:10]} (${r['unrealized']:,.0f}, {r['traders']} traders)" for r in rows if r['anomaly'])[:1500])
rows=[r for r in rows if not r['anomaly']]
# chain summary and concentration
bych=collections.defaultdict(lambda:{"tokens":0,"positions":0,"realized":0.0,"unrealized":0.0})
for r in rows: c=bych[r['chain']]; c['tokens']+=1; c['positions']+=r['positions']; c['realized']+=r['realized']; c['unrealized']+=r['unrealized']
M.append("\n## By chain\n\n| chain | tokens | positions | realized $ (captured) | unrealized $ (open) |\n|---|---|---|---|---|")
for c,v in sorted(bych.items(),key=lambda kv:-kv[1]['positions']): M.append(f"| {c} | {v['tokens']} | {v['positions']} | {v['realized']:,.0f} | {v['unrealized']:,.0f} |")
tot_un=sum(r['unrealized'] for r in memes if r['unrealized']>0); top10=sum(r['unrealized'] for r in sorted(memes,key=lambda r:-r['unrealized'])[:10])
M.append(f"\nConcentration: the top 10 memes carry {100*top10/tot_un:.0f}% of all positive unrealized meme PnL across the 147 traders: "+", ".join(f"{r['symbol']} (${r['unrealized']:,.0f}, {r['traders']} traders)" for r in sorted(memes,key=lambda r:-r['unrealized'])[:10]))
M.append(f"\nMost-traded memes by number of leaderboard traders: "+", ".join(f"{r['symbol']} ({r['traders']})" for r in memes[:40]))
open(f'{OUT}/docs/MEMES.md','w').write("\n".join(M))
print("tokens",len(rows),"top:",[(r['symbol'],r['traders']) for r in rows[:15]])
print("top unrealized:",[(r['symbol'],round(r['unrealized'])) for r in sorted(rows,key=lambda r:-r['unrealized'])[:10]])
