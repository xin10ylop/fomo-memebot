import json,statistics as st,collections
d=json.load(open('dossiers.json'))
research=json.load(open('/home/user/fomo-memebot/docs/research_round1.json'))
notes={}
for r in research.get('researchers',[]):
    for f in r.get('findings',[]):
        c=f.get('claim','')
        for h in d:
            if c.startswith(h) or f" {h} " in c[:60] or c.startswith(f"{h}:"): notes.setdefault(h,[]).append(c[:220])
rows=[]
for h,v in d.items():
    p=v.get('profile',{}); pf=v.get('portfolio',{}); ft=v.get('fomo_trades',{}); rh=v.get('robinhood_onchain',{}); so=(v.get('solana_onchain') or {}).get('ledger',{})
    pnl_all=v['pnl'].get('all') or v['pnl'].get('30d') or v['pnl'].get('7d') or v['pnl'].get('24h') or 0
    vol=p.get('volume') or 0; followers=p.get('followers') or 0
    top1=pf.get('top1_share'); haircut=pf.get('haircut_pct')
    unreal=ft.get('unrealized_open_sum') or 0
    real_fomo=ft.get('sum_realized_sampled'); wr=ft.get('win_rate_sampled'); closed_total=ft.get('closed_total') or 0
    rh_real=rh.get('realized_usd_avgcost'); rh_priced=rh.get('priced_share') or 0; rh_full=rh.get('tokens_fully_priced') or 0
    sold_nobuy=rh.get('sold_without_buy_usd') or 0
    sol_real=so.get('realized'); sol_win=so.get('token_win_rate')
    pnl_vol=(pnl_all/vol) if vol else None
    # classification rules (evidence-based, conservative)
    cls="unknown"; why=[]
    if sold_nobuy>=100000 and sold_nobuy>=0.3*max(1,rh.get('sell_usd') or 1): cls="insider_or_allocation"; why.append(f"sold ${sold_nobuy:,.0f} of tokens never bought on-chain")
    elif pnl_vol is not None and pnl_vol>=3 and (top1 or 0)>=0.6: cls="luck_one_bag"; why.append(f"PnL/volume {pnl_vol:.1f}x, top holding {top1:.0%} of portfolio")
    elif followers>=150000: cls="kol_flow_mover"; why.append(f"{followers:,} followers")
    elif (top1 or 0)>=0.75 and unreal>0.7*max(pnl_all,1): cls="luck_one_bag"; why.append(f"top holding {top1:.0%}, unrealized {unreal/pnl_all:.0%} of PnL")
    elif ((rh_full>=5 and rh_real is not None and rh_real>50000) or (sol_real is not None and sol_real>50000)) and (wr or 0)>=0.4: cls="skill_candidate"; why.append(f"on-chain realized RH ${rh_real or 0:,.0f} (fully-priced tokens {rh_full}) / SOL ${sol_real or 0:,.0f}, sampled win rate {wr}")
    elif (real_fomo is not None and real_fomo<-20000) or ((sol_real or 0)<-30000): cls="active_churner_negative"; why.append(f"sampled realized fomo {real_fomo}, SOL realized {sol_real}")
    elif (top1 or 0)>=0.5: cls="concentrated_bag"; why.append(f"top holding {top1:.0%} of portfolio")
    rows.append({"handle":h,"rank_all":v['ranks'].get('all'),"pnl_all":pnl_all,"volume":vol,"pnl_over_volume":pnl_vol,"followers":followers,"portfolio_value":pf.get('value'),"top1_share":top1,"liq_haircut":haircut,"pnl24_over_mtm":pf.get('pnl24_over_mtm'),
                 "fomo_closed_total":closed_total,"fomo_sample_realized":real_fomo,"fomo_sample_winrate":wr,"rh_fills":rh.get('n_fills'),"rh_priced_share":rh_priced,"rh_realized_fullpriced":rh_real,"rh_sold_without_buy":sold_nobuy,"rh_entry_lag_min_median":rh.get('entry_lag_min_median'),"sol_realized":sol_real,"sol_token_winrate":sol_win,"classification":cls,"why":"; ".join(why),"research":notes.get(h,[])[:2]})
rows.sort(key=lambda r:(r['rank_all'] is None, r['rank_all'] or 999))
json.dump(rows,open('/home/user/fomo-memebot/data/derived/trader_classification.json','w'),indent=1)
print(collections.Counter(r['classification'] for r in rows))
md=["# Trader-by-trader classification (rule-based, from on-chain and fomo data)\n","Classes: insider_or_allocation = sells tokens never bought on-chain; luck_one_bag = PnL is unrealized appreciation of one early bag; kol_flow_mover = audience large enough to move prices; skill_candidate = repeatable realized profits on fully priced tokens; active_churner_negative = many trades, negative realized; concentrated_bag = one holding dominates; unknown = insufficient priced data.\n",
    "| # | handle | class | PnL all | PnL/volume | followers | top holding % | liquidity haircut | sampled closed realized | RH realized (fully priced tokens) | sold w/o buy | SOL realized | why |","|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    f=lambda x,fmt: (fmt.format(x) if x is not None else "")
    md.append(f"| {r['rank_all'] or ''} | {r['handle']} | {r['classification']} | {f(r['pnl_all'],'{:,.0f}')} | {f(r['pnl_over_volume'],'{:.1f}x')} | {r['followers']:,} | {f(r['top1_share'],'{:.0%}')} | {f(r['liq_haircut'],'{:.0%}')} | {f(r['fomo_sample_realized'],'{:,.0f}')} | {f(r['rh_realized_fullpriced'],'{:,.0f}')} | {f(r['rh_sold_without_buy'],'{:,.0f}')} | {f(r['sol_realized'],'{:,.0f}')} | {r['why']} |")
open('/home/user/fomo-memebot/docs/TRADERS.md','w').write("\n".join(md)); print("wrote docs/TRADERS.md",len(rows),"rows")
for r in rows[:20]: print(r['rank_all'],r['handle'],r['classification'],'|',r['why'][:110])
