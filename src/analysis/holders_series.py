import json,glob,collections
ser=collections.defaultdict(list)
for f in sorted(glob.glob('fapi/snapshots/*.json')):
    try: d=json.load(open(f))
    except Exception: continue
    t=d.get('t')
    for board in ('tok_trending','tok_most-held','tok_graduated'):
        b=d.get(board) or {}; toks=b.get('tokens') if isinstance(b,dict) else b
        for x in toks or []:
            tk=x.get('token') or {}; a=(tk.get('address') or tk.get('mint') or '') 
            a=a.lower() if a.startswith('0x') else a
            if not a: continue
            ser[a].append({"t":t,"board":board,"holders":x.get('holders'),"fomoBuyers":x.get('fomoBuyers'),"mcap":x.get('marketCapUsd'),"vol24":x.get('volume24hUsd'),"symbol":tk.get('symbol'),"network":x.get('network')})
out={}
for a,xs in ser.items():
    xs.sort(key=lambda r:(r['t'] or ''))
    hs=[r['holders'] for r in xs if isinstance(r.get('holders'),(int,float))]
    out[a]={"symbol":xs[-1]['symbol'],"network":xs[-1]['network'],"n_snapshots":len(xs),"first_seen":xs[0]['t'],"last_seen":xs[-1]['t'],"holders_first":hs[0] if hs else None,"holders_last":hs[-1] if hs else None,"holders_max":max(hs) if hs else None,"fomoBuyers_last":xs[-1].get('fomoBuyers'),"mcap_last":xs[-1].get('mcap'),"series":[(r['t'],r['holders'],r['fomoBuyers'],r['mcap']) for r in xs]}
json.dump(out,open('fapi/holders_series.json','w'))
print('tokens with board history',len(out)); import itertools
for a,v in sorted(out.items(),key=lambda kv:-(kv[1]['holders_last'] or 0))[:10]: print(v['symbol'],v['network'],v['n_snapshots'],v['holders_first'],v['holders_last'],v['fomoBuyers_last'],v['mcap_last'])
