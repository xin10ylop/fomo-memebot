import json,glob,os,sys,time,statistics as st,collections,urllib.request,random,datetime
# Exact-swap verification of dip reversion: for 1m crash events in RH pools (liq>=100k), fetch swaps [-10min,+60min], rebuild price path from sqrtPrice.
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"}
SWAP_V3="0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"; SWAP_V4="0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
PM="0x8366a39cc670b4001a1121b8f6a443a643e40951"; BPS=9.9
def call(payload,tries=5):
    for i in range(tries):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(payload).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=120))
        except urllib.error.HTTPError as e: time.sleep(5*(i+1) if e.code==429 else 3)
        except Exception: time.sleep(3)
    return None
def s256(x): return x-(1<<256) if x>=(1<<255) else x
def s128(x):
    x&=(1<<128)-1; return x-(1<<128) if x>=(1<<127) else x
pools=json.load(open('gt/pools_v3.json'))
def best_pool(p):
    if not p or not p.get('pools'): return None
    b=[q for q in p['pools'] if q.get('base')]; return max(b,key=lambda q:q['liq']) if b else None
# block<->time anchors
bl={}
for f in glob.glob('rh/blocks/blocks*.json'):
    try: bl.update(json.load(open(f)))
    except: pass
import bisect
pts=sorted((v,int(k,16)) for k,v in bl.items()); ts_=[p[0] for p in pts]; bn_=[p[1] for p in pts]
def block_at(ts):
    i=bisect.bisect_left(ts_,ts)
    if i<=0: return bn_[0]-int((ts_[0]-ts)*BPS)
    if i>=len(ts_): return bn_[-1]+int((ts-ts_[-1])*BPS)
    t0,b0,t1,b1=ts_[i-1],bn_[i-1],ts_[i],bn_[i]
    return int(b0+(b1-b0)*(ts-t0)/(t1-t0)) if t1>t0 else b0
ev=[r for r in json.load(open('crash_reversion_1m.json')) if r['net']=='robinhood' and r['liq']>=100000]
random.seed(3); random.shuffle(ev); ev=ev[:int(sys.argv[1]) if len(sys.argv)>1 else 150]
print("events",len(ev),file=sys.stderr)
res=[]
for e in ev:
    bp=best_pool(pools.get(e['a']))
    if not bp: continue
    b0=block_at(e['t']+60)   # end of crash minute
    frm=b0-int(600*BPS); to=b0+int(3600*BPS)
    if len(bp['address'])==42: flt={"fromBlock":hex(frm),"toBlock":hex(to),"address":bp['address'],"topics":[SWAP_V3]}; kind="v3"
    else: flt={"fromBlock":hex(frm),"toBlock":hex(to),"address":PM,"topics":[SWAP_V4,bp['address']]}; kind="v4"
    r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[flt]}); time.sleep(0.12)
    sw=[]
    for lg in ((r or {}).get('result') or []):
        d=lg['data']
        if len(d)<2+64*3: continue
        sp=int(d[130:194],16); sw.append({"b":int(lg['blockNumber'],16),"i":int(lg['logIndex'],16),"sp":sp})
    sw.sort(key=lambda x:(x['b'],x['i']))
    if len(sw)<10: continue
    # orientation: token price direction unknown; use the crash itself: price should be lower at b0 than 10 min before
    def pr(x,inv): p=(x['sp']/2**96)**2; return 1/p if inv else p
    pre=[x for x in sw if x['b']<=b0-int(300*BPS)]; at0=[x for x in sw if x['b']<=b0]
    if not pre or not at0: continue
    ok=None
    for inv in (True,False):
        if pr(at0[-1],inv)/pr(pre[-1],inv)-1<-0.08: ok=inv; break
    if ok is None: continue   # crash not visible in swaps (candle artifact)
    inv=ok; p0=pr(at0[-1],inv)
    # our entry: first swap after b0+5 blocks (we react ~0.5s later); we pay at the post-swap price
    ent=next((x for x in sw if x['b']>=b0+5),None)
    if not ent: continue
    pe=pr(ent,inv)
    def at(sec):
        tb=b0+int(sec*BPS); c=[x for x in sw if x['b']<=tb]; return pr(c[-1],inv) if c else None
    rec={"a":e['a'],"t":e['t'],"liq":e['liq'],"kind":kind,"n_sw":len(sw),"crash_swaps":pr(at0[-1],inv)/pr(pre[-1],inv)-1,"entry_vs_p0":pe/p0-1}
    for sec in (60,300,900,1800,3600):
        a=at(sec); rec[f"x{sec}"]=(a/pe-1) if a else None
    mn=[pr(x,inv) for x in sw if b0<x['b']<=b0+int(3600*BPS)]; rec["min60"]=(min(mn)/pe-1) if mn else None
    res.append(rec)
json.dump(res,open('crash_swaps.json','w'))
print("verified crash events",len(res),collections.Counter(r['kind'] for r in res))
def rep(rs,label):
    if len(rs)<8: return
    line=f"  {label:30s} n={len(rs):3d} crash(swaps) med={st.median([r['crash_swaps'] for r in rs]):+.3f} entry_vs_p0 med={st.median([r['entry_vs_p0'] for r in rs]):+.3f}"
    for sec in (60,300,900,1800,3600):
        xs=[r[f"x{sec}"] for r in rs if r.get(f"x{sec}") is not None]
        if xs: line+=f" | x{sec}: med={st.median(xs):+.3f} p>0={sum(x>0 for x in xs)/len(xs):.2f}"
    pn=[r["x1800"]-0.02-2*500/(max(r['liq'],1000)/2) for r in rs if r.get("x1800") is not None]
    print(line+f" | net30m med={st.median(pn):+.3f} p>0={sum(x>0 for x in pn)/len(pn):.2f} | min60 med={st.median([r['min60'] for r in rs if r.get('min60') is not None]):+.3f}")
rep(res,"all verified"); rep([r for r in res if r['kind']=='v4'],"v4"); rep([r for r in res if r['kind']=='v3'],"v3")
rep([r for r in res if r['liq']>=500000],"liq>=500k"); rep([r for r in res if r['crash_swaps']<=-0.2],"crash<=-20% (swaps)")
