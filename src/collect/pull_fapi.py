import json, urllib.request, time, os, sys, glob
K="fapi_38babbd7079b48aea53b44b32b0a3faf1cd6d4de865b46cb86e3bfb0b3e10c2a"
def get(u, tries=4):
    for i in range(tries):
        try:
            req=urllib.request.Request(u, headers={"authorization":f"Bearer {K}","User-Agent":"curl/8"})
            with urllib.request.urlopen(req, timeout=90) as r:
                rem=r.headers.get("x-ratelimit-remaining"); return json.load(r), rem
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(20); continue
            print("HTTP",e.code,u,file=sys.stderr); return None, None
        except Exception as e:
            print("ERR",u,e,file=sys.stderr); time.sleep(5*(i+1))
    return None, None
handles=[]
for w in ['24h','7d','30d','all']:
    for t in json.load(open(f'fapi/lb/{w}.json'))['traders']:
        if t['handle'] not in handles: handles.append(t['handle'])
print("handles",len(handles),file=sys.stderr)
rem=None
for i,h in enumerate(handles):
    for kind,path in [("trades",f"/v2/users/{h}/trades?limit=100"),("balances",f"/v2/users/{h}/balances")]:
        out=f"fapi/{kind}/{h}.json"
        if os.path.exists(out): continue
        d,rem=get("https://api.fomoapi.io"+path)
        if d is not None: json.dump(d,open(out,"w"))
        time.sleep(1.6)
    if i%10==0: print(i,h,"remaining",rem,file=sys.stderr,flush=True)
print("DONE remaining",rem,file=sys.stderr)
