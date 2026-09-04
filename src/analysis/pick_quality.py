import json,glob,os,bisect,datetime,collections,statistics as st,sys,math
# Pick quality per trader: for each BUY/position-open event (trader, token, ts), measure forward path from 15m candles:
#  entry = open of first candle after ts; MFE within 24h/48h (max high / entry - 1); close returns at 1h/4h/24h/48h; hit rate of +50% / +100% within 48h; drawdown.
def load(a):
    f=f'gt/ohlcv/{a}.json'
    if not os.path.exists(f): return None
    d=json.load(open(f)); c=sorted(d['candles'],key=lambda x:x[0])
    if not c: return None
    return {"t":[x[0] for x in c],"o":[x[1] for x in c],"h":[x[2] for x in c],"l":[x[3] for x in c],"c":[x[4] for x in c],"v":[x[5] for x in c]}
def path(o,ts):
    i=bisect.bisect_right(o['t'],ts)
    if i>=len(o['t']) or o['t'][i]-ts>3600: return None
    e=o['o'][i]
    if not e or e<=0: return None
    r={"entry":e,"entry_t":o['t'][i],"lag_s":o['t'][i]-ts}
    for h,lab in ((3600,'1h'),(4*3600,'4h'),(24*3600,'24h'),(48*3600,'48h'),(7*86400,'7d')):
        j=bisect.bisect_right(o['t'],ts+h)-1
        r[f"ret_{lab}"]=(o['c'][j]/e-1) if j>i else None
        if lab in ('24h','48h'):
            r[f"mfe_{lab}"]=(max(o['h'][i:j+1])/e-1) if j>i else None
            r[f"mae_{lab}"]=(min(o['l'][i:j+1])/e-1) if j>i else None
    return r
def iso(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
events=[]
# (1) fomo position opens (createdAt) - all traders
for f in glob.glob('fapi/trades/*.json'):
    h=f.split('/')[-1][:-5]
    for t in json.load(open(f)).get('trades',[]):
        a=(t.get('token') or {}).get('address')
        if a and t.get('createdAt'): events.append({"h":h,"token":a.lower() if a.startswith('0x') else a,"ts":iso(t['createdAt']),"src":"fomo_open","status":t['status']})
# (2) on-chain RH buys (exact) where ledger exists: first buy per token per trader
for f in glob.glob('rh/receipts/*.ledger.json'):
    h=f.split('/')[-1][:-12]; seen=set()
    for r in json.load(open(f)):
        if r['side']=='buy' and r['ts'] and r['token'] not in seen:
            seen.add(r['token']); events.append({"h":h,"token":r['token'],"ts":r['ts'],"src":"rh_buy","usd":r.get('usd')})
print("events",len(events),collections.Counter(e['src'] for e in events))
cache={}; res=[]; miss=collections.Counter()
for e in events:
    k=e['token']
    if k not in cache: cache[k]=load(k) or load(e['token'])
    o=cache[k]
    if not o: miss['no_ohlcv']+=1; continue
    p=path(o,e['ts'])
    if not p: miss['no_candle']+=1; continue
    res.append({**e,**p})
print("priced",len(res),"missing",dict(miss))
json.dump(res,open('pick_quality_events.json','w'))
def summarize(rows):
    out={}
    for lab in ('1h','4h','24h','48h','7d'):
        xs=[r[f"ret_{lab}"] for r in rows if r.get(f"ret_{lab}") is not None]
        if xs: out[lab]={"n":len(xs),"mean":st.mean(xs),"median":st.median(xs),"p_pos":sum(x>0 for x in xs)/len(xs)}
    m=[r["mfe_48h"] for r in rows if r.get("mfe_48h") is not None]
    if m: out["mfe48"]={"n":len(m),"p_ge50":sum(x>=0.5 for x in m)/len(m),"p_ge100":sum(x>=1 for x in m)/len(m),"median":st.median(m)}
    return out
print("\n== ALL fomo_open events ==",json.dumps(summarize([r for r in res if r['src']=='fomo_open']),indent=0)[:800])
print("\n== ALL rh_buy events ==",json.dumps(summarize([r for r in res if r['src']=='rh_buy']),indent=0)[:800])
# per trader
by=collections.defaultdict(list)
for r in res: by[r['h']].append(r)
rows=[]
for h,v in by.items():
    if len(v)<8: continue
    s=summarize(v); rows.append((h,len(v),s.get('24h',{}).get('median'),s.get('24h',{}).get('mean'),s.get('48h',{}).get('p_pos'),s.get('mfe48',{}).get('p_ge50'),s.get('mfe48',{}).get('p_ge100')))
rows.sort(key=lambda r:-(r[5] or 0))
print("\nper-trader (n>=8): handle n med24h mean24h p_pos48h p_mfe50 p_mfe100")
for r in rows[:40]: print(f"  {r[0]:18s} n={r[1]:3d} med24={r[2]:+.3f} mean24={r[3]:+.3f} ppos48={r[4]:.2f} mfe50={r[5]:.2f} mfe100={r[6]:.2f}" if r[2] is not None else r)
