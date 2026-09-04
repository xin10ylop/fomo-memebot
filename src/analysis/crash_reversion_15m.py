import json,glob,os,statistics as st,collections,datetime
pools=json.load(open('gt/pools_v3.json'))
rows=[]; ntok=0
for f in glob.glob('gt/ohlcv/*.json'):
    a=f.split('/')[-1][:-5]; d=json.load(open(f)); c=sorted(d['candles'],key=lambda x:x[0])
    if len(c)<30: continue
    p=(d.get('pool') or {}); liq=float(p.get('liq') or 0); net=d.get('network'); ntok+=1
    last_t=c[-1][0]
    t=[x[0] for x in c]; o=[x[1] for x in c]; cl=[x[4] for x in c]; v=[x[5] for x in c]
    last_sig=-99
    for i in range(4,len(c)-17):
        if t[i+1]-t[i]!=900 or t[i]-t[i-1]!=900: continue
        if not cl[i-1] or not o[i+1]: continue
        r=cl[i]/cl[i-1]-1
        if r>-0.15 or v[i]<2000: continue
        if i-last_sig<8: continue
        last_sig=i; e=o[i+1]
        rec={"a":a,"net":net,"liq":liq,"t":t[i],"r":r,"v":v[i],"days_to_end":(last_t-t[i])/86400,"prior1h":(cl[i-1]/cl[i-4]-1) if cl[i-4] else None}
        for hh,lab in ((1,'15m'),(4,'1h'),(16,'4h'),(96,'24h')):
            j=i+1+hh; rec[f"x{lab}"]=(cl[j]/e-1) if j<len(c) and t[j]-t[i+1]<=hh*900+900 else None
        j=min(len(c)-1,i+1+16); rec["mae4h"]=min(x[3] for x in c[i+1:j+1])/e-1 if j>i+1 else None
        rows.append(rec)
print("tokens",ntok,"crash events (15m <=-15%, vol>=2k)",len(rows),collections.Counter(r['net'] for r in rows))
def rep(rs,label):
    if len(rs)<10: return
    line=f"  {label:46s} n={len(rs):5d}"
    for lab in ('15m','1h','4h','24h'):
        xs=[r[f"x{lab}"] for r in rs if r.get(f"x{lab}") is not None]
        if xs: line+=f" | {lab}: med={st.median(xs):+.3f} mean={st.mean(xs):+.3f} p>0={sum(x>0 for x in xs)/len(xs):.2f}"
    print(line)
    pn=[r["x1h"]-0.02-2*500/(max(r['liq'],1000)/2) for r in rs if r.get("x1h") is not None]
    m=[r['mae4h'] for r in rs if r.get('mae4h') is not None]
    if pn: print(f"  {'':46s}   net1h ($500,2%+impact): med={st.median(pn):+.3f} mean={st.mean(pn):+.3f} p>0={sum(x>0 for x in pn)/len(pn):.2f} | p(x4h<-30%)={sum(1 for r in rs if (r.get('x4h') or 0)<-0.3)/len(rs):.2f} | mae4h med={st.median(m):+.3f}")
rep(rows,"all crashes")
rep([r for r in rows if r['liq']>=100000],"liq>=100k (current)")
rep([r for r in rows if r['liq']>=100000 and r['days_to_end']>=2],"liq>=100k, event >=2d before series end")
rep([r for r in rows if r['liq']>=100000 and r['days_to_end']<2],"liq>=100k, event <2d before end")
rep([r for r in rows if r['liq']<100000],"liq<100k")
rep([r for r in rows if r['net']=='robinhood' and r['liq']>=100000],"RH liq>=100k")
rep([r for r in rows if r['net']=='solana' and r['liq']>=100000],"SOL liq>=100k")
rep([r for r in rows if r['liq']>=100000 and r['r']<=-0.25],"liq>=100k crash<=-25%")
rep([r for r in rows if r['liq']>=100000 and (r['prior1h'] or 0)>0.2],"liq>=100k, prior 1h up >20% (blowoff)")
rep([r for r in rows if r['liq']>=100000 and (r['prior1h'] or 0)<=0],"liq>=100k, prior 1h flat/down")
rep([r for r in rows if r['liq']>=100000 and r['t']<datetime.datetime(2026,8,15).timestamp()],"liq>=100k before Aug15")
rep([r for r in rows if r['liq']>=100000 and r['t']>=datetime.datetime(2026,8,15).timestamp()],"liq>=100k Aug15+")
print("by token (liq>=100k):",collections.Counter(r['a'][:8] for r in rows if r['liq']>=100000).most_common(6))
json.dump(rows,open('crash_reversion_15m.json','w'))
