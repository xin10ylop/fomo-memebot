import json,glob,os,sys,time,datetime,collections
from gt_common import *
dex=json.load(open('dex/tokens.json'))
def iso(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
need={}
def add(a,ts,chain=None,prio=2,w=1):
    if not a: return
    k=a.lower() if a.startswith('0x') else a
    x=need.setdefault(k,{"chain":chain,"min_ts":ts,"prio":prio,"w":0})
    if chain and not x["chain"]: x["chain"]=chain
    if ts and (x["min_ts"] is None or ts<x["min_ts"]): x["min_ts"]=ts
    x["prio"]=min(x["prio"],prio); x["w"]+=w
for f in glob.glob('fapi/trades/*.json'):
    for t in json.load(open(f)).get('trades',[]):
        a=(t.get('token') or {}).get('address'); add(a, iso(t['createdAt']) if t.get('createdAt') else None, None, 0 if t.get('status')=='closed' else 1)
if os.path.exists('rh_fill_token_demand.json'):
    for a,n in json.load(open('rh_fill_token_demand.json')): add(a,None,'robinhood',0 if n>=3 else 1,n)
for f in glob.glob('rh/logs/*.ledger.json'):
    for r in json.load(open(f)):
        if r.get('side') in ('buy','sell') and r.get('ts'): add(r['token'],r['ts'],'robinhood',1,0)
for f in glob.glob('helius/parsed/*.ledger.json'):
    for r in json.load(open(f)).get('rows',[]):
        if r.get('side')=='buy' and r.get('usd') and r['usd']>=50: add(r['mint'],r['ts'],'solana',1)
for l in open('fapi/ws_alerts.jsonl'):
    try: d=json.loads(l)
    except: continue
    add(d.get('tokenAddress'), (d.get('ts') or 0)/1000 or None, d.get('chain'), 1)
for f in glob.glob('fapi/balances/*.json'):
    for t in json.load(open(f)).get('holdings',[]) or []:
        a=(t.get('token') or {}).get('address'); add(a,None,t.get('chain'),3)
for a,x in need.items():
    ps=(dex.get(a) or {}).get('pairs') or []
    if ps and not x["chain"]: x["chain"]=sorted(ps,key=lambda p:-((p.get('liquidity') or {}).get('usd') or 0))[0]['chainId']
pools=load_pools()
bychain=collections.defaultdict(list)
for a,x in need.items():
    net=NET.get(x["chain"]) or ('robinhood' if a.startswith('0x') else 'solana'); bychain[net].append(a)
print({k:len(v) for k,v in bychain.items()},file=sys.stderr,flush=True)
for net,addrs in bychain.items(): discover(net,addrs,pools)
miss=[a for a,x in need.items() if pools.get(a,{}).get('miss') and a.startswith('0x')]
for net in ['bsc','base']: discover(net,[a for a in miss if pools.get(a,{}).get('miss')],pools)
print("pools known",sum(1 for v in pools.values() if best_pool(v)),"missing",sum(1 for v in pools.values() if not best_pool(v)),file=sys.stderr,flush=True)
now=time.time()
order=sorted(need.items(), key=lambda kv:(kv[1]["prio"], -kv[1]["w"], kv[1]["min_ts"] or now))
for i,(a,x) in enumerate(order):
    p=pools.get(a); bp=best_pool(p)
    if not bp: continue
    of=f"gt/ohlcv/{a}.json"
    if os.path.exists(of):
        try:
            cur=json.load(open(of))
            if (cur.get('pool') or {}).get('address')==bp['address']: continue
        except Exception: pass
    target=(x["min_ts"] or now-30*86400)-86400
    candles=fetch_ohlcv(p['network'],bp['address'],15,target)
    json.dump({"network":p['network'],"pool":bp,"tf":"15m","candles":candles},open(of,"w"))
    if i%25==0: print(i,"/",len(order),a[:10],"candles",len(candles),file=sys.stderr,flush=True)
print("DONE",file=sys.stderr)
