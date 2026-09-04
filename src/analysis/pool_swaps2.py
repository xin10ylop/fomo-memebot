import json,urllib.request,time,bisect,glob,datetime,sys
# usage: pool_swaps2.py <day> <pool address or v4 poolId> <label>
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
SWAP_V3="0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"; SWAP_V4="0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"; PM="0x8366a39cc670b4001a1121b8f6a443a643e40951"
day,pool,label=sys.argv[1],sys.argv[2].lower(),sys.argv[3]; v4=len(pool)>42
ADDR=PM if v4 else pool; TOPICS=[SWAP_V4,pool] if v4 else [SWAP_V3]
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
def call(payload,tries=6):
    for i in range(tries):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(payload).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=120))
        except urllib.error.HTTPError as e: time.sleep(3*(i+1))
        except Exception as e: time.sleep(2)
t0=datetime.datetime.fromisoformat(day+'T00:00:00+00:00').timestamp(); b0,b1=blk(t0),blk(t0+86400)
logs=[]; step=4000; b=b0; n=0
while b<b1:
    e=min(b1,b+step); r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":hex(b),"toBlock":hex(e-1),"address":ADDR,"topics":TOPICS}]})
    if r is None: break
    if 'error' in r: step=max(200,step//2); continue
    res=r['result']
    for l in res: logs.append({"b":int(l['blockNumber'],16),"tx":l['transactionHash'],"li":int(l['logIndex'],16),"data":l['data'],"topics":l['topics']})
    n+=1; b=e
    if len(res)>6000: step=max(200,step//2)
    elif len(res)<1500: step=min(40000,step*2)
    time.sleep(0.25)
json.dump(logs,open(f'rh/swaps_{label}_{day}.json','w')); print('DONE',label,len(logs),'calls',n,file=sys.stderr)
