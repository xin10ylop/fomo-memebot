import json,urllib.request,time,bisect,glob,datetime,sys,os
# Pons V2 curve trades (per-token curve contracts; topic-filtered, no address) for a window of one day, plus creation events with full topics for V2 and the 0x7ed5 pad.
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
BUY="0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL="0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
V2F="0xe33e9e479df8802cb0866d5d05258bec4cf62948"; PADF="0x7ed598bcef8bd9edd8c97a195c6d13f40801ec7e"
day=sys.argv[1]; h0=int(sys.argv[2]); h1=int(sys.argv[3])
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
def call(payload,tries=10):
    for i in range(tries):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(payload).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=180))
        except Exception as e: time.sleep(4*(i+1))
t0=datetime.datetime.fromisoformat(day+'T00:00:00+00:00').timestamp()
def scan(params_fn,b0,b1,step,label,out_path,mapper):
    f=open(out_path,'w'); b=b0; n=0; tot=0
    while b<b1:
        e=min(b1,b+step); r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[params_fn(b,e-1)]})
        if r is None: time.sleep(15); continue
        if 'error' in r: step=max(20,step//2); continue
        res=r['result']
        for l in res: f.write(json.dumps(mapper(l))+'\n')
        tot+=len(res); n+=1; b=e
        if len(res)>7000: step=max(20,step//2)
        elif len(res)<2500: step=min(20000,int(step*1.5))
        if n%25==0: f.flush(); print(label,n,'calls',b-b0,'/',b1-b0,'blocks',tot,'logs',file=sys.stderr,flush=True)
        time.sleep(0.25)
    f.close(); print('DONE',label,tot,file=sys.stderr,flush=True)
# 1) creation events with full topics for the whole day (V2 + pad)
for F,name in ((V2F,'v2'),(PADF,'pad')):
    scan(lambda b,e,F=F:{"fromBlock":hex(b),"toBlock":hex(e),"address":F},blk(t0),blk(t0+86400),20000,'create_'+name,f'rh/creates_{name}_{day}.jsonl',
         lambda l:[int(l['blockNumber'],16),l['transactionHash'],l['topics'],l['data']])
# 2) curve buys/sells for the window
scan(lambda b,e:{"fromBlock":hex(b),"toBlock":hex(e),"topics":[[BUY,SELL]]},blk(t0+h0*3600),blk(t0+h1*3600),300,'curve',f'rh/v2curve_{day}_{h0}-{h1}.jsonl',
     lambda l:[int(l['blockNumber'],16),int(l['logIndex'],16),l['transactionHash'],l['address'].lower(),l['topics'][0][:10],l['data']])
