import json,urllib.request,time,glob,bisect,datetime,collections,sys,os
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"; PONS='0x39dbed3a2bd333467115de45665cc57f813c4571'
DEAD='0x000000000000000000000000000000000000dead'; ZERO='0x0000000000000000000000000000000000000000'
def call(p,tries=6):
    for i in range(tries):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(p).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=120))
        except Exception as e: time.sleep(3*(i+1))
blocks={}
for f in glob.glob('rh/blocks/blocks*.json'):
    try: blocks.update(json.load(open(f)))
    except Exception: pass
pts=sorted((int(k,16),v) for k,v in blocks.items()); xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
def bts(b):
    i=bisect.bisect_left(xs,b)
    if i<=0: return ys[0]-(xs[0]-b)/9.9
    if i>=len(xs): return ys[-1]+(b-xs[-1])/9.9
    x0,y0,x1,y1=xs[i-1],ys[i-1],xs[i],ys[i]; return y0+(y1-y0)*(b-x0)/(x1-x0)
latest=int(call({"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]})['result'],16)
mint=int(json.load(open('rh/mints/mints.json'))[PONS],16); print('PONS mint block',mint,'latest',latest,file=sys.stderr)
logs=[]
for topic2 in (DEAD,ZERO):
    b=mint; step=2_000_000
    while b<=latest:
        e=min(latest,b+step)
        r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":hex(b),"toBlock":hex(e),"address":PONS,"topics":[TRANSFER,None,"0x"+topic2[2:].rjust(64,'0')]}]})
        if r is None: print('fail',b,file=sys.stderr); break
        if 'error' in r: step=max(50_000,step//2); print('shrink',step,str(r['error'])[:80],file=sys.stderr); continue
        res=r['result']; logs+=[{"b":int(l['blockNumber'],16),"tx":l['transactionHash'],"from":"0x"+l['topics'][1][-40:],"to":topic2,"amt":int(l['data'],16)/1e18} for l in res]
        b=e+1; time.sleep(0.3)
json.dump(logs,open('rh/pons_burns.json','w'))
print('burn transfers',len(logs),file=sys.stderr)
# daily series
tm=json.load(open('/home/user/fomo-memebot/data/derived/token_metrics.json'))
cs=sorted(json.load(open(f'gt/ohlcv/{PONS}.json'))['candles'],key=lambda x:x[0]); ct=[c[0] for c in cs]
def px(ts):
    i=bisect.bisect_right(ct,ts)-1; return cs[max(0,i)][4]
daily=collections.defaultdict(lambda:{'pons':0,'usd':0,'n':0}); senders=collections.Counter()
for l in logs:
    ts=bts(l['b']); d=datetime.datetime.utcfromtimestamp(ts).date(); daily[d]['pons']+=l['amt']; daily[d]['usd']+=l['amt']*px(ts); daily[d]['n']+=1; senders[l['from']]+=l['amt']
fees={datetime.datetime.utcfromtimestamp(t).date():v for t,v in json.load(open('llama/pons_dailyRevenue.json'))['totalDataChart']}
print('top burn senders (PONS):',[(s[:10],round(v/1e6,1)) for s,v in senders.most_common(5)])
print('date   burned_PONS  burn_USD  protocol_rev  burn/rev  n')
tot_u=tot_r=0
for d in sorted(daily):
    v=daily[d]; r=fees.get(d,0); tot_u+=v['usd']; tot_r+=r
    print(f"{d} {v['pons']/1e6:10.2f}M ${v['usd']:>10,.0f} ${r:>10,.0f} {100*v['usd']/r if r else 0:6.0f}% {v['n']}")
print(f"TOTAL burned USD ${tot_u:,.0f} vs protocol revenue ${tot_r:,.0f} -> {100*tot_u/tot_r:.0f}% ; total PONS burned {sum(v['pons'] for v in daily.values())/1e6:.1f}M")
