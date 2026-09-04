import json,urllib.request,time,os,sys,glob
# For every Robinhood token with leaderboard fills: mint tx -> deployer (tx.from), and Pons locker feeRedirects(token) -> creator fee recipient.
RPC="https://rpc.mainnet.chain.robinhood.com"; H={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) curl/8"}
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
LOCKERS=["0x736d76699c26d0d966744cae304c000d471f7f35","0x31ca5e101941a93a7dd6d0497928700625cf54b5"]
SEL_FEE="0x"+"e5b3a4d5"  # placeholder replaced below by keccak of feeRedirects(address)
def call(payload,tries=5):
    for i in range(tries):
        try:
            req=urllib.request.Request(RPC,data=json.dumps(payload).encode(),headers=H); return json.load(urllib.request.urlopen(req,timeout=120))
        except urllib.error.HTTPError as e: time.sleep(4*(i+1) if e.code==429 else 3)
        except Exception: time.sleep(3)
    return None
from eth_utils import keccak
SEL_FEE="0x"+keccak(text="feeRedirects(address)").hex()[:8]
toks=set()
for f in glob.glob('rh/logs/*.ledger.json'):
    for r in json.load(open(f)):
        if r['side'] in ('buy','sell'): toks.add(r['token'])
mints=json.load(open('rh/mints/mints.json'))
toks=sorted(toks); out_f='rh/creators/creators.json'; out=json.load(open(out_f)) if os.path.exists(out_f) else {}
tm=json.load(open('/home/user/fomo-memebot/data/derived/token_metrics.json'))
todo=sorted([t for t in toks if t not in out],key=lambda a:-(tm.get(a,{}).get('traders') or 0)); print("tokens",len(toks),"todo",len(todo),file=sys.stderr,flush=True)
for i in range(0,len(todo),10):
    chunk=todo[i:i+10]
    r=call([{"jsonrpc":"2.0","id":j,"method":"eth_getLogs","params":[{"fromBlock":(hex(mints[a]) if isinstance(mints.get(a),int) else (mints.get(a) or "0x0")),"toBlock":(hex(mints[a]) if isinstance(mints.get(a),int) else (mints.get(a) or "latest")),"address":a,"topics":[TRANSFER,"0x"+"0"*64]}]} for j,a in enumerate(chunk)])
    minttx={}
    if r:
        for x in r:
            res=x.get('result')
            if res: minttx[chunk[x['id']]]={"tx":res[0]['transactionHash'],"block":res[0]['blockNumber'],"to":"0x"+res[0]['topics'][2][-40:]}
    time.sleep(1.0)
    txs=[v['tx'] for v in minttx.values()]
    r2=call([{"jsonrpc":"2.0","id":j,"method":"eth_getTransactionByHash","params":[t]} for j,t in enumerate(txs)]) if txs else []
    frm={}
    for x in (r2 or []):
        if x.get('result'): frm[txs[x['id']]]={"from":(x['result'].get('from') or '').lower(),"to":(x['result'].get('to') or '').lower()}
    time.sleep(1.0)
    # feeRedirects on both lockers
    calls=[]
    for a in chunk:
        for L in LOCKERS: calls.append((a,L))
    r3=call([{"jsonrpc":"2.0","id":j,"method":"eth_call","params":[{"to":L,"data":SEL_FEE+a[2:].rjust(64,'0')},"latest"]} for j,(a,L) in enumerate(calls)])
    fee={}
    for x in (r3 or []):
        res=x.get('result')
        if res and len(res)>=66 and int(res,16)!=0:
            a,L=calls[x['id']]; fee[a]="0x"+res[-40:]
    time.sleep(1.0)
    for a in chunk:
        m=minttx.get(a,{}); t=frm.get(m.get('tx'),{})
        out[a]={"mint_tx":m.get('tx'),"mint_block":m.get('block'),"mint_to":m.get('to'),"deployer":t.get('from'),"factory":t.get('to'),"fee_recipient":fee.get(a)}
    json.dump(out,open(out_f,'w'))
    if (i//10)%20==0: print(i,"/",len(todo),file=sys.stderr,flush=True)
print("DONE",len(out),file=sys.stderr)
