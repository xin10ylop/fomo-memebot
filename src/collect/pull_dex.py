import json,urllib.request,time,os,sys,glob,re
# collect unique token addresses from trades + balances (+ ws feed), fetch DexScreener metadata in batches of 30, cache
cache_f="dex/tokens.json"
cache=json.load(open(cache_f)) if os.path.exists(cache_f) else {}
addrs=set()
for f in glob.glob('fapi/trades/*.json'):
    for t in json.load(open(f)).get('trades',[]): 
        a=(t.get('token') or {}).get('address'); 
        if a: addrs.add(a)
for f in glob.glob('fapi/balances/*.json'):
    for t in json.load(open(f)).get('holdings',[]) or []:
        a=(t.get('token') or {}).get('address')
        if a: addrs.add(a)
if os.path.exists('fapi/ws_alerts.jsonl'):
    for l in open('fapi/ws_alerts.jsonl'):
        try: a=json.loads(l).get('tokenAddress')
        except: a=None
        if a: addrs.add(a)
todo=[a for a in addrs if a not in cache]
print("unique tokens",len(addrs),"todo",len(todo),file=sys.stderr)
def get(u,tries=3):
    for i in range(tries):
        try:
            req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 curl/8","Accept":"application/json"})
            return json.load(urllib.request.urlopen(req,timeout=60))
        except Exception as e:
            err=e; time.sleep(4*(i+1))
    print("FAIL",u[:80],err,file=sys.stderr); return None
for i in range(0,len(todo),30):
    batch=todo[i:i+30]
    d=get("https://api.dexscreener.com/latest/dex/tokens/"+",".join(batch))
    if d is None: continue
    by={}
    for p in d.get('pairs') or []:
        ba=p['baseToken']['address']; 
        # keep all pairs per token, sorted later
        by.setdefault(ba,[]).append({k:p.get(k) for k in ['chainId','dexId','pairAddress','priceUsd','priceNative','liquidity','fdv','marketCap','pairCreatedAt','volume','txns','priceChange','labels']} | {'quote':p['quoteToken']['symbol'],'symbol':p['baseToken']['symbol'],'name':p['baseToken']['name']})
    for a in batch:
        # dexscreener returns checksummed evm addrs; match case-insensitively
        found=None
        for k,v in by.items():
            if k.lower()==a.lower(): found=v
        cache[a]={"fetchedAt":int(time.time()),"pairs":found or []}
    json.dump(cache,open(cache_f,"w"))
    if (i//30)%10==0: print(i,"/",len(todo),file=sys.stderr,flush=True)
    time.sleep(0.35)
print("DONE cache",len(cache),file=sys.stderr)
