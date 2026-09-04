import json,urllib.request,time,os,sys,glob
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"; WETH="0x0bd7d308f8e1639fab988df18a8011f41eacad73"
def call(payload,tries=5):
    for i in range(tries):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(payload).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=120))
        except urllib.error.HTTPError as e: time.sleep(6*(i+1) if e.code==429 else 3)
        except Exception: time.sleep(3)
    return None
def load(f): 
    try: return json.load(open(f))
    except Exception: return {}
def save(obj,f):
    cur=load(f); cur.update(obj); json.dump(cur,open(f+f".{os.getpid()}","w")); os.replace(f+f".{os.getpid()}",f); return cur
blocks_f='rh/blocks/blocks.json'; mints_f='rh/mints/mints.json'
blocks=load(blocks_f); mints=load(mints_f)
files=[f for f in glob.glob('rh/receipts/*.json') if not f.endswith('.ledger.json')]
if len(sys.argv)>1: files=[f'rh/receipts/{h}.json' for h in sys.argv[1:]]
for f in files:
    d=json.load(open(f)); rcs=d['receipts']
    need=sorted({v['b'] for v in rcs.values() if v['b'] not in blocks})
    for i in range(0,len(need),100):
        chunk=need[i:i+100]; r=call([{"jsonrpc":"2.0","id":j,"method":"eth_getBlockByNumber","params":[b,False]} for j,b in enumerate(chunk)])
        if r:
            for x in r:
                if x.get('result'): blocks[chunk[x['id']]]=int(x['result']['timestamp'],16)
        time.sleep(0.3)
    blocks=save(blocks,blocks_f)
    toks=sorted({l['a'] for v in rcs.values() for l in v['l'] if l['e']=='T' and l['a']!=WETH and l['a'] not in mints})
    for i in range(0,len(toks),40):
        chunk=toks[i:i+40]; r=call([{"jsonrpc":"2.0","id":j,"method":"eth_getLogs","params":[{"fromBlock":"0x0","toBlock":"latest","address":a,"topics":[TRANSFER,"0x"+"0"*64]}]} for j,a in enumerate(chunk)])
        if r:
            for x in r:
                res=x.get('result')
                if res is not None: mints[chunk[x['id']]]=(res[0]['blockNumber'] if res else None)
        time.sleep(0.35)
    mints=save(mints,mints_f)
    print(f,"blocks",len(need),"tokens",len(toks),"-> total blocks",len(blocks),"mints",len(mints),file=sys.stderr,flush=True)
print("DONE",file=sys.stderr)
