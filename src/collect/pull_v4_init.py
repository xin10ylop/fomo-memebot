import json,urllib.request,time,bisect,glob,datetime,sys
from eth_utils import keccak
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
PM="0x8366a39cc670b4001a1121b8f6a443a643e40951"; INIT="0x"+keccak(text="Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)").hex()
day=sys.argv[1]
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
        except Exception as e: time.sleep(4*(i+1))
t0=datetime.datetime.fromisoformat(day+'T00:00:00+00:00').timestamp(); b0,b1=blk(t0-600),blk(t0+86400)
out=[]; b=b0; step=20000
while b<b1:
    e=min(b1,b+step); r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":hex(b),"toBlock":hex(e-1),"address":PM,"topics":[INIT]}]})
    if r is None: time.sleep(10); continue
    if 'error' in r: step=max(500,step//2); continue
    for l in r['result']:
        d=l['data'][2:]
        out.append({"b":int(l['blockNumber'],16),"tx":l['transactionHash'],"pid":l['topics'][1],"c0":"0x"+l['topics'][2][-40:],"c1":"0x"+l['topics'][3][-40:],"fee":int(d[0:64],16),"hooks":"0x"+d[128:192][-40:],"sqrtP":int(d[192:256],16)})
    b=e
    if len(r['result'])>7000: step=max(500,step//2)
    elif len(r['result'])<2000: step=min(100000,step*2)
    time.sleep(0.4)
json.dump(out,open(f'rh/v4init_{day}.json','w')); print('DONE',len(out),file=sys.stderr)
