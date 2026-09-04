import json,urllib.request,time,os,sys,glob,datetime
# 1-minute candles around feed events (tokens in ws_alerts). Pulls last ~1000 minutes per token (one page) + extra pages back to the earliest alert.
pools=json.load(open('gt/pools_multi.json'))
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
        except Exception: last[0]=time.time(); time.sleep(3)
    return None
ev={}
for l in open('fapi/ws_alerts.jsonl'):
    try: d=json.loads(l)
    except: continue
    if d.get('type')!='alert' or not d.get('tokenAddress'): continue
    a=d['tokenAddress'].lower(); ts=d['ts']/1000
    x=ev.setdefault(a,{"min":ts,"max":ts,"n":0}); x["min"]=min(x["min"],ts); x["max"]=max(x["max"],ts); x["n"]+=1
order=sorted(ev.items(),key=lambda kv:-kv[1]["n"])
print("feed tokens",len(order),file=sys.stderr)
for i,(a,x) in enumerate(order):
    p=pools.get(a)
    if not p or not p.get('pools'): continue
    of=f"gt/ohlcv1m/{a}.json"
    prev=json.load(open(of)) if os.path.exists(of) else {"candles":[]}
    have=set(c[0] for c in prev["candles"])
    pool=max(p['pools'],key=lambda q:q['liq'])
    target=x["min"]-3600*3
    candles=list(prev["candles"]); before=None
    for page in range(6):
        u=f"https://api.geckoterminal.com/api/v2/networks/{p['network']}/pools/{pool['address']}/ohlcv/minute?aggregate=1&limit=1000&currency=usd"+(f"&before_timestamp={before}" if before else "")
        r=get(u); o=(((r or {}).get('data') or {}).get('attributes') or {}).get('ohlcv_list') or []
        if not o: break
        candles+=[c for c in o if c[0] not in have]; before=o[-1][0]
        if o[-1][0]<=target or len(o)<1000: break
        if prev["candles"] and o[-1][0]<=min(have): break
    candles=sorted({c[0]:c for c in candles}.values(),key=lambda c:c[0])
    json.dump({"network":p['network'],"pool":pool,"tf":"1m","candles":candles},open(of,"w"))
    if i%20==0: print(i,"/",len(order),a[:10],"n",len(candles),file=sys.stderr,flush=True)
print("DONE",file=sys.stderr)
