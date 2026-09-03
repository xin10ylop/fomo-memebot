import json,glob,collections,datetime,statistics as st,math,os
def iso(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00')) if s else None
lb={w:{t['handle']:t for t in json.load(open(f'fapi/lb/{w}.json'))['traders']} for w in ['24h','7d','30d','all']}
handles=[]
for w in ['24h','7d','30d','all']:
    for h in lb[w]:
        if h not in handles: handles.append(h)
dex=json.load(open('dex/tokens.json')) if os.path.exists('dex/tokens.json') else {}
def dexinfo(a):
    v=dex.get(a) or {}; ps=v.get('pairs') or []
    if not ps: return None
    ps=sorted(ps,key=lambda p:-((p.get('liquidity') or {}).get('usd') or 0))
    p=ps[0]; return {"chain":p['chainId'],"liq":(p.get('liquidity') or {}).get('usd'),"fdv":p.get('fdv'),"mcap":p.get('marketCap'),"price":float(p['priceUsd']) if p.get('priceUsd') else None,"created":p.get('pairCreatedAt'),"dex":p.get('dexId')}
rows=[]
for h in handles:
    r={"handle":h}
    for w in ['24h','7d','30d','all']:
        t=lb[w].get(h)
        r[f"rank_{w}"]=t['rank'] if t else None; r[f"pnl_{w}"]=t['pnlUsd'] if t else None
    t=lb['all'].get(h) or lb['30d'].get(h) or lb['7d'].get(h) or lb['24h'].get(h)
    r.update({"followers":t.get('followers'),"trades_count":t.get('trades'),"volume":t.get('volumeUsd'),"holdings_n":t.get('holdings'),"sol_wallet":t['wallets'].get('solana'),"evm_wallet":t['wallets'].get('evm')})
    # balances
    bf=f'fapi/balances/{h}.json'
    if os.path.exists(bf):
        b=json.load(open(bf)); hs=b.get('holdings') or []
        tot=sum((x.get('valueUsd') or 0) for x in hs); r["port_value"]=tot
        r["by_chain"]={k:round(v.get('valueUsd',0)) for k,v in (b.get('byChain') or {}).items()}
        hs2=sorted(hs,key=lambda x:-(x.get('valueUsd') or 0))
        r["top1_share"]=(hs2[0]['valueUsd']/tot) if hs2 and tot else None
        r["top3_share"]=(sum(x['valueUsd'] for x in hs2[:3])/tot) if hs2 and tot else None
        r["mtm_24h_est"]=sum((x.get('valueUsd') or 0)*(1-1/(1+(x.get('change24h') or 0)/100)) for x in hs if x.get('change24h') is not None and x.get('change24h')>-100)
        r["pnl24_over_mtm"]=(r["pnl_24h"]/r["mtm_24h_est"]) if r.get("pnl_24h") and r["mtm_24h_est"] else None
        # liquidity-adjusted value of top holdings: position value vs pool liquidity
        adj=0; illiq=0
        for x in hs2[:20]:
            di=dexinfo((x.get('token') or {}).get('address'))
            v=x.get('valueUsd') or 0
            if di and di.get('liq'):
                L=di['liq']; 
                # constant-product impact approx: selling v into pool with liquidity L (half quote): proceeds ≈ v / (1 + v/(L/2))
                proceeds=v/(1+v/(L/2)); adj+=proceeds; illiq+= (v-proceeds)
            else: adj+=v*0.5; illiq+=v*0.5
        adj+=sum((x.get('valueUsd') or 0) for x in hs2[20:])
        r["port_value_liq_adj"]=adj; r["illiquidity_haircut"]=illiq
        r["top_holdings"]=[{"sym":(x.get('token') or {}).get('symbol'),"chain":x.get('chain'),"val":round(x.get('valueUsd') or 0),"chg24":x.get('change24h')} for x in hs2[:5]]
    # trades
    tf=f'fapi/trades/{h}.json'
    if os.path.exists(tf):
        d=json.load(open(tf)); tr=d.get('trades') or []
        c=[t for t in tr if t.get('status')=='closed']; o=[t for t in tr if t.get('status')=='open']
        r["open_n"]=d.get('activeCount'); r["closed_total"]=d.get('closedCount'); r["closed_sampled"]=len(c)
        pn=[t['realizedPnlUsd'] for t in c if t.get('realizedPnlUsd') is not None]
        if pn:
            r["c_win_rate"]=sum(p>0 for p in pn)/len(pn); r["c_sum_pnl"]=sum(pn); r["c_median_pnl"]=st.median(pn)
            wins=[p for p in pn if p>0]; losses=[-p for p in pn if p<0]
            r["c_avg_win"]=st.mean(wins) if wins else 0; r["c_avg_loss"]=st.mean(losses) if losses else 0
            r["c_profit_factor"]=(sum(wins)/sum(losses)) if losses else None
            r["c_top1_pnl_share"]=(max(pn)/sum(wins)) if wins else None
        hold=[(iso(t['closedAt'])-iso(t['createdAt'])).total_seconds()/3600 for t in c if t.get('createdAt') and t.get('closedAt')]
        if hold: r["c_hold_h_median"]=st.median(hold); r["c_hold_h_p25"]=sorted(hold)[len(hold)//4]; r["c_hold_h_p75"]=sorted(hold)[3*len(hold)//4]
        mult=[t['avgExitPrice']/t['avgEntryPrice'] for t in c if t.get('avgEntryPrice') and t.get('avgExitPrice')]
        if mult: r["c_exit_mult_median"]=st.median(mult); r["c_exit_mult_max"]=max(mult); r["c_exit_mult_gt2"]=sum(m>=2 for m in mult)/len(mult)
        r["thesis_rate"]=sum(1 for t in tr if t.get('thesis'))/len(tr) if tr else None
        # open positions: unrealized
        un=[t.get('unrealizedPnlUsd') or 0 for t in o]
        r["open_unrealized_sum"]=sum(un); r["open_unrealized_pos_n"]=sum(1 for u in un if u>0)
        # entry timestamps for open positions -> activity by hour
        hrs=collections.Counter(iso(t['createdAt']).hour for t in tr if t.get('createdAt'))
        r["active_hours_utc_top3"]=[h for h,_ in hrs.most_common(3)]
        days=collections.Counter(iso(t['createdAt']).date().isoformat() for t in tr if t.get('createdAt'))
        r["trade_days_sampled"]=len(days); r["first_trade_sampled"]=min(days) if days else None
        # chain mix via dex info
        ch=collections.Counter()
        for t in tr:
            di=dexinfo((t.get('token') or {}).get('address')); ch[di['chain'] if di else 'unknown']+=1
        r["trade_chain_mix"]=dict(ch)
        # entry mcap for closed trades: avgEntryPrice * supply (supply = fdv/price now)
        em=[]
        for t in c:
            di=dexinfo((t.get('token') or {}).get('address'))
            if di and di.get('fdv') and di.get('price') and t.get('avgEntryPrice'):
                supply=di['fdv']/di['price']; em.append(t['avgEntryPrice']*supply)
        if em: r["c_entry_mcap_median"]=st.median(em); r["c_entry_mcap_p25"]=sorted(em)[len(em)//4]; r["c_entry_mcap_p75"]=sorted(em)[3*len(em)//4]
    # solana on-chain activity
    sf=f'helius/sigs/{h}.json'
    if os.path.exists(sf):
        s=json.load(open(sf))['sigs']; bt=[x['blockTime'] for x in s if x.get('blockTime')]
        r["sol_tx_n"]=len(s)
        if bt:
            r["sol_first_tx"]=datetime.datetime.utcfromtimestamp(min(bt)).date().isoformat(); r["sol_last_tx"]=datetime.datetime.utcfromtimestamp(max(bt)).date().isoformat()
            r["sol_active_days"]=len({datetime.datetime.utcfromtimestamp(t).date() for t in bt})
            r["sol_fail_rate"]=sum(1 for x in s if x.get('err'))/len(s)
    rows.append(r)
json.dump(rows,open('features_v1.json','w'),indent=1)
print("rows",len(rows))
import pandas as pd
df=pd.DataFrame(rows)
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)
cols=[c for c in ['handle','rank_all','pnl_all','pnl_24h','port_value','top1_share','pnl24_over_mtm','illiquidity_haircut','closed_total','c_win_rate','c_sum_pnl','c_profit_factor','c_hold_h_median','c_exit_mult_median','c_entry_mcap_median','sol_tx_n','trade_chain_mix'] if c in df.columns]
print(df[cols].head(40).to_string())
