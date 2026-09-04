import json,urllib.request,time,os,sys,glob,datetime,collections
NET={'robinhood':'robinhood','solana':'solana','bsc':'bsc','base':'base','ethereum':'eth'}
dex=json.load(open('dex/tokens.json'))
last=[0.0]
def get(u,tries=4):
    for i in range(tries):
        gap=time.time()-last[0]
        if gap<2.05: time.sleep(2.05-gap)
        try:
            req=urllib.request.Request(u,headers={"Accept":"application/json","User-Agent":"Mozilla/5.0 curl/8"})
            r=urllib.request.urlopen(req,timeout=60); last[0]=time.time(); return json.load(r)
        except urllib.error.HTTPError as e:
            last[0]=time.time()
            if e.code==429: time.sleep(15); continue
            if e.code==404: return None
            time.sleep(3)
        except Exception as e: last[0]=time.time(); time.sleep(3)
    return None
def iso(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
need={}
def add(a,ts,chain=None,prio=2):
    if not a: return
    x=need.setdefault(a,{"chain":chain,"min_ts":ts,"prio":prio})
    if chain and not x["chain"]: x["chain"]=chain
    if ts and (x["min_ts"] is None or ts<x["min_ts"]): x["min_ts"]=ts
    x["prio"]=min(x["prio"],prio)
for f in glob.glob('fapi/trades/*.json'):
    for t in json.load(open(f)).get('trades',[]):
        a=(t.get('token') or {}).get('address'); add(a, iso(t['createdAt']) if t.get('createdAt') else None, None, 0 if t.get('status')=='closed' else 1)
for l in open('fapi/ws_alerts.jsonl'):
    try: d=json.loads(l)
    except: continue
    add(d.get('tokenAddress'), (d.get('ts') or 0)/1000 or None, d.get('chain'), 1)
for f in glob.glob('rh/receipts/*.ledger.json'):
    for r in json.load(open(f)):
        if r.get('side') in ('buy','sell','in','out') and r.get('ts'): add(r['token'], r['ts'], 'robinhood', 0)
for f in glob.glob('fapi/balances/*.json'):
    for t in json.load(open(f)).get('holdings',[]) or []:
        a=(t.get('token') or {}).get('address'); add(a,None,t.get('chain'),3)
for a,x in need.items():
    ps=(dex.get(a) or {}).get('pairs') or []
    if ps and not x["chain"]: x["chain"]=sorted(ps,key=lambda p:-((p.get('liquidity') or {}).get('usd') or 0))[0]['chainId']
# ---- pool discovery via multi endpoint ----
pools_f='gt/pools_multi.json'; pools=json.load(open(pools_f)) if os.path.exists(pools_f) else {}
def discover(net,addrs):
    for i in range(0,len(addrs),30):
        chunk=addrs[i:i+30]
        r=get(f"https://api.geckoterminal.com/api/v2/networks/{net}/tokens/multi/"+",".join(chunk)+"?include=top_pools")
        found=set()
        if r:
            inc={x['id']:x['attributes'] for x in r.get('included',[])}
            for t in r.get('data',[]):
                a=t['attributes']['address']; found.add(a.lower())
                tp=[p['id'] for p in (t['relationships'].get('top_pools') or {}).get('data',[])]
                pl=[{"id":pid,"address":pid.split('_',1)[1],"liq":float(inc.get(pid,{}).get('reserve_in_usd') or 0),"created":inc.get(pid,{}).get('pool_created_at'),"name":inc.get(pid,{}).get('name')} for pid in tp]
                pools[a.lower()]={"network":net,"symbol":t['attributes'].get('symbol'),"fdv":t['attributes'].get('fdv_usd'),"total_supply":t['attributes'].get('total_supply'),"decimals":t['attributes'].get('decimals'),"pools":pl}
        for a in chunk:
            if a.lower() not in found and a.lower() not in pools: pools[a.lower()]={"network":net,"pools":[],"miss":True}
        json.dump(pools,open(pools_f,"w"))
bychain=collections.defaultdict(list)
for a,x in need.items():
    if a.lower() in pools and not pools[a.lower()].get('miss'): continue
    net=NET.get(x["chain"])
    if net: bychain[net].append(a)
    else: bychain['?'].append(a)
print({k:len(v) for k,v in bychain.items()},file=sys.stderr)
for net,addrs in bychain.items():
    if net=='?': continue
    discover(net,[a for a in addrs if a.lower() not in pools or pools[a.lower()].get('miss')])
# unknown-chain tokens: try robinhood if 0x else solana
unk=[a for a in bychain['?'] if a.lower() not in pools or pools[a.lower()].get('miss')]
discover('robinhood',[a for a in unk if a.startswith('0x')]); discover('solana',[a for a in unk if not a.startswith('0x')])
still=[a for a in unk if pools.get(a.lower(),{}).get('miss')]
for net in ['bsc','base']:
    discover(net,[a for a in still if a.startswith('0x') and pools.get(a.lower(),{}).get('miss')])
    # refresh 'still'
    still=[a for a in still if pools.get(a.lower(),{}).get('miss')]
print("pools known",sum(1 for v in pools.values() if v.get('pools')),"missing",sum(1 for v in pools.values() if not v.get('pools')),file=sys.stderr,flush=True)
# ---- OHLCV ----
now=time.time()
order=sorted(need.items(), key=lambda kv:(kv[1]["prio"], kv[1]["min_ts"] or now))
for i,(a,x) in enumerate(order):
    p=pools.get(a.lower())
    if not p or not p.get('pools'): continue
    of=f"gt/ohlcv/{a}.json"
    if os.path.exists(of): continue
    pool=max(p['pools'],key=lambda q:q['liq'])
    target=(x["min_ts"] or now-30*86400)-86400
    candles=[]; before=None
    for page in range(10):
        u=f"https://api.geckoterminal.com/api/v2/networks/{p['network']}/pools/{pool['address']}/ohlcv/minute?aggregate=15&limit=1000&currency=usd"+(f"&before_timestamp={before}" if before else "")
        r=get(u)
        o=(((r or {}).get('data') or {}).get('attributes') or {}).get('ohlcv_list') or []
        if not o: break
        candles+=o; before=o[-1][0]
        if o[-1][0]<=target or len(o)<1000: break
    json.dump({"network":p['network'],"pool":pool,"tf":"15m","candles":candles},open(of,"w"))
    if i%25==0: print(i,"/",len(order),a[:10],"candles",len(candles),file=sys.stderr,flush=True)
print("DONE",file=sys.stderr)
