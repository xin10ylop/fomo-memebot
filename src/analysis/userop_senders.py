import json,urllib.request,time,os
# tokens whose mint tx went through the ERC-4337 EntryPoint: the real creator is the userOp sender (smart account = fomo EVM wallet)
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
EP="0x0000000071727de22e5e9d8baf0edac6f37da032"; UOP="0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"
c=json.load(open('rh/creators/creators.json')); out_f='rh/creators/userop_senders.json'; out=json.load(open(out_f)) if os.path.exists(out_f) else {}
todo=[(a,v['mint_tx']) for a,v in c.items() if (v.get('factory') or '').lower()==EP and v.get('mint_tx') and a not in out]
for i in range(0,len(todo),8):
    ch=todo[i:i+8]
    req=urllib.request.Request(RPC,data=json.dumps([{"jsonrpc":"2.0","id":j,"method":"eth_getTransactionReceipt","params":[tx]} for j,(a,tx) in enumerate(ch)]).encode(),headers=H)
    try: r=json.load(urllib.request.urlopen(req,timeout=120))
    except Exception as e: print('err',e); time.sleep(5); continue
    for x in r:
        rec=x.get('result') or {}; a=ch[x['id']][0]; senders=[]
        for l in rec.get('logs',[]):
            if l.get('address','').lower()==EP and l.get('topics') and l['topics'][0]==UOP and len(l['topics'])>2: senders.append('0x'+l['topics'][2][-40:])
        out[a]={"senders":senders,"n_logs":len(rec.get('logs',[]))}
    time.sleep(1.0)
json.dump(out,open(out_f,'w')); print('userop tokens',len(out), sum(1 for v in out.values() if v['senders']))
