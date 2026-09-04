import json,urllib.request,time,collections,datetime,bisect,glob,sys,os
# tx.from for the first 5 buy transactions after the creator's own buy on every Pons V2 curve launched in the window (to detect bundle wallets)
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
DAY='2026-09-03'; H0,H1=12,18
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
def bts(b):
    i=bisect.bisect_left(xs,b)
    if i<=0: return ys[0]-(xs[0]-b)/9.9
    if i>=len(xs): return ys[-1]+(b-xs[-1])/9.9
    x0,y0,x1,y1=xs[i-1],ys[i-1],xs[i],ys[i]; return y0+(y1-y0)*(b-x0)/(x1-x0)
t0day=datetime.datetime.fromisoformat(DAY+'T00:00:00+00:00').timestamp()
creates={}
for line in open(f'rh/creates_v2_{DAY}.jsonl'):
    b,tx,topics,data=json.loads(line); ts=bts(b)
    if t0day+H0*3600<=ts<t0day+H1*3600-1800: creates['0x'+topics[2][-40:].lower()]={'tx':tx,'creator':'0x'+topics[3][-40:].lower()}
per=collections.defaultdict(list)
for line in open(f'rh/v2curve_{DAY}_{H0}-{H1}.jsonl'):
    b,li,tx,addr,t0,data=json.loads(line)
    if addr in creates and t0=='0xec36bf57': per[addr].append((b,li,tx))
todo=[]
for addr,L in per.items():
    L.sort(); seen=[]
    for b,li,tx in L:
        if tx==creates[addr]['tx'] or tx in seen: continue
        seen.append(tx)
        if len(seen)>=5: break
    todo+=[(addr,tx) for tx in seen]
out_f='rh/first_buyers_2026-09-03.json'; out=json.load(open(out_f)) if os.path.exists(out_f) else {}
todo=[(a,t) for a,t in todo if t not in out]; print('txs to fetch',len(todo),file=sys.stderr,flush=True)
for i in range(0,len(todo),10):
    ch=todo[i:i+10]; r=call([{"jsonrpc":"2.0","id":j,"method":"eth_getTransactionByHash","params":[t]} for j,(a,t) in enumerate(ch)])
    for x in (r or []):
        if x.get('result'): out[ch[x['id']][1]]={'curve':ch[x['id']][0],'from':x['result']['from'].lower(),'to':(x['result'].get('to') or '').lower()}
    if (i//10)%100==0: json.dump(out,open(out_f,'w')); print(i,file=sys.stderr,flush=True)
    time.sleep(0.15)
json.dump(out,open(out_f,'w')); print('DONE',len(out),file=sys.stderr)
