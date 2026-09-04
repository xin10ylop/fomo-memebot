import json,urllib.request,time,os,sys
K="fapi_38babbd7079b48aea53b44b32b0a3faf1cd6d4de865b46cb86e3bfb0b3e10c2a"
tm=json.load(open('/home/user/fomo-memebot/data/derived/token_metrics.json'))
memes=sorted([t for t in tm.values() if t.get('category')=='meme'],key=lambda t:-t['traders'])[:200]
NET={'robinhood':'robinhood','solana':'sol','bsc':'bnb','base':'base','eth':'eth'}
os.makedirs('fapi/theses',exist_ok=True)
def get(u):
    req=urllib.request.Request(u,headers={"authorization":f"Bearer {K}","User-Agent":"curl/8"})
    with urllib.request.urlopen(req,timeout=60) as r: return json.load(r), r.headers.get("x-ratelimit-remaining")
rem=None
for t in memes:
    out=f"fapi/theses/{t['address']}.json"
    if os.path.exists(out): continue
    net=NET.get(t['chain'])
    try:
        d,rem=get(f"https://api.fomoapi.io/v2/thesis/token/{t['address']}?limit=100"+(f"&network={net}" if net else "")); json.dump(d,open(out,'w'))
    except Exception as e: print("err",t['symbol'],e,file=sys.stderr)
    time.sleep(1.2)
print("DONE remaining",rem,file=sys.stderr)
