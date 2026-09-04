import json,os,sys,time,collections
from gt_common import *
pools=load_pools(); ev={}
for l in open('fapi/ws_alerts.jsonl'):
    try: d=json.loads(l)
    except: continue
    if d.get('type')!='alert' or not d.get('tokenAddress'): continue
    a=d['tokenAddress'].lower(); ts=d['ts']/1000
    x=ev.setdefault(a,{"min":ts,"max":ts,"n":0,"chain":d.get('chain')}); x["min"]=min(x["min"],ts); x["max"]=max(x["max"],ts); x["n"]+=1
bychain=collections.defaultdict(list)
for a,x in ev.items():
    if a not in pools or pools[a].get('miss'): bychain[NET.get(x['chain']) or ('robinhood' if a.startswith('0x') else 'solana')].append(a)
for net,addrs in bychain.items(): discover(net,addrs,pools)
order=sorted(ev.items(),key=lambda kv:-kv[1]["n"]); print("feed tokens",len(order),file=sys.stderr,flush=True)
for i,(a,x) in enumerate(order):
    p=pools.get(a); bp=best_pool(p)
    if not bp: continue
    of=f"gt/ohlcv1m/{a}.json"; existing=None
    if os.path.exists(of):
        cur=json.load(open(of))
        if (cur.get('pool') or {}).get('address')==bp['address']:
            existing=cur['candles']
            if existing and max(c[0] for c in existing)>=x["max"]-120 and min(c[0] for c in existing)<=x["min"]-3600: continue
    candles=fetch_ohlcv(p['network'],bp['address'],1,x["min"]-3*3600,max_pages=6,existing=existing)
    json.dump({"network":p['network'],"pool":bp,"tf":"1m","candles":candles},open(of,"w"))
    if i%20==0: print(i,"/",len(order),a[:10],"n",len(candles),file=sys.stderr,flush=True)
print("DONE",file=sys.stderr)
