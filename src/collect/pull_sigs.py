import json,urllib.request,time,os,sys
H="670e21c4-37f4-4b1a-948a-6e0b3fb86047"
def rpc(method,params,tries=3):
    for i in range(tries):
        try:
            req=urllib.request.Request(f"https://mainnet.helius-rpc.com/?api-key={H}",data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),headers={"Content-Type":"application/json"})
            return json.load(urllib.request.urlopen(req,timeout=60))
        except Exception as e:
            time.sleep(3*(i+1)); err=e
    print("FAIL",err,file=sys.stderr); return {}
handles={}
for w in ['24h','7d','30d','all']:
    for t in json.load(open(f'fapi/lb/{w}.json'))['traders']:
        if t['wallets'].get('solana'): handles[t['handle']]=t['wallets']['solana']
print("wallets",len(handles),file=sys.stderr)
credits=0
for h,w in handles.items():
    out=f"helius/sigs/{h}.json"
    if os.path.exists(out): continue
    allsigs=[]; before=None
    while True:
        p={"limit":1000}
        if before: p["before"]=before
        r=rpc("getSignaturesForAddress",[w,p]); credits+=1
        sigs=r.get('result',[]); allsigs+=sigs
        if len(sigs)<1000 or len(allsigs)>=30000: break
        before=sigs[-1]['signature']; time.sleep(0.3)
    json.dump({"handle":h,"wallet":w,"sigs":allsigs},open(out,"w"))
    time.sleep(0.3)
print("DONE credits",credits,file=sys.stderr)
