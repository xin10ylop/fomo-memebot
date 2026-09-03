import json,glob,os,bisect,datetime,collections,statistics as st,sys
# Load 15m OHLCV per token
def load_ohlcv(a):
    f=f'gt/ohlcv/{a}.json'
    if not os.path.exists(f): return None
    d=json.load(open(f)); c=sorted(d['candles'],key=lambda x:x[0])
    return {"t":[x[0] for x in c],"o":[x[1] for x in c],"h":[x[2] for x in c],"l":[x[3] for x in c],"c":[x[4] for x in c],"v":[x[5] for x in c],"net":d['network']}
def fwd_returns(o,ts,horizons=(900,3600,4*3600,24*3600,72*3600)):
    # entry = open of first candle starting AFTER ts (no lookahead); exit = close of candle covering ts+h
    i=bisect.bisect_right(o['t'],ts)  # first candle with start > ts
    if i>=len(o['t']): return None
    if o['t'][i]-ts>3600: return None  # gap: no candle within an hour after event
    entry=o['o'][i]; out={"entry":entry,"entry_t":o['t'][i]}
    for h in horizons:
        j=bisect.bisect_right(o['t'],ts+h)-1
        if j<=i or j>=len(o['t']): out[f"r_{h}"]=None; continue
        out[f"r_{h}"]=o['c'][j]/entry-1
    # max drawup/drawdown within 24h
    j=bisect.bisect_right(o['t'],ts+86400)-1
    if j>i:
        out["mfe_24h"]=max(o['h'][i:j+1])/entry-1; out["mae_24h"]=min(o['l'][i:j+1])/entry-1
    return out
def iso(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
if __name__=="__main__":
    events=[]
    for f in glob.glob('fapi/trades/*.json'):
        h=f.split('/')[-1][:-5]
        for t in json.load(open(f)).get('trades',[]):
            a=(t.get('token') or {}).get('address')
            if a and t.get('createdAt'): events.append({"h":h,"token":a,"ts":iso(t['createdAt']),"status":t['status'],"realized":t.get('realizedPnlUsd')})
    print("position-open events",len(events))
    res=[]; miss=collections.Counter()
    cache={}
    for e in events:
        if e['token'] not in cache: cache[e['token']]=load_ohlcv(e['token'])
        o=cache[e['token']]
        if not o or not o['t']: miss['no_ohlcv']+=1; continue
        r=fwd_returns(o,e['ts'])
        if not r: miss['no_candle']+=1; continue
        res.append({**e,**r})
    print("events with prices",len(res),"missing",dict(miss))
    for h in (900,3600,14400,86400,259200):
        xs=[r[f"r_{h}"] for r in res if r.get(f"r_{h}") is not None]
        if xs: print(f"h={h:>6}s n={len(xs):4d} mean={st.mean(xs):+.3f} median={st.median(xs):+.3f} p(>0)={sum(x>0 for x in xs)/len(xs):.2f} p(>+50%)={sum(x>0.5 for x in xs)/len(xs):.2f} p(<-50%)={sum(x<-0.5 for x in xs)/len(xs):.2f}")
    json.dump(res,open('event_study_positions.json','w'))
