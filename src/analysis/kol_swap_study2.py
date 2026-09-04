import json,glob,os,sys,time,bisect,collections,statistics as st,urllib.request,datetime,random
# v2: adds placebo (same pool, 10 min earlier), entry sensitivity, KOL-sell-within-window, impact/cost model, concentration checks.
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"}
SWAP_V3="0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"; SWAP_V4="0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
PM="0x8366a39cc670b4001a1121b8f6a443a643e40951"; BPS=9.9; WETH="0x0bd7d308f8e1639fab988df18a8011f41eacad73"
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
MINF=int(sys.argv[1]) if len(sys.argv)>1 else 20000; MAXEV=int(sys.argv[2]) if len(sys.argv)>2 else 600
ledgers={}
events=[]
for f in glob.glob('rh/logs/*.ledger.json'):
    h=f.split('/')[-1][:-12]; fol=lb.get(h,{}).get('followers') or 0
    rows=json.load(open(f)); ledgers[h]=rows
    if fol<MINF: continue
    for r in rows:
        if r['side']=='buy' and r['amt']>0 and ((r['usd'] or 0)>=1000 or r['usd'] is None):
            events.append({"h":h,"followers":fol,"token":r['token'],"b":r['b'],"amt":r['amt'],"usd":r['usd'],"ts":r['ts'],"mint":r.get('mint')})
random.seed(7); random.shuffle(events)
print("candidate events",len(events),file=sys.stderr)
def swaps(pool_addr,frm,to):
    if len(pool_addr)==42: flt={"fromBlock":hex(frm),"toBlock":hex(to),"address":pool_addr,"topics":[SWAP_V3]}; kind="v3"
    else: flt={"fromBlock":hex(frm),"toBlock":hex(to),"address":PM,"topics":[SWAP_V4,pool_addr]}; kind="v4"
    r=call({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[flt]}); time.sleep(0.12)
    sw=[]
    for lg in ((r or {}).get('result') or []):
        d=lg['data']
        if len(d)<2+64*3: continue
        a0=int(d[2:66],16); a1=int(d[66:130],16); sp=int(d[130:194],16)
        a0,a1=(s256(a0),s256(a1)) if kind=="v3" else (s128(a0),s128(a1))
        sw.append({"b":int(lg['blockNumber'],16),"i":int(lg['logIndex'],16),"a0":a0,"a1":a1,"sp":sp})
    sw.sort(key=lambda x:(x['b'],x['i'])); return sw,kind
def analyze(sw,kind,b0,tok_is_1,kol_idx):
    def price(x):
        p=(x['sp']/2**96)**2; return (1/p) if tok_is_1 else p
    def qin(x):
        q=x['a0'] if tok_is_1 else x['a1']; return q if kind=="v3" else -q
    after=sw[kol_idx+1:]; p_kol=price(sw[kol_idx]); p_pre=price(sw[kol_idx-1]) if kol_idx>0 else p_kol
    out={"impact_kol":p_kol/p_pre-1,"n_after_10m":len(after)}
    for k in (2,10,30):
        ent=next((x for x in after if x['b']>=b0+k),None); pe=price(ent) if ent else p_kol
        out[f"entry{k}_vs_kol"]=pe/p_kol-1
        def at(sec):
            tb=b0+int(sec*BPS); cand=[x for x in sw if x['b']<=tb]; return price(cand[-1]) if cand else None
        for sec in (15,30,60,120,300,600):
            a=at(sec); out[f"e{k}_r{sec}"]=(a/pe-1) if a else None
        tb=b0+int(60*BPS); mx=[price(x) for x in after if x['b']<=tb]; out[f"e{k}_mfe60"]=(max(mx)/pe-1) if mx else None
    def flow(s0,s1):
        bb0=b0+int(s0*BPS); bb1=b0+int(s1*BPS); return sum(qin(x) for x in after if bb0<x['b']<=bb1)/1e18
    out["flow_0_15"]=flow(0,15); out["flow_15_60"]=flow(15,60); out["flow_60_300"]=flow(60,300); out["n_15_60"]=sum(1 for x in after if b0+int(15*BPS)<x['b']<=b0+int(60*BPS))
    return out
out_f='kol_swap_events2.jsonl'; done=set()
if os.path.exists(out_f):
    for l in open(out_f): done.add(json.loads(l)['key'])
n=0
for e in events:
    key=f"{e['h']}|{e['token']}|{e['b']}"
    if key in done: continue
    if n>=MAXEV: break
    bp=best_pool(pools.get(e['token']))
    if not bp: continue
    n+=1
    sw,kind=swaps(bp['address'],e['b']-int(60*BPS),e['b']+int(600*BPS))
    if len(sw)<3: continue
    raw=int(round(e['amt']*1e18)); tok_is_1=None; kol_idx=None
    for idx,x in enumerate(sw):
        if x['b']==e['b']:
            if abs(abs(x['a1'])-raw)<=raw*0.03+1: tok_is_1=True; kol_idx=idx; break
            if abs(abs(x['a0'])-raw)<=raw*0.03+1: tok_is_1=False; kol_idx=idx; break
    if tok_is_1 is None: continue   # only precisely matched KOL swaps
    rec={"key":key,"h":e['h'],"followers":e['followers'],"token":e['token'],"b":e['b'],"ts":e['ts'],"usd":e['usd'],"kind":kind,"liq":bp['liq'],"symbol":pools[e['token']].get('symbol'),
         "age_min":((e['b']-int(e['mint'],16))/BPS/60) if e.get('mint') else None}
    rec.update(analyze(sw,kind,e['b'],tok_is_1,kol_idx))
    # KOL sells same token within 10 min after?
    rec["kol_sell_10m"]=any(r['side']=='sell' and r['token']==e['token'] and e['b']<r['b']<=e['b']+int(600*BPS) for r in ledgers[e['h']])
    # placebo: same pool, window 10 min earlier; pick the swap closest to (b-6000) as pseudo-event
    pb=e['b']-int(600*BPS)
    psw,_=swaps(bp['address'],pb-int(60*BPS),pb+int(600*BPS))
    if len(psw)>=3:
        idxs=[i for i,x in enumerate(psw) if x['b']<=pb]
        if idxs:
            pi=idxs[-1]; pl=analyze(psw,kind,psw[pi]['b'],tok_is_1,pi); rec["placebo"]={k:pl[k] for k in pl if k.startswith('e2_') or k in ('impact_kol','n_after_10m')}
    open(out_f,'a').write(json.dumps(rec)+"\n")
    if n%50==0: print(n,"processed",file=sys.stderr,flush=True)
allr=[json.loads(l) for l in open(out_f)]
print("matched KOL events",len(allr),"leaders",len({r['h'] for r in allr}),"tokens",len({r['token'] for r in allr}),collections.Counter(r['kind'] for r in allr))
def med(xs): return st.median(xs) if xs else None
def rep(rows,label):
    if len(rows)<5: return
    print(f"\n  == {label} (n={len(rows)}) impact_kol med={med([r['impact_kol'] for r in rows]):+.3f} kol_sells_within_10m={sum(r['kol_sell_10m'] for r in rows)/len(rows):.2f} liq med=${med([r['liq'] for r in rows]):,.0f}")
    for k in (2,10,30):
        line=f"     entry N+{k:<2} (vs kol {med([r[f'entry{k}_vs_kol'] for r in rows]):+.3f}):"
        for sec in (15,30,60,120,300,600):
            xs=[r[f"e{k}_r{sec}"] for r in rows if r.get(f"e{k}_r{sec}") is not None]
            if xs: line+=f" r{sec}={st.median(xs):+.3f}({sum(x>0 for x in xs)/len(xs):.2f})"
        m=[r[f"e{k}_mfe60"] for r in rows if r.get(f"e{k}_mfe60") is not None]
        if m: line+=f" mfe60={st.median(m):+.3f}"
        print(line)
    pl=[r['placebo'] for r in rows if r.get('placebo')]
    if pl:
        line="     PLACEBO N+2 :"
        for sec in (15,30,60,120,300,600):
            xs=[p[f"e2_r{sec}"] for p in pl if p.get(f"e2_r{sec}") is not None]
            if xs: line+=f" r{sec}={st.median(xs):+.3f}({sum(x>0 for x in xs)/len(xs):.2f})"
        m=[p["e2_mfe60"] for p in pl if p.get("e2_mfe60") is not None]
        if m: line+=f" mfe60={st.median(m):+.3f}"
        print(line+f"  [n={len(pl)}]")
    # simple net PnL model: enter at N+10, exit at 60s; costs 2% (fees) + impact 2*size/(liq/2) with size $500
    pn=[]
    for r in rows:
        if r.get('e10_r60') is None: continue
        imp=2*500/(max(r['liq'],1000)/2); pn.append(r['e10_r60']-0.02-imp)
    if pn: print(f"     $500 clip, N+10 entry, 60s exit, 2% fees + impact: median net {st.median(pn):+.3f}, mean {st.mean(pn):+.3f}, p>0 {sum(x>0 for x in pn)/len(pn):.2f}, n={len(pn)}")
rep(allr,"ALL matched")
rep([r for r in allr if r['followers']>=200000],"followers>=200k")
rep([r for r in allr if 50000<=r['followers']<200000],"followers 50k-200k")
rep([r for r in allr if r['followers']<50000],"followers<50k")
rep([r for r in allr if (r['usd'] or 0)>=5000],"KOL buy usd>=5k")
rep([r for r in allr if 1000<=(r['usd'] or 0)<5000],"KOL buy usd 1k-5k")
rep([r for r in allr if r['liq']>=200000],"pool liq>=200k")
rep([r for r in allr if r['liq']<200000],"pool liq<200k")
rep([r for r in allr if not r['kol_sell_10m']],"no KOL sell within 10m")
rep([r for r in allr if r['ts'] and r['ts']<datetime.datetime(2026,8,15).timestamp()],"before Aug 15")
rep([r for r in allr if r['ts'] and r['ts']>=datetime.datetime(2026,8,15).timestamp()],"Aug 15 onward")
# concentration
byday=collections.Counter(datetime.datetime.utcfromtimestamp(r['ts']).date().isoformat() for r in allr if r['ts']); print("\nevents by day:",sorted(byday.items()))
bytok=collections.Counter(r['symbol'] for r in allr); print("top tokens:",bytok.most_common(10))
byh=collections.Counter(r['h'] for r in allr); print("top leaders:",byh.most_common(10))
