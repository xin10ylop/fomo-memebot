import json,urllib.request,time,sys,os
K="fapi_38babbd7079b48aea53b44b32b0a3faf1cd6d4de865b46cb86e3bfb0b3e10c2a"
def get(u):
    req=urllib.request.Request(u,headers={"authorization":f"Bearer {K}","User-Agent":"curl/8"})
    with urllib.request.urlopen(req,timeout=90) as r: return json.load(r), r.headers.get("x-ratelimit-remaining")
last_trades=0
while True:
    stamp=time.strftime("%Y%m%dT%H%M",time.gmtime()); snap={"t":int(time.time())}; rem=None
    for w in ['24h','7d','30d','all']:
        try: snap[f"lb_{w}"],rem=get(f"https://api.fomoapi.io/v2/leaderboard/{w}?limit=100")
        except Exception as e: print(stamp,"lb",w,e,file=sys.stderr)
        time.sleep(1.5)
    for b in ['trending','most-held','graduated']:
        try: snap[f"tok_{b}"],rem=get(f"https://api.fomoapi.io/v2/leaderboard/tokens/{b}?limit=100")
        except Exception as e: print(stamp,"tok",b,e,file=sys.stderr)
        time.sleep(1.5)
    json.dump(snap,open(f"fapi/snapshots/{stamp}.json","w"))
    print(stamp,"saved remaining",rem,file=sys.stderr,flush=True)
    # every 6h: re-pull trades for all leaderboard handles (accumulates closed-trade history)
    if time.time()-last_trades>6*3600:
        handles=[]
        for w in ['24h','7d','30d','all']:
            for t in (snap.get(f"lb_{w}") or {}).get('traders',[]):
                if t['handle'] not in handles: handles.append(t['handle'])
        for f in os.listdir('fapi/trades'):
            h=f[:-5]
            if h not in handles: handles.append(h)
        os.makedirs(f"fapi/trades_hist/{stamp}",exist_ok=True)
        for h in handles:
            try:
                d,rem=get(f"https://api.fomoapi.io/v2/users/{h}/trades?limit=2000"); json.dump(d,open(f"fapi/trades_hist/{stamp}/{h}.json","w"))
            except Exception as e: print(stamp,"trades",h,e,file=sys.stderr)
            time.sleep(1.6)
        last_trades=time.time(); print(stamp,"trades re-pulled",len(handles),"remaining",rem,file=sys.stderr,flush=True)
    time.sleep(1800)
