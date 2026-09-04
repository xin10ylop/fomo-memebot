import json,glob,os,bisect,datetime,statistics as st,collections,time
# H3: buy tokens that are still trading 48h after pool creation (survivors), hold 1d/3d/7d. Universe = tokens with 15m candles (leaderboard-touched tokens).
pools=json.load(open('gt/pools_v3.json'))
def iso(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
rows=[]
for f in glob.glob('gt/ohlcv/*.json'):
    a=f.split('/')[-1][:-5]; d=json.load(open(f)); c=sorted(d['candles'],key=lambda x:x[0])
    if len(c)<8: continue
    created=d.get('pool',{}).get('created')
    if not created: continue
    t0=iso(created); t=[x[0] for x in c]
    # survivor check at 48h: candles exist in [t0+36h, t0+48h] with volume
    i48=bisect.bisect_right(t,t0+48*3600)
    win=[x for x in c[:i48] if x[0]>=t0+36*3600]
    if not win: continue
    vol12=sum(x[5] for x in win)
    if vol12<5000: continue
    if i48>=len(c): continue
    entry=c[i48][1]; e_t=c[i48][0]
    if not entry: continue
    rec={"token":a,"net":d.get('network'),"vol12h_before":vol12,"entry_t":e_t,"entry":entry}
    for hh,lab in ((24,'1d'),(72,'3d'),(168,'7d')):
        j=bisect.bisect_right(t,e_t+hh*3600)-1
        rec[f"r_{lab}"]=(c[j][4]/entry-1) if j>i48 and c[j][0]>=e_t+hh*3600-1800 else None
    j=bisect.bisect_right(t,e_t+7*86400)-1
    rec["mfe_7d"]=max(x[2] for x in c[i48:j+1])/entry-1 if j>i48 else None
    # momentum filter: price at 48h vs price at 24h
    i24=bisect.bisect_right(t,t0+24*3600)-1
    rec["mom_24_48"]=(entry/c[i24][4]-1) if i24>=0 and c[i24][4] else None
    rows.append(rec)
print("survivor entries",len(rows),collections.Counter(r['net'] for r in rows))
def rep(rs,label):
    if len(rs)<5: return
    print(f"  {label:34s} n={len(rs)}")
    for lab in ('1d','3d','7d'):
        xs=[r[f"r_{lab}"] for r in rs if r.get(f"r_{lab}") is not None]
        if xs: print(f"     {lab}: n={len(xs)} med={st.median(xs):+.3f} mean={st.mean(xs):+.3f} p>0={sum(x>0 for x in xs)/len(xs):.2f} p>+50%={sum(x>0.5 for x in xs)/len(xs):.2f} p<-50%={sum(x<-0.5 for x in xs)/len(xs):.2f}")
    m=[r['mfe_7d'] for r in rs if r.get('mfe_7d') is not None]
    if m: print(f"     mfe7d: med={st.median(m):+.3f} p>=+100%={sum(x>=1 for x in m)/len(m):.2f}")
rep(rows,"all survivors")
rep([r for r in rows if r['net']=='robinhood'],"robinhood")
rep([r for r in rows if r['net']=='solana'],"solana")
rep([r for r in rows if r.get('mom_24_48') is not None and r['mom_24_48']>0],"momentum 24h->48h positive")
rep([r for r in rows if r.get('mom_24_48') is not None and r['mom_24_48']<=0],"momentum 24h->48h negative")
rep([r for r in rows if r['vol12h_before']>=100000],"vol(36-48h)>=100k")
json.dump(rows,open('survivor_test.json','w'))
