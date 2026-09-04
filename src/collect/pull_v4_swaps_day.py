import json,urllib.request,time,bisect,glob,datetime,sys,os
# All Uniswap v4 PoolManager Swap events on Robinhood Chain for one UTC day (every pool), stored compactly.
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
SWAP_V4="0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"; PM="0x8366a39cc670b4001a1121b8f6a443a643e40951"
day=sys.argv[1]; part=int(sys.argv[2]) if len(sys.argv)>2 else 0; nparts=int(sys.argv[3]) if len(sys.argv)>3 else 1
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
def call(payload,tries=8):
    for i in range(tries):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(payload).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=180))
        except urllib.error.HTTPError as e: time.sleep(3*(i+1))
        except Exception as e: time.sleep(3)
def s256(x): return x-(1<<256) if x>=(1<<255) else x
t0=datetime.datetime.fromisoformat(day+'T00:00:00+00:00').timestamp(); B0,B1=blk(t0),blk(t0+86400); b0=B0+(B1-B0)*part//nparts; b1=B0+(B1-B0)*(part+1)//nparts
out=f'rh/v4swaps_{day}.p{part}.jsonl'; f=open(out,'a'); prog=f'rh/v4swaps_{day}.p{part}.progress'
b=int(open(prog).read()) if os.path.exists(prog) else b0; step=300; n=0; tot=0
while b<b1:
    e=min(b1,b+step); r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":hex(b),"toBlock":hex(e-1),"address":PM,"topics":[SWAP_V4]}]})
    if r is None: print('fail',b,file=sys.stderr); time.sleep(10); continue
    if 'error' in r: step=max(20,step//2); continue
    res=r['result']
    for l in res:
        d=l['data'][2:]
        f.write(json.dumps([int(l['blockNumber'],16),int(l['logIndex'],16),l['transactionHash'],l['topics'][1],s256(int(d[0:64],16)),s256(int(d[64:128],16)),int(d[128:192],16),int(d[192:256],16)])+'\n')
    tot+=len(res); n+=1; b=e; open(prog,'w').write(str(b))
    if len(res)>7000: step=max(20,step//2)
    elif len(res)<2500: step=min(5000,int(step*1.5))
    if n%50==0: f.flush(); print(n,'calls',b-b0,'/',b1-b0,'blocks',tot,'logs',file=sys.stderr,flush=True)
    time.sleep(0.2)
f.close(); print('DONE',day,tot,'logs',n,'calls',file=sys.stderr)
