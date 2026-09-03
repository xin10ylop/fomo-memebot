import json,glob,collections,sys,os,datetime,bisect
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"; USDT="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCdmbqV3o8G"; WSOL="So11111111111111111111111111111111111111112"
STABLES={USDC,USDT}
solp=json.load(open('prices/sol_90d.json'))['prices']; solt=[p[0]/1000 for p in solp]
def sol_usd(ts):
    i=bisect.bisect_left(solt,ts); i=min(max(i,0),len(solp)-1); return solp[i][1]
def ledger(handle):
    f=f'helius/parsed/{handle}.jsonl'
    if not os.path.exists(f): return None
    w=json.load(open(f'helius/sigs/{handle}.json'))['wallet']
    rows=[]
    for l in open(f):
        t=json.loads(l)
        if t.get('transactionError'): continue
        ts=t['timestamp']; delta=collections.defaultdict(float); native=0.0
        for ad in t.get('accountData',[]):
            if ad['account']==w: native+=ad.get('nativeBalanceChange',0)/1e9
            for tb in ad.get('tokenBalanceChanges',[]):
                if tb.get('userAccount')==w:
                    amt=int(tb['rawTokenAmount']['tokenAmount'])/10**tb['rawTokenAmount']['decimals']; delta[tb['mint']]+=amt
        # wrapped SOL counts as native
        native+=delta.pop(WSOL,0.0)
        stable=sum(delta.pop(m,0.0) for m in list(STABLES))
        toks={m:a for m,a in delta.items() if abs(a)>0}
        if not toks: continue
        if len(toks)!=1: 
            # multi-token tx (e.g. token->token swap or airdrop batch) - record each leg without price
            for m,a in toks.items(): rows.append({"ts":ts,"sig":t['signature'],"mint":m,"amount":a,"usd":None,"side":"in" if a>0 else "out","src":t.get('source'),"type":t.get('type'),"multi":True})
            continue
        m,a=next(iter(toks.items()))
        usd_out=-(stable if stable<0 else 0)+(-native*sol_usd(ts) if native<0 else 0)
        usd_in=(stable if stable>0 else 0)+(native*sol_usd(ts) if native>0 else 0)
        if a>0 and usd_out>0.5: side="buy"; usd=usd_out
        elif a<0 and usd_in>0.5: side="sell"; usd=usd_in
        elif a>0: side="in"; usd=None
        else: side="out"; usd=None
        rows.append({"ts":ts,"sig":t['signature'],"mint":m,"amount":a,"usd":usd,"side":side,"src":t.get('source'),"type":t.get('type'),"multi":False})
    rows.sort(key=lambda r:r['ts'])
    return rows
def fifo_pnl(rows):
    # per mint: average-cost realized pnl; positions
    pos=collections.defaultdict(lambda:{"qty":0.0,"cost":0.0,"realized":0.0,"buys":0,"sells":0,"first":None,"last":None,"buy_usd":0.0,"sell_usd":0.0,"free_in":0.0})
    trades=[]
    for r in rows:
        p=pos[r['mint']]; p['first']=p['first'] or r['ts']; p['last']=r['ts']
        if r['side']=='buy':
            p['qty']+=r['amount']; p['cost']+=r['usd']; p['buys']+=1; p['buy_usd']+=r['usd']
        elif r['side']=='sell':
            q=-r['amount']; 
            if p['qty']>1e-9:
                avg=p['cost']/p['qty'] if p['qty']>0 else 0; used=min(q,p['qty']); realized=r['usd']-avg*used
                # if selling more than held (airdrop/transfer-in), extra proceeds count as realized with zero cost
                if q>p['qty']: realized=r['usd']-avg*p['qty']
                p['realized']+=realized; p['cost']-=avg*used; p['qty']-=used
                trades.append({"mint":r['mint'],"ts":r['ts'],"usd":r['usd'],"realized":realized,"hold_h":(r['ts']-p['first'])/3600})
            else:
                p['realized']+=r['usd']; trades.append({"mint":r['mint'],"ts":r['ts'],"usd":r['usd'],"realized":r['usd'],"hold_h":None,"no_cost":True})
            p['sells']+=1; p['sell_usd']+=r['usd']
        elif r['side']=='in': p['free_in']+=r['amount']; p['qty']+=r['amount']
        elif r['side']=='out': p['qty']=max(0.0,p['qty']+r['amount'])
    return pos,trades
if __name__=="__main__":
    out={}
    for f in sorted(glob.glob('helius/parsed/*.jsonl')):
        h=f.split('/')[-1][:-6]
        if not os.path.exists(f+'.done'): continue
        rows=ledger(h); 
        if rows is None: continue
        pos,trades=fifo_pnl(rows)
        buys=[r for r in rows if r['side']=='buy']; sells=[r for r in rows if r['side']=='sell']
        real=sum(t['realized'] for t in trades)
        by_tok=collections.defaultdict(float)
        for t in trades: by_tok[t['mint']]+=t['realized']
        top=sorted(by_tok.items(),key=lambda kv:-kv[1])[:3]
        wins=sum(1 for v in by_tok.values() if v>0); n=len(by_tok)
        out[h]={"n_buys":len(buys),"n_sells":len(sells),"buy_usd":sum(r['usd'] for r in buys),"sell_usd":sum(r['usd'] for r in sells),"realized":real,"tokens_traded":n,"token_win_rate":wins/n if n else None,"top3_tokens_pnl":[(k[:8],round(v)) for k,v in top],"top1_share":(top[0][1]/sum(v for v in by_tok.values() if v>0)) if top and top[0][1]>0 else None,"first":datetime.datetime.utcfromtimestamp(rows[0]['ts']).date().isoformat() if rows else None,"median_buy_usd":sorted(r['usd'] for r in buys)[len(buys)//2] if buys else None}
        json.dump({"rows":rows,"trades":trades,"pos":{k:v for k,v in pos.items()}},open(f'helius/parsed/{h}.ledger.json','w'))
    json.dump(out,open('sol_ledger_summary.json','w'),indent=1)
    import pandas as pd; pd.set_option('display.width',250)
    df=pd.DataFrame(out).T.sort_values('realized',ascending=False)
    print(df[['n_buys','n_sells','buy_usd','sell_usd','realized','tokens_traded','token_win_rate','top1_share','median_buy_usd','first']].to_string())
