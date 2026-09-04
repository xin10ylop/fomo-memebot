import json,glob,collections,os,sys,bisect,datetime
# Log-based Robinhood ledger: rows from ERC-20 Transfer logs to/from each trader wallet; counterparty classification; candle pricing.
WETH="0x0bd7d308f8e1639fab988df18a8011f41eacad73"; ROUTER="0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f"
blocks={}
for _f in glob.glob('rh/blocks/blocks*.json'):
    try: blocks.update(json.load(open(_f)))
    except Exception: pass
_pts=sorted((int(k,16),v) for k,v in blocks.items()); _xs=[p[0] for p in _pts]; _ys=[p[1] for p in _pts]
def block_ts(bhex):
    """exact timestamp if known, else linear interpolation between nearest anchors (median error <1s where anchors are dense)"""
    if bhex in blocks: return blocks[bhex]
    b=int(bhex,16); i=bisect.bisect_left(_xs,b)
    if i<=0: return _ys[0]-(_xs[0]-b)/9.9 if _xs else None
    if i>=len(_xs): return _ys[-1]+(b-_xs[-1])/9.9
    x0,y0,x1,y1=_xs[i-1],_ys[i-1],_xs[i],_ys[i]
    return y0+(y1-y0)*(b-x0)/(x1-x0) if x1>x0 else y0
mints=json.load(open('rh/mints/mints.json')) if os.path.exists('rh/mints/mints.json') else {}
files=sorted(f for f in glob.glob('rh/logs/*.json') if not f.endswith('.ledger.json'))
# counterparty stats across wallets
cp_in=collections.defaultdict(set); cp_out=collections.defaultdict(set)
for f in files:
    d=json.load(open(f)); w=d['wallet'].lower()
    for l in d['in']: cp_in["0x"+l['topics'][1][-40:]].add(w)
    for l in d['out']: cp_out["0x"+l['topics'][2][-40:]].add(w)
legit=set(cp_out)|{ROUTER}
cp_in_cnt=collections.Counter()
for f in files:
    d=json.load(open(f))
    for l in d['in']: cp_in_cnt["0x"+l['topics'][1][-40:]]+=1
# inbound-only counterparties that hit many wallets or send many transfers are airdrop/spam senders
airdroppers={a for a,ws in cp_in.items() if a not in legit and (len(ws)>=5 or cp_in_cnt[a]>=50)}
_cc={}
def tok_price(a,ts):
    if a not in _cc:
        series=[]
        for f in (f'gt/ohlcv1m/{a}.json',f'gt/ohlcv/{a}.json'):
            if os.path.exists(f):
                c=sorted(json.load(open(f))['candles'],key=lambda x:x[0])
                if c: series.append({"t":[x[0] for x in c],"c":[x[4] for x in c],"o":[x[1] for x in c],"liq":(json.load(open(f)).get('pool') or {}).get('liq')})
        _cc[a]=series
    if not ts: return None,None
    for o in _cc[a]:
        i=bisect.bisect_right(o['t'],ts)-1
        if i>=0 and ts-o['t'][i]<=3600*6: return o['c'][i],o['liq']
        if i<0 and o['t'][0]-ts<3600*6: return o['o'][0],o['liq']
    return None,None
def build(f):
    d=json.load(open(f)); w=d['wallet'].lower(); rows=[]
    for l in d['in']+d['out']:
        a=l['address'].lower()
        if a==WETH: continue
        frm="0x"+l['topics'][1][-40:]; to="0x"+l['topics'][2][-40:]
        amt=int(l['data'],16)/1e18 if l['data'] and l['data']!='0x' else 0
        if amt<=0: continue
        ts=block_ts(l['blockNumber']); b=int(l['blockNumber'],16)
        if to==w:
            v=amt; cp=frm
            kind="fill" if cp in legit else ("airdrop" if cp in airdroppers else ("mint" if cp=="0x"+"0"*40 else "transfer_in"))
        else:
            v=-amt; cp=to; kind="fill" if cp in legit else "transfer_out"
        px,liq=tok_price(a,ts) if kind=="fill" else (None,None)
        usd=abs(v)*px if px else None
        side="buy" if v>0 else "sell"
        if kind=="fill" and usd is not None:
            if usd<5: kind="dust"
            elif liq and usd>5*float(liq)+1e6: kind="suspect"  # implausible vs pool liquidity
        rows.append({"ts":ts,"b":b,"tx":l['transactionHash'],"token":a,"amt":v,"usd":usd,"px":px,"side":side if kind=="fill" else kind,"cp":cp,"mint":mints.get(a),"ts_exact":l['blockNumber'] in blocks})
    rows.sort(key=lambda r:(r['b'],r['tx']))
    return w,rows
if __name__=="__main__":
    summ={}
    for f in files:
        h=f.split('/')[-1][:-5]; w,rows=build(f)
        json.dump(rows,open(f'rh/logs/{h}.ledger.json','w'))
        c=collections.Counter(r['side'] for r in rows)
        fills=[r for r in rows if r['side'] in ('buy','sell')]
        unpriced=[r for r in rows if r['side'] in ('buy','sell') and r['usd'] is None]
        summ[h]={"rows":len(rows),**c,"fills_priced":sum(1 for r in fills if r['usd'] is not None),"buy_usd":sum(r['usd'] or 0 for r in fills if r['side']=='buy'),"sell_usd":sum(r['usd'] or 0 for r in fills if r['side']=='sell'),"fill_tokens":len({r['token'] for r in fills}),"unpriced_fill_tokens":len({r['token'] for r in unpriced})}
    json.dump(summ,open('rh_ledger_v2_summary.json','w'),indent=1)
    print("airdroppers",len(airdroppers),"legit counterparties",len(legit))
    tot=collections.Counter()
    for h,s in summ.items():
        for k in ('buy','sell','airdrop','transfer_in','transfer_out','dust','suspect','mint'): tot[k]+=s.get(k,0)
    print("totals",dict(tot),"fills priced",sum(s['fills_priced'] for s in summ.values()),"unpriced fill tokens",len(set().union(*[set() for _ in []])) )
    top=sorted(summ.items(),key=lambda kv:-(kv[1].get('buy',0)+kv[1].get('sell',0)))[:12]
    for h,s in top: print(f"  {h:18s} buys={s.get('buy',0):4d} sells={s.get('sell',0):4d} priced={s['fills_priced']:4d} buy_usd={s['buy_usd']:12,.0f} sell_usd={s['sell_usd']:12,.0f} airdrop={s.get('airdrop',0)} tin={s.get('transfer_in',0)} tout={s.get('transfer_out',0)} tokens={s['fill_tokens']} unpriced_tok={s['unpriced_fill_tokens']}")
    # token demand for price pulls: tokens by number of leaderboard wallets with fills
    dem=collections.Counter()
    for f in files:
        h=f.split('/')[-1][:-5]
        for r in json.load(open(f'rh/logs/{h}.ledger.json')):
            if r['side'] in ('buy','sell'): dem[r['token']]+=1
    json.dump(dem.most_common(),open('rh_fill_token_demand.json','w'))
    print("fill tokens total",len(dem),"with >=3 fills",sum(1 for k,v in dem.items() if v>=3))
