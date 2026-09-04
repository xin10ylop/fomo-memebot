import json,urllib.request,time,bisect,glob,datetime,sys,collections
# ERC-20 Transfer logs to/from the top sniper-bot wallets over the 12:00-18:00 window (any token), to reconstruct their trades
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def call(p):
    for i in range(8):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(p).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=120))
        except Exception as e: time.sleep(3*(i+1))
blocks={}
for f in glob.glob('rh/blocks/blocks*.json'):
    try: blocks.update(json.load(open(f)))
    except Exception: pass
pts=sorted((int(k,16),v) for k,v in blocks.items()); xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
def blk(ts):
    i=bisect.bisect_left(ys,ts)
    if i>=len(ys): return int(xs[-1]+(ts-ys[-1])*9.9)
    if i<=0: return int(xs[0]-(ys[0]-ts)*9.9)
    x0,y0,x1,y1=xs[i-1],ys[i-1],xs[i],ys[i]; return int(x0+(x1-x0)*(ts-y0)/(y1-y0))
t0=datetime.datetime.fromisoformat('2026-09-03T00:00:00+00:00').timestamp(); b0,b1=blk(t0+12*3600),blk(t0+18*3600+3600)   # +1h to catch exits
fb=json.load(open('rh/first_buyers_2026-09-03.json')); bw=json.load(open('rh/bundle_wallets_2026-09-03.json')); bots=set(bw['bots'])
cnt=collections.Counter(v['from'] for v in fb.values() if v['from'] in bots); top=[w for w,n in cnt.most_common(15)]
print('top bots',[(w[:10],n) for w,n in cnt.most_common(15)],file=sys.stderr)
out={}
for w in top:
    logs=[]
    for side,topics in (('in',[TRANSFER,None,"0x"+w[2:].rjust(64,'0')]),('out',[TRANSFER,"0x"+w[2:].rjust(64,'0')])):
        b=b0; step=50000
        while b<b1:
            e=min(b1,b+step); r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":hex(b),"toBlock":hex(e-1),"topics":topics}]})
            if r is None: time.sleep(5); continue
            if 'error' in r: step=max(1000,step//2); continue
            for l in r['result']: logs.append({'side':side,'b':int(l['blockNumber'],16),'tx':l['transactionHash'],'token':l['address'].lower(),'amt':int(l['data'],16) if l['data']!='0x' else 0,'cp':('0x'+l['topics'][1][-40:]) if side=='in' else ('0x'+l['topics'][2][-40:])})
            b=e
            if len(r['result'])<2000: step=min(200000,step*2)
            time.sleep(0.2)
    out[w]=logs; print(w[:10],'logs',len(logs),file=sys.stderr,flush=True); json.dump(out,open('rh/bot_transfers_2026-09-03.json','w'))
print('DONE',file=sys.stderr)
