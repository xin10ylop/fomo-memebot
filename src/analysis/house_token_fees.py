import json,datetime,statistics as st,math
# Fee-momentum rule for launchpad ("house") tokens: hold when mean fees over the last `short` days > mean over the last `long` days.
def day(ts): return datetime.datetime.utcfromtimestamp(ts).date()
def load_fees(slug): return {day(t):v for t,v in json.load(open(f'llama/{slug}_dailyFees.json'))['totalDataChart']}
def series_test(name,fees,px,short=7,long=30):
    days=sorted(d for d in px if d in fees); f=[fees[d] for d in days]; p=[px[d] for d in days]
    if len(days)<long+10: print(name,'too short',len(days)); return
    eq=1.0; pos=None; held=0; ent=0; curve=[1.0]
    for i in range(long,len(days)-1):
        s=st.mean(f[i-short+1:i+1])>st.mean(f[i-long+1:i+1])
        if s and not pos: ent+=1
        pos=s; r=p[i+1]/p[i]-1
        if pos: eq*=1+r; held+=1
        curve.append(eq)
    peak=1; mdd=0
    for e in curve: peak=max(peak,e); mdd=min(mdd,e/peak-1)
    pk=p[long]; bdd=0
    for x in p[long:]: pk=max(pk,x); bdd=min(bdd,x/pk-1)
    pairs=[]
    for i in range(long+7,len(days)-7,7):
        fc=st.mean(f[i-6:i+1])/max(1e-9,st.mean(f[i-13:i-6]))-1; pairs.append((fc,p[i+7]/p[i]-1))
    up=[pc for fc,pc in pairs if fc>0]; dn=[pc for fc,pc in pairs if fc<=0]
    print(f"{name}: {days[long]}→{days[-1]} | rule {short}d>{long}d: x{eq:.2f} (maxDD {100*mdd:.0f}%, in market {100*held/(len(days)-long-1):.0f}%, {ent} entries) | buy&hold x{p[-1]/p[long]:.2f} (maxDD {100*bdd:.0f}%) | next week after fee-up weeks {100*st.mean(up) if up else float('nan'):+.1f}% (n={len(up)}) vs fee-down {100*st.mean(dn) if dn else float('nan'):+.1f}% (n={len(dn)})")
if __name__=='__main__':
    cg=json.load(open('prices/pump_cg.json')); series_test('PUMP',load_fees('pump.fun'),{day(t/1000):v for t,v in cg['prices']})
    cg=json.load(open('prices/bonk_cg.json')); series_test('BONK vs letsbonk fees',load_fees('letsbonk.fun'),{day(t/1000):v for t,v in cg['prices']})
    tm=json.load(open('/home/user/fomo-memebot/data/derived/token_metrics.json')); a=[k for k,t in tm.items() if t['symbol']=='PONS' and t['chain']=='robinhood'][0]
    px={}
    for c in sorted(json.load(open(f'gt/ohlcv/{a}.json'))['candles'],key=lambda x:x[0]): px[day(c[0])]=c[4]
    series_test('PONS',load_fees('pons'),px,3,14)
