import json,urllib.request,time,os,sys
RPC="https://rpc.mainnet.chain.robinhood.com"
TOPIC="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def rpc(m,p,tries=4):
    for i in range(tries):
        try:
            req=urllib.request.Request(RPC,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"})
            r=json.load(urllib.request.urlopen(req,timeout=180))
            if "error" in r: raise Exception(str(r["error"])[:200])
            return r["result"]
        except Exception as e:
            err=e; time.sleep(3*(i+1))
    print("FAIL",m,str(err)[:150],file=sys.stderr); return None
bn=int(rpc("eth_blockNumber",[]),16); print("head",bn,file=sys.stderr)
wallets={}
for w in ['24h','7d','30d','all']:
    for t in json.load(open(f'fapi/lb/{w}.json'))['traders']:
        e=t['wallets'].get('evm')
        if e: wallets[t['handle']]=e.lower()
print("evm wallets",len(wallets),file=sys.stderr)
def getlogs_all(topics):
    # split range if too many logs / error
    out=[]; stack=[(0,bn)]
    while stack:
        a,b=stack.pop()
        r=rpc("eth_getLogs",[{"fromBlock":hex(a),"toBlock":hex(b),"topics":topics}])
        if r is None:
            if b-a<1000: continue
            m=(a+b)//2; stack+=[(a,m),(m+1,b)]; continue
        out+=r
    return out
for i,(h,e) in enumerate(wallets.items()):
    out=f"rh/logs/{h}.json"
    if os.path.exists(out): continue
    pad="0x"+e[2:].rjust(64,"0")
    inc=getlogs_all([TOPIC,None,pad]); outg=getlogs_all([TOPIC,pad])
    json.dump({"handle":h,"wallet":e,"head":bn,"in":inc,"out":outg},open(out,"w"))
    print(i,h,"in",len(inc),"out",len(outg),file=sys.stderr,flush=True)
    time.sleep(0.2)
print("DONE",file=sys.stderr)
