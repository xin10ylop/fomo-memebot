import json,urllib.request,time,sys,os
K="fapi_38babbd7079b48aea53b44b32b0a3faf1cd6d4de865b46cb86e3bfb0b3e10c2a"
def get(u):
    req=urllib.request.Request(u,headers={"authorization":f"Bearer {K}","User-Agent":"curl/8"})
    with urllib.request.urlopen(req,timeout=90) as r: return json.load(r), r.headers.get("x-ratelimit-remaining")
while True:
    stamp=time.strftime("%Y%m%dT%H%M",time.gmtime()); snap={"t":int(time.time())}
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
    time.sleep(1800)
