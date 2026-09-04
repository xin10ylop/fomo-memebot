import json,collections,statistics as st,os
rows=json.load(open('/home/user/fomo-memebot/data/derived/creator_seat_2026-09-03.json'))
quotes=json.load(open('rh/launch_quotes_2026-09-03.json')) if os.path.exists('rh/launch_quotes_2026-09-03.json') else {}
tm=json.load(open('/home/user/fomo-memebot/data/derived/token_metrics.json'))
bundle=set(); bots=set()
if os.path.exists('rh/bundle_wallets_2026-09-03.json'):
    bw=json.load(open('rh/bundle_wallets_2026-09-03.json')); bundle={tuple(x) for x in bw['bundle']}; bots=set(bw['bots'])
fb=json.load(open('rh/first_buyers_2026-09-03.json')) if os.path.exists('rh/first_buyers_2026-09-03.json') else {}
by_curve=collections.defaultdict(list)
for tx,v in fb.items(): by_curve[v['curve']].append(v['from'])
DEC={'native':18,'0x0bd7d308f8e1639fab988df18a8011f41eacad73':18,'0x5fc5360d0400a0fd4f2af552add042d716f1d168':6,'0xc1a0957594a80aa55a12e76ae4cdf513e84301c7':6}
PX={'native':2445.0,'0x0bd7d308f8e1639fab988df18a8011f41eacad73':2445.0,'0x5fc5360d0400a0fd4f2af552add042d716f1d168':1.0,'0xc1a0957594a80aa55a12e76ae4cdf513e84301c7':1.0}
def usd(units,q):
    # units = raw/1e18 ; convert with the quote's decimals and price
    dec=DEC.get(q,18); px=PX.get(q) or (tm.get(q,{}).get('price') if q in tm else None)
    if px is None: return None
    return units*1e18/10**dec*px
n_priced=0; cls_tot=collections.defaultdict(lambda:{'n':0,'stake':0.0,'fees':0.0,'sale':0.0,'pos':0,'per':[]})
for r in rows:
    q=quotes.get(r['curve'])
    if q is None: continue
    s=usd(r['q0'],q); f=usd(r['fees'],q); a=usd(r['pnl_realized'],q)
    if s is None: continue
    n_priced+=1
    buyers=by_curve.get(r['curve'],[]); has_bundle=any((r['creator'],w) in bundle for w in buyers); has_bot=any(w in bots for w in buyers)
    if r['serial']>=10: c='serial >=10/day'
    elif r['serial']>=2: c='2-9/day'
    else: c='one-off'
    for key in ('ALL',c,('no bundle among first buyers' if not has_bundle else 'own bundle among first buyers'),('one-off & no bundle' if c=='one-off' and not has_bundle else None),('nobody else bought' if not buyers else None)):
        if key is None: continue
        t=cls_tot[key]; t['n']+=1; t['stake']+=s; t['fees']+=f; t['sale']+=a; t['pos']+= (f+a)>0; t['per'].append(f+a)
print(f"launches priced in USD: {n_priced} of {len(rows)} (quotes known {len(quotes)}); first-buyer data for {len(by_curve)} launches")
print(f"{'cohort':30s} {'n':>5s} {'stake/launch $':>14s} {'fees $/launch':>13s} {'sale $/launch':>13s} {'total $ (6h)':>13s} {'per-launch mean $':>17s} {'median $':>9s} {'p90 $':>8s} {'share >$0':>9s}")
for key,t in sorted(cls_tot.items(),key=lambda kv:-kv[1]['n']):
    per=sorted(t['per']); n=t['n']
    print(f"{key:30s} {n:5d} {t['stake']/n:14,.0f} {t['fees']/n:13,.0f} {t['sale']/n:13,.0f} {t['fees']+t['sale']:13,.0f} {(t['fees']+t['sale'])/n:17,.0f} {per[n//2]:9,.0f} {per[9*n//10]:8,.0f} {100*t['pos']/n:8.0f}%")
