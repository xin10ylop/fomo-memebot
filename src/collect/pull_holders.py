import json,urllib.request,time,os,sys
K="fapi_38babbd7079b48aea53b44b32b0a3faf1cd6d4de865b46cb86e3bfb0b3e10c2a"
rows=json.load(open('/home/user/fomo-memebot/data/derived/memes_traded.json'))
memes=[r for r in rows if r.get('category')=='meme' and not r.get('anomaly')][:160]
def get(u):
    req=urllib.request.Request(u,headers={"authorization":f"Bearer {K}","User-Agent":"curl/8"})
    with urllib.request.urlopen(req,timeout=60) as r: return json.load(r), r.headers.get("x-ratelimit-remaining")
rem=None
for i,r in enumerate(memes):
    out=f"fapi/holders/{r['address']}.json"
    if os.path.exists(out): continue
    try:
        d,rem=get(f"https://api.fomoapi.io/token/{r['address']}/holders?limit=100"); json.dump(d,open(out,'w'))
    except Exception as e: print("err",r['symbol'],e,file=sys.stderr)
    time.sleep(1.3)
print("DONE remaining",rem,file=sys.stderr)
