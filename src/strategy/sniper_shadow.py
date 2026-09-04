import json,urllib.request,time,datetime,os,sys,collections
# Live shadow test of the first-block sniper rule (no capital): watch Pons V2 creations, and 20 s later reconstruct what buying 3% of supply (<= $300)
# at the first non-creator price and selling 7 s later into the subsequent buyers would have returned (exact curve exits, 1%+1% fees).
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
V2F="0xe33e9e479df8802cb0866d5d05258bec4cf62948"; BUY="0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL="0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"; ETH_USD=2445.0
LOG='paper/sniper_shadow.jsonl'
def call(p):
    for i in range(6):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(p).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=60))
        except Exception as e: time.sleep(2*(i+1))
def lifo_value(stack,tk):
    out=0.0; need=tk
    for tokens,quote in reversed(stack):
        if need<=0: break
        take=min(tokens,need); out+=quote*take/tokens; need-=take
    return out*0.99
seen_creators=collections.Counter(); pending=[]; last=int(call({"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]})['result'],16)
day=datetime.datetime.utcnow().date()
while True:
    try:
        head=int(call({"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]})['result'],16)
        if datetime.datetime.utcnow().date()!=day: seen_creators=collections.Counter(); day=datetime.datetime.utcnow().date()
        if head>last:
            r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":hex(last+1),"toBlock":hex(head),"address":V2F}]})
            for l in (r or {}).get('result',[]):
                if len(l['topics'])<4: continue
                d=l['data'][2:]; w=[int(d[i:i+64],16) for i in range(0,len(d),64)]
                creator='0x'+l['topics'][3][-40:].lower(); cv='0x'+l['topics'][2][-40:].lower(); tok='0x'+l['topics'][1][-40:].lower()
                prior=seen_creators[creator]; seen_creators[creator]+=1
                pending.append({'b':int(l['blockNumber'],16),'t':time.time(),'curve':cv,'token':tok,'creator':creator,'prior':prior,'q0':w[1]/1e18,'tk0':w[2]/1e18,'ctx':l['transactionHash']})
            last=head
        # evaluate launches older than 25 s
        now=time.time(); ready=[p for p in pending if now-p['t']>25]; pending=[p for p in pending if now-p['t']<=25]
        for p in ready:
            r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":hex(p['b']),"toBlock":hex(p['b']+400),"address":p['curve'],"topics":[[BUY,SELL]]}]})
            logs=sorted((r or {}).get('result',[]),key=lambda l:(int(l['blockNumber'],16),int(l['logIndex'],16)))
            # quote asset: ERC-20 transferred into the curve in the creation tx, else native
            rc=(call({"jsonrpc":"2.0","id":1,"method":"eth_getTransactionReceipt","params":[p['ctx']]}) or {}).get('result') or {}
            quote='native'
            for l in rc.get('logs',[]):
                if l['topics'][0]==TRANSFER and len(l['topics'])>2 and ('0x'+l['topics'][2][-40:]).lower()==p['curve'] and l['address'].lower()!=p['token']: quote=l['address'].lower(); break
            ev=[]
            for l in logs:
                d=l['data'][2:]; w=[int(d[i:i+64],16) for i in range(0,len(d),64)]; buy=l['topics'][0]==BUY
                ev.append({'b':int(l['blockNumber'],16),'buy':buy,'q':(w[0] if buy else w[1])/1e18,'tk':(w[1] if buy else w[0])/1e18})
            rec={'t':p['t'],'curve':p['curve'],'creator':p['creator'],'prior':p['prior'],'quote':quote,'n_events':len(ev),'eligible':p['prior']==0 and quote=='native'}
            first=[e for e in ev[1:] if e['buy']]
            if first and (first[0]['b']-p['b'])/9.9<=3.0 and quote=='native':
                p_in=first[0]['q']/first[0]['tk']; tk_bot=min(0.03e9,300.0/(p_in*ETH_USD)); cost=tk_bot*p_in*1.01
                stack=[[p['tk0'],p['q0']],[tk_bot,tk_bot*p_in]]; out=None; b_in=first[0]['b']
                for e in ev[1:]:
                    if e['b']<=b_in: continue
                    if e['buy']: stack.append([e['tk'],e['q']])
                    else:
                        need=e['tk']
                        while need>1e-12 and stack:
                            tokens,quote_=stack[-1]; take=min(tokens,need)
                            if take>=tokens-1e-12: stack.pop()
                            else: stack[-1]=[tokens-take,quote_*(tokens-take)/tokens]
                            need-=take
                    if (e['b']-b_in)/9.9>=7.0: out=lifo_value(stack,tk_bot); break
                if out is None: out=lifo_value(stack,tk_bot)
                rec.update({'entry_s':(b_in-p['b'])/9.9,'cost_usd':cost*ETH_USD,'exit_usd':out*ETH_USD,'pnl_usd':(out-cost)*ETH_USD,'roi':out/cost-1})
            open(LOG,'a').write(json.dumps(rec)+'\n')
        time.sleep(2)
    except Exception as e:
        open(LOG,'a').write(json.dumps({'t':time.time(),'error':str(e)[:200]})+'\n'); time.sleep(5)
