import json,urllib.request,time,sys,datetime,os
# tx.from (creator) for every launch of a day, batches of 10
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
DAY=sys.argv[1]
L=[x for x in json.load(open('rh/launches_all.json')) if datetime.datetime.utcfromtimestamp(x['ts']).strftime('%Y-%m-%d')==DAY]
out_f=f'rh/launch_creators_{DAY}.json'; out=json.load(open(out_f)) if os.path.exists(out_f) else {}
todo=[x['tx'] for x in L if x['tx'] not in out]; print('todo',len(todo),file=sys.stderr)
for i in range(0,len(todo),10):
    ch=todo[i:i+10]
    for k in range(6):
        try:
            req=urllib.request.Request(RPC,data=json.dumps([{"jsonrpc":"2.0","id":j,"method":"eth_getTransactionByHash","params":[t]} for j,t in enumerate(ch)]).encode(),headers=H)
            r=json.load(urllib.request.urlopen(req,timeout=60))
            for x in r:
                if x.get('result'): out[ch[x['id']]]=x['result']['from'].lower()
            break
        except Exception as e: time.sleep(3*(k+1))
    if (i//10)%100==0: json.dump(out,open(out_f,'w')); print(i,file=sys.stderr,flush=True)
    time.sleep(0.5)
json.dump(out,open(out_f,'w')); print('DONE',len(out),file=sys.stderr)
