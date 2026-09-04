import json,urllib.request,time,os,sys,collections
NET={'robinhood':'robinhood','solana':'solana','bsc':'bsc','base':'base','ethereum':'eth'}
_last=[0.0]
def get(u,tries=4):
    for i in range(tries):
        gap=time.time()-_last[0]
        if gap<2.05: time.sleep(2.05-gap)
        try:
            req=urllib.request.Request(u,headers={"Accept":"application/json","User-Agent":"Mozilla/5.0 curl/8"})
            r=urllib.request.urlopen(req,timeout=60); _last[0]=time.time(); return json.load(r)
        except urllib.error.HTTPError as e:
            _last[0]=time.time()
            if e.code==429: time.sleep(15); continue
            if e.code==404: return None
            time.sleep(3)
        except Exception: _last[0]=time.time(); time.sleep(3)
    return None
POOLS_F='gt/pools_v3.json'
def load_pools(): return json.load(open(POOLS_F)) if os.path.exists(POOLS_F) else {}
def save_pools(p): json.dump(p,open(POOLS_F+'.tmp','w')); os.replace(POOLS_F+'.tmp',POOLS_F)
def discover(net,addrs,pools):
    addrs=[a for a in addrs if a.lower() not in pools or pools[a.lower()].get('miss')]
    for i in range(0,len(addrs),30):
        chunk=addrs[i:i+30]
        r=get(f"https://api.geckoterminal.com/api/v2/networks/{net}/tokens/multi/"+",".join(chunk)+"?include=top_pools")
        found=set()
        if r:
            inc={x['id']:x for x in r.get('included',[])}
            for t in r.get('data',[]):
                a=t['attributes']['address'].lower(); found.add(a); tid=t['id']; pl=[]
                for pid in [p['id'] for p in (t['relationships'].get('top_pools') or {}).get('data',[])]:
                    po=inc.get(pid)
                    if not po: continue
                    rel=po.get('relationships',{}); base=((rel.get('base_token') or {}).get('data') or {}).get('id')==tid
                    qid=(((rel.get('quote_token') if base else rel.get('base_token')) or {}).get('data') or {}).get('id','')
                    pl.append({"address":pid.split('_',1)[1],"liq":float(po['attributes'].get('reserve_in_usd') or 0),"created":po['attributes'].get('pool_created_at'),"name":po['attributes'].get('name'),"base":base,"quote":qid.split('_',1)[1] if '_' in qid else qid})
                pools[a]={"network":net,"symbol":t['attributes'].get('symbol'),"fdv":t['attributes'].get('fdv_usd'),"total_supply":t['attributes'].get('total_supply'),"decimals":t['attributes'].get('decimals'),"pools":pl}
        for a in chunk:
            if a.lower() not in found: pools[a.lower()]={"network":net,"pools":[],"miss":True}
        save_pools(pools)
def best_pool(p):
    if not p or not p.get('pools'): return None
    base=[q for q in p['pools'] if q.get('base')]
    return max(base,key=lambda q:q['liq']) if base else None
def fetch_ohlcv(net,pool,agg,target_ts,max_pages=10,existing=None):
    have=set(c[0] for c in (existing or [])); candles=list(existing or []); before=None
    for page in range(max_pages):
        u=f"https://api.geckoterminal.com/api/v2/networks/{net}/pools/{pool}/ohlcv/minute?aggregate={agg}&limit=1000&currency=usd"+(f"&before_timestamp={before}" if before else "")
        r=get(u); o=(((r or {}).get('data') or {}).get('attributes') or {}).get('ohlcv_list') or []
        if not o: break
        candles+=[c for c in o if c[0] not in have]; before=o[-1][0]
        if o[-1][0]<=target_ts or len(o)<1000: break
        if have and o[-1][0]<=min(have): break
    return sorted({c[0]:c for c in candles}.values(),key=lambda c:c[0])
