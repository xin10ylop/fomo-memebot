import json,urllib.request,time,sys,os
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def call(p):
    for i in range(8):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(p).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=120))
        except Exception as e: time.sleep(3*(i+1))
rows=json.load(open('/home/user/fomo-memebot/data/derived/creator_seat_2026-09-03.json')); creates={}; tok_of={}
for line in open('rh/creates_v2_2026-09-03.jsonl'):
    b,tx,topics,data=json.loads(line); cv='0x'+topics[2][-40:].lower(); creates[cv]=tx; tok_of[cv]='0x'+topics[1][-40:].lower()
out_f='rh/launch_quotes_2026-09-03.json'; out=json.load(open(out_f)) if os.path.exists(out_f) else {}
todo=[r['curve'] for r in rows if r['curve'] not in out]; print('todo',len(todo),file=sys.stderr,flush=True)
for i in range(0,len(todo),10):
    ch=todo[i:i+10]; r=call([{"jsonrpc":"2.0","id":j,"method":"eth_getTransactionReceipt","params":[creates[c]]} for j,c in enumerate(ch)])
    for x in (r or []):
        rc=x.get('result') or {}; cv=ch[x['id']]; quote='native'
        for l in rc.get('logs',[]):
            a=l['address'].lower()
            if l['topics'][0]==TRANSFER and len(l['topics'])>2 and ('0x'+l['topics'][2][-40:]).lower()==cv and a!=tok_of[cv]: quote=a; break
        out[cv]=quote
    if (i//10)%50==0: json.dump(out,open(out_f,'w')); print(i,file=sys.stderr,flush=True)
    time.sleep(0.15)
json.dump(out,open(out_f,'w')); print('DONE',len(out),file=sys.stderr)
