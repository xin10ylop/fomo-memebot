import json,collections,statistics as st,random
# Who are the first buyers on each launch? Cluster: 'bundle' = wallet that is among the first 5 buyers on >=3 launches of the SAME creator in the window;
# 'sniper bot' = wallet among the first 5 buyers on >=10 launches of DIFFERENT creators; else 'other'.
fb=json.load(open('rh/first_buyers_2026-09-03.json')); rows=json.load(open('/home/user/fomo-memebot/data/derived/creator_seat_2026-09-03.json'))
creates={}
for line in open('rh/creates_v2_2026-09-03.jsonl'):
    import json as _j; b,tx,topics,data=_j.loads(line); creates['0x'+topics[2][-40:].lower()]='0x'+topics[3][-40:].lower()
by_curve=collections.defaultdict(list)
for tx,v in fb.items(): by_curve[v['curve']].append(v['from'])
pair=collections.Counter(); wallet_creators=collections.defaultdict(set); wallet_launches=collections.Counter()
for cv,buyers in by_curve.items():
    cr=creates.get(cv)
    for w in set(buyers): pair[(cr,w)]+=1; wallet_creators[w].add(cr); wallet_launches[w]+=1
bundle={(cr,w) for (cr,w),n in pair.items() if n>=3}
bots={w for w,cs in wallet_creators.items() if len(cs)>=10}
print(f"launches with first-buyer data {len(by_curve)}; distinct first-buyer wallets {len(wallet_launches)}; bundle (creator,wallet) pairs {len(bundle)}; bot wallets (first buyer on >=10 creators' launches) {len(bots)}")
serial=collections.Counter(creates.values())
def cls(w,cr):
    if w==cr: return 'creator'
    if (cr,w) in bundle: return 'bundle'
    if w in bots: return 'bot'
    return 'other'
for label,sel in (('serial >=10/day',lambda cr:serial[cr]>=10),('2-9/day',lambda cr:2<=serial[cr]<10),('one-off',lambda cr:serial[cr]==1)):
    c=collections.Counter(); n=0; launches_with_bundle=0; launches_with_any=0
    for cv,buyers in by_curve.items():
        cr=creates.get(cv)
        if not sel(cr): continue
        launches_with_any+=1; k=[cls(w,cr) for w in buyers]; c.update(k); n+=len(k)
        if 'bundle' in k: launches_with_bundle+=1
    print(f"  {label:16s} launches {launches_with_any:5d} | first-5 buyers by class: "+', '.join(f"{k} {100*v/max(1,n):.0f}%" for k,v in c.most_common())+f" | launches with a bundle wallet among first buyers {100*launches_with_bundle/max(1,launches_with_any):.0f}%")
# top bot wallets: how many launches, how many creators
print('\ntop sniper-bot wallets (launches, creators):',[(w[:10],wallet_launches[w],len(wallet_creators[w])) for w in sorted(bots,key=lambda w:-wallet_launches[w])[:8]])
# per creator: share of their launches where first buyers are their own bundle
top=collections.Counter(creates[cv] for cv in by_curve).most_common(8)
for cr,n in top:
    bw={w for (c2,w) in bundle if c2==cr}; ls=[cv for cv in by_curve if creates[cv]==cr]
    share=sum(1 for cv in ls if any(w in bw for w in by_curve[cv]))/len(ls)
    print(f"  creator {cr[:10]} launches {len(ls):4d} bundle wallets {len(bw):3d} launches with bundle first-buyer {100*share:.0f}%")
json.dump({'bundle':[list(x) for x in bundle],'bots':sorted(bots)},open('rh/bundle_wallets_2026-09-03.json','w'))

# ---- creator expectancy split by who the first buyers are (join with creator_seat rows)
seat={r['curve']:r for r in rows}
def cohort(label,sel):
    g=[]
    for cv,buyers in by_curve.items():
        r=seat.get(cv)
        if not r or not sel(cv,buyers): continue
        g.append(r)
    if len(g)<20: print(f"  {label:52s} n={len(g)} (too few)"); return
    Q=sum(r['q0'] for r in g); F=sum(r['fees'] for r in g); A=sum(r['pnl_realized'] for r in g)
    v=[(r['fees']+r['pnl_realized'])/r['q0'] for r in g if r['q0']>=0.01]
    print(f"  {label:52s} n={len(g):5d} pooled fees+sale {100*(F+A)/Q:+5.0f}% of stake (fees {100*F/Q:+4.0f}, sale {100*A/Q:+4.0f}) | per-launch median {100*st.median(v) if v else 0:+4.0f}% | stake/launch {Q/len(g):.3f}")
print("\n## creator expectancy by first-buyer composition")
cohort('first buyers include a bundle wallet (own cluster)',lambda cv,b:any((creates[cv],w) in bundle for w in b))
cohort('no bundle wallet; first buyers include a sniper bot',lambda cv,b:not any((creates[cv],w) in bundle for w in b) and any(w in bots for w in b))
cohort('no bundle, no known bot (organic/unknown buyers)',lambda cv,b:not any((creates[cv],w) in bundle for w in b) and not any(w in bots for w in b))
cohort('one-off creator, no bundle',lambda cv,b:serial[creates[cv]]==1 and not any((creates[cv],w) in bundle for w in b))
cohort('serial creator, no bundle',lambda cv,b:serial[creates[cv]]>=10 and not any((creates[cv],w) in bundle for w in b))
cohort('serial creator, bundle present',lambda cv,b:serial[creates[cv]]>=10 and any((creates[cv],w) in bundle for w in b))
# launches with no first buyer at all (only the creator traded): their expectancy
solo=[r for cv,r in seat.items() if cv not in by_curve]
if solo:
    Q=sum(r['q0'] for r in solo); print(f"  {'nobody else bought (creator only)':52s} n={len(solo):5d} pooled fees+sale {100*(sum(r['fees'] for r in solo)+sum(r['pnl_realized'] for r in solo))/Q:+5.0f}% of stake")
