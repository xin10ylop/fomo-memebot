import json,urllib.request,time,bisect,glob,datetime,sys,os
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
SWAP_V3="0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"; SWAP_V4="0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"; PM="0x8366a39cc670b4001a1121b8f6a443a643e40951"
pools=json.load(open('gt/pools_v3.json')); tm=json.load(open('/home/user/fomo-memebot/data/derived/token_metrics.json'))
a=[k for k,t in tm.items() if t['symbol']=='PONS' and t['chain']=='robinhood'][0]
pl=[p for p in pools[a]['pools'] if 'USDG' in p['name']][0]; pool=pl['address']; v4=len(pool)>42; print('pool',pl['name'],pool,'v4' if v4 else 'v3',file=sys.stderr)
ADDR=PM if v4 else pool; TOPICS=[SWAP_V4,pool] if v4 else [SWAP_V3]
blocks={}
for f in glob.glob('rh/blocks/blocks*.json'):
    try: blocks.update(json.load(open(f)))
    except Exception: pass
pts=sorted((int(k,16),v) for k,v in blocks.items()); xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
def blk(ts):  # block for timestamp via anchors
    i=bisect.bisect_left(ys,ts)
    if i>=len(ys): return int(xs[-1]+(ts-ys[-1])*9.9)
    if i<=0: return int(xs[0]-(ys[0]-ts)*9.9)
    x0,y0,x1,y1=xs[i-1],ys[i-1],xs[i],ys[i]; return int(x0+(x1-x0)*(ts-y0)/(y1-y0))
def call(payload,tries=6):
    for i in range(tries):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(payload).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=120))
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(3*(i+1))
            else: 
                body=e.read()[:200]; print('http',e.code,body,file=sys.stderr); time.sleep(2)
        except Exception as e: print('err',e,file=sys.stderr); time.sleep(2)
    return None
day=sys.argv[1] if len(sys.argv)>1 else '2026-09-03'
t0=datetime.datetime.fromisoformat(day+'T00:00:00+00:00').timestamp(); t1=t0+86400
b0,b1=blk(t0),blk(t1); print('blocks',b0,b1,b1-b0,file=sys.stderr)
out=f'rh/pons_swaps_{day}.json'; logs=[]
step=4000; b=b0; n=0
while b<b1:
    e=min(b1,b+step)
    r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":hex(b),"toBlock":hex(e-1),"address":ADDR,"topics":TOPICS}]})
    if r is None: print('giving up at',b,file=sys.stderr); break
    if 'error' in r:
        msg=str(r['error'])[:120]
        if 'limit' in msg.lower() or 'too many' in msg.lower() or 'range' in msg.lower(): step=max(200,step//2); print('shrink',step,msg,file=sys.stderr); continue
        print('rpc error',msg,file=sys.stderr); break
    res=r.get('result') or []
    for l in res: logs.append({"b":int(l['blockNumber'],16),"tx":l['transactionHash'],"li":int(l['logIndex'],16),"data":l['data'],"sender":("0x"+l['topics'][2][-40:]) if v4 else ("0x"+l['topics'][1][-40:])})
    n+=1; b=e
    if len(res)>6000: step=max(200,step//2)
    elif len(res)<1500: step=min(40000,step*2)
    if n%10==0: print(n,'calls',b,'logs',len(logs),file=sys.stderr,flush=True); json.dump(logs,open(out,'w'))
    time.sleep(0.25)
json.dump(logs,open(out,'w')); print('DONE',day,'logs',len(logs),'calls',n,file=sys.stderr)
