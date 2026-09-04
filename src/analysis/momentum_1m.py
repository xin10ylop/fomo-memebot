import json,glob,os,statistics as st,collections,math
# Intraday momentum/breakout backtest on 1m candles (feed tokens). Signal at minute t (using candles <= t): ret5 = close[t]/close[t-5]-1, vol ratio = vol(last 5)/vol(prev 30 avg*5).
# Entry at open[t+1]; exits at fixed horizons; costs: fee_rt (2% Pons pool both sides) + impact based on pool liq (size $500).
BAD=set(json.load(open('gt/ohlcv1m_bad.json')))
rows=[]
for f in glob.glob('gt/ohlcv1m/*.json'):
    a=f.split('/')[-1][:-5]
    if a in BAD: continue
    d=json.load(open(f)); c=sorted(d['candles'],key=lambda x:x[0]); liq=(d.get('pool') or {}).get('liq') or 0; net=d.get('network')
    if len(c)<120: continue
    t=[x[0] for x in c]; o=[x[1] for x in c]; h=[x[2] for x in c]; l=[x[3] for x in c]; cl=[x[4] for x in c]; v=[x[5] for x in c]
    # require contiguous minutes: skip if gaps > 1 min between consecutive candles for the lookback
    last_sig=-999
    for i in range(35,len(c)-61):
        if t[i]-t[i-5]!=300 or t[i+1]-t[i]!=60: continue
        if i-last_sig<30: continue  # one signal per 30 min per token
        r5=cl[i]/cl[i-5]-1 if cl[i-5] else None
        r30=cl[i]/cl[i-30]-1 if cl[i-30] else None
        v5=sum(v[i-4:i+1]); v30=sum(v[i-34:i-4])/6
        if r5 is None or r30 is None: continue
        e=o[i+1]
        if not e: continue
        rec={"a":a,"net":net,"liq":liq,"t":t[i],"r5":r5,"r30":r30,"vr":(v5/v30) if v30>0 else None,"v5":v5}
        for hh in (5,15,30,60):
            j=i+1+hh
            rec[f"x{hh}"]=(cl[j]/e-1) if j<len(c) and t[j]-t[i+1]<=hh*60+120 else None
        rows.append(rec)
        if r5>0.10 and (rec['vr'] or 0)>2: last_sig=i
print("signal candidates",len(rows),"tokens",len({r['a'] for r in rows}))
def rep(rs,label):
    if len(rs)<10: return
    line=f"  {label:44s} n={len(rs):5d}"
    for hh in (5,15,30,60):
        xs=[r[f"x{hh}"] for r in rs if r.get(f"x{hh}") is not None]
        if xs: line+=f" | x{hh}: med={st.median(xs):+.4f} mean={st.mean(xs):+.4f} p>0={sum(x>0 for x in xs)/len(xs):.2f}"
    print(line)
    # net of costs for 30m exit, $500 clip
    pn=[r["x30"]-0.02-2*500/(max(r['liq'],1000)/2) for r in rs if r.get("x30") is not None]
    if pn: print(f"  {'':44s}   net30 (2% fees+impact $500): med={st.median(pn):+.4f} mean={st.mean(pn):+.4f} p>0={sum(x>0 for x in pn)/len(pn):.2f}")
rep(rows,"baseline (all minutes)")
rep([r for r in rows if r['r5']>0.10 and (r['vr'] or 0)>2],"5m breakout >10% with vol ratio>2")
rep([r for r in rows if r['r5']>0.20 and (r['vr'] or 0)>3],"5m breakout >20% with vol ratio>3")
rep([r for r in rows if r['r5']>0.10 and (r['vr'] or 0)>2 and r['liq']>=100000],"breakout>10%, vr>2, liq>=100k")
rep([r for r in rows if r['r5']<-0.15],"5m crash <-15% (mean reversion?)")
rep([r for r in rows if r['r5']<-0.15 and r['liq']>=100000],"5m crash <-15%, liq>=100k")
rep([r for r in rows if r['r30']>0.30 and r['r5']>0],"30m momentum >30% and 5m up")
rep([r for r in rows if r['r30']>0.30 and r['r5']>0 and r['liq']>=100000],"30m mom>30%, liq>=100k")
rep([r for r in rows if r['net']=='robinhood' and r['r5']>0.10 and (r['vr'] or 0)>2],"RH: breakout>10% vr>2")
rep([r for r in rows if r['net']=='solana' and r['r5']>0.10 and (r['vr'] or 0)>2],"SOL: breakout>10% vr>2")
