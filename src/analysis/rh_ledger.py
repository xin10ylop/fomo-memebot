import json,glob,collections,sys,os,bisect,datetime
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SWAP_V3="0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
WETH="0x0bd7d308f8e1639fab988df18a8011f41eacad73"
ethp=json.load(open('prices/eth_90d.json'))['prices']; etht=[p[0]/1000 for p in ethp]
def eth_usd(ts):
    i=bisect.bisect_left(etht,ts); i=min(max(i,0),len(ethp)-1); return ethp[i][1]
blocks=json.load(open('rh/blocks/blocks.json')) if os.path.exists('rh/blocks/blocks.json') else {}
mints=json.load(open('rh/mints/mints.json')) if os.path.exists('rh/mints/mints.json') else {}
def h2i(x): return int(x,16)
def ledger(handle):
    f=f'rh/receipts/{handle}.json'
    if not os.path.exists(f): return None
    d=json.load(open(f)); w=d['wallet'].lower(); rows=[]
    for txh,rc in d['receipts'].items():
        if rc.get('status')!='0x1': continue
        tx=d['tx'].get(txh,{}); bn=rc['blockNumber']; ts=blocks.get(bn)
        tok=collections.defaultdict(float); weth=0.0; usdc_like=0.0
        for lg in rc['logs']:
            if not lg['topics'] or lg['topics'][0]!=TRANSFER or len(lg['topics'])<3: continue
            frm="0x"+lg['topics'][1][-40:]; to="0x"+lg['topics'][2][-40:]; amt=h2i(lg['data']) if lg['data']!='0x' else 0
            a=lg['address'].lower()
            if to==w: 
                if a==WETH: weth+=amt/1e18
                else: tok[a]+=amt/1e18
            if frm==w:
                if a==WETH: weth-=amt/1e18
                else: tok[a]-=amt/1e18
        # native ETH sent as tx.value (buys) - only if wallet is the sender
        eth_out=0.0
        if tx.get('from','').lower()==w and tx.get('value'): eth_out=h2i(tx['value'])/1e18
        # ETH received on sells: not visible in logs (internal tx). Use Swap events: find swap where token leg matches
        swap_eth=0.0
        for lg in rc['logs']:
            if lg['topics'] and lg['topics'][0]==SWAP_V3 and len(lg['data'])>=2+64*2:
                a0=int(lg['data'][2:66],16); a1=int(lg['data'][66:130],16)
                a0=a0-(1<<256) if a0>=(1<<255) else a0; a1=a1-(1<<256) if a1>=(1<<255) else a1
                swap_eth+=0  # placeholder; per-pool token ordering unknown here
        toks={a:v for a,v in tok.items() if abs(v)>1e-12}
        if not toks: continue
        for a,v in toks.items():
            side="in" if v>0 else "out"; usd=None; eth=None
            if v>0 and (eth_out>0 or weth<0):
                eth=eth_out+(-weth); usd=eth*eth_usd(ts) if ts else None; side="buy"
            elif v<0 and weth>0:
                eth=weth; usd=eth*eth_usd(ts) if ts else None; side="sell"
            rows.append({"ts":ts,"block":h2i(bn),"tx":txh,"token":a,"amount":v,"eth":eth,"usd":usd,"side":side,"to":tx.get('to'),"n_tokens":len(toks),"mint_block":(h2i(mints[a]) if mints.get(a) else None)})
    rows.sort(key=lambda r:(r['block']))
    return rows
if __name__=="__main__":
    summ={}
    for f in sorted(glob.glob('rh/receipts/*.json')):
        h=f.split('/')[-1][:-5]; rows=ledger(h)
        if not rows: continue
        json.dump(rows,open(f'rh/receipts/{h}.ledger.json','w'))
        sides=collections.Counter(r['side'] for r in rows)
        # sells with unknown usd (native ETH received) count
        summ[h]={"rows":len(rows),**sides,"buy_usd":sum(r['usd'] or 0 for r in rows if r['side']=='buy'),"sell_usd":sum(r['usd'] or 0 for r in rows if r['side']=='sell'),"tokens":len({r['token'] for r in rows}),"first":datetime.datetime.utcfromtimestamp(min(r['ts'] for r in rows if r['ts'])).date().isoformat() if any(r['ts'] for r in rows) else None}
        print(h,summ[h])
    json.dump(summ,open('rh_ledger_summary.json','w'),indent=1)
    # inspect the 'to' contracts (routers) and out-without-sell patterns
    if summ:
        h=list(summ)[0]; rows=json.load(open(f'rh/receipts/{h}.ledger.json'))
        print("routers:",collections.Counter(r['to'] for r in rows).most_common(5))
        outs=[r for r in rows if r['side']=='out'][:3]; print("sample outs:",json.dumps(outs)[:800])
