import json,urllib.request,time,os,sys,glob
RPC="https://rpc.mainnet.chain.robinhood.com"
H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SWAP_V3="0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
SWAP_V4="0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
WETH="0x0bd7d308f8e1639fab988df18a8011f41eacad73"
MAX_TX=8000
def call(payload,tries=5):
    for i in range(tries):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(payload).encode(),headers=H)
            return json.load(urllib.request.urlopen(req,timeout=120))
        except urllib.error.HTTPError as e:
            time.sleep(6*(i+1) if e.code==429 else 3)
        except Exception as e: time.sleep(3)
    print("FAIL batch",file=sys.stderr); return None
def batch(method,params_list,size=40,sleep=0.35):
    out={}
    for i in range(0,len(params_list),size):
        chunk=params_list[i:i+size]
        r=call([{"jsonrpc":"2.0","id":j,"method":method,"params":p} for j,p in enumerate(chunk)])
        if r is None: continue
        for x in r:
            if x.get('result') is not None: out[json.dumps(chunk[x['id']])]=x['result']
        time.sleep(sleep)
    return out
def compact(rc,w):
    logs=[]
    for lg in rc.get('logs',[]):
        t=lg.get('topics') or []
        if not t: continue
        if t[0]==TRANSFER and len(t)>=3:
            frm="0x"+t[1][-40:]; to="0x"+t[2][-40:]
            if frm==w or to==w or lg['address'].lower()==WETH:
                logs.append({"a":lg['address'].lower(),"e":"T","f":frm,"t":to,"v":lg['data'],"i":lg['logIndex']})
        elif t[0] in (SWAP_V3,SWAP_V4):
            logs.append({"a":lg['address'].lower(),"e":"S3" if t[0]==SWAP_V3 else "S4","d":lg['data'][:2+64*5],"i":lg['logIndex'],"topics":t[1:]})
    return {"b":rc['blockNumber'],"s":rc['status'],"g":rc.get('gasUsed'),"gp":rc.get('effectiveGasPrice'),"l":logs}
blocks_f='rh/blocks/blocks.json'; blocks=json.load(open(blocks_f)) if os.path.exists(blocks_f) else {}
mints_f='rh/mints/mints.json'; mints=json.load(open(mints_f)) if os.path.exists(mints_f) else {}
# priority: leaderboard all-time rank, then others
prio=[]
for wname in ['all','30d','7d','24h']:
    for t in json.load(open(f'fapi/lb/{wname}.json'))['traders']:
        if t['handle'] not in prio: prio.append(t['handle'])
files=[f'rh/logs/{h}.json' for h in prio if os.path.exists(f'rh/logs/{h}.json')]
for f in files:
    h=f.split('/')[-1][:-5]; out=f"rh/receipts/{h}.json"
    if os.path.exists(out): continue
    d=json.load(open(f)); w=d['wallet'].lower(); logs=d['in']+d['out']
    bytx={}
    for l in logs: bytx.setdefault(l['transactionHash'],int(l['blockNumber'],16))
    txs=sorted(bytx,key=lambda t:-bytx[t])[:MAX_TX]  # most recent first, capped
    rc=batch("eth_getTransactionReceipt",[[t] for t in txs])
    receipts={json.loads(k)[0]:compact(v,w) for k,v in rc.items()}
    txd=batch("eth_getTransactionByHash",[[t] for t in txs])
    txinfo={json.loads(k)[0]:{"value":v.get('value'),"to":(v.get('to') or '').lower(),"from":(v.get('from') or '').lower(),"sel":(v.get('input') or '')[:10]} for k,v in txd.items()}
    json.dump({"handle":h,"wallet":w,"n_tx_total":len(bytx),"receipts":receipts,"tx":txinfo},open(out,"w"))
    need=sorted({v['b'] for v in receipts.values() if v['b'] not in blocks})
    bl=batch("eth_getBlockByNumber",[[b,False] for b in need],size=100,sleep=0.3)
    for k,v in bl.items(): blocks[json.loads(k)[0]]=int(v['timestamp'],16)
    json.dump(blocks,open(blocks_f,"w"))
    toks=sorted({l['a'] for v in receipts.values() for l in v['l'] if l['e']=='T' and l['a']!=WETH and l['a'] not in mints})
    for i in range(0,len(toks),40):
        chunk=toks[i:i+40]
        r=call([{"jsonrpc":"2.0","id":j,"method":"eth_getLogs","params":[{"fromBlock":"0x0","toBlock":"latest","address":a,"topics":[TRANSFER,"0x"+"0"*64]}]} for j,a in enumerate(chunk)])
        if r:
            for x in r:
                res=x.get('result')
                if res is not None: mints[chunk[x['id']]]=(res[0]['blockNumber'] if res else None)
        time.sleep(0.35)
    json.dump(mints,open(mints_f,"w"))
    print(h,"txs",len(txs),"of",len(bytx),"receipts",len(receipts),"blocks",len(blocks),"mints",len(mints),file=sys.stderr,flush=True)
print("DONE",file=sys.stderr)
