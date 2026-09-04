import json,glob,os,sys,time,bisect,collections,statistics as st,urllib.request
# Seconds-resolution event study: price path from pool Swap events around leader buys on Robinhood Chain.
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"}
SWAP_V3="0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
SWAP_V4="0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
PM="0x8366a39cc670b4001a1121b8f6a443a643e40951"
BPS=9.9  # blocks per second
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
lb={}
for w in ['24h','7d','30d','all']:
    for t in json.load(open(f'fapi/lb/{w}.json'))['traders']: lb[t['handle']]=t
MINF=int(sys.argv[1]) if len(sys.argv)>1 else 50000; MAXEV=int(sys.argv[2]) if len(sys.argv)>2 else 300
events=[]
for f in glob.glob('rh/logs/*.ledger.json'):
    h=f.split('/')[-1][:-12]; fol=lb.get(h,{}).get('followers') or 0
    if fol<MINF: continue
    for r in json.load(open(f)):
        if r['side']=='buy' and r['amt']>0 and ((r['usd'] or 0)>=1000 or r['usd'] is None):
            events.append({"h":h,"followers":fol,"token":r['token'],"b":r['b'],"amt":r['amt'],"usd":r['usd'],"ts":r['ts'],"mint":r.get('mint')})
events.sort(key=lambda e:-e['b'])  # most recent first
print("candidate events",len(events),"from",len({e['h'] for e in events}),"leaders",file=sys.stderr)
out_f='kol_swap_events.jsonl'; done=set()
if os.path.exists(out_f):
    for l in open(out_f): done.add(json.loads(l)['key'])
res=[]; n=0
for e in events:
    key=f"{e['h']}|{e['token']}|{e['b']}"
    if key in done: continue
    if n>=MAXEV: break
    bp=best_pool(pools.get(e['token']))
    if not bp: continue
    n+=1
    frm=e['b']-int(60*BPS); to=e['b']+int(600*BPS)
    if len(bp['address'])==42: flt={"fromBlock":hex(frm),"toBlock":hex(to),"address":bp['address'],"topics":[SWAP_V3]}; kind="v3"
    else: flt={"fromBlock":hex(frm),"toBlock":hex(to),"address":PM,"topics":[SWAP_V4,bp['address']]}; kind="v4"
    r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[flt]}); time.sleep(0.15)
    logs=(r or {}).get('result') or []
    sw=[]
    for lg in logs:
        d=lg['data']; 
        if len(d)<2+64*3: continue
        a0=int(d[2:66],16); a1=int(d[66:130],16); sp=int(d[130:194],16)
        a0,a1=(s256(a0),s256(a1)) if kind=="v3" else (s128(a0),s128(a1))
        sw.append({"b":int(lg['blockNumber'],16),"i":int(lg['logIndex'],16),"a0":a0,"a1":a1,"sp":sp})
    sw.sort(key=lambda x:(x['b'],x['i']))
    if len(sw)<3: continue
    # orientation: find KOL swap in event block matching token amount
    raw=int(round(e['amt']*1e18)); tok_is_1=None; kol_idx=None
    for idx,x in enumerate(sw):
        if x['b']==e['b']:
            if abs(abs(x['a1'])-raw)<=raw*0.03+1: tok_is_1=True; kol_idx=idx; break
            if abs(abs(x['a0'])-raw)<=raw*0.03+1: tok_is_1=False; kol_idx=idx; break
    if tok_is_1 is None:
        # fallback: address ordering with quote assumed WETH/ETH(v4 native=0x0)
        WETH="0x0bd7d308f8e1639fab988df18a8011f41eacad73"
        tok_is_1 = (e['token']>WETH) if kind=="v3" else True
        # kol swap = last swap at/before event block
        kol_idx=max([i for i,x in enumerate(sw) if x['b']<=e['b']],default=None)
        if kol_idx is None: continue
        orient="assumed"
    else: orient="matched"
    def price(x):
        p=(x['sp']/2**96)**2  # currency1 per currency0
        return (1/p) if tok_is_1 else p   # token price in quote units
    # quote flow sign convention: in v3, positive amount = pool received. For v4 event, amounts are from the swapper's view (negative = paid) -> flip
    def quote_in(x):
        q=x['a0'] if tok_is_1 else x['a1']
        return q if kind=="v3" else -q   # positive = quote paid into pool (buy pressure)
    p_pre=price(sw[kol_idx-1]) if kol_idx>0 else price(sw[kol_idx]); p_kol=price(sw[kol_idx])
    # our entry: first swap strictly after event block+2 (we act at N+2); if none within 30 blocks, use p_kol
    after=[x for x in sw[kol_idx+1:]]
    ent=next((x for x in after if x['b']>=e['b']+2),None)
    p_entry=price(ent) if ent else p_kol
    def at(sec):
        tb=e['b']+int(sec*BPS); cand=[x for x in sw if x['b']<=tb]
        return price(cand[-1]) if cand else None
    def mx(sec):
        tb=e['b']+int(sec*BPS); cand=[price(x) for x in after if x['b']<=tb]
        return max(cand) if cand else None
    def flow(s0,s1):
        b0=e['b']+int(s0*BPS); b1=e['b']+int(s1*BPS)
        return sum(quote_in(x) for x in after if b0<x['b']<=b1)/1e18, sum(1 for x in after if b0<x['b']<=b1)
    rec={"key":key,"h":e['h'],"followers":e['followers'],"token":e['token'],"b":e['b'],"usd":e['usd'],"kind":kind,"orient":orient,"n_swaps_10min":len(after),
         "impact_kol":p_kol/p_pre-1,"entry_vs_kol":p_entry/p_kol-1,
         "r15":(at(15)/p_entry-1) if at(15) else None,"r60":(at(60)/p_entry-1) if at(60) else None,"r300":(at(300)/p_entry-1) if at(300) else None,"r600":(at(600)/p_entry-1) if at(600) else None,
         "mfe60":(mx(60)/p_entry-1) if mx(60) else None,"mfe300":(mx(300)/p_entry-1) if mx(300) else None,
         "flow_0_15":flow(0,15),"flow_15_60":flow(15,60),"flow_60_300":flow(60,300),"age_min":((e['b']-int(e['mint'],16))/BPS/60) if e.get('mint') else None}
    res.append(rec); open(out_f,'a').write(json.dumps(rec)+"\n")
    if n%25==0: print(n,"events done",file=sys.stderr,flush=True)
# report on all accumulated
allr=[json.loads(l) for l in open(out_f)] if os.path.exists(out_f) else []
print("total events with swap paths",len(allr),collections.Counter(r['kind'] for r in allr),collections.Counter(r['orient'] for r in allr))
def rep(rows,label):
    if len(rows)<5: return
    def q(k):
        xs=[r[k] for r in rows if r.get(k) is not None]
        return (len(xs),st.median(xs),st.mean(xs),sum(x>0 for x in xs)/len(xs)) if xs else None
    print(f"  {label:32s} n={len(rows):4d} kol_impact med={st.median([r['impact_kol'] for r in rows]):+.3f} entry_vs_kol med={st.median([r['entry_vs_kol'] for r in rows]):+.3f}")
    for k in ('r15','r60','r300','r600','mfe60','mfe300'):
        v=q(k)
        if v: print(f"      {k:7s} n={v[0]:4d} med={v[1]:+.4f} mean={v[2]:+.4f} p>0={v[3]:.2f}")
    fl=[r['flow_15_60'][0] for r in rows]; print(f"      net quote flow 15-60s: median {st.median(fl):+.4f} (quote units), p>0={sum(x>0 for x in fl)/len(fl):.2f}; swaps in 15-60s median {st.median([r['flow_15_60'][1] for r in rows])}")
rep(allr,"all")
rep([r for r in allr if r['orient']=='matched'],"orientation matched")
rep([r for r in allr if r['followers']>=200000],"followers>=200k")
rep([r for r in allr if (r['usd'] or 0)>=5000],"usd>=5k")
rep([r for r in allr if r['kind']=='v3'],"v3 pools")
rep([r for r in allr if r['kind']=='v4'],"v4 pools")
rep([r for r in allr if r['age_min'] is not None and r['age_min']<=120],"token age<=2h")
