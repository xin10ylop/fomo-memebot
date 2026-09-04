import json,urllib.request,time,sys
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
FACTORIES={"0xa5aab3f0c6eeadf30ef1d3eb997108e976351feb":"ponsV1","0xe33e9e479df8802cb0866d5d05258bec4cf62948":"ponsV2","0x22e99278308b393ea1260859b181ad7e78f5eeed":"long","0x7ed598bcef8bd9edd8c97a195c6d13f40801ec7e":"pad_7ed5"}
def call(p,tries=6):
    for i in range(tries):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(p).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=120))
        except Exception as e: time.sleep(3*(i+1))
latest=int(call({"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]})['result'],16)
out={}
for F,name in FACTORIES.items():
    logs=[]; b=8_000_000; step=500_000
    while b<=latest:
        e=min(latest,b+step); r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":hex(b),"toBlock":hex(e),"address":F}]})
        if r is None: break
        if 'error' in r: step=max(2_000,step//2); continue
        logs+=[{"b":int(l['blockNumber'],16),"t0":l['topics'][0],"t1":(l['topics'][1] if len(l['topics'])>1 else None),"t2":(l['topics'][2] if len(l['topics'])>2 else None),"tx":l['transactionHash'],"nd":len(l['data'])} for l in r['result']]
        b=e+1
        if len(r['result'])>5000: step=max(2_000,step//2)
        elif len(r['result'])<800: step=min(4_000_000,step*2)
        time.sleep(0.25)
    out[name]=logs; print(name,len(logs),file=sys.stderr,flush=True); json.dump(out,open('rh/factory_logs.json','w'))
print('DONE',file=sys.stderr)
