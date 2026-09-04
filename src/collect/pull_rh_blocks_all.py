import json,urllib.request,time,os,sys,glob
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"; WETH="0x0bd7d308f8e1639fab988df18a8011f41eacad73"
ROUTER="0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f"
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
    json.dump(obj,open(f+".tmp","w")); os.replace(f+".tmp",f)
SHARD=int(sys.argv[1]) if len(sys.argv)>1 else 0; NSH=int(sys.argv[2]) if len(sys.argv)>2 else 1
blocks_f=f'rh/blocks/blocks_shard{SHARD}.json' if NSH>1 else 'rh/blocks/blocks.json'; mints_f='rh/mints/mints.json'
blocks=load(blocks_f); mints=load(mints_f)
known=load('rh/blocks/blocks.json'); blocks.update({}) 
# collect needed blocks (all logs) and tokens (fills only: counterparty router or seen as both in/out counterparties)
need_blocks=set(); toks=set(); cp_in={}; cp_out=set()
files=[f for f in glob.glob('rh/logs/*.json') if not f.endswith('.ledger.json')]
for f in files:
    d=json.load(open(f)); w=d['wallet'].lower()
    for l in d['in']+d['out']:
        need_blocks.add(l['blockNumber'])
    for l in d['in']:
        frm="0x"+l['topics'][1][-40:]; cp_in.setdefault(frm,set()).add(w)
    for l in d['out']:
        to="0x"+l['topics'][2][-40:]; cp_out.add(to)
legit={ROUTER}|cp_out
for f in files:
    d=json.load(open(f))
    for l in d['in']:
        frm="0x"+l['topics'][1][-40:]
        if frm in legit: toks.add(l['address'].lower())
    for l in d['out']: toks.add(l['address'].lower())
need=sorted(b for b in need_blocks if b not in blocks and b not in known)
need=[b for i,b in enumerate(need) if i%NSH==SHARD]; tk=sorted(t for t in toks if t not in mints and t!=WETH) if SHARD==NSH-1 else []
print("blocks needed",len(need),"tokens needed",len(tk),file=sys.stderr,flush=True)
for i in range(0,len(need),100):
    chunk=need[i:i+100]; r=call([{"jsonrpc":"2.0","id":j,"method":"eth_getBlockByNumber","params":[b,False]} for j,b in enumerate(chunk)])
    if r:
        for x in r:
            if x.get('result'): blocks[chunk[x['id']]]=int(x['result']['timestamp'],16)
    if (i//100)%20==0: save(blocks,blocks_f); print("blocks",i,"/",len(need),file=sys.stderr,flush=True)
    time.sleep(0.25)
save(blocks,blocks_f)
for i in range(0,len(tk),40):
    chunk=tk[i:i+40]; r=call([{"jsonrpc":"2.0","id":j,"method":"eth_getLogs","params":[{"fromBlock":"0x0","toBlock":"latest","address":a,"topics":[TRANSFER,"0x"+"0"*64]}]} for j,a in enumerate(chunk)])
    if r:
        for x in r:
            res=x.get('result')
            if res is not None: mints[chunk[x['id']]]=(res[0]['blockNumber'] if res else None)
    if (i//40)%20==0: save(mints,mints_f); print("mints",i,"/",len(tk),file=sys.stderr,flush=True)
    time.sleep(0.3)
save(mints,mints_f); print("DONE blocks",len(blocks),"mints",len(mints),file=sys.stderr)
