import json,urllib.request,time,os,sys,glob
H="670e21c4-37f4-4b1a-948a-6e0b3fb86047"
MAX_SIGS=5000  # first pass: wallets with <=5000 sigs
credits=0
def get(u,tries=4):
    global credits
    for i in range(tries):
        try:
            req=urllib.request.Request(u,headers={"User-Agent":"curl/8"})
            r=json.load(urllib.request.urlopen(req,timeout=120)); credits+=100; return r
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(10); continue
            print("HTTP",e.code,u[:100],file=sys.stderr); credits+=100; return None
        except Exception as e:
            err=e; time.sleep(5*(i+1))
    print("FAIL",u[:100],err,file=sys.stderr); return None
files=sorted(glob.glob('helius/sigs/*.json'), key=lambda f: len(json.load(open(f))['sigs']))
for f in files:
    d=json.load(open(f)); h=d['handle']; w=d['wallet']; n=len(d['sigs'])
    if n>MAX_SIGS or n==0: continue
    out=f"helius/parsed/{h}.jsonl"
    if os.path.exists(out+".done"): continue
    before=None; got=0
    with open(out,"w") as fo:
        while True:
            u=f"https://api.helius.xyz/v0/addresses/{w}/transactions?api-key={H}&limit=100"+(f"&before={before}" if before else "")
            r=get(u)
            if r is None: break
            for tx in r: fo.write(json.dumps(tx)+"\n")
            got+=len(r)
            if len(r)<100: break
            before=r[-1]['signature']; time.sleep(0.25)
    open(out+".done","w").write(str(got))
    print(h,"sigs",n,"parsed",got,"credits",credits,file=sys.stderr,flush=True)
    if credits>400000: print("CREDIT CAP HIT",file=sys.stderr); break
print("DONE credits",credits,file=sys.stderr)
